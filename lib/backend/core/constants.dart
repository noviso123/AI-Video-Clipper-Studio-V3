/// Constantes de configuração offline
class AppConstants {
  // Viral Analysis Thresholds
  static const double viralScoreThreshold = 70.0;
  static const int maxViralMoments = 5;
  static const double minClipDuration = 3.0;
  static const double maxClipDuration = 60.0;
  
  // Palavras-chave virais (PT-BR)
  static const List<String> viralKeywords = [
    'como', 'melhor', 'pior', 'incrível', 'nunca',
    'segredo', 'truque', 'hack', 'dica', 'atenção',
    'cuidado', 'erro', 'funciona', 'resultado', 'prova',
    'descubra', 'aprenda', 'veja', 'assista', 'imperdível'
  ];
  
  // Video Processing
  static const int targetWidth = 1080;
  static const int targetHeight = 1920;  // 9:16
  static const int targetFPS = 30;
  static const String videoCodec = 'h264';
  static const String audioCodec = 'aac';
  
  // Face Detection (para Neural Engine)
  static const double minFaceSize = 0.1;
  static const double faceDetectionInterval = 0.5;  // segundos
  
  // Audio Analysis
  static const int audioSampleRate = 44100;
  static const double audioRMSThreshold = 500.0;
  
  // Storage
  static const String tempFolderName = 'temp_videos';
  static const String exportFolderName = 'ai_video_clipper';
}
