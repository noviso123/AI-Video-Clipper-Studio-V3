"""
Processador de Voz Offline (CPU Optimized)
Limpa áudio, remove ruído e normaliza para clonagem.
"""
import logging
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        pass

    def process_audio(self, input_path: str, output_path: str) -> bool:
        """
        Trata o áudio removendo silêncios longos e normalizando volume.
        Não usa IA pesada para rodar rápido na CPU.
        """
        try:
            logger.info(f"🔊 Processando áudio: {Path(input_path).name}")

            # Carregar áudio
            sound = AudioSegment.from_file(input_path)

            # 1. Converter para Mono e 22kHz (Padrão para treino leve)
            sound = sound.set_channels(1).set_frame_rate(22050)

            # 2. Normalização de Volume
            change_in_dBFS = -20.0 - sound.dBFS
            sound = sound.apply_gain(change_in_dBFS)

            # 3. Remover silêncios (Trimming simples)
            # Divide onde silêncio > 1000ms
            chunks = split_on_silence(
                sound,
                min_silence_len=1000,
                silence_thresh=sound.dBFS-16
            )

            # Recombinar com silêncio curto (300ms)
            output_sound = AudioSegment.empty()
            if chunks:
                for chunk in chunks:
                    output_sound += chunk + AudioSegment.silent(duration=300)
            else:
                output_sound = sound # Se não conseguiu dividir, usa original normalizado

            # 4. Exportar
            output_path = str(output_path) # Garantir string
            output_sound.export(output_path, format="wav")

            logger.info(f"✅ Áudio tratado salvo em: {Path(output_path).name}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao processar voz: {e}")
            return False
