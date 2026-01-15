"""
Módulo de Aprimoramento de Áudio (Fase 18)
Responsável por limpar ruídos, nivelar volume e equalizar voz.
"""
import logging
from pathlib import Path
import noisereduce as nr
from pydub import AudioSegment, effects
import numpy as np
import soundfile as sf
import librosa

logger = logging.getLogger(__name__)

class AudioEnhancer:
    def __init__(self):
        logger.info("🎚️ Audio Enhancer: Inicializado")

    def enhance_audio(self, input_path: Path, output_path: Path, reduce_noise: bool = True):
        """
        Aplica pipeline de melhoria de áudio:
        1. Noise Reduction (Stationary)
        2. Normalization
        3. Dynamic Compression
        """
        try:
            logger.info(f"   🎚️ Aprimorando áudio: {input_path.name}")

            # 1. Carregar áudio com Librosa (para Noise Reduce)
            if reduce_noise:
                y, sr = librosa.load(str(input_path), sr=None)

                # Assumir que os primeiros 0.5s são ruído (ou usar estatística geral)
                # Se o áudio for muito curto, usar perfil conservador
                noise_part = y[:2000] if len(y) > 2000 else y

                # Aplicar redução de ruído leve (prop_decrease=0.5 para não ficar robótico)
                reduced_noise = nr.reduce_noise(
                    y=y,
                    sr=sr,
                    y_noise=noise_part,
                    prop_decrease=0.6,
                    n_std_thresh_stationary=1.5
                )

                # Salvar temporário para Pydub pegar
                temp_wav = input_path.with_suffix('.temp_nr.wav')
                sf.write(str(temp_wav), reduced_noise, sr)

                # Carregar no Pydub
                audio = AudioSegment.from_wav(str(temp_wav))
                temp_wav.unlink(missing_ok=True)
            else:
                audio = AudioSegment.from_file(str(input_path))

            # 2. Compressão Dinâmica (Deixar voz "cheia")
            # Normalize primeiro
            audio = effects.normalize(audio)

            # Compressão (Threshold -20dB, Ratio 4.0)
            # Pydub tem compressão limitada, usando compressão manual simples
            # (Aumentar partes baixas sem estourar as altas)
            compressed = effects.compress_dynamic_range(
                audio,
                threshold=-20.0,
                ratio=4.0,
                attack=5.0,
                release=50.0
            )

            # 3. Normalizar final (-1.0 dBFS)
            final_audio = effects.normalize(compressed, headroom=1.0)

            # Exportar
            final_audio.export(str(output_path), format="mp3", bitrate="192k")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro no Audio Enhancer: {e}")
            # Em caso de erro, copiar o original se possível
            return None
