"""
Agente Diretor (Fase 9)
Planeja edição frame-a-frame e coordena outros agentes
"""
from typing import List, Dict, Optional
from pathlib import Path
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class DirectorAgent:
    """
    Agente Diretor: Planeja e coordena a edição

    Responsabilidades:
    - Criar plano de edição frame-a-frame
    - Decidir onde inserir B-Rolls
    - Definir timing de legendas
    - Coordenar Copywriter e Executor
    """

    def __init__(self):
        self.edit_plan = []

    def create_edit_plan(
        self,
        transcript_segments: List[Dict],
        emotion_peaks: List[Dict],
        moment: Dict
    ) -> Dict:
        """
        Cria plano de edição detalhado para um clipe

        Args:
            transcript_segments: Segmentos da transcrição
            emotion_peaks: Picos de emoção detectados
            moment: Momento viral selecionado

        Returns:
            Plano de edição estruturado
        """
        logger.info("🎬 AGENTE DIRETOR - Criando plano de edição")

        start = moment['start']
        end = moment['end']
        duration = end - start

        # Estrutura do plano
        edit_plan = {
            'duration': duration,
            'start': start,
            'end': end,
            'hook': moment['hook'],
            'score': moment['score'],
            'sections': [],
            'broll_moments': [],
            'caption_moments': [],
            'effects': []
        }

        # 1. Definir seções do clipe
        edit_plan['sections'] = self._define_sections(duration)

        # 2. Identificar momentos para B-Rolls
        edit_plan['broll_moments'] = self._identify_broll_moments(
            transcript_segments, start, end
        )

        # 3. Definir momentos de legendas
        edit_plan['caption_moments'] = self._define_caption_timing(
            transcript_segments, start, end
        )

        # 4. Sugerir efeitos
        edit_plan['effects'] = self._suggest_effects(emotion_peaks, start, end)

        logger.info(f"   ✅ Plano criado:")
        logger.info(f"      - {len(edit_plan['sections'])} seções")
        logger.info(f"      - {len(edit_plan['broll_moments'])} B-Rolls")
        logger.info(f"      - {len(edit_plan['caption_moments'])} momentos de legenda")
        logger.info(f"      - {len(edit_plan['effects'])} efeitos sugeridos")

        return edit_plan

    def _define_sections(self, duration: float) -> List[Dict]:
        """Define seções do clipe (intro, body, outro)"""
        sections = []

        # Intro (primeiros 3 segundos)
        sections.append({
            'name': 'intro',
            'start': 0,
            'end': min(3, duration * 0.1),
            'notes': 'Hook inicial - capturar atenção'
        })

        # Body (meio do clipe)
        sections.append({
            'name': 'body',
            'start': 3,
            'end': duration - 3,
            'notes': 'Conteúdo principal'
        })

        # Outro (últimos 3 segundos)
        sections.append({
            'name': 'outro',
            'start': duration - 3,
            'end': duration,
            'notes': 'Call to action ou cliffhanger'
        })

        return sections

    def _identify_broll_moments(
        self,
        segments: List[Dict],
        start: float,
        end: float
    ) -> List[Dict]:
        """Identifica momentos ideais para B-Rolls"""
        broll_moments = []

        # Palavras-chave que sugerem B-Roll
        broll_keywords = ['dinheiro', 'sucesso', 'viagem', 'comida', 'tecnologia', 'trabalho']

        for segment in segments:
            if segment['start'] >= start and segment['end'] <= end:
                text_lower = segment['text'].lower()

                for keyword in broll_keywords:
                    if keyword in text_lower:
                        broll_moments.append({
                            'timestamp': segment['start'] - start,  # Relativo ao clipe
                            'duration': 2.0,
                            'keyword': keyword,
                            'text': segment['text']
                        })
                        break

        return broll_moments[:3]  # Máximo 3 B-Rolls

    def _define_caption_timing(
        self,
        segments: List[Dict],
        start: float,
        end: float
    ) -> List[Dict]:
        """Define timing das legendas"""
        caption_moments = []

        for segment in segments:
            if segment['start'] >= start and segment['end'] <= end:
                caption_moments.append({
                    'start': segment['start'] - start,
                    'end': segment['end'] - start,
                    'text': segment['text'],
                    'emphasis': self._detect_emphasis(segment['text'])
                })

        return caption_moments

    def _detect_emphasis(self, text: str) -> bool:
        """Detecta se o texto precisa de ênfase"""
        emphasis_words = ['importante', 'nunca', 'sempre', 'cuidado', 'segredo', 'verdade']
        text_lower = text.lower()
        return any(word in text_lower for word in emphasis_words)

    def _suggest_effects(
        self,
        emotion_peaks: List[Dict],
        start: float,
        end: float
    ) -> List[Dict]:
        """Sugere efeitos baseados nos picos de emoção"""
        effects = []

        for peak in emotion_peaks:
            if start <= peak['timestamp'] <= end:
                timestamp_relative = peak['timestamp'] - start

                if peak['type'] == 'volume_spike':
                    effects.append({
                        'timestamp': timestamp_relative,
                        'type': 'zoom_in',
                        'intensity': peak['intensity'],
                        'duration': 0.5
                    })
                elif peak['type'] == 'silence':
                    effects.append({
                        'timestamp': timestamp_relative,
                        'type': 'slow_motion',
                        'intensity': 0.5,
                        'duration': peak['duration']
                    })
                elif peak['type'] == 'excitement':
                    effects.append({
                        'timestamp': timestamp_relative,
                        'type': 'shake',
                        'intensity': peak['intensity'] * 0.3,
                        'duration': 0.3
                    })

        return effects[:5]  # Máximo 5 efeitos


if __name__ == "__main__":
    # Teste rápido
    director = DirectorAgent()

    test_moment = {
        'start': 10.0,
        'end': 40.0,
        'hook': 'O segredo do sucesso',
        'score': 9.0
    }

    plan = director.create_edit_plan([], [], test_moment)
    print(f"Plano criado com {len(plan['sections'])} seções")
