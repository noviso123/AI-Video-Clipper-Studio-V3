"""
Módulo de Transcrição (Stage 2)
Transcreve áudio usando OpenAI Whisper com timestamps word-level
"""
from typing import List, Dict, Optional
from pathlib import Path
import whisper
import json
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class AudioTranscriber:
    """Transcrição de áudio usando Whisper"""

    def __init__(self, model_name: Optional[str] = None):
        """
        Inicializa o transcriber

        Args:
            model_name: Nome do modelo Whisper (tiny, base, small, medium, large)
                       Se None, usa o configurado em Config
        """
        self.model_name = model_name or Config.WHISPER_MODEL
        self.language = Config.WHISPER_LANGUAGE
        self.model = None

        logger.info(f"🎤 Inicializando Whisper modelo: {self.model_name}")

    def load_model(self):
        """Carrega o modelo Whisper (lazy loading)"""
        if self.model is None:
            logger.info(f"⏳ Carregando modelo Whisper '{self.model_name}'...")
            logger.info("   (Primeira execução pode demorar - baixando modelo)")

            try:
                self.model = whisper.load_model(self.model_name)
                logger.info("✅ Modelo carregado com sucesso!")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo: {e}")
                raise

    def transcribe(self, audio_path: Path) -> List[Dict]:
        """
        Transcreve áudio com timestamps

        Args:
            audio_path: Caminho do arquivo de áudio

        Returns:
            Lista de segmentos com transcrição e timestamps:
            [
                {
                    'start': 0.0,
                    'end': 2.5,
                    'text': 'Olá pessoal',
                    'words': [  # Se disponível
                        {'word': 'Olá', 'start': 0.0, 'end': 0.5},
                        {'word': 'pessoal', 'start': 0.6, 'end': 2.5}
                    ]
                },
                ...
            ]
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")

        self.load_model()

        logger.info(f"🎙️ Transcrevendo: {audio_path.name}")
        logger.info(f"   Modelo: {self.model_name}")
        logger.info(f"   Idioma: {self.language}")

        try:
            # Transcrição com Whisper
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                task='transcribe',
                verbose=Config.DEBUG_MODE,
                word_timestamps=True  # Ativa timestamps word-level
            )

            segments = []
            for segment in result['segments']:
                segment_data = {
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                }

                # Adicionar timestamps de palavras se disponíveis
                if 'words' in segment:
                    segment_data['words'] = [
                        {
                            'word': word['word'].strip(),
                            'start': word['start'],
                            'end': word['end']
                        }
                        for word in segment['words']
                    ]

                segments.append(segment_data)

            total_duration = segments[-1]['end'] if segments else 0
            logger.info(f"✅ Transcrição concluída!")
            logger.info(f"   Total de segmentos: {len(segments)}")
            logger.info(f"   Duração: {total_duration//60:.0f}:{total_duration%60:02.0f}")

            return segments

        except Exception as e:
            logger.error(f"❌ Erro na transcrição: {e}")
            raise

    def export_srt(self, segments: List[Dict], output_path: Path):
        """
        Exporta transcrição no formato SRT (legendas)

        Args:
            segments: Lista de segmentos da transcrição
            output_path: Caminho do arquivo SRT de saída
        """
        logger.info(f"💾 Exportando SRT: {output_path.name}")

        def format_timestamp(seconds: float) -> str:
            """Converte segundos para formato SRT (HH:MM:SS,mmm)"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
                f.write(f"{segment['text']}\n\n")

        logger.info(f"✅ SRT exportado com sucesso!")

    def export_json(self, segments: List[Dict], output_path: Path):
        """
        Exporta transcrição no formato JSON

        Args:
            segments: Lista de segmentos da transcrição
            output_path: Caminho do arquivo JSON de saída
        """
        logger.info(f"💾 Exportando JSON: {output_path.name}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'model': self.model_name,
                'language': self.language,
                'segments': segments
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ JSON exportado com sucesso!")

    def get_words_in_range(self, segments: List[Dict], start_time: float, end_time: float) -> List[Dict]:
        """
        Extrai palavras dentro de um intervalo de tempo específico

        Args:
            segments: Lista de segmentos da transcrição
            start_time: Tempo inicial em segundos
            end_time: Tempo final em segundos

        Returns:
            Lista de palavras com timestamps dentro do intervalo
        """
        words_in_range = []

        for segment in segments:
            # Pular segmentos fora do intervalo
            if segment['end'] < start_time or segment['start'] > end_time:
                continue

            # Se o segmento tem palavras individuais
            if 'words' in segment:
                for word in segment['words']:
                    if start_time <= word['start'] <= end_time or start_time <= word['end'] <= end_time:
                        words_in_range.append(word)
            else:
                # Se não tem palavras individuais, usar o segmento completo
                if start_time <= segment['start'] <= end_time:
                    words_in_range.append({
                        'word': segment['text'],
                        'start': segment['start'],
                        'end': segment['end']
                    })

        return words_in_range


if __name__ == "__main__":
    # Teste rápido
    transcriber = AudioTranscriber(model_name='tiny')  # Usar tiny para testes

    # Exemplo (descomente para testar)
    # segments = transcriber.transcribe(Path("temp/audio_test.mp3"))
    # print(f"Total de segmentos: {len(segments)}")
