import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

// Events
abstract class ExportEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class ExportStarted extends ExportEvent {
  final String videoPath;
  ExportStarted(this.videoPath);
  
  @override
  List<Object?> get props => [videoPath];
}

// States
abstract class ExportState extends Equatable {
  @override
  List<Object?> get props => [];
}

class ExportInitial extends ExportState {}

class ExportInProgress extends ExportState {
  final double progress;
  ExportInProgress(this.progress);
  
  @override
  List<Object?> get props => [progress];
}

class ExportSuccess extends ExportState {
  final String exportedPath;
  ExportSuccess(this.exportedPath);
  
  @override
  List<Object?> get props => [exportedPath];
}

class ExportFailure extends ExportState {
  final String error;
  ExportFailure(this.error);
  
  @override
  List<Object?> get props => [error];
}

// BLoC
class ExportBloc extends Bloc<ExportEvent, ExportState> {
  ExportBloc() : super(ExportInitial()) {
    on<ExportStarted>(_onExportStarted);
  }

  Future<void> _onExportStarted(
    ExportStarted event,
    Emitter<ExportState> emit,
  ) async {
    try {
      emit(ExportInProgress(0.0));
      
      // Simular exportação
      for (var i = 1; i <= 10; i++) {
        await Future.delayed(const Duration(milliseconds: 300));
        emit(ExportInProgress(i / 10));
      }
      
      // TODO: Salvar na galeria usando gal (Gal.putVideo(path))
      emit(ExportSuccess('/path/to/exported/video.mp4'));
    } catch (e) {
      emit(ExportFailure(e.toString()));
    }
  }
}
