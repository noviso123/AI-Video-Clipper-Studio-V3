"""
Módulo de Narração 100% Offline e Orgânico
Tecnologia: Kokoro TTS (Neural v0.19) + Morphing Paramétrico (FFmpeg)
"""
from typing import Optional, List
from pathlib import Path
import os
import sys
import json
import subprocess
import shutil

from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Monkeypatch para Kokoro (NumPy Pickle Fix)
import numpy as np
_old_load = np.load
np.load = lambda *a,**k: _old_load(*a, allow_pickle=True, **k)

class VoiceAnalyzer:
    """Analisa características da voz do usuário para adaptação paramétrica"""

    def __init__(self):
        try:
            import librosa
            import numpy as np
            self.librosa = librosa
            self.np = np
            self.available = True
        except ImportError:
            self.available = False
            logger.warning("Librosa não disponível para análise de voz")

    def analyze_samples(self, samples_dir: str) -> dict:
        """Retorna perfil da voz: pitch médio (Hz)"""
        if not self.available:
            return {"pitch_mean": 115.0} # Default masculino (Lewis)

        pitches = []
        files = [f for f in os.listdir(samples_dir) if f.endswith('.wav')]

        for f in files[:5]:
            try:
                path = os.path.join(samples_dir, f)
                # Carregar e cortar silêncio
                y, sr = self.librosa.load(path, sr=None)
                y, _ = self.librosa.effects.trim(y, top_db=20) # Remove silêncio/ruído

                # PYIN com limites humanos (50Hz a 300Hz para homens/mulheres normais)
                # C2 (~65Hz) a C5 (~523Hz)
                f0, voiced_flag, voiced_probs = self.librosa.pyin(
                    y,
                    fmin=self.librosa.note_to_hz('C2'),
                    fmax=self.librosa.note_to_hz('C5')
                )
                if f0 is not None:
                    # Filtra apenas onde a certeza (probabilidade) é alta > 0.6
                    valid_f0 = f0[(voiced_flag) & (voiced_probs > 0.6)]

                    if len(valid_f0) > 0:
                        # Ignora outliers (muito agudo/grave)
                        median_pitch = self.np.median(valid_f0)
                        pitches.append(median_pitch)

            except Exception as e:
                logger.warning(f"Erro ao analisar {f}: {e}")

        if pitches:
            # Média das medianas
            avg_pitch = float(self.np.mean(pitches))

            # SANITY CHECK: Se der > 200Hz mas o usuário parece ser homem (baseado no histórico),
            # pode ser erro. Mas vamos confiar no dado limpo.
            logger.info(f"📊 Perfil de Voz Detectado (Refinado): {avg_pitch:.1f} Hz")
            return {"pitch_mean": avg_pitch}

        return {"pitch_mean": 115.0}


class VoiceNarrator:
    """Gera narrações usando Kokoro TTS (Offline) + Adaptação Orgânica"""

    def __init__(self):
        self.base_dir = os.getcwd()
        self.model_dir = os.path.join(self.base_dir, 'models', 'custom_voice_pro')
        self.temp_dir = os.path.join(self.base_dir, 'temp')

        self.analyzer = VoiceAnalyzer()
        self.voice_profile = None
        self.custom_voice_config = None
        self.has_custom_voice = False

        self._load_custom_voice()

        # Analisar perfil se tiver voz
        if self.has_custom_voice and self.voice_profile is None:
            samples_dir = self.custom_voice_config.get('samples_dir', self.model_dir)
            self.voice_profile = self.analyzer.analyze_samples(samples_dir)

    def _load_custom_voice(self):
        """Carrega configuração do modelo de voz"""
        config_path = os.path.join(self.model_dir, 'custom_voice_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.custom_voice_config = json.load(f)
                self.custom_voice_config['samples_dir'] = self.model_dir
                self.has_custom_voice = True
                logger.info(f"🎤 Narrador: Modelo '{self.custom_voice_config.get('model_name')}' carregado.")
            except Exception as e:
                logger.warning(f"Erro no modelo oficial: {e}")

    def _get_ffmpeg_path(self):
        """Retorna o caminho do executável do FFmpeg"""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return 'ffmpeg'

    def _normalize_text(self, text: str) -> str:
        """Limpa e traduz termos técnicos para evitar que a IA fale inglês"""
        import re

        # Mapa de tradução de termos comuns que fazem a IA 'virar a chave' para inglês
        traducoes = {
            r'\bAI\b': 'a í',
            r'\bIA\b': 'i á',
            r'\bVideo\b': 'vídeo',
            r'\bClipper\b': 'clíper',
            r'\bURL\b': 'u érre éle',
            r'\bReels\b': 'riills',
            r'\bTikTok\b': 'tic tóc',
            r'\bShorts\b': 'xórts',
            r'\bScript\b': 'escripite',
            r'\bAI Video\b': 'vídeo de i á',
            r'\bOnline\b': 'onláine',
            r'\bOffline\b': 'ofláine',
            r'\bApp\b': 'ép',
            r'\bAndroid\b': 'andróidi',
            r'\biPhone\b': 'aifone',
            r'\bSetup\b': 'setáp',
            r'\bLogin\b': 'loguim',
            r'\bDownload\b': 'daunloude'
        }

        # Aplicar substituições (case insensitive para garantir)
        for eng, pt in traducoes.items():
            text = re.sub(eng, pt, text, flags=re.IGNORECASE)

        # Substituições de caracteres especiais
        text = text.replace('&', ' e ')
        text = text.replace('%', ' por cento ')
        text = text.replace('$', ' reais ')
        text = text.replace('@', ' arroba ')
        text = text.replace('#', ' hashtag ')

        # Forçar minúsculas (ajuda na consistência do fonetizador)
        text = text.lower()

        # Remover tudo que não for alfanumérico PT-BR ou pontuação básica
        # Mantém letras com acentos, números e pontuação esencial
        text = re.sub(r'[^a-z0-9áàâãéèêíïóôõöúç \.,!\?\-\n]', ' ', text)

        # Remove espaços duplos
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    # Vozes Disponíveis no Kokoro-ONNX (Neutras para PT-BR)
    VOICES = {
        'michael': 'am_michael', # Masculino padrão
        'bella': 'af_bella',     # Feminino padrão
        'sarah': 'af_sarah',     # Feminino suave
        'am_michael': 'am_michael',
        'af_bella': 'af_bella',
        'af_sarah': 'af_sarah',
        'am_fenix': 'am_fenix',
        'am_puck': 'am_puck'
    }

    def _generate_kokoro(self, text: str, output: str, voice: str = "am_michael", log_callback=None) -> bool:
        """Geração via Kokoro TTS (Ultra High Quality Neural) - Forçado PT-BR"""
        try:
            from kokoro_onnx import Kokoro
            import soundfile as sf
            import numpy as np

            onnx_path = os.path.join(self.base_dir, 'models', 'kokoro', 'kokoro-v0_19.onnx')
            voices_path = os.path.join(self.base_dir, 'models', 'kokoro', 'voices.bin')

            if not os.path.exists(onnx_path) or not os.path.exists(voices_path):
                msg = "❌ Kokoro Model não encontrado."
                if log_callback: log_callback(msg)
                logger.error(msg)
                return False

            # Limpeza rigorosa do texto
            text = self._normalize_text(text)
            if not text: return False

            # Validar voz
            kokoro_voice = self.VOICES.get(voice.lower(), "am_michael")

            if log_callback: log_callback(f"🗣️ Gerando com Kokoro (Voz: {kokoro_voice}, Lang: PT-BR)...")

            # Init Kokoro
            kokoro = Kokoro(onnx_path, voices_path)

            samples, sample_rate = kokoro.create(
                text,
                voice=kokoro_voice,
                speed=1.0,
                lang="pt-br"
            )

            sf.write(output, samples, sample_rate)

            if os.path.exists(output) and os.path.getsize(output) > 0:
                 return True
            else:
                 return False

        except Exception as e:
            if log_callback: log_callback(f"❌ Erro Kokoro: {e}")
            return False

    def generate_multi_voice_narration(self, script: str, output_path: Path, log_callback=None) -> bool:
        """Processa roteiro com marcadores de voz: [VOICE: bella] texto..."""
        import re
        import soundfile as sf
        import numpy as np

        logger.info("🎙️ Iniciando Narração Multi-Voz...")

        # Regex para encontrar blocos de voz
        # Ex: [VOICE: bella] Olá tudo bem? [VOICE: michael] Sim e você?
        pattern = r'\[VOICE:\s*(\w+)\](.*?)(?=\[VOICE:|\Z)'
        matches = re.findall(pattern, script, re.DOTALL | re.IGNORECASE)

        if not matches:
            # Se não houver marcadores, usa a voz padrão para o texto todo
            return self.generate_narration(script, output_path, log_callback=log_callback)

        all_samples = []
        sample_rate = 24000 # Kokoro default

        for i, (voice_name, text) in enumerate(matches):
            text = text.strip()
            if not text: continue

            temp_chunk = os.path.join(self.temp_dir, f"chunk_{i}.wav")
            if self._generate_kokoro(text, temp_chunk, voice=voice_name, log_callback=log_callback):
                samples, sr = sf.read(temp_chunk)
                all_samples.append(samples)
                sample_rate = sr
                if os.path.exists(temp_chunk): os.remove(temp_chunk)

        if not all_samples:
            return False

        # Concatenar todos os samples
        final_samples = np.concatenate(all_samples)
        sf.write(str(output_path), final_samples, sample_rate)

        if log_callback: log_callback(f"✅ Narração Multi-Voz Concluída: {len(matches)} vozes.")
        return True

    def _apply_organic_morphing(self, input_path, output_path, log_callback):
        """Aplica a transformação de voz de forma orgânica (Pitch puro)"""
        try:
             target_pitch = self.voice_profile.get("pitch_mean", 115.0)
             base_pitch_faber = 115.0 # Faber é barítono

             # Ratio 1.0 = Igual.
             # < 1.0 = Mais grave (e mais lento, natural).
             # > 1.0 = Mais agudo (e mais rápido, natural).
             pitch_ratio = target_pitch / base_pitch_faber

             # Limite de sanidade (80% a 120%)
             pitch_ratio = max(0.8, min(1.2, pitch_ratio))

             # Se for muito próximo, não mexer para não perder qualidade
             if abs(pitch_ratio - 1.0) < 0.02:
                 shutil.move(input_path, output_path)
                 if log_callback: log_callback("✅ Voz Natural Mantida (Sem alteração necessária).")
                 return True

             filters = []
             ffmpeg_cmd = self._get_ffmpeg_path()

             # MODO ORGÂNICO: Apenas asetrate. O tempo muda junto com o tom.
             new_rate = int(44100 * pitch_ratio)
             filters.append(f"asetrate={new_rate}")

             if log_callback: log_callback(f"🔧 Ajuste Orgânico de Tom ({pitch_ratio:.2f}x)...")

             # Normalização final
             filters.append("speechnorm=e=12.5:r=0.0001:l=1")
             filters.append("loudnorm=I=-14:TP=-1.0:LRA=11")

             filter_chain = ",".join(filters)

             subprocess.run([
                ffmpeg_cmd, '-y', '-i', input_path, '-af', filter_chain,
                '-c:a', 'libmp3lame', '-b:a', '192k', str(output_path)
             ], capture_output=True, timeout=60)

             if os.path.exists(input_path): os.remove(input_path)
             if log_callback: log_callback("✅ Áudio Personalizado Pronto!")
             return True

        except Exception as e:
            if log_callback: log_callback(f"❌ Erro Morphing: {e}")
            return False

    def generate_narration(self, text: str, output_path: Path, style: str = "neutral", polish: bool = False, log_callback=None) -> bool:
        """Gera narração final (Pipeline Kokoro)"""
        # Ignora 'polish' pois removemos dependencias online

        if log_callback: log_callback("🎬 Iniciando Motor Kokoro (Offline)...")

        temp_file = os.path.join(self.temp_dir, 'narration_raw.wav')

        # 1. Gerar Base
        if self._generate_kokoro(text, temp_file, log_callback):
            # 2. Aplicar Personalização
            if self.has_custom_voice:
                return self._apply_organic_morphing(temp_file, str(output_path), log_callback)
            else:
                shutil.move(temp_file, str(output_path))
                if log_callback: log_callback("✅ Áudio Base Pronto (Sem customização).")
                return True

        return False

# Singleton
narrator = None
def get_narrator() -> VoiceNarrator:
    global narrator
    if narrator is None:
        narrator = VoiceNarrator()
    return narrator
