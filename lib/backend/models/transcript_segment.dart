import 'package:equatable/equatable.dart';

/// Segmento de transcrição de áudio
class TranscriptSegment extends Equatable {
  final double startTime;
  final double endTime;
  final String text;
  final double confidence;
  
  const TranscriptSegment({
    required this.startTime,
    required this.endTime,
    required this.text,
    required this.confidence,
  });
  
  double get duration => endTime - startTime;
  
  @override
  List<Object?> get props => [startTime, endTime, text, confidence];
}
