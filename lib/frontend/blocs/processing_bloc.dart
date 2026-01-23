import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../backend/models/viral_moment.dart';

// Events
abstract class ProcessingEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class ProcessingStarted extends ProcessingEvent {
  final String videoPath;
  ProcessingStarted(this.videoPath);
  
  @override
  List<Object?> get props => [videoPath];
}

// States
abstract class ProcessingState extends Equatable {
  @override
  List<Object?> get props => [];
}

class ProcessingInitial extends ProcessingState {}

class ProcessingInProgress extends ProcessingState {
  final String currentStep;
  final double progress;
  
  ProcessingInProgress(this.currentStep, this.progress);
  
  @override
  List<Object?> get props => [currentStep, progress];
}

class ProcessingSuccess extends ProcessingState {
  final List<ViralMoment> viralMoments;
  ProcessingSuccess(this.viralMoments);
  
  @override
  List<Object?> get props => [viralMoments];
}

class ProcessingFailure extends ProcessingState {
  final String error;
  ProcessingFailure(this.error);
  
  @override
  List<Object?> get props => [error];
}

// BLoC
class ProcessingBloc extends Bloc<ProcessingEvent, ProcessingState> {
  ProcessingBloc() : super(ProcessingInitial()) {
    on<ProcessingStarted>(_onProcessingStarted);
  }

  Future<void> _onProcessingStarted(
    ProcessingStarted event,
    Emitter<ProcessingState> emit,
  ) async {
    try {
      // Etapa 1: Transcrição
      emit(ProcessingInProgress('Transcrevendo áudio...', 0.2));
      await Future.delayed(const Duration(seconds: 2));
      
      // Etapa 2: Detecção de rostos
      emit(ProcessingInProgress('Detectando rostos...', 0.4));
      await Future.delayed(const Duration(seconds: 2));
      
      // Etapa 3: Análise viral
      emit(ProcessingInProgress('Analisando momentos virais...', 0.6));
      await Future.delayed(const Duration(seconds: 2));
      
      // Etapa 4: Edição
      emit(ProcessingInProgress('Editando clips...', 0.8));
      await Future.delayed(const Duration(seconds: 2));
      
      // Resultado (mock)
      final viralMoments = [
        ViralMoment(
          startTime: 10.0,
          endTime: 18.0,
          viralScore: 95.0,
          hook: 'INCRÍVEL descoberta!',
          context: 'Momento viral de alto impacto',
          detectedKeywords: ['incrível', 'descoberta'],
          hasFaces: true,
          faceCount: 2,
        ),
      ];
      
      emit(ProcessingSuccess(viralMoments));
    } catch (e) {
      emit(ProcessingFailure(e.toString()));
    }
  }
}
