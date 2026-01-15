"""
Módulo de Análise de Emoção do Áudio (Fase 11)
Detecta picos emocionais no áudio para identificar momentos virais
"""
from typing import List, Dict, Optional
from pathlib import Path
import numpy as np
import librosa
from pydub import AudioSegment
from pydub.silence import detect_silence
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class AudioEmotionAnalyzer:
    """Analisa áudio para detectar picos emocionais"""

    def __init__(self):
        self.volume_threshold = Config.VOLUME_THRESHOLD

    def detect_emotion_peaks(self, audio_path: Path) -> List[Dict]:
        """
        Detecta picos emocionais no áudio

        Args:
            audio_path: Caminho do arquivo de áudio

        Returns:
            Lista de picos emocionais:
            [
                {
                    'timestamp': 125.5,
                    'type': 'volume_spike',  # ou 'silence', 'excitement'
                    'intensity': 0.85,  # 0-1
                    'duration': 3.2
                },
                ...
            ]
        """
        logger.info(f"🎭 Analisando emoções do áudio: {audio_path.name}")

        emotion_peaks = []

        try:
            # 1. Detectar picos de volume
            volume_peaks = self._detect_volume_spikes(audio_path)
            emotion_peaks.extend(volume_peaks)

            # 2. Detectar silêncios tensos
            silence_peaks = self._detect_dramatic_silences(audio_path)
            emotion_peaks.extend(silence_peaks)

            # 3. Detectar excitação (pitch alto)
            excitement_peaks = self._detect_excitement(audio_path)
            emotion_peaks.extend(excitement_peaks)

            # Ordenar por timestamp
            emotion_peaks.sort(key=lambda x: x['timestamp'])

            logger.info(f"✅ {len(emotion_peaks)} picos emocionais detectados")

            return emotion_peaks

        except Exception as e:
            logger.error(f"❌ Erro na análise de emoção: {e}")
            return []

    def _detect_volume_spikes(self, audio_path: Path) -> List[Dict]:
        """Detecta picos de volume (exclamações, gritos)"""
        logger.info("   📊 Detectando picos de volume...")

        peaks = []

        try:
            # Carregar áudio com librosa
            y, sr = librosa.load(str(audio_path), sr=None)

            # Calcular RMS energy em janelas de 0.5s
            frame_length = int(0.5 * sr)
            hop_length = int(0.25 * sr)

            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

            # Normalizar
            rms_normalized = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)

            # Detectar picos acima do threshold
            threshold = self.volume_threshold

            in_spike = False
            spike_start = 0

            for i, energy in enumerate(rms_normalized):
                timestamp = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)

                if energy > threshold and not in_spike:
                    # Início de um pico
                    in_spike = True
                    spike_start = timestamp

                elif energy <= threshold and in_spike:
                    # Fim de um pico
                    in_spike = False
                    duration = timestamp - spike_start

                    if duration >= 0.3:  # Mínimo de 0.3s
                        peaks.append({
                            'timestamp': spike_start,
                            'type': 'volume_spike',
                            'intensity': float(energy),
                            'duration': duration
                        })

            logger.info(f"      Encontrados {len(peaks)} picos de volume")

        except Exception as e:
            logger.warning(f"      Erro na detecção de volume: {e}")

        return peaks

    def _detect_dramatic_silences(self, audio_path: Path) -> List[Dict]:
        """Detecta pausas dramáticas (silêncios tensos)"""
        logger.info("   🤫 Detectando silêncios dramáticos...")

        peaks = []

        try:
            # Fix: Pydub needs explicit ffmpeg path on Windows
            try:
                import imageio_ffmpeg
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                AudioSegment.converter = ffmpeg_path
                AudioSegment.ffmpeg = ffmpeg_path
            except:
                pass  # Usar ffmpeg do sistema

            # Usar pydub para detectar silêncios
            audio = AudioSegment.from_file(str(audio_path))

            # Detectar silêncios de pelo menos 1 segundo
            silences = detect_silence(
                audio,
                min_silence_len=1000,  # 1 segundo
                silence_thresh=audio.dBFS - 20  # 20dB abaixo da média
            )

            for start_ms, end_ms in silences:
                duration = (end_ms - start_ms) / 1000.0

                # Apenas silêncios entre 1-3 segundos (pausas dramáticas)
                if 1.0 <= duration <= 3.0:
                    peaks.append({
                        'timestamp': start_ms / 1000.0,
                        'type': 'silence',
                        'intensity': 0.6,  # Intensidade fixa para silêncios
                        'duration': duration
                    })

            logger.info(f"      Encontrados {len(peaks)} silêncios dramáticos")

        except Exception as e:
            logger.warning(f"      Erro na detecção de silêncios: {e}")

        return peaks

    def _detect_excitement(self, audio_path: Path) -> List[Dict]:
        """Detecta excitação através de pitch alto"""
        logger.info("   🎤 Detectando excitação (pitch)...")

        peaks = []

        try:
            # Carregar áudio
            y, sr = librosa.load(str(audio_path), sr=None)

            # Extrair pitch (f0)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

            # Processar em janelas de 0.5s
            hop_length = int(0.5 * sr)

            for i in range(0, pitches.shape[1], hop_length // 512):
                if i >= pitches.shape[1]:
                    break

                # Pegar pitch médio na janela
                pitch_window = pitches[:, i]
                pitch_window = pitch_window[pitch_window > 0]  # Remover zeros

                if len(pitch_window) > 0:
                    avg_pitch = np.mean(pitch_window)

                    # Pitch alto indica excitação (> 300 Hz)
                    if avg_pitch > 300:
                        timestamp = librosa.frames_to_time(i, sr=sr, hop_length=512)

                        peaks.append({
                            'timestamp': timestamp,
                            'type': 'excitement',
                            'intensity': min(avg_pitch / 500.0, 1.0),
                            'duration': 0.5
                        })

            logger.info(f"      Encontrados {len(peaks)} momentos de excitação")

        except Exception as e:
            logger.warning(f"      Erro na detecção de excitação: {e}")

        return peaks

    def get_high_intensity_moments(self, emotion_peaks: List[Dict], threshold: float = 0.7) -> List[Dict]:
        """
        Filtra apenas momentos de alta intensidade emocional

        Args:
            emotion_peaks: Lista de picos emocionais
            threshold: Intensidade mínima (0-1)

        Returns:
            Lista filtrada de picos de alta intensidade
        """
        return [peak for peak in emotion_peaks if peak['intensity'] >= threshold]

    def cluster_nearby_peaks(self, emotion_peaks: List[Dict], time_window: float = 5.0) -> List[Dict]:
        """
        Agrupa picos próximos em clusters (momentos emocionais)

        Args:
            emotion_peaks: Lista de picos emocionais
            time_window: Janela de tempo para agrupar (segundos)

        Returns:
            Lista de clusters emocional
        """
        if not emotion_peaks:
            return []

        clusters = []
        current_cluster = [emotion_peaks[0]]

        for peak in emotion_peaks[1:]:
            if peak['timestamp'] - current_cluster[-1]['timestamp'] <= time_window:
                current_cluster.append(peak)
            else:
                # Finalizar cluster atual
                clusters.append(self._merge_cluster(current_cluster))
                current_cluster = [peak]

        # Adicionar último cluster
        clusters.append(self._merge_cluster(current_cluster))

        return clusters

    def _merge_cluster(self, peaks: List[Dict]) -> Dict:
        """Mescla múltiplos picos em um único cluster"""
        return {
            'timestamp': peaks[0]['timestamp'],
            'end': peaks[-1]['timestamp'] + peaks[-1]['duration'],
            'types': list(set(p['type'] for p in peaks)),
            'intensity': np.mean([p['intensity'] for p in peaks]),
            'peak_count': len(peaks)
        }


# Alias para compatibilidade
AudioAnalyzer = AudioEmotionAnalyzer


if __name__ == "__main__":
    # Teste rápido
    analyzer = AudioEmotionAnalyzer()

    # Exemplo (descomente para testar)
    # peaks = analyzer.detect_emotion_peaks(Path("temp/audio_test.mp3"))
    # print(f"Picos encontrados: {len(peaks)}")
