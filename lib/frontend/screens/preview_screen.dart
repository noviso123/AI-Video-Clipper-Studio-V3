import 'package:flutter/cupertino.dart';
import 'package:video_player/video_player.dart';
import 'dart:io';
import '../../backend/services/social_share_service.dart';

/// Tela de preview de clips gerados
class PreviewScreen extends StatefulWidget {
  const PreviewScreen({super.key});

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  final List<Map<String, dynamic>> _clips = [
    {
      'title': 'Clip Viral #1',
      'duration': '0:08',
      'score': 95,
      'thumbnail': null,
    },
    {
      'title': 'Clip Viral #2',
      'duration': '0:12',
      'score': 87,
      'thumbnail': null,
    },
    {
      'title': 'Clip Viral #3',
      'duration': '0:06',
      'score': 82,
      'thumbnail': null,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: CupertinoNavigationBar(
        middle: const Text('Clips Gerados'),
        backgroundColor: CupertinoColors.black,
        trailing: CupertinoButton(
          padding: EdgeInsets.zero,
          child: const Icon(CupertinoIcons.share),
          onPressed: _shareAll,
        ),
      ),
      child: SafeArea(
        child: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: _clips.length,
          itemBuilder: (context, index) {
            final clip = _clips[index];
            return _buildClipCard(clip, index);
          },
        ),
      ),
    );
  }

  Widget _buildClipCard(Map<String, dynamic> clip, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: CupertinoColors.darkBackgroundGray,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thumbnail placeholder
            Container(
              height: 200,
              width: double.infinity,
              color: CupertinoColors.systemGrey,
              child: const Center(
                child: Icon(
                  CupertinoIcons.play_circle,
                  size: 60,
                  color: CupertinoColors.white,
                ),
              ),
            ),
            
            // Info
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        clip['title'],
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: _getScoreColor(clip['score']),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '${clip['score']}',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: CupertinoColors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Duração: ${clip['duration']}',
                    style: const TextStyle(
                      fontSize: 14,
                      color: CupertinoColors.systemGrey,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Botões de ação
                  Row(
                    children: [
                      Expanded(
                        child: CupertinoButton(
                          padding: EdgeInsets.zero,
                          color: CupertinoColors.systemBlue,
                          borderRadius: BorderRadius.circular(8),
                          onPressed: () => _playClip(index),
                          child: const Text('Reproduzir'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: CupertinoButton(
                          padding: EdgeInsets.zero,
                          color: CupertinoColors.systemGreen,
                          borderRadius: BorderRadius.circular(8),
                          onPressed: () => _shareClip(index),
                          child: const Text('Compartilhar'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 90) return CupertinoColors.systemGreen;
    if (score >= 80) return CupertinoColors.systemBlue;
    if (score >= 70) return CupertinoColors.systemOrange;
    return CupertinoColors.systemRed;
  }

  // No class state
  VideoPlayerController? _videoController;

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  void _playClip(int index) {
      // Simulação de path
      final mockPath = '/path/to/generated/clip.mp4'; 
      // Em app real: final path = _clips[index]['path'];
      
      _videoController?.dispose();
      _videoController = VideoPlayerController.file(File(mockPath))
        ..initialize().then((_) {
          setState(() {});
          _videoController!.play();
          _showVideoDialog();
        });
  }

  void _showVideoDialog() {
    showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        content: AspectRatio(
          aspectRatio: _videoController!.value.aspectRatio,
          child: VideoPlayer(_videoController!),
        ),
        actions: [
          CupertinoDialogAction(
            child: const Text('Fechar'),
            onPressed: () {
              _videoController?.pause();
              Navigator.pop(context);
            },
          ),
        ],
      ),
    );
  }

  void _shareClip(int index) async {
    // Simulação de path (no app real viria do clip['path'])
    final mockPath = '/path/to/generated/clip.mp4'; 
    
    final shareService = SocialShareService();
    // await shareService.shareVideo(mockPath, text: _clips[index]['title']);
    print('Sharing ${_clips[index]['title']}');
    
    // Mostra opções de compartilhamento
    if (!mounted) return;
    showCupertinoModalPopup(
      context: context,
      builder: (context) => CupertinoActionSheet(
        title: const Text('Compartilhar Clip'),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.pop(context);
              shareService.shareVideo(mockPath, text: _clips[index]['title']);
            },
            child: const Text('Share Sheet (iOS Nativo)'),
          ),
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.pop(context);
              shareService.shareToInstagram(mockPath);
            },
            child: const Text('Abrir Instagram'),
          ),
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.pop(context);
              shareService.shareToTikTok(mockPath);
            },
            child: const Text('Abrir TikTok'),
          ),
        ],
        cancelButton: CupertinoActionSheetAction(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
      ),
    );
  }

  void _shareAll() {
    print('Share all clips');
  }
}
