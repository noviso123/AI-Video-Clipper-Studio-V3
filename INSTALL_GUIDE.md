# Guia de Instalação - Flutter no Linux

Este guia mostra como instalar o Flutter no Linux para desenvolver o app AI Video Clipper iOS.

## 📋 Requisitos

- Sistema Linux (Ubuntu, Fedora, etc)
- 2GB+ de espaço em disco
- Git instalado

## 🚀 Instalação do Flutter

### Passo 1: Download do Flutter SDK

```bash
cd ~
git clone https://github.com/flutter/flutter.git -b stable
```

### Passo 2: Adicionar Flutter ao PATH

```bash
# Adicionar ao .bashrc ou .zshrc
echo 'export PATH="$PATH:$HOME/flutter/bin"' >> ~/.bashrc

# Recarregar terminal
source ~/.bashrc
```

### Passo 3: Verificar Instalação

```bash
flutter --version
flutter doctor
```

**Saída esperada:**
```
Flutter 3.19.x • channel stable
Tools • Dart 3.3.x • DevTools 2.31.x
```

### Passo 4: Configurar Suporte iOS

```bash
flutter config --enable-ios
```

> **Nota:** Você NÃO precisa do Xcode instalado no Linux. O build será feito remotamente via Codemagic ou GitHub Actions.

## 🛠️ Configurar Projeto AI Video Clipper

### Passo 1: Navegar para o Projeto

```bash
cd /home/jsatiro/Documentos/AI-Video-Clipper-Studio-V3/ai_video_clipper_ios
```

### Passo 2: Instalar Dependências

```bash
flutter pub get
```

**Saída esperada:**
```
Running "flutter pub get" in ai_video_clipper_ios...
Resolving dependencies...
+ cupertino_icons 1.0.6
+ flutter_bloc 8.1.0
+ youtube_explode_dart 2.2.1
... (mais pacotes)
Got dependencies!
```

### Passo 3: Verificar Código

```bash
# Análise estática
flutter analyze

# Formatar código (opcional)
flutter format .
```

## 📦 Build Remoto

### Opção A: Codemagic (Recomendado)

1. **Criar conta grátis**: https://codemagic.io/signup
2. **Conectar repositório**:
   - GitHub/GitLab/Bitbucket
   - Selecionar projeto `ai_video_clipper_ios`
3. **Configurar Build**:
   - Codemagic detecta automaticamente `codemagic.yaml`
   - Configurar certificado Apple Developer
4. **Iniciar Build**:
   - Push código para repositório
   - Build automático (~10-15 min)
   - Download `.ipa` gerado

### Opção B: GitHub Actions (Gratuito)

1. **Push código para GitHub**:
```bash
cd ai_video_clipper_ios
git init
git add .
git commit -m "Initial Flutter iOS project"
git remote add origin https://github.com/SEU_USUARIO/ai-video-clipper-ios.git
git push -u origin main
```

2. **Build automático**:
   - GitHub Actions inicia automaticamente
   - Verificar aba "Actions" no repositório
   - Download artefato após conclusão

## 📱 Instalação no iPhone

### Pré-requisitos

- Apple ID (conta gratuita ou paga $99/ano)
- iPhone 16E conectado via USB ou WiFi

### Método 1: Sideloadly (Windows/Mac/Linux)

```bash
# 1. Download Sideloadly
# https://sideloadly.io/

# 2. Instalar no PC
# Seguir instruções da plataforma

# 3. Conectar iPhone via USB

# 4. Arrastar arquivo .ipa para Sideloadly

# 5. Digitar Apple ID e senha

# 6. App instalado! ✅
```

### Método 2: AltStore (Renovação Automática)

```bash
# 1. Download AltStore
# https://altstore.io/

# 2. Instalar AltServer no PC

# 3. Conectar iPhone na mesma rede WiFi

# 4. Arrastar .ipa para AltStore

# 5. AltStore renova app automaticamente a cada 7 dias
```

## ⚠️ Troubleshooting

### Flutter não encontrado
```bash
# Verificar se Flutter está no PATH
echo $PATH | grep flutter

# Se não estiver, adicionar novamente
export PATH="$PATH:$HOME/flutter/bin"
```

### Erro "pub get failed"
```bash
# Limpar cache
flutter clean
rm -rf ~/.pub-cache

# Reinstalar dependências
flutter pub get
```

### Build iOS falha no GitHub Actions
- Verificar quota de minutos grátis (2000/mês)
- Checar logs detalhados na aba Actions
- Tentar Codemagic como alternativa

### App expira em 7 dias (conta grátis)
- Normal com conta Apple Developer gratuita
- Opções:
  1. Reinstalar via Sideloadly/AltStore (rápido)
  2. Usar AltStore com renovação automática
  3. Adquirir conta paga ($99/ano) para apps permanentes

## ✅ Próximos Passos

Após instalação bem-sucedida:

1. ✅ Flutter instalado e funcionando
2. ✅ Dependências do projeto baixadas
3. ✅ Build remoto configurado
4. ✅ App instalado no iPhone

**Agora você pode:**
- Editar código no Linux
- Push para GitHub
- Build automático na nuvem
- Instalação no iPhone

## 📚 Recursos Úteis

- [Documentação Flutter](https://docs.flutter.dev/)
- [Codemagic Docs](https://docs.codemagic.io/)
- [GitHub Actions Flutter](https://docs.github.com/actions)
- [Apple Developer](https://developer.apple.com/)

## 🆘 Suporte

Problemas? Abra uma issue no repositório com:
- Logs de erro completos
- Versão do Flutter (`flutter --version`)
- Sistema operacional
