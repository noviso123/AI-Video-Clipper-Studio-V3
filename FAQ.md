# ❓ FAQ - Perguntas Frequentes

## 📋 Geral

### Q: Quanto custa usar o sistema?
**A**: Completamente gratuito! Roda 100% localmente no seu PC sem custos de API.

### Q: Preciso de GPU NVIDIA?
**A**: Não é obrigatório, mas acelera 10x a transcrição. O sistema funciona perfeitamente apenas com CPU.

### Q: Funciona em qualquer vídeo do YouTube?
**A**: Sim, desde que seja um vídeo público. Vídeos privados ou com restrições não funcionam.

### Q: Quanto tempo demora para processar um vídeo?
**A**:
- PC fraco (i5, 8GB): ~15-20 min para vídeo de 10 min
- PC médio (i5, 16GB): ~10-15 min para vídeo de 10 min
- PC forte (i7 + GPU): ~5-8 min para vídeo de 10 min

---

## 🔧 Instalação

### Q: "Python não está no PATH", como resolver?
**A**: Reinstale o Python e marque a opção "Add Python to PATH" durante a instalação.

### Q: Erro "FFmpeg não encontrado"
**A**:
```bash
# Windows
winget install ffmpeg
# Ou baixe em: https://ffmpeg.org/download.html

# Linux
sudo apt install ffmpeg

# Mac
brew install ffmpeg
```

### Q: "No module named 'whisper'"
**A**: Ative o ambiente virtual primeiro:
```bash
.\venv\Scripts\Activate.ps1  # Windows PowerShell
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

---

## 🎬 Uso

### Q: Nenhum momento viral foi identificado, o que fazer?
**A**:
1. Edite `.env` e reduza `VOLUME_THRESHOLD=0.5`
2. Tente com vídeo mais dinâmico (entrevistas, podcasts com emoção variada)
3. Vídeos monotonos (aulas, tutoriais calmos) geram menos momentos virais

### Q: Posso processar vídeos de outras plataformas além do YouTube?
**A**: Atualmente apenas YouTube. Para outros sites, baixe o vídeo manualmente primeiro.

### Q: Como escolher o modelo Whisper ideal?
**A**:
- `tiny`: Testes rápidos, precisão ~70%
- `base`: **Recomendado** - equilíbrio ideal
- `small`: PC forte, precisão ~85%
- `medium/large`: Apenas com GPU potente

### Q: Os clipes ficaram com qualidade ruim
**A**: Edite `.env`:
```env
VIDEO_QUALITY=ultra  # ao invés de 'high'
```

### Q: Posso personalizar a duração dos clipes?
**A**: Sim! Edite `.env`:
```env
CLIP_DURATION_MIN=45  # mín. 45 segundos
CLIP_DURATION_MAX=90  # máx. 90 segundos
```

---

## 🎯 Análise Viral

### Q: Como funciona o sistema de scoring (0-10)?
**A**: Combina múltiplos fatores:
- **Keywords virais**: dinheiro, segredo, urgência (+3 pontos)
- **Números específicos**: valores, datas (+1 ponto)
- **Perguntas**: "como", "por que" (+0.5 pontos)
- **Picos emocionais** no áudio (+2 pontos)
- **Início forte**: palavras de impacto (+1 ponto)

### Q: Posso ajustar o threshold de qualidade?
**A**: Sim! No código `curator.py`, linha ~18:
```python
self.min_score = 7.0  # ao invés de 8.0
```

### Q: Por que alguns vídeos geram apenas 1-2 clipes?
**A**: O sistema só seleciona momentos com score 8+. Vídeos sem picos emocionais fortes geram menos clipes.

---

## 📁 Arquivos

### Q: Onde ficam os clipes finais?
**A**: Na pasta `exports/` na raiz do projeto.

### Q: Posso deletar a pasta `temp/`?
**A**: Sim, mas será recriada no próximo processamento. Contém arquivos intermediários.

### Q: Quanto espaço em disco preciso?
**A**:
- Instalação: ~2 GB (Python + dependências)
- Por vídeo processado: ~200-500 MB temporários
- Clipes finais: ~10-15 MB cada

---

## ⚡ Performance

### Q: Como acelerar o processamento?
**A**:
1. Use modelo `tiny` para testes: `--whisper-model tiny`
2. Instale CUDA se tiver GPU NVIDIA
3. Aumente RAM disponível (feche outros programas)
4. Use SSD ao invés de HD

### Q: Posso processar vários vídeos de uma vez?
**A**: Sim, mas sequencialmente. Crie um script:
```bash
python main.py --url "URL1" --clips 3
python main.py --url "URL2" --clips 3
python main.py --url "URL3" --clips 3
```

### Q: O sistema usa muito meu PC?
**A**: Sim, especialmente durante transcrição. Use `WHISPER_MODEL=tiny` ou processe à noite.

---

## 🎨 Edição

### Q: Posso mudar o formato dos clipes (ex: 16:9)?
**A**: Sim! Edite `.env`:
```env
OUTPUT_RESOLUTION=1920x1080  # 16:9 horizontal
```

### Q: Como adicionar meu logo nos vídeos?
**A**: Atualmente não suportado. Planejado para futuras versões.

### Q: Os clipes ficam centralizados, posso mudar?
**A**: Por enquanto apenas crop central. Face tracking está planejado.

---

## 🐛 Erros Comuns

### Q: "MemoryError" ou PC trava
**A**:
- Use modelo `tiny`
- Feche outros programas
- Processe vídeos menores (< 20 min)

### Q: "Error downloading video"
**A**:
- Verifique se o vídeo é público
- Teste a URL no navegador
- Alguns vídeos têm proteção anti-bot

### Q: "Codec error" ao renderizar
**A**: Reinstale FFmpeg e reinicie o terminal.

### Q: Legendas SRT não aparecem
**A**: As legendas são geradas mas não embutidas no vídeo (planejado para futuras versões).

---

## 🔮 Futuro

### Q: Quando terá legendas dinâmicas?
**A**: O módulo está criado, será integrado na próxima versão (Fase 7).

### Q: Vai ter publicação automática no TikTok?
**A**: Planejado para Fase 14 (opcional).

### Q: Posso contribuir com o código?
**A**: Sim! É open source. Envie pull requests.

### Q: Terá versão com interface gráfica?
**A**: Planejado (Streamlit ou Gradio).

---

## 💡 Dicas Avançadas

### Q: Como encontrar vídeos bons para processar?
**A**: Prefira:
- Podcasts com múltiplos participantes
- Entrevistas dinâmicas
- Vídeos com variação emocional
- Conteúdo sobre dinheiro, sucesso, erro, segredos

### Q: Qual a melhor estratégia de publicação?
**A**:
1. Gere 5-7 clipes por vídeo
2. Publique os top 3 (score 9+) imediatamente
3. Guarde os 8-8.9 para "recheio" de calendário
4. Teste diferentes títulos nos hooks sugeridos

### Q: Posso usar comercialmente?
**A**: Sim, mas respeite direitos autorais dos vídeos originais.

---

## 📞 Ainda com dúvidas?

1. Consulte `USAGE.md` para guia completo
2. Veja `SUMMARY.md` para visão técnica
3. Cheque logs em `logs/clipper_YYYYMMDD.log`
4. Abra uma issue no GitHub
