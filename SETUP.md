# 🚀 Guia de Instalação e Configuração

## Pré-requisitos

Antes de começar, você precisa ter instalado:

### 1. Python 3.10 ou superior

Verifique se já tem instalado:
```bash
python --version
```

Se não tiver, baixe em: https://www.python.org/downloads/

**IMPORTANTE**: Na instalação do Python, marque a opção "Add Python to PATH"

### 2. FFmpeg

FFmpeg é essencial para processamento de vídeo.

#### Windows:
1. Baixe em: https://ffmpeg.org/download.html ou
2. Use Chocolatey: `choco install ffmpeg` ou
3. Use winget: `winget install ffmpeg`

#### Linux:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/Fedora
```

#### macOS:
```bash
brew install ffmpeg
```

**Verificar instalação**:
```bash
ffmpeg -version
```

### 3. CUDA Toolkit (Opcional, mas MUITO recomendado se tiver GPU NVIDIA)

Se você tem uma placa de vídeo NVIDIA (GTX/RTX), instale o CUDA para acelerar 10x:

1. Baixe em: https://developer.nvidia.com/cuda-downloads
2. Escolha sua versão do Windows
3. Instale normalmente

---

## Instalação do Projeto

### Passo 1: Criar Ambiente Virtual

```bash
# Navegue até a pasta do projeto
cd "C:\Users\12001036\Downloads\Manus ai video\ai-video-clipper"

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat

# Linux/macOS:
source venv/bin/activate
```

**IMPORTANTE**: Sempre ative o ambiente virtual antes de usar o sistema!

### Passo 2: Instalar Dependências

```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar todas as dependências
pip install -r requirements.txt
```

**Tempo estimado**: 5-10 minutos (dependendo da sua internet)

**Se tiver GPU NVIDIA** e quiser acelerar o Whisper:
```bash
# Instalar PyTorch com CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Passo 3: Configurar Variáveis de Ambiente

```bash
# Copiar o arquivo de exemplo
copy .env.example .env

# Editar o arquivo .env (use Notepad ou qualquer editor)
notepad .env
```

**Configurações recomendadas para começar**:

Para PC **FRACO** (8 GB RAM, sem GPU):
```env
WHISPER_MODEL=tiny
CRITIC_ENABLED=false
FACE_TRACKING_ENABLED=false
```

Para PC **MÉDIO** (16 GB RAM, sem GPU):
```env
WHISPER_MODEL=base
CRITIC_ENABLED=true
FACE_TRACKING_ENABLED=true
```

Para PC **FORTE** (16+ GB RAM, COM GPU NVIDIA):
```env
WHISPER_MODEL=small
CRITIC_ENABLED=true
FACE_TRACKING_ENABLED=true
```

---

## Primeiro Teste

Vamos testar se tudo está funcionando!

### Teste Rápido (Download + Transcrição)

```bash
python main.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --clips 1 --whisper-model tiny
```

**O que vai acontecer**:
1. ✅ Download do vídeo (alguns segundos)
2. ✅ Extração do áudio
3. ✅ Transcrição com Whisper (~2-5 minutos dependo do PC)
4. ✅ Exibição da transcrição no terminal

**Arquivos gerados** em `temp/`:
- `video_XXXXX.mp4` - Vídeo baixado
- `audio_XXXXX.mp3` - Áudio extraído
- `transcript_XXXXX.srt` - Legendas
- `transcript_XXXXX.json` - Transcrição completa

---

## Problemas Comuns

### ❌ "python: comando não encontrado"
- **Solução**: Reinstale o Python marcando "Add to PATH"

### ❌ "ffmpeg: comando não encontrado"
- **Solução**: Instale o FFmpeg e reinicie o terminal

### ❌ "No module named 'whisper'"
- **Solução**: Ative o ambiente virtual (`.\venv\Scripts\Activate.ps1`) e rode `pip install -r requirements.txt` novamente

### ❌ Whisper muito lento (mais de 10 minutos)
- **Solução**: Use um modelo menor (`--whisper-model tiny`) ou instale CUDA se tiver GPU NVIDIA

### ❌ "Out of memory" / Travou o PC
- **Solução**: Use modelo `tiny` ou `base`, feche outros programas

---

## Próximos Passos

Após a instalação bem-sucedida:

1. ✅ Teste com um vídeo curto primeiro (5-10 minutos)
2. ✅ Verifique a transcrição gerada em `temp/transcript_*.srt`
3. ✅ Ajuste o modelo Whisper conforme a performance do seu PC
4. 🚧 Aguarde os próximos módulos (análise viral, edição, etc.)

---

## Comandos Úteis

```bash
# Ver ajuda completa
python main.py --help

# Processar vídeo mantendo arquivos temporários
python main.py --url "..." --keep-temp

# Usar modelo Whisper específico
python main.py --url "..." --whisper-model small

# Desativar agente crítico (mais rápido)
python main.py --url "..." --no-critic
```

---

## Status do Desenvolvimento

- ✅ Download de vídeos (YouTube)
- ✅ Transcrição com Whisper
- 🚧 Análise viral com IA (em desenvolvimento)
- 🚧 Edição automática de vídeo
- 🚧 Legendas dinâmicas
- 🚧 Sistema multi-agente
- 🚧 Gerador de variantes

---

## Suporte

Se encontrar problemas:
1. Verifique que FFmpeg está instalado (`ffmpeg -version`)
2. Verifique que está no ambiente virtual (deve aparecer `(venv)` no terminal)
3. Tente com modelo `tiny` primeiro
4. Verifique os logs em `logs/clipper_YYYYMMDD.log`
