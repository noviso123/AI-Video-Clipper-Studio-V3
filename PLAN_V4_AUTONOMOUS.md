# IMPLANTAÇÃO V4: AUTONOMOUS EVENT-DRIVEN PIPELINE

## 🎯 Objetivo
Transformar o sistema de "Clipping Sob Demanda" para uma "Plataforma Autônoma de Engenharia de Conteúdo", capaz de monitorar, ingerir, processar e agendar conteúdo sem intervenção humana constante.

## 🏗️ Nova Arquitetura de Pastas (Pipeline Físico)

O sistema operará como uma linha de montagem física de arquivos:

```
/ai-video-clipper
 ├── /00_monitor_config     # Listas de alvos (insta_targets.txt, youtube_channels.txt)
 ├── /01_ingestion_buffer   # BUFFER: Stories aguardando agrupamento (Batching)
 ├── /02_raw_content        # INPUT: Conteúdo consolidado pronto para análise (Reels, YT, StoryBatches)
 ├── /03_transcriptions     # DATA: JSONs do Whisper e Metadados
 ├── /04_cutting_room       # WORK: Área de trabalho do FFMPEG (Cortes, Crops, Legendas)
 ├── /05_ready_queue        # OUTPUT: Vídeos finais aguardando janela de postagem
 └── /db                    # STATE: SQLite controlando o estado de tudo
```

---

## 🧩 Módulos do Sistema

### 1. Core: Database & State Manager (`src/core/database.py`)
- **Tecnologia:** SQLite
- **Função:** Cérebro central que mantem o estado. NADA acontece sem registro aqui.
- **Tabelas:**
  - `story_batches`: Controla os "Lotes de Stories" (ID, Status, LastUpdate).
  - `media_jobs`: Rastreia cada conteúdo desde a ingestão até o posto (Type, Source, Status, Priority).
  - `publish_queue`: Fila de agendamento com regras de vazão.

### 2. Módulo: Omni-Monitor (`src/modules/monitor.py`)
- **Função:** Olheiro vigiando as redes.
- **Lógica:** Threads independentes para Insta e YT.
- **Router Integrado:**
  - Detectou Story? -> `/01_ingestion_buffer` + Update DB (Reset Timer 30min).
  - Detectou Reels? -> `/02_raw_content` (Prioridade Alta).
  - Detectou YouTube? -> `/02_raw_content` (Modo Miner).

### 3. Módulo: Batch Processor (`src/modules/batch_processor.py`)
- **Função:** O "Gari" do Buffer.
- **Trigger:** Cron a cada 5 min.
- **Regra:** `SELECT * FROM batches WHERE last_update < NOW-30min AND status='OPEN'`
- **Ação:** `ffmpeg concat` -> Move para `/02_raw_content`.

### 4. Módulo: Deep Miner & Face Tracking (`src/modules/mining.py`)
- **YouTube Strategy:**
  - Analisa vídeo em janelas deslizantes.
  - Extrai múltiplos clipes.
  - **Auto-Crop:** Usa `mediapipe` para detectar rostos e manter o sujeito centralizado ao converter 16:9 para 9:16.

### 5. Módulo: Intelligent Scheduler (`src/modules/scheduler.py`)
- **Função:** Porteiro de Saída.
- **Regra:** "Não postar mais que 1 vídeo a cada X horas".
- **Ação:** Verifica slot disponível -> Move para "Published" ou chama API de postagem.

---

## 📅 Plano de Execução Imediata

1.  **Infraestrutura:** Criar estrutura de pastas e Banco de Dados SQLite.
2.  **Monitor Dummy:** Criar o esqueleto do Monitor (o scraper real do Insta é complexo, faremos um simulador/watcher de pasta primeiro).
3.  **Batch Logic:** Implementar a lógica de "30 minutos de silêncio" para Stories.
4.  **Auto-Crop:** Integrar `mediapipe` para cortes verticais inteligentes.

---

> **⚠️ NOTA TÉCNICA:**
> A integração real com Instagram (Scraping) é delicada e bloqueia fácil. Para esta fase V4, focaremos na **Lógica de Engenharia** (Monitorar pastas/RSS e Processar). A coleta bruta do Instagram pode exigir proxies ou APIs pagas no futuro.
