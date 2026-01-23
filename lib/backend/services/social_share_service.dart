import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:gal/gal.dart';
import 'package:flutter/services.dart';

class SocialShareService {
  
  /// Compartilha o arquivo de vídeo usando o Share Sheet nativo do iOS
  Future<void> shareVideo(String videoPath, {String? text}) async {
    final xFile = XFile(videoPath);
    await Share.shareXFiles([xFile], text: text);
  }

  /// Tenta abrir o Instagram para compartilhar (Deep Link)
  /// Note: O Instagram não suporta envio direto de arquivo via URL scheme.
  /// O fluxo correto no iOS é salvar na galeria e abrir o Instagram para o usuário postar.
  Future<void> shareToInstagram(String videoPath) async {
    // 1. Salvar na galeria
    await Gal.putVideo(videoPath);
    
    // 2. Abrir Instagram
    final Uri url = Uri.parse('instagram://library?AssetPath=$videoPath');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      // Fallback: abrir apenas o app
      final Uri webUrl = Uri.parse('https://instagram.com');
      await launchUrl(webUrl, mode: LaunchMode.externalApplication);
    }
  }

  /// Tenta abrir o TikTok (Deep Link)
  Future<void> shareToTikTok(String videoPath) async {
    await Gal.putVideo(videoPath);
    
    final Uri url = Uri.parse('tiktok://share');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      final Uri webUrl = Uri.parse('https://tiktok.com');
      await launchUrl(webUrl, mode: LaunchMode.externalApplication);
    }
  }

  /// Copia hashtags virais para a área de transferência
  Future<void> copyHashtags(String hashtags) async {
    await Clipboard.setData(ClipboardData(text: hashtags));
  }

}
