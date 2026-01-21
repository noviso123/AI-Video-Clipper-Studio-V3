# 🎬 AI Video Clipper Studio V3

> **Gerador automático de clips virais para YouTube/TikTok/Reels**
> Transcrição em Português Brasileiro • 100% Offline • Interface Web Moderna

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

---

## ⚡ Instalação Rápida (Clone e Use!)

### 🪟 Windows
```batch
git clone https://github.com/noviso123/AI-Video-Clipper-Studio-V3.git
cd AI-Video-Clipper-Studio-V3
install.bat
start_system.bat
```

### 🐧 Linux (Ubuntu, Fedora, Bazzite, etc)
```bash
git clone https://github.com/noviso123/AI-Video-Clipper-Studio-V3.git
cd AI-Video-Clipper-Studio-V3
chmod +x install.sh start.sh
./install.sh
./start.sh
```

**Pronto!** O instalador vai automaticamente:
- ✅ Criar ambiente virtual Python
- ✅ Instalar FFmpeg (Linux)
- ✅ Instalar todas as dependências
- ✅ Baixar modelo VOSK PT-BR (~50MB)
- ✅ Configurar tudo automaticamente

---

## 🚀 Como Usar

1. **Acessar:** http://localhost:5000
2. **Cole uma URL do YouTube** ou selecione arquivo local
3. **Configure:** número de clips, duração min/max
4. **Clique em** 🚀 GERAR CLIPS
5. **Baixe** os clips da galeria!

---

## 📋 Requisitos

| Componente | Versão |
|------------|--------|
| **Python** | 3.10, 3.11, 3.12 |
| **FFmpeg** | 4.0+ (instalado automaticamente no Linux) |
| **RAM** | 4GB+ recomendado |
| **Disco** | 500MB livres |

### FFmpeg no Windows (se necessário)
```powershell
winget install ffmpeg
```

---

## 🗂️ Estrutura

```
AI-Video-Clipper-Studio-V3/
├── install.bat / install.sh  # 🔧 Instalador automático
├── start_system.bat / start.sh  # 🚀 Iniciar
├── download_models.py  # 📥 Baixar modelo VOSK
├── requirements.txt  # 📦 Dependências
├── app.py  # 🌐 Servidor Flask
├── main.py  # ⚙️ Motor de processamento
├── src/modules/  # 🧩 Módulos (transcriber, editor, etc)
├── models/  # 🧠 Modelo VOSK (~50MB)
└── exports/  # 📤 Clips gerados
```

---

## ⚙️ Configuração (Opcional)

Edite o arquivo `.env`:

```env
# Telegram Bot (opcional)
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id

# Configurações
MAX_CLIPS=5
MIN_CLIP_DURATION=30
MAX_CLIP_DURATION=120
```

---

## 🔧 Solução de Problemas

### Python não encontrado
- **Windows:** Baixe de https://python.org (marque "Add to PATH")
- **Linux:** `sudo apt install python3 python3-pip python3-venv`

### FFmpeg não encontrado
- **Windows:** `winget install ffmpeg`
- **Ubuntu:** `sudo apt install ffmpeg`
- **Fedora/Bazzite:** `sudo dnf install ffmpeg`

### Erro de modelo
Execute novamente: `python download_models.py`

---

## 🎯 Funcionalidades

- 🎙️ **Transcrição automática** em Português (VOSK)
- ✂️ **Corte inteligente** por análise de conteúdo
- 📝 **Legendas automáticas** sincronizadas
- 🎨 **Interface moderna** dark mode
- 📊 **Barra de progresso** em tempo real
- 💾 **100% Offline** após instalação
- 🔄 **Restauração de estado** ao recarregar

---

## 📄 Licença

MIT License - Use livremente!

---

**Feito com ❤️ para criadores de conteúdo**
