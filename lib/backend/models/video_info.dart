import 'package:equatable/equatable.dart';

/// Modelo de dados para informações do vídeo
class VideoInfo extends Equatable {
  final String id;
  final String title;
  final String url;
  final String? localPath;
  final int durationSeconds;
  final String? thumbnailUrl;
  
  const VideoInfo({
    required this.id,
    required this.title,
    required this.url,
    this.localPath,
    required this.durationSeconds,
    this.thumbnailUrl,
  });
  
  VideoInfo copyWith({
    String? id,
    String? title,
    String? url,
    String? localPath,
    int? durationSeconds,
    String? thumbnailUrl,
  }) {
    return VideoInfo(
      id: id ?? this.id,
      title: title ?? this.title,
      url: url ?? this.url,
      localPath: localPath ?? this.localPath,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
    );
  }
  
  @override
  List<Object?> get props => [id, title, url, localPath, durationSeconds, thumbnailUrl];
}
