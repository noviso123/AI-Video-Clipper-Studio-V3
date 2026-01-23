import 'package:flutter/cupertino.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/download_bloc.dart';
import '../../backend/services/video_downloader_service.dart';
import 'processing_screen.dart';

/// Tela inicial - Input de URL
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _urlController = TextEditingController();

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _processVideo(BuildContext context) async {
    if (_urlController.text.isEmpty) {
      _showAlert('Erro', 'Por favor, cole a URL do vídeo');
      return;
    }

    // Navegar para ProcessingScreen
    if (!mounted) return;
    Navigator.push(
      context,
      CupertinoPageRoute(
        builder: (context) => ProcessingScreen(videoUrl: _urlController.text),
      ),
    );
  }

  void _showAlert(String title, String message) {
    showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          CupertinoDialogAction(
            isDefaultAction: true,
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => DownloadBloc(VideoDownloaderService()),
      child: BlocListener<DownloadBloc, DownloadState>(
        listener: (context, state) {
          if (state is DownloadFailure) {
            _showAlert('Erro', state.error);
          }
        },
        child: BlocBuilder<DownloadBloc, DownloadState>(
          builder: (context, state) {
            final isProcessing = state is DownloadInProgress;

            return CupertinoPageScaffold(
              navigationBar: const CupertinoNavigationBar(
                middle: Text('AI Video Clipper'),
                backgroundColor: CupertinoColors.black,
              ),
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        CupertinoIcons.video_camera_solid,
                        size: 80,
                        color: CupertinoColors.systemBlue,
                      ),
                      const SizedBox(height: 30),
                      const Text(
                        'Cole a URL do vídeo',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 20),
                      CupertinoTextField(
                        controller: _urlController,
                        placeholder: 'https://youtube.com/watch?v=...',
                        prefix: const Padding(
                          padding: EdgeInsets.only(left: 8.0),
                          child: Icon(CupertinoIcons.link, size: 20),
                        ),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: CupertinoColors.darkBackgroundGray,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        keyboardType: TextInputType.url,
                        textInputAction: TextInputAction.done,
                        maxLines: 3,
                        minLines: 1,
                        enabled: !isProcessing,
                      ),
                      const SizedBox(height: 30),
                      SizedBox(
                        width: double.infinity,
                        child: CupertinoButton.filled(
                          onPressed: isProcessing ? null : () => _processVideo(context),
                          child: isProcessing
                              ? const CupertinoActivityIndicator(color: CupertinoColors.white)
                              : const Text('Processar Vídeo'),
                        ),
                      ),
                      const SizedBox(height: 20),
                      const Text(
                        '✅ 100% Offline\n🚀 Otimizado para iPhone 16E',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 14,
                          color: CupertinoColors.systemGrey,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
