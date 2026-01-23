import '../models/viral_moment.dart';
import '../models/transcript_segment.dart';
import '../core/constants.dart';

/// Service para análise viral offline (regras heurísticas)
class ViralAnalyzer {
  
  /// Analisa segmentos e retorna momentos virais
  List<ViralMoment> analyzeSegments(
    List<TranscriptSegment> segments, {
    Map<double, int>? faceCountByTime,
  }) {
    final viralMoments = <ViralMoment>[];

    for (final segment in segments) {
      final score = _calculateViralScore(segment, faceCountByTime);
      
      if (score >= AppConstants.viralScoreThreshold) {
        viralMoments.add(ViralMoment(
          startTime: segment.startTime,
          endTime: segment.endTime,
          viralScore: score,
          hook: _extractHook(segment.text),
          context: segment.text,
          detectedKeywords: _findKeywords(segment.text),
          hasFaces: _hasFacesAtTime(segment.startTime, faceCountByTime),
          faceCount: _getFaceCount(segment.startTime, faceCountByTime),
        ));
      }
    }

    // Ordenar por score e retornar top momentos
    viralMoments.sort((a, b) => b.viralScore.compareTo(a.viralScore));
    return viralMoments.take(AppConstants.maxViralMoments).toList();
  }

  /// Calcula score viral de um segmento
  double _calculateViralScore(
    TranscriptSegment segment,
    Map<double, int>? faceCountByTime,
  ) {
    double score = 0.0;

    // 1. Palavras gatilho (30 pontos)
    score += _scoreKeywords(segment.text);

    // 2. Densidade de rostos (25 pontos)
    final faceCount = _getFaceCount(segment.startTime, faceCountByTime);
    score += (faceCount * 5.0).clamp(0, 25);

    // 3. Duração ideal (15 pontos)
    if (segment.duration >= 3.0 && segment.duration <= 7.0) {
      score += 15.0;
    } else if (segment.duration >= 7.0 && segment.duration <= 15.0) {
      score += 10.0;
    }

    // 4. Confiança da transcrição (10 pontos)
    score += segment.confidence * 10.0;

    // 5. Comprimento do texto (10 pontos)
    final wordCount = segment.text.split(' ').length;
    if (wordCount >= 5 && wordCount <= 20) {
      score += 10.0;
    }

    // 6. Pontuação/Exclamação (10 pontos)
    if (segment.text.contains('!') || segment.text.contains('?')) {
      score += 10.0;
    }

    return score.clamp(0, 100);
  }

  /// Score baseado em palavras-chave virais
  double _scoreKeywords(String text) {
    final lowerText = text.toLowerCase();
    int matches = 0;

    for (final keyword in AppConstants.viralKeywords) {
      if (lowerText.contains(keyword)) {
        matches++;
      }
    }

    return (matches * 6.0).clamp(0, 30);
  }

  /// Extrai hook (primeira frase ou primeiras palavras)
  String _extractHook(String text) {
    final sentences = text.split(RegExp(r'[.!?]'));
    if (sentences.isNotEmpty && sentences.first.length > 5) {
      return sentences.first.trim();
    }
    
    final words = text.split(' ');
    if (words.length > 10) {
      return '${words.take(10).join(' ')}...';
    }
    
    return text;
  }

  /// Encontra palavras-chave no texto
  List<String> _findKeywords(String text) {
    final lowerText = text.toLowerCase();
    return AppConstants.viralKeywords
        .where((keyword) => lowerText.contains(keyword))
        .toList();
  }

  /// Verifica se há rostos no timestamp
  bool _hasFacesAtTime(double time, Map<double, int>? faceCountByTime) {
    if (faceCountByTime == null) return false;
    
    // Buscar timestamp mais próximo
    final closestTime = faceCountByTime.keys
        .reduce((a, b) => (a - time).abs() < (b - time).abs() ? a : b);
    
    return (faceCountByTime[closestTime] ?? 0) > 0;
  }

  /// Retorna quantidade de rostos no timestamp
  int _getFaceCount(double time, Map<double, int>? faceCountByTime) {
    if (faceCountByTime == null) return 0;
    
    final closestTime = faceCountByTime.keys
        .reduce((a, b) => (a - time).abs() < (b - time).abs() ? a : b);
    
    return faceCountByTime[closestTime] ?? 0;
  }
}
