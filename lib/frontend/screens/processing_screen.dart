import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/processing_bloc.dart';
import 'preview_screen.dart';

/// Tela de processamento com progresso em tempo real
class ProcessingScreen extends StatefulWidget {
  final String videoUrl;
  
  const ProcessingScreen({super.key, required this.videoUrl});

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {

  void _showError(String message) {
    showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: const Text('Erro'),
        content: Text(message),
        actions: [
          CupertinoDialogAction(
            child: const Text('OK'),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => ProcessingBloc()..add(ProcessingStarted(widget.videoUrl)),
      child: BlocListener<ProcessingBloc, ProcessingState>(
        listener: (context, state) {
          if (state is ProcessingSuccess) {
            // Navegar para PreviewScreen quando terminar
            Navigator.pushReplacement(
              context,
              CupertinoPageRoute(builder: (context) => const PreviewScreen()),
            );
          } else if (state is ProcessingFailure) {
            _showError(state.error);
          }
        },
        child: BlocBuilder<ProcessingBloc, ProcessingState>(
          builder: (context, state) {
            String currentStep = 'Iniciando...';
            double progress = 0.0;
            bool isProcessing = true;

            if (state is ProcessingInProgress) {
              currentStep = state.currentStep;
              progress = state.progress;
            } else if (state is ProcessingSuccess) {
              currentStep = 'Concluído!';
              progress = 1.0;
              isProcessing = false;
            }

            return CupertinoPageScaffold(
              navigationBar: const CupertinoNavigationBar(
                middle: Text('Processando'),
                backgroundColor: CupertinoColors.black,
              ),
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (isProcessing)
                        const CupertinoActivityIndicator(
                          radius: 40,
                          color: CupertinoColors.systemBlue,
                        )
                      else
                        const Icon(
                          CupertinoIcons.check_mark_circled_solid,
                          size: 80,
                          color: CupertinoColors.systemGreen,
                        ),
                      
                      const SizedBox(height: 40),
                      
                      Text(
                        currentStep,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      
                      const SizedBox(height: 30),
                      
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: LinearProgressIndicator(
                          value: progress,
                          minHeight: 10,
                          backgroundColor: CupertinoColors.darkBackgroundGray,
                          valueColor: const AlwaysStoppedAnimation<Color>(
                            CupertinoColors.systemBlue,
                          ),
                        ),
                      ),
                      
                      const SizedBox(height: 10),
                      
                      Text(
                        '${(progress * 100).toInt()}%',
                        style: const TextStyle(
                          fontSize: 16,
                          color: CupertinoColors.systemGrey,
                        ),
                      ),
                      
                      const SizedBox(height: 40),
                      
                      if (isProcessing)
                        CupertinoButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Cancelar'),
                        )
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
