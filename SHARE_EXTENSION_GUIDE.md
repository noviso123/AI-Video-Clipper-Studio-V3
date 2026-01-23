# Publicação Nativa iOS - Share Extension

Esta documentação explica a nova abordagem de publicação de vídeos diretamente do iPhone usando compartilhamento nativo do iOS.

## 🎯 Por Que Abandonamos Selenium/Automação Desktop?

A abordagem anterior (Python/Linux) utilizava:
- ❌ Selenium para controle de navegador
- ❌ ChromeDriver/undetected-chromedriver
- ❌ Scripts de login manual (Instagram, TikTok, YouTube)
- ❌ Browser profiles persistentes
- ❌ Cookies/sessões

**Problemas:**
1. Não funciona no iOS (sem navegadores completos)
2. Alto uso de memória e CPU
3. Quebra frequentemente (mudanças nas UIs dos sites)
4. Requer manutenção constante

---

## ✅ Nova Abordagem: iOS Native Share

### Conceito

Em vez de automatizar navegadores, o app **delega a publicação ao próprio iOS** usando:

1. **Share Sheet** - Interface nativa de compartilhamento
2. **App Extensions** - Apps nativos de redes sociais
3. **Direct Share** - Integração profunda com apps instalados

---

## 📱 Implementação Flutter

### 1. Básico - Share Sheet

```dart
import 'package:share_plus/share_plus.dart';

Future<void> shareVideo(String videoPath) async {
  try {
    final result = await Share.shareXFiles(
      [XFile(videoPath)],
      text: 'Vídeo criado com AI Video Clipper',
      subject: 'Meu Viral! 🔥',
    );

    if (result.status == ShareResultStatus.success) {
      print('✅ Vídeo compartilhado!');
    }
  } catch (e) {
    print('❌ Erro ao compartilhar: $e');
  }
}
```

**O que acontece:**
- iOS abre o Share Sheet nativo
- Usuário escolhe Instagram/TikTok/YouTube/WhatsApp
- App destino recebe o vídeo DIRETO
- Usuário adiciona legenda/hashtags manualmente no app

**Vantagens:**
- ✅ Zero configuração
- ✅ Funciona com QUALQUER app instalado
- ✅ Nativo e rápido
- ✅ Sem risco de ban/quebra

---

### 2. Avançado - Direct Share para Apps Específicos

#### Instagram Stories

```dart
import 'package:url_launcher/url_launcher.dart';

Future<void> shareToInstagramStories(String videoPath) async {
  // Instagram aceita URL scheme
  final uri = Uri.parse('instagram://sharesheet');
  
  if (await canLaunchUrl(uri)) {
    // Copiar vídeo para pasteboard
    // Instagram pega automaticamente
    await launchUrl(uri);
  } else {
    // Instagram não instalado
    print('Instagram não encontrado');
  }
}
```

#### TikTok

```dart
Future<void> shareToTikTok(String videoPath) async {
  // TikTok tem SDK oficial para iOS
  // Requer configuração no Info.plist
  final uri = Uri.parse('tiktokopensdk://');
  
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri);
  }
}
```

#### YouTube

YouTube não tem URL scheme direto, mas podemos:
1. Usar Share Sheet (YouTube aparece automaticamente)
2. Implementar upload via YouTube Data API v3

```dart
// Opção futura: YouTube API direta
import 'package:googleapis/youtube/v3.dart';

Future<void> uploadToYouTube(String videoPath, String title) async {
  // Requer OAuth2
  // Usa biblioteca googleapis
  // API key no Info.plist
}
```

---

## 🔧 Configuração no projeto Flutter

### pubspec.yaml

```yaml
dependencies:
  share_plus: ^7.2.2        # Share sheet nativo
  url_launcher: ^6.2.4      # URL schemes
  gallery_saver: ^2.3.2     # Salvar na galeria primeiro
```

### ios/Runner/Info.plist

Adicionar URL schemes suportados:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>instagram</string>
    <string>instagram-stories</string>
    <string>tiktokopensdk</string>
    <string>youtube</string>
</array>
```

---

## 🎬 Fluxo no App

### Opção 1: Share Direto (Simples)

```
1. Usuário processa vídeo
2. App mostra preview
3. Botão "Compartilhar"
4. iOS Share Sheet aparece
5. Usuário escolhe app
6. Publicação manual no app destino
```

### Opção 2: Menu com Atalhos (Melhor UX)

```
1. Usuário processa vídeo
2. App mostra preview
3. Tela com botões:
   - 📸 Instagram
   - 🎵 TikTok
   - 📹 YouTube
   - 💾 Salvar na Galeria
   - 📤 Outros...
4. Cada botão abre o app específico
5. Publicação manual (mas mais rápido)
```

---

## 📝 Interface Sugerida (Flutter)

```dart
class ExportOptionsScreen extends StatelessWidget {
  final String videoPath;
  final String title;
  final String description;
  final List<String> hashtags;

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: CupertinoNavigationBar(
        middle: Text('Publicar Vídeo'),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // Preview do vídeo
            VideoPlayerWidget(videoPath),
            
            SizedBox(height: 20),
            
            // Botões de compartilhamento
            _ShareButton(
              icon: CupertinoIcons.photo,
              label: 'Instagram',
              color: Colors.purple,
              onTap: () => _shareToInstagram(),
            ),
            
            _ShareButton(
              icon: CupertinoIcons.music_note,
              label: 'TikTok',
              color: Colors.black,
              onTap: () => _shareToTikTok(),
            ),
            
            _ShareButton(
              icon: CupertinoIcons.play_rectangle,
              label: 'YouTube',
              color: Colors.red,
              onTap: () => _shareToYouTube(),
            ),
            
            _ShareButton(
              icon: CupertinoIcons.square_arrow_up,
              label: 'Outros Apps',
              color: CupertinoColors.systemBlue,
              onTap: () => _shareGeneric(),
            ),
            
            _ShareButton(
              icon: CupertinoIcons.floppy_disk,
              label: 'Salvar na Galeria',
              color: CupertinoColors.systemGreen,
              onTap: () => _saveToGallery(),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 🚀 Metadados Pre-filled

Podemos copiar metadados para clipboard antes de abrir o app:

```dart
import 'package:flutter/services.dart';

Future<void> shareWithMetadata(String videoPath, metadata) async {
  // 1. Copiar descrição + hashtags para clipboard
  final text = '${metadata.description}\n\n${metadata.hashtags.join(' ')}';
  await Clipboard.setData(ClipboardData(text: text));
  
  // 2. Mostrar instrução
  showCupertinoDialog(
    context: context,
    builder: (context) => CupertinoAlertDialog(
      title: Text('Texto Copiado!'),
      content: Text('Cole no app de destino (Cmd+V)'),
      actions: [
        CupertinoDialogAction(
          child: Text('Abrir Instagram'),
          onPressed: () {
            Navigator.pop(context);
            shareToInstagram(videoPath);
          },
        ),
      ],
    ),
  );
}
```

---

## ✅ Vantagens da Abordagem Nativa

| Característica | Selenium (Antigo) | iOS Native (Novo) |
|---|---|---|
| Funciona no iOS | ❌ Não | ✅ Sim |
| Velocidade | 🐌 Lento | ⚡ Instantâneo |
| Manutenção | 🔧 Alta | ✅ Zero |
| Risco de ban | ⚠️ Alto | ✅ Zero |
| Suporte a novos apps | ❌ Manual | ✅ Automático |
| Memória | 🐘 ~500MB | 🪶 ~10MB |

---

## ⚠️ Limitações

1. **Usuário precisa publicar manualmente**
   - Não há automação 100% (Apple não permite)
   - Mas é MUITO mais rápido que abrir app → gravar → editar

2. **Necessita apps instalados**
   - Se usuário não tem Instagram, não pode publicar nele
   - Solução: Detectar apps instalados e mostrar apenas disponíveis

3. **Sem agendamento**
   - Publicação é imediata
   - Para agendar, precisaria de servidor externo (fora do escopo mobile)

---

## 🎯 Próximos Passos

### Fase 1 (Flutter)
- [x] Implementar Share Sheet básico (`share_plus`)
- [ ] Criar tela de exportação com botões
- [ ] Implementar URL schemes (Instagram, TikTok)

### Fase 2 (Metadados)
- [ ] Copy to clipboard com metadados
- [ ] Template de caption otimizado
- [ ] Preview antes de compartilhar

### Fase 3 (Avançado)
- [ ] Detectar apps instalados
- [ ] Analytics de publicações
- [ ] Historical de vídeos compartilhados

---

## 📚 Referências

- [Share Plus Plugin](https://pub.dev/packages/share_plus)
- [URL Launcher](https://pub.dev/packages/url_launcher)
- [Instagram URL Schemes](https://developers.facebook.com/docs/instagram/sharing-to-stories/)
- [TikTok iOS SDK](https://developers.tiktok.com/doc/login-kit-ios)
- [YouTube Data API](https://developers.google.com/youtube/v3)

---

> [!NOTE]
> Esta abordagem é **100% compatível com App Store** e **não viola nenhuma política** das plataformas de rede social. O usuário mantém controle total sobre suas publicações.
