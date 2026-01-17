# 🎬 AI Video Clipper - Sistema de Clipping Automático

Sistema profissional para transformar vídeos longos do YouTube em clipes virais para TikTok, Instagram Reels e YouTube Shorts.

## ✨ Diferenciais

- **🧠 Sistema Multi-Agente**: 5 agentes especializados trabalhando em equipe
- **🎭 Análise de Emoção**: Detecta risadas, picos de volume e momentos virais
- **✂️ Edição Automática**: Gera clipes 9:16 prontos para publicar
- **🔄 Loop de Feedback**: Agente crítico garante qualidade 8/10+ (em desenvolvimento)
- **🎨 Edição Dopaminérgica**: B-rolls automáticos e legendas dinâmicas (em desenvolvimento)
- **💯 100% Local**: Roda completamente no seu PC, custo zero

## 🚀 Status Atual: 100% Completo ✅

**Funcionalidades Completas**:
- ✅ Download de vídeos do YouTube
- ✅ Transcrição com Whisper (word-level timestamps)
- ✅ Análise viral automática (emoção + keywords)
- ✅ Geração de clipes 9:16 (TikTok/Reels/Shorts)
- ✅ Legendas dinâmicas word-level (3 estilos)
- ✅ Sistema multi-agente (Curador, Copywriter, Diretor, Crítico)
- ✅ Variantes anti-spam para múltiplas plataformas
- ✅ B-Rolls automáticos com Pexels API

## 🎨 Funcionalidades Avançadas

```bash
# Clipes básicos
python main.py --url "URL" --clips 3

# Com legendas estilo Hormozi
python main.py --url "URL" --clips 3 --captions

# Com variantes para cada plataforma
python main.py --url "URL" --clips 3 --variants

# Com avaliação do agente crítico
python main.py --url "URL" --clips 3 --critic

# TUDO junto (máxima qualidade)
python main.py --url "URL" --clips 5 --captions --variants --critic
```

---

## 📚 Documentação Completa

| Documento | Descrição |
|-----------|-----------|
| [README.md](README.md) | 👈 Você está aqui - Visão geral |
| [QUICKSTART.md](QUICKSTART.md) | ⚡ Setup em 3 passos + primeiros comandos |
| [SETUP.md](SETUP.md) | 🔧 Instalação detalhada passo-a-passo |
| [USAGE.md](USAGE.md) | 📖 Guia completo de uso com exemplos |
| [FAQ.md](FAQ.md) | ❓ Perguntas frequentes e troubleshooting |
| [SUMMARY.md](SUMMARY.md) | 📊 Resumo técnico do sistema |
| [CHANGELOG.md](CHANGELOG.md) | 📝 Histórico de versões e features |
| [examples.py](examples.py) | 💻 Script interativo com demos |

**Recomendação**: Comece por `QUICKSTART.md` para uso imediato!

---

## 🚀 Instalação Rápida

### 1. Requisitos
- Python 3.10+
- FFmpeg
- 8+ GB RAM (16 GB recomendado)
- GPU NVIDIA com CUDA (opcional, mas acelera 10x)

### 2. Instalação Automática (Recomendado)

**Windows (PowerShell):**
```powershell
.\run_windows.ps1
```

**Linux (Bazzite/Fedora/Ubuntu) & macOS:**
```bash
chmod +x setup.sh run_web.sh
./setup.sh
```

### 3. Instalação Manual

```bash
# Clone o repositório
git clone <seu-repo>
cd ai-video-clipper

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure suas variáveis de ambiente
cp .env.example .env
# Edite .env com suas preferências
```

### 3. Primeiro Uso

```bash
# Validar instalação
python tests/test_setup.py

# Gerar clipes de um vídeo
python main.py --url "https://youtube.com/watch?v=..." --clips 3
```

**Resultado**: 3 clipes verticais 9:16 prontos para publicar em `exports/`

📖 **Guias Detalhados**:
- [`SETUP.md`](SETUP.md) - Instalação completa passo-a-passo
- [`USAGE.md`](USAGE.md) - Guia de uso com exemplos e otimizações

---

## 📋 Configurações

Edite o arquivo `.env` para ajustar:

- **WHISPER_MODEL**: `tiny`, `base`, `small`, `medium`, `large`
  - PC fraco: use `tiny` ou `base`
  - PC forte: use `small` ou `medium`

- **CRITIC_ENABLED**: `true` para ativar o agente crítico
- **FACE_TRACKING_ENABLED**: `true` para crop inteligente
- **AUDIO_EMOTION_DETECTION**: `true` para detectar picos emocionais

## 🎯 Como Funciona

```
YouTube URL
    ↓
[1] Download do Vídeo (yt-dlp)
    ↓
[2] Transcrição (Whisper)
    ↓
[3] Análise de Emoção (Librosa)
    ↓
[4] Agente Curador → Seleciona momentos virais
    ↓
[5] Agente Copywriter → Cria hooks impactantes
    ↓
[6] Agente Diretor → Planeja edição
    ↓
[7] Agente Executor → Renderiza vídeo
    ↓
[8] Agente Crítico → Avalia qualidade
    ↓
✅ Clipes prontos em /exports
```

## 📊 Performance Esperada

| Hardware | Whisper Model | Tempo (10 min de vídeo) |
|----------|---------------|-------------------------|
| CPU i5 (sem GPU) | tiny | ~5 min |
| CPU i5 (sem GPU) | base | ~10 min |
| CPU i7 + GPU NVIDIA | base | ~2 min |
| CPU i7 + GPU NVIDIA | small | ~4 min |

## 🛠️ Estrutura do Projeto

```
ai-video-clipper/
├── src/
│   ├── core/           # Configuração e logging
│   ├── modules/        # Download, transcrição, edição
│   ├── agents/         # Sistema multi-agente
│   └── assets/         # Fontes, overlays, sons
├── tests/              # Testes automatizados
├── exports/            # Vídeos finalizados
├── temp/               # Arquivos temporários
└── main.py             # Script principal
```

## 📝 Roadmap

- [x] Fase 1: Planejamento
- [x] Fase 2: Estrutura do projeto
- [x] Fase 3-4: Download e Transcrição
- [x] Fase 5: Análise viral (emoção + keywords)
- [x] Fase 6: Edição de vídeo 9:16
- [x] Fase 7: Legendas dinâmicas word-level
- [x] Fase 8-10: Sistema multi-agente completo + B-rolls
- [x] Fase 11-12: Agente crítico + Variantes anti-spam
- [x] Fase 13-15: Deploy e testes finais

**Status**: ✅ 100% Completo!

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra issues e pull requests.

## 📄 Licença

MIT License

## ⚠️ Aviso

Use este sistema de forma responsável e respeite os direitos autorais dos vídeos originais.
