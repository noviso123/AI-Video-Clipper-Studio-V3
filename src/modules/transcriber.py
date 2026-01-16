"""
Módulo de Transcrição (Stage 2)
100% OFFLINE - Usa Vosk com modelos locais
SEM SIMULAÇÃO - Apenas transcrição real
"""
from typing import List, Dict, Optional
from pathlib import Path
import json
import os
import wave
import subprocess

from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Importar Vosk
VOSK_AVAILABLE = False
vosk_module = None
try:
    import vosk
    vosk.SetLogLevel(-1)
    vosk_module = vosk
    VOSK_AVAILABLE = True
except ImportError:
    logger.error("❌ Vosk não instalado! Execute: pip install vosk")


class AudioTranscriber:
    """Transcrição 100% OFFLINE usando Vosk - SEM SIMULAÇÃO"""

    # Modelos suportados (ordem de preferência)
    VOSK_MODELS = [
        "vosk-model-pt-fb-v0.1.1-20220516_2113",  # Facebook model (melhor)
        "vosk-model-small-pt-0.3",                 # Small model
        "vosk-model-small-pt",
        "vosk-model-pt",
    ]

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or 'vosk'
        self.language = getattr(Config, 'WHISPER_LANGUAGE', 'pt')
        self.vosk_model = None
        self.model_path = None

        if VOSK_AVAILABLE:
            logger.info("🎤 Engine: Vosk (100% OFFLINE)")
        else:
            logger.error("❌ Vosk não disponível!")

    def load_model(self) -> bool:
        """Carrega modelo Vosk"""
        if self.vosk_model is not None:
            return True

        if not VOSK_AVAILABLE:
            raise RuntimeError("Vosk não está instalado! Execute: pip install vosk")

        logger.info("⏳ Procurando modelo Vosk...")

        # Procurar modelo
        self.model_path = self._find_vosk_model()

        if not self.model_path:
            raise RuntimeError(
                "❌ Modelo Vosk não encontrado!\n"
                "Baixe em: https://alphacephei.com/vosk/models\n"
                "Extraia em: ai-video-clipper/models/"
            )

        logger.info(f"   Modelo encontrado: {os.path.basename(self.model_path)}")
        logger.info(f"   Carregando...")

        try:
            self.vosk_model = vosk_module.Model(self.model_path)
            logger.info("✅ Modelo Vosk carregado com sucesso!")
            return True
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar modelo Vosk: {e}")

    def _find_vosk_model(self) -> Optional[str]:
        """Procura modelo Vosk nos diretórios conhecidos"""
        base_dirs = [
            os.path.join(os.getcwd(), "models"),
            os.getcwd(),
            os.path.expanduser("~/.vosk"),
            os.path.expanduser("~/Downloads"),
            "C:/vosk",
            "D:/vosk",
        ]

        # Procurar por cada modelo conhecido
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                continue

            # Primeiro, procurar pelos nomes exatos
            for model_name in self.VOSK_MODELS:
                model_path = os.path.join(base_dir, model_name)
                if os.path.exists(model_path) and self._is_valid_model(model_path):
                    return model_path

            # Depois, procurar por qualquer pasta que pareça ser modelo Vosk
            try:
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path) and 'vosk' in item.lower():
                        if self._is_valid_model(item_path):
                            return item_path
            except:
                pass

        return None

    def _is_valid_model(self, path: str) -> bool:
        """Verifica se é um modelo Vosk válido"""
        # Modelo Vosk deve ter pasta 'am' ou 'conf' ou arquivo 'mfcc.conf'
        return (
            os.path.exists(os.path.join(path, "am")) or
            os.path.exists(os.path.join(path, "conf")) or
            os.path.exists(os.path.join(path, "mfcc.conf")) or
            os.path.exists(os.path.join(path, "graph"))
        )

    def transcribe(self, audio_path: Path) -> List[Dict]:
        """Transcreve áudio usando Vosk (100% offline)"""
        if not audio_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

        # Carregar modelo
        self.load_model()

        logger.info(f"🎙️ Transcrevendo: {audio_path.name}")
        logger.info(f"   Modelo: {os.path.basename(self.model_path)}")

        # Converter para WAV 16kHz mono
        wav_path = self._prepare_audio(audio_path)

        return self._process_audio(wav_path)

    def _get_ffmpeg_path(self) -> str:
        """Localiza o binário do FFmpeg de forma robusta"""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return 'ffmpeg'

    def _prepare_audio(self, audio_path: Path) -> Path:
        """Prepara áudio para Vosk (WAV 16kHz mono)"""
        wav_path = audio_path.with_name(audio_path.stem + '_vosk.wav')

        # Se já existe e é recente, usar
        if wav_path.exists():
            try:
                import wave
                with wave.open(str(wav_path), 'rb') as wf:
                    if wf.getframerate() == 16000 and wf.getnchannels() == 1:
                        logger.info("   Usando WAV existente")
                        return wav_path
            except:
                pass

        logger.info("   Convertendo para WAV 16kHz...")

        try:
            ffmpeg_exe = self._get_ffmpeg_path()
            result = subprocess.run([
                ffmpeg_exe, '-y', '-i', str(audio_path),
                '-ar', '16000', '-ac', '1',
                '-sample_fmt', 's16',
                '-f', 'wav', str(wav_path)
            ], capture_output=True, timeout=600)

            if result.returncode == 0 and wav_path.exists():
                logger.info("   ✅ Conversão concluída")
                return wav_path
            else:
                error_msg = result.stderr.decode() if result.stderr else "Erro desconhecido"
                logger.warning(f"   FFmpeg erro: {error_msg[:200]}")
        except subprocess.TimeoutExpired:
            logger.error("   Timeout na conversão")
        except Exception as e:
            logger.error(f"   Erro crítico na conversão: {e}")

        # Se falhou, tentar usar original (provavelmente falhará no Vosk se não for WAV)
        return audio_path

    def _process_audio(self, wav_path: Path) -> List[Dict]:
        """Processa áudio com Vosk"""
        logger.info("   Processando transcrição...")

        try:
            wf = wave.open(str(wav_path), "rb")
        except Exception as e:
            raise RuntimeError(f"Erro ao abrir áudio: {e}")

        # Verificar formato
        if wf.getnchannels() != 1:
            wf.close()
            raise RuntimeError("Áudio deve ser mono (1 canal)")

        sample_rate = wf.getframerate()
        total_frames = wf.getnframes()
        total_duration = total_frames / sample_rate

        logger.info(f"   Duração: {int(total_duration//60)}:{int(total_duration%60):02d}")

        # Criar reconhecedor
        rec = vosk_module.KaldiRecognizer(self.vosk_model, sample_rate)
        rec.SetWords(True)

        segments = []
        current_time = 0.0
        processed_frames = 0
        last_progress = 0

        # Processar em chunks
        chunk_size = 4000

        while True:
            data = wf.readframes(chunk_size)
            if len(data) == 0:
                break

            processed_frames += chunk_size

            # Mostrar progresso a cada 10%
            progress = int((processed_frames / total_frames) * 100)
            if progress >= last_progress + 10:
                logger.info(f"   Progresso: {progress}%")
                last_progress = progress

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    text = result['text'].strip()
                    if text:
                        # Calcular duração baseada no resultado
                        if 'result' in result and result['result']:
                            words = result['result']
                            start = words[0].get('start', current_time)
                            end = words[-1].get('end', start + 1)
                        else:
                            # Estimar baseado em palavras
                            word_count = len(text.split())
                            duration = word_count * 0.35
                            start = current_time
                            end = current_time + duration

                        segments.append({
                            'start': round(start, 2),
                            'end': round(end, 2),
                            'text': text
                        })

                        current_time = end

        # Processar resultado final
        final = json.loads(rec.FinalResult())
        if final.get('text'):
            text = final['text'].strip()
            if text:
                if 'result' in final and final['result']:
                    words = final['result']
                    start = words[0].get('start', current_time)
                    end = words[-1].get('end', start + 1)
                else:
                    word_count = len(text.split())
                    start = current_time
                    end = current_time + word_count * 0.35

                segments.append({
                    'start': round(start, 2),
                    'end': round(end, 2),
                    'text': text
                })

        wf.close()

        if not segments:
            raise RuntimeError("Nenhum texto transcrito. Verifique o áudio.")

        self._log_result(segments)
        return segments

    def _log_result(self, segments: List[Dict]):
        """Log dos resultados"""
        total_duration = segments[-1]['end'] if segments else 0
        total_words = sum(len(s['text'].split()) for s in segments)

        logger.info(f"✅ Transcrição concluída!")
        logger.info(f"   Segmentos: {len(segments)}")
        logger.info(f"   Palavras: {total_words}")
        logger.info(f"   Duração transcrita: {int(total_duration//60)}:{int(total_duration%60):02d}")

    def export_srt(self, segments: List[Dict], output_path: Path):
        """Exporta para SRT"""
        def fmt(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{fmt(seg['start'])} --> {fmt(seg['end'])}\n")
                f.write(f"{seg['text']}\n\n")

        logger.info(f"💾 SRT exportado: {output_path.name}")

    def export_json(self, segments: List[Dict], output_path: Path):
        """Exporta para JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 JSON exportado: {output_path.name}")

    def get_words_in_range(self, segments: List[Dict], start: float, end: float) -> List[Dict]:
        """Extrai texto em um intervalo de tempo"""
        words = []
        for seg in segments:
            if seg['end'] < start or seg['start'] > end:
                continue

            # Segmento está no intervalo
            overlap_start = max(seg['start'], start)
            overlap_end = min(seg['end'], end)

            if overlap_end > overlap_start:
                words.append({
                    'word': seg['text'],
                    'start': seg['start'],
                    'end': seg['end']
                })

        return words
