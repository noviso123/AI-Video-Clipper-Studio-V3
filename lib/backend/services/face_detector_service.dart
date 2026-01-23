import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:flutter/services.dart';
import 'dart:io';

/// Service para detecção de rostos usando Vision API (Neural Engine)
class FaceDetectorService {
  late final FaceDetector _faceDetector;
  bool _isInitialized = false;

  /// Inicializa o detector de rostos
  Future<void> initialize() async {
    if (_isInitialized) return;

    final options = FaceDetectorOptions(
      enableClassification: false,
      enableContours: false,
      enableTracking: true,          // Tracking para performance
      minFaceSize: 0.1,               // Rostos mínimos 10% do frame
      performanceMode: FaceDetectorMode.accurate, // Usa Neural Engine
    );

    _faceDetector = FaceDetector(options: options);
    _isInitialized = true;
  }

  /// Detecta rostos em um frame de vídeo
  Future<List<Face>> detectFacesInImage(String imagePath) async {
    if (!_isInitialized) await initialize();

    try {
      final inputImage = InputImage.fromFilePath(imagePath);
      final faces = await _faceDetector.processImage(inputImage);
      return faces;
    } catch (e) {
      print('Erro na detecção de rostos: $e');
      return [];
    }
  }

  /// Analisa vídeo completo e retorna mapa de rostos por timestamp
  /// timestamp -> quantidade de rostos
  Future<Map<double, int>> analyzeVideoForFaces(
    String videoPath, {
    double sampleInterval = 0.5, // Analisar 1 frame a cada 0.5s
  }) async {
    final faceCountByTime = <double, int>{};

    try {
      // 1. Extrair frames usando Platform Channel nativo
      const platform = MethodChannel('com.videoclipper.ai/video_processor');
      final List<dynamic>? framePaths = await platform.invokeMethod('extractFrames', {
        'videoPath': videoPath,
        'interval': sampleInterval,
      });

      if (framePaths == null || framePaths.isEmpty) {
        print('⚠️ Nenhum frame extraído do vídeo');
        return faceCountByTime;
      }

      // 2. Analisar cada frame extraído
      for (int i = 0; i < framePaths.length; i++) {
        final String framePath = framePaths[i] as String;
        final double timestamp = i * sampleInterval;

        final faces = await detectFacesInImage(framePath);
        if (faces.isNotEmpty) {
          faceCountByTime[timestamp] = faces.length;
        }

        // Limpar arquivo temporário do frame para economizar espaço
        try {
          await File(framePath).delete();
        } catch (_) {}
      }
      
      return faceCountByTime;
    } catch (e) {
      print('Erro ao analisar vídeo: $e');
      return faceCountByTime;
    }
  }

  /// Retorna dados estruturados de rostos detectados
  Map<String, dynamic> getFaceData(Face face) {
    final boundingBox = face.boundingBox;
    
    return {
      'x': boundingBox.left,
      'y': boundingBox.top,
      'width': boundingBox.width,
      'height': boundingBox.height,
      'center_x': boundingBox.left + (boundingBox.width / 2),
      'center_y': boundingBox.top + (boundingBox.height / 2),
      'area': boundingBox.width * boundingBox.height,
      'tracking_id': face.trackingId,
    };
  }

  void dispose() {
    if (_isInitialized) {
      _faceDetector.close();
    }
  }
}
