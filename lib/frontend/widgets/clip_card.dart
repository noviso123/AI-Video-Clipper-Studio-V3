import 'package:flutter/cupertino.dart';

/// Widget de card customizado para clips
class ClipCard extends StatelessWidget {
  final String title;
  final String duration;
  final int score;
  final VoidCallback onPlay;
  final VoidCallback onShare;

  const ClipCard({
    super.key,
    required this.title,
    required this.duration,
    required this.score,
    required this.onPlay,
    required this.onShare,
  });

  @override
  Widget build(BuildContext context) {
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
              height: 180,
              width: double.infinity,
              color: CupertinoColors.systemGrey,
              child: const Center(
                child: Icon(
                  CupertinoIcons.play_circle,
                  size: 50,
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
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      _ScoreBadge(score: score),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    duration,
                    style: const TextStyle(
                      fontSize: 14,
                      color: CupertinoColors.systemGrey,
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Botões
                  Row(
                    children: [
                      Expanded(
                        child: CupertinoButton(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          color: CupertinoColors.systemBlue,
                          borderRadius: BorderRadius.circular(8),
                          onPressed: onPlay,
                          child: const Text('Reproduzir', style: TextStyle(fontSize: 14)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: CupertinoButton(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          color: CupertinoColors.systemGreen,
                          borderRadius: BorderRadius.circular(8),
                          onPressed: onShare,
                          child: const Text('Compartilhar', style: TextStyle(fontSize: 14)),
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
}

class _ScoreBadge extends StatelessWidget {
  final int score;

  const _ScoreBadge({required this.score});

  @override
  Widget build(BuildContext context) {
    Color color;
    if (score >= 90) {
      color = CupertinoColors.systemGreen;
    } else if (score >= 80) {
      color = CupertinoColors.systemBlue;
    } else if (score >= 70) {
      color = CupertinoColors.systemOrange;
    } else {
      color = CupertinoColors.systemRed;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '$score',
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: CupertinoColors.white,
        ),
      ),
    );
  }
}
