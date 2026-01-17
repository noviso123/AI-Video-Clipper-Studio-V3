# 🚀 Quick Start - AI Video Clipper

## ⚡ Setup em 3 Passos

### 1. Execute o Script de Setup (Orquestrador Automático)

**Windows (PowerShell):**
```powershell
.\run_windows.ps1
```

**Linux (Bazzite/Fedora/Ubuntu) & macOS:**
```bash
chmod +x setup.sh run_web.sh
./setup.sh
```

O script irá:
- ✅ Verificar Python e FFmpeg
- ✅ Criar ambiente virtual
- ✅ Instalar todas as dependências
- ✅ Validar a instalação

### 2. Configure o .env (Opcional)
```bash
# O arquivo .env já foi criado com valores padrão
# Edite apenas se quiser personalizar:
notepad .env  # Windows
nano .env     # Linux
```

**Configurações importantes**:
- `WHISPER_MODEL=base` → Use `tiny` para PC fraco, `small` para PC forte
- `VOLUME_THRESHOLD=0.7` → Reduza para 0.5 se não encontrar momentos virais

### 3. Gere Seu Primeiro Clipe!
```bash
python main.py --url "https://youtube.com/watch?v=VIDEO_ID" --clips 3
```

**Resultado**: 3 clipes verticais em `exports/` prontos para TikTok/Reels/Shorts! 🎉

---

## 📱 Exemplo Prático

```bash
# 1. Ativar ambiente virtual (se não ativou)
.\venv\Scripts\Activate.ps1   # Windows PowerShell
venv\Scripts\activate.bat      # Windows CMD
source venv/bin/activate       # Linux/Mac

# 2. Processar vídeo
python main.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ" --clips 3

# 3. Verificar resultado
dir exports\              # Windows
ls exports/              # Linux/Mac

# 4. Assistir clipes
start exports\clip_01_score9.2.mp4   # Windows
open exports/clip_01_score9.2.mp4    # Mac
```

---

## 🎯 Comandos Mais Usados

### Básico
```bash
python main.py --url "URL" --clips 3
```

### Qualidade Máxima (PC forte)
```bash
python main.py --url "URL" --clips 5 --whisper-model small
```

### Rápido (PC fraco)
```bash
python main.py --url "URL" --clips 3 --whisper-model tiny
```

### Personalizado
```bash
python main.py --url "URL" --clips 5 --output ./meus_videos --keep-temp
```

---

## 🐛 Problemas Comuns

### "Python não encontrado"
**Solução**: Instale Python 3.10+ e marque "Add to PATH" na instalação

### "FFmpeg não encontrado"
**Solução**:
- Windows: `winget install ffmpeg` ou baixe em ffmpeg.org
- Linux: `sudo apt install ffmpeg`
- Mac: `brew install ffmpeg`

### "No module named 'whisper'"
**Solução**:
```bash
.\venv\Scripts\Activate.ps1  # Ative o ambiente virtual primeiro
pip install -r requirements.txt
```

### "Nenhum momento viral identificado"
**Solução**:
1. Edite `.env` e mude `VOLUME_THRESHOLD=0.5`
2. Tente com um vídeo diferente (dinâmico, com variação de emoção)

---

## ⚙️ Ajustes de Performance

### PC Fraco (8 GB RAM)
Edite `.env`:
```env
WHISPER_MODEL=tiny
VIDEO_QUALITY=medium
FACE_TRACKING_ENABLED=false
```

### PC Forte (16+ GB + GPU)
Edite `.env`:
```env
WHISPER_MODEL=small
VIDEO_QUALITY=ultra
FACE_TRACKING_ENABLED=true
```

---

## 📊 O Que Esperar

**Tempo de processamento** (vídeo de 10 min):
- PC fraco (i5, 8GB, sem GPU): ~15-20 min
- PC médio (i5, 16GB, sem GPU): ~10-15 min
- PC forte (i7, 32GB, GPU): ~5-8 min

**Arquivos gerados**:
- 3-5 clipes MP4 em formato 9:16
- Tamanho: ~10-15 MB por clipe
- Qualidade: 1080p, 30fps

---

## 📚 Próximos Passos

1. ✅ Teste com 2-3 vídeos diferentes
2. ✅ Ajuste `VOLUME_THRESHOLD` se necessário
3. ✅ Escolha os clipes com score 8.5+
4. ✅ Publique no TikTok/Reels/Shorts
5. ✅ Use os hooks sugeridos como títulos

---

## 🆘 Suporte

- 📖 Consulte `SETUP.md` para instalação detalhada
- 📖 Consulte `USAGE.md` para guia completo
- 📖 Consulte `README.md` para visão geral
- 🐛 Verifique logs em `logs/clipper_YYYYMMDD.log`

---

**Pronto! Seu sistema está configurado e funcionando! 🚀**

Comece gerando clipes de vídeos do YouTube e veja a mágica acontecer! 🎬
