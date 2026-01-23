import 'package:equatable/equatable.dart';

/// Representa um momento viral detectado
class ViralMoment extends Equatable {
  final double startTime;
  final double endTime;
  final double viralScore;
  final String hook;
  final String context;
  final List<String> detectedKeywords;
  final bool hasFaces;
  final int faceCount;
  
  const ViralMoment({
    required this.startTime,
    required this.endTime,
    required this.viralScore,
    required this.hook,
    required this.context,
    this.detectedKeywords = const [],
    this.hasFaces = false,
    this.faceCount = 0,
  });
  
  double get duration => endTime - startTime;
  
  @override
  List<Object?> get props => [
    startTime,
    endTime,
    viralScore,
    hook,
    context,
    detectedKeywords,
    hasFaces,
    faceCount,
  ];
  
  @override
  String toString() => 'ViralMoment(${startTime}s-${endTime}s, score: $viralScore)';
}
