import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../backend/services/video_downloader_service.dart';
import '../../backend/models/video_info.dart' as models;

// Events
abstract class DownloadEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class DownloadVideoRequested extends DownloadEvent {
  final String url;
  DownloadVideoRequested(this.url);
  
  @override
  List<Object?> get props => [url];
}

// States
abstract class DownloadState extends Equatable {
  @override
  List<Object?> get props => [];
}

class DownloadInitial extends DownloadState {}

class DownloadInProgress extends DownloadState {
  final double progress;
  DownloadInProgress(this.progress);
  
  @override
  List<Object?> get props => [progress];
}

class DownloadSuccess extends DownloadState {
  final models.VideoInfo videoInfo;
  DownloadSuccess(this.videoInfo);
  
  @override
  List<Object?> get props => [videoInfo];
}

class DownloadFailure extends DownloadState {
  final String error;
  DownloadFailure(this.error);
  
  @override
  List<Object?> get props => [error];
}

// BLoC
class DownloadBloc extends Bloc<DownloadEvent, DownloadState> {
  final VideoDownloaderService _downloaderService;

  DownloadBloc(this._downloaderService) : super(DownloadInitial()) {
    on<DownloadVideoRequested>(_onDownloadRequested);
  }

  Future<void> _onDownloadRequested(
    DownloadVideoRequested event,
    Emitter<DownloadState> emit,
  ) async {
    try {
      emit(DownloadInProgress(0.0));
      
      // Simular progresso
      for (var i = 1; i <= 5; i++) {
        await Future.delayed(const Duration(milliseconds: 500));
        emit(DownloadInProgress(i / 5));
      }
      
      // Download real
      final videoInfo = await _downloaderService.downloadVideo(event.url);
      emit(DownloadSuccess(videoInfo));
    } catch (e) {
      emit(DownloadFailure(e.toString()));
    }
  }
}
