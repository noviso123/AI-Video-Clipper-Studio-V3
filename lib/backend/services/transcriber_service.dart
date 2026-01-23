import 'package:flutter/services.dart';
import '../models/transcript_segment.dart';
import 'dart:io';

/// Service para transcrição de áudio usando Speech Framework iOS
class TranscriberService {
  // bool _isInitialized = false; // Não necessário via MethodChannel

  /// Inicializa o Speech Framework (Nativo tratada no Swift)
  Future<bool> initialize() async {
    return true; 
  }

  static const platform = MethodChannel('com.videoclipper.ai/transcriber');

  /// Transcreve arquivo de áudio completo usando Speech Framework nativo
  Future<List<TranscriptSegment>> transcribeAudio(String audioPath) async {
    try {
      if (Platform.isIOS) {
        // Chamada nativa para iOS
        final result = await platform.invokeMethod('transcribeAudio', {
          'audioPath': audioPath,
        });

        if (result != null && result is Map) {
          final segmentsData = result['segments'] as List? ?? [];
          
          return segmentsData.map((data) {
            final segmentMap = Map<String, dynamic>.from(data as Map);
            return TranscriptSegment(
              startTime: (segmentMap['startTime'] as num).toDouble(),
              endTime: (segmentMap['startTime'] as num).toDouble() + (segmentMap['duration'] as num).toDouble(),
              text: segmentMap['text'] as String,
              confidence: (segmentMap['confidence'] as num).toDouble(),
            );
          }).toList();
        }
      } 
      
      // Fallback ou Android (não implementado nativamente ainda)
      print('⚠️ Transcrição nativa não disponível ou retornou nulo');
      return [];
      
    } catch (e) {
      print('Erro na transcrição nativa: $e');
      return [];
    }
  }

  /// Verifica se o dispositivo suporta transcrição offline
  Future<bool> isOfflineAvailable() async {
    // No iOS com Speech Framework, geralmente suporta se tiver internet ou dictation pack
    // Retornamos true por padrão pois gerenciamos falhas no Swift
    return true;
  }

  void dispose() {
    // Nada para descartar no lado Dart
  }
}
