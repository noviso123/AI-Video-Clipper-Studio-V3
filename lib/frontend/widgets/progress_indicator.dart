import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

/// Widget de progresso circular customizado
class ProgressIndicator extends StatelessWidget {
  final double progress;
  final String label;
  final double size;

  const ProgressIndicator({
    super.key,
    required this.progress,
    required this.label,
    this.size = 120,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Background circle
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator.adaptive(
                  value: 1.0,
                  strokeWidth: 8,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    CupertinoColors.darkBackgroundGray,
                  ),
                ),
              ),
              
              // Progress circle
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator.adaptive(
                  value: progress,
                  strokeWidth: 8,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    CupertinoColors.systemBlue,
                  ),
                ),
              ),
              
              // Percentage text
              Text(
                '${(progress * 100).toInt()}%',
                style: TextStyle(
                  fontSize: size * 0.2,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            color: CupertinoColors.systemGrey,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
