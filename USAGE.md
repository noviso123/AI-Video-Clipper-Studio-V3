# 📝 Guia Rápido de Uso

## 🚀 Uso Básico

### Comando Simples (Linux/macOS)
```bash
python main.py --url "https://youtube.com/watch?v=VIDEO_ID"
```

### Comando Simples (Windows)
```powershell
# Usando o Orquestrador Automático (Recomendado)
.\run_windows.ps1

# Ou via comando direto
python main.py --url "https://youtube.com/watch?v=VIDEO_ID"
```

Isso irá:
1. Baixar o vídeo do YouTube
2. Transcrever com Whisper (modelo `base` por padrão)
3. Analisar e identificar 3 momentos virais
4. Gerar 3 clipes em formato 9:16 prontos para publicar

### Comando Completo
```bash
python main.py \
  --url "https://youtube.com/watch?v=VIDEO_ID" \
  --clips 5 \
  --whisper-model small \
  --output ./meus_clipes
```

---

## 🎛️ Opções Disponíveis

| Opção | Valores | Descrição |
|-------|---------|-----------|
| `--url` | URL | **Obrigatório**: Link do vídeo do YouTube |
| `--clips` | 1-10 | Número de clipes a gerar (padrão: 3) |
| `--whisper-model` | tiny, base, small, medium, large | Modelo de transcrição (padrão: base) |
| `--output` | caminho | Diretório de saída (padrão: exports/) |
| `--keep-temp` | flag | Manter arquivos temporários |
| `--no-critic` | flag | Desativar agente crítico (futuro) |
| `--no-face-tracking` | flag | Desativar rastreamento de rosto (futuro) |

---

## 📊 Escolhendo o Modelo Whisper

| Modelo | RAM | Velocidade* | Precisão | Quando Usar |
|--------|-----|------------|----------|-------------|
| `tiny` | ~1 GB | ⚡⚡⚡ Muito rápido | 70% | Testes rápidos |
| `base` | ~1 GB | ⚡⚡ Rápido | 80% | **Uso geral (recomendado)** |
| `small` | ~2 GB | ⚡ Médio | 85% | Melhor qualidade, PC bom |
| `medium` | ~5 GB | 🐌 Lento | 90% | Máxima precisão |
| `large` | ~10 GB | 🐌🐌 Muito lento | 95% | Apenas com GPU potente |

*Velocidade para vídeo de 10 minutos em CPU i5

---

## 💡 Exemplos Práticos

### 1. Teste Rápido (Vídeo Curto)
```bash
python main.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ" --whisper-model tiny --clips 1
```

### 2. Produção de Conteúdo (Qualidade)
```bash
python main.py --url "URL_DO_VIDEO" --whisper-model small --clips 5
```

### 3. Processamento em Lote
```bash
# Criar arquivo urls.txt com uma URL por linha
for url in $(cat urls.txt); do
  python main.py --url "$url" --clips 3
done
```

### 4. Manter Tudo Organizado
```bash
python main.py \
  --url "URL_DO_VIDEO" \
  --output "./projetos/video1/" \
  --keep-temp
```

---

## 🎯 Workflow Recomendado

### Para Iniciantes
1. **Teste com vídeo curto** (5-10 min) usando `--whisper-model tiny`
2. **Verifique os clipes** gerados em `exports/`
3. **Ajuste configurações** no `.env` se necessário
4. **Escale** para vídeos mais longos

### Para Produção
1. **Use `--whisper-model base` ou `small`** para melhor qualidade
2. **Gere 5-7 clipes** por vídeo (`--clips 5`)
3. **Revise clipes** antes de publicar
4. **Personalize títulos** usando os hooks sugeridos

---

## ⚙️ Configurações Avançadas (.env)

```env
# Ajustar threshold de emoção (0.5 = mais sensível, 0.9 = menos sensível)
VOLUME_THRESHOLD=0.7

# Duração dos clipes (em segundos)
CLIP_DURATION_MIN=30
CLIP_DURATION_MAX=60

# Qualidade de exportação
VIDEO_QUALITY=high  # low, medium, high, ultra
```

---

## 🐛 Solução de Problemas

### Clipes não são gerados
- **Causa**: Nenhum momento viral detectado
- **Solução**: Reduza `VOLUME_THRESHOLD` no `.env` para 0.5

### Whisper muito lento
- **Causa**: Modelo muito pesado ou sem GPU
- **Solução**: Use `--whisper-model tiny` ou `base`

### Erro de memória
- **Causa**: RAM insuficiente
- **Solução**:
  - Use modelo `tiny`
  - Feche outros programas
  - Processe vídeos menores

### Vídeo tremido/qualidade ruim
- **Causa**: Bitrate muito baixo
- **Solução**: Configure `VIDEO_QUALITY=high` ou `ultra` no `.env`

---

## 📈 Dicas de Otimização

### Para PC Fraco (8 GB RAM)
```env
WHISPER_MODEL=tiny
VIDEO_QUALITY=medium
FACE_TRACKING_ENABLED=false
```

### Para PC Forte (16+ GB RAM + GPU)
```env
WHISPER_MODEL=small
VIDEO_QUALITY=ultra
FACE_TRACKING_ENABLED=true
```

### Para Máxima Velocidade
```bash
python main.py --url "..." --whisper-model tiny --clips 3
# ~5 min para vídeo de 10 min
```

### Para Máxima Qualidade
```bash
python main.py --url "..." --whisper-model medium --clips 5
# ~20 min para vídeo de 10 min
```

---

## 🎬 Pós-Processamento

### Validar Clipes
```bash
# Listar clipes gerados
ls -lh exports/

# Ver metadados
ffprobe exports/clip_01_score9.2.mp4
```

### Publicar em Massa
1. Revise todos os clipes em `exports/`
2. Escolha os melhores (score 8.5+)
3. Use os hooks como títulos das postagens
4. Publique no TikTok, Reels e Shorts

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique `logs/clipper_YYYYMMDD.log`
2. Execute com `DEBUG_MODE=true` no `.env`
3. Teste com vídeo diferente
4. Consulte `SETUP.md` para validar instalação
