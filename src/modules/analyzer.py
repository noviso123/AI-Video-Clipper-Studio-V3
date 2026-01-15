"""
Módulo de Análise Viral (Stage 3)
Identifica momentos virais usando análise de texto local
"""
from typing import List, Dict, Optional
from pathlib import Path
import re
from collections import Counter
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class ViralAnalyzer:
    """Analisa transcrição e emoções para identificar momentos virais"""

    def __init__(self):
        # Palavras-chave virais (triggers emocionais)
        self.viral_keywords = {
            'dinheiro': ['dinheiro', 'real', 'reais', 'mil', 'milhão', 'rico', 'renda', 'ganhar', 'lucro'],
            'segredo': ['segredo', 'verdade', 'ninguém', 'escondido', 'revelar'],
            'urgência': ['agora', 'hoje', 'rápido', 'urgente', 'última chance'],
            'polêmica': ['polêmica', 'controverso', 'chocante', 'absurdo', 'inacreditável'],
            'sucesso': ['sucesso', 'vitória', 'conquista', 'resultado', 'transformação'],
            'erro': ['erro', 'errado', 'falha', 'problema', 'armadilha'],
            'emoção': ['amor', 'medo', 'raiva', 'feliz', 'triste', 'chorar']
        }

    def analyze_transcript(
        self,
        segments: List[Dict],
        emotion_peaks: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Analisa transcrição e identifica momentos virais

        Args:
            segments: Lista de segmentos da transcrição
            emotion_peaks: Lista opcional de picos emocionais do áudio

        Returns:
            Lista de momentos virais ordenados por score:
            [
                {
                    'start': 125.0,
                    'end': 155.0,
                    'score': 9.5,
                    'hook': 'O segredo para ganhar R$ 10mil/mês',
                    'reason': 'Promessa forte + número específico',
                    'keywords': ['dinheiro', 'segredo'],
                    'emotion_intensity': 0.8
                },
                ...
            ]
        """
        logger.info("🔍 Analisando potencial viral da transcrição...")

        viral_moments = []

        # Analisar cada segmento possível de 30-60 segundos
        clip_min = Config.CLIP_DURATION_MIN
        clip_max = Config.CLIP_DURATION_MAX

        for i, segment in enumerate(segments):
            start_time = segment['start']

            # Tentar diferentes durações
            for duration in [30, 45, 60]:
                if duration < clip_min or duration > clip_max:
                    continue

                end_time = start_time + duration

                # Coletar texto neste intervalo
                clip_text = self._get_text_in_range(segments, start_time, end_time)

                if not clip_text:
                    continue

                # Calcular score viral
                score_data = self._calculate_viral_score(
                    clip_text,
                    start_time,
                    end_time,
                    emotion_peaks
                )

                if score_data['score'] >= 6.0:  # Threshold mínimo
                    viral_moments.append({
                        'start': start_time,
                        'end': end_time,
                        'score': score_data['score'],
                        'hook': self._generate_hook(clip_text),
                        'reason': score_data['reason'],
                        'keywords': score_data['keywords'],
                        'emotion_intensity': score_data['emotion_intensity'],
                        'text_preview': clip_text[:100] + '...'
                    })

        # Ordenar por score (melhor primeiro)
        viral_moments.sort(key=lambda x: x['score'], reverse=True)

        # Remover sobreposições (manter apenas o melhor em cada região)
        viral_moments = self._remove_overlaps(viral_moments)

        logger.info(f"✅ {len(viral_moments)} momentos virais identificados")

        return viral_moments

    def _get_text_in_range(self, segments: List[Dict], start: float, end: float) -> str:
        """Extrai texto dentro de um intervalo de tempo"""
        texts = []
        for seg in segments:
            if seg['start'] >= start and seg['end'] <= end:
                texts.append(seg['text'])
            elif seg['start'] < end and seg['end'] > start:
                # Sobreposição parcial
                texts.append(seg['text'])

        return ' '.join(texts)

    def _calculate_viral_score(
        self,
        text: str,
        start: float,
        end: float,
        emotion_peaks: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calcula score viral de um trecho

        Returns:
            {
                'score': float,
                'reason': str,
                'keywords': List[str],
                'emotion_intensity': float
            }
        """
        score = 5.0  # Base score
        reasons = []
        found_keywords = []

        text_lower = text.lower()

        # 1. Análise de palavras-chave (+3 pontos máximo)
        keyword_score = 0
        for category, keywords in self.viral_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_score += 0.5
                    found_keywords.append(keyword)
                    if keyword_score == 0.5:  # Primeira vez
                        reasons.append(f"Contém palavra viral: {category}")

        score += min(keyword_score, 3.0)

        # 2. Análise de números (+1 ponto)
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            score += 1.0
            reasons.append("Contém números específicos")

        # 3. Análise de perguntas (+0.5 pontos)
        if '?' in text or any(word in text_lower for word in ['como', 'por que', 'qual']):
            score += 0.5
            reasons.append("Contém pergunta")

        # 4. Análise de emoção do áudio (+2 pontos máximo)
        emotion_intensity = 0.0
        if emotion_peaks:
            # Verificar se há picos emocionais neste intervalo
            peaks_in_range = [
                p for p in emotion_peaks
                if start <= p['timestamp'] <= end
            ]

            if peaks_in_range:
                emotion_intensity = sum(p['intensity'] for p in peaks_in_range) / len(peaks_in_range)
                score += emotion_intensity * 2.0
                reasons.append(f"Picos emocionais detectados ({len(peaks_in_range)})")

        # 5. Análise de início forte (+1 ponto)
        first_words = text_lower.split()[:5]
        strong_starts = ['olha', 'cuidado', 'atenção', 'nunca', 'sempre', 'todo', 'ninguém']
        if any(word in first_words for word in strong_starts):
            score += 1.0
            reasons.append("Início forte")

        # Limitar score máximo a 10
        score = min(score, 10.0)

        return {
            'score': round(score, 1),
            'reason': ' | '.join(reasons) if reasons else 'Análise padrão',
            'keywords': list(set(found_keywords)),
            'emotion_intensity': emotion_intensity
        }

    def _generate_hook(self, text: str) -> str:
        """Gera um hook (título) viral para o clipe"""
        # Pegar primeira frase ou primeiras 60 caracteres
        sentences = text.split('.')
        first_sentence = sentences[0].strip()

        if len(first_sentence) > 60:
            # Truncar e adicionar reticências
            hook = first_sentence[:57] + '...'
        else:
            hook = first_sentence

        # Capitalizar
        hook = hook.capitalize()

        # Adicionar emoji se contiver palavras-chave
        text_lower = text.lower()
        if any(word in text_lower for word in ['dinheiro', 'rico', 'mil']):
            hook = '💰 ' + hook
        elif any(word in text_lower for word in ['segredo', 'verdade']):
            hook = '🔥 ' + hook
        elif any(word in text_lower for word in ['cuidado', 'erro', 'armadilha']):
            hook = '⚠️ ' + hook

        return hook

    def _remove_overlaps(self, moments: List[Dict], min_gap: float = 10.0) -> List[Dict]:
        """
        Remove momentos sobrepostos, mantendo apenas o de maior score

        Args:
            moments: Lista de momentos virais
            min_gap: Gap mínimo entre momentos (segundos)
        """
        if not moments:
            return []

        filtered = [moments[0]]

        for moment in moments[1:]:
            # Verificar se sobrepõe com o último adicionado
            last = filtered[-1]

            if moment['start'] >= last['end'] + min_gap:
                # Não sobrepõe, adicionar
                filtered.append(moment)
            # Se sobrepõe, não adiciona (pois moments está ordenado por score)

        return filtered


if __name__ == "__main__":
    # Teste rápido
    analyzer = ViralAnalyzer()

    # Exemplo de segmentos
    test_segments = [
        {'start': 0.0, 'end': 5.0, 'text': 'O segredo para ganhar dinheiro rápido'},
        {'start': 5.0, 'end': 10.0, 'text': 'que ninguém te conta é este aqui'},
        {'start': 10.0, 'end': 15.0, 'text': 'você precisa investir mil reais'},
    ]

    moments = analyzer.analyze_transcript(test_segments)
    print(f"Momentos virais: {len(moments)}")
    if moments:
        print(f"Melhor score: {moments[0]['score']}")
