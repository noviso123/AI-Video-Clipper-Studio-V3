import 'package:youtube_explode_dart/youtube_explode_dart.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import '../models/video_info.dart' as models;

/// Service para download de vídeos do YouTube (offline storage)
class VideoDownloaderService {
  final YoutubeExplode _yt = YoutubeExplode();

  /// Baixa vídeo do YouTube e retorna informações
  Future<models.VideoInfo> downloadVideo(String url) async {
    try {
      // 1. Extrair informações do vídeo
      final video = await _yt.videos.get(url);
      
      // 2. Obter melhor stream de vídeo (1080p ou menor)
      final manifest = await _yt.videos.streamsClient.getManifest(video.id);
      
      // Ordenar manualmente por qualidade (resolução/bitrate)
      final streams = manifest.muxed.toList();
      streams.sort((a, b) => compareVideoQuality(a, b));
      final streamInfo = streams.last;
      
      // streams.last lança erro se vazio, então check explícito:
      if (streams.isEmpty) {
        throw Exception('Nenhum stream de vídeo disponível');
      }

      // 3. Preparar diretório temporário
      final tempDir = await getTemporaryDirectory();
      final videoPath = '${tempDir.path}/${video.id.value}.mp4';
      final videoFile = File(videoPath);

      // 4. Download do vídeo
      final videoStream = _yt.videos.streamsClient.get(streamInfo);
      final output = videoFile.openWrite();
      
      await for (final chunk in videoStream) {
        output.add(chunk);
      }
      await output.flush();
      await output.close();

      // 5. Retornar informações
      return models.VideoInfo(
        id: video.id.value,
        title: video.title,
        url: url,
        localPath: videoPath,
        durationSeconds: video.duration?.inSeconds ?? 0,
        thumbnailUrl: video.thumbnails.highResUrl,
      );
    } catch (e) {
      rethrow;
    }
  }

  /// Download apenas do áudio (para transcrição)
  Future<String> downloadAudio(String videoId) async {
    try {
      final manifest = await _yt.videos.streamsClient.getManifest(videoId);
      final manifest = await _yt.videos.streamsClient.getManifest(videoId);
      final audioStream = manifest.audioOnly.withHighestBitrate();
      
      if (audioStream == null) {
        throw Exception('Nenhum stream de áudio disponível');
      }

      final tempDir = await getTemporaryDirectory();
      final audioPath = '${tempDir.path}/${videoId}_audio.m4a';
      final audioFile = File(audioPath);

      final stream = _yt.videos.streamsClient.get(audioStream);
      final output = audioFile.openWrite();
      
      await for (final chunk in stream) {
        output.add(chunk);
      }
      await output.flush();
      await output.close();

      return audioPath;
    } catch (e) {
      rethrow;
    }
  }

  int compareVideoQuality(MuxedStreamInfo a, MuxedStreamInfo b) {
    return a.bitrate.compareTo(b.bitrate);
  }

  void dispose() {
    _yt.close();
  }
}
