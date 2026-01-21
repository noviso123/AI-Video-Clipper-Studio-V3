"""
Analisador Viral Profissional (Nível IA) - 100% Offline
Sistema de scoring avançado sem dependência de LLMs.
Score normalizado de 0-100 para cada momento viral.
"""
import re
import math
from typing import List, Dict, Tuple
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class ViralAnalyzer:
    """
    Analisador Profissional de Momentos Virais.

    Score Final (0-100) = Combinação ponderada de:
    - Hook Score (25%): Força do gancho inicial
    - Emotion Score (25%): Intensidade emocional
    - Structure Score (20%): Padrões de estrutura viral
    - Engagement Score (15%): Previsão de engajamento
    - Rhythm Score (15%): Ritmo e cadência da fala
    """

    def __init__(self):
        self._init_trigger_database()
        self._init_emotion_lexicon()
        self._init_engagement_patterns()

    def _init_trigger_database(self):
        """Base de dados de gatilhos mentais com scores."""
        self.triggers = {
            # === GATILHOS DE ABERTURA (Hooks) ===
            'hook_power': {
                'peso': 20,
                'frases': [
                    'você não vai acreditar', 'isso vai mudar', 'o segredo que',
                    'ninguém te contou', 'pare tudo', 'atenção', 'urgente',
                    'descobri algo', 'finalmente revelado', 'a verdade sobre',
                    'você precisa saber', 'antes que seja tarde', 'cuidado com'
                ]
            },
            # === GATILHOS DE CURIOSIDADE ===
            'curiosidade': {
                'peso': 15,
                'frases': [
                    'por que', 'como é possível', 'o que acontece quando',
                    'você sabia que', 'incrível', 'surpreendente', 'chocante',
                    'inesperado', 'nunca imaginei', 'impressionante'
                ]
            },
            # === GATILHOS DE AÇÃO ===
            'acao': {
                'peso': 12,
                'frases': [
                    'faça isso agora', 'tente isso', 'experimente', 'comece',
                    'pare de', 'nunca mais', 'sempre faça', 'evite'
                ]
            },
            # === GATILHOS DE PROVA ===
            'prova': {
                'peso': 10,
                'frases': [
                    'comprovado', 'resultados', 'funciona', 'testei',
                    'na prática', 'exemplo real', 'caso de sucesso'
                ]
            },
            # === GATILHOS NUMÉRICOS ===
            'numeros': {
                'peso': 8,
                'patterns': [
                    r'\d+\s*(dicas|formas|maneiras|passos|segredos)',
                    r'(primeiro|segundo|terceiro|último)',
                    r'\d+%', r'r\$\s*\d+'
                ]
            }
        }

    def _init_emotion_lexicon(self):
        """Léxico de emoções com intensidade."""
        self.emotions = {
            # Emoções Positivas Fortes (score alto)
            'positivo_forte': {
                'score': 15,
                'words': [
                    'incrível', 'fantástico', 'maravilhoso', 'extraordinário',
                    'espetacular', 'sensacional', 'perfeito', 'excelente',
                    'impressionante', 'revolucionário', 'transformador'
                ]
            },
            # Emoções Positivas Médias
            'positivo_medio': {
                'score': 8,
                'words': [
                    'bom', 'ótimo', 'legal', 'interessante', 'útil',
                    'funciona', 'ajuda', 'resolve', 'melhora'
                ]
            },
            # Emoções Negativas (geram curiosidade)
            'negativo_forte': {
                'score': 12,
                'words': [
                    'erro', 'problema', 'perigo', 'cuidado', 'evite',
                    'terrível', 'horrível', 'desastre', 'catástrofe',
                    'fracasso', 'falha', 'prejuízo'
                ]
            },
            # Emoções de Surpresa
            'surpresa': {
                'score': 14,
                'words': [
                    'chocante', 'surpreendente', 'inesperado', 'inacreditável',
                    'impressionante', 'absurdo', 'loucura', 'bizarro'
                ]
            },
            # Emoções de Urgência
            'urgencia': {
                'score': 13,
                'words': [
                    'agora', 'urgente', 'rápido', 'imediato', 'antes',
                    'última chance', 'não perca', 'corra', 'aproveite'
                ]
            }
        }

    def _init_engagement_patterns(self):
        """Padrões que indicam alto engajamento."""
        self.engagement_patterns = {
            'pergunta_direta': {
                'score': 10,
                'pattern': r'\?'
            },
            'call_to_action': {
                'score': 12,
                'keywords': ['comenta', 'compartilha', 'salva', 'segue', 'curte', 'manda']
            },
            'frase_curta_impacto': {
                'score': 8,
                'max_words': 7
            },
            'numero_lista': {
                'score': 10,
                'pattern': r'^[0-9]+[\.\)]'
            }
        }

    # =========================================================================
    # MÉTODOS PRINCIPAIS
    # =========================================================================

    def analyze_transcript(
        self,
        segments: List[Dict],
        min_duration: int = 30,
        max_duration: int = 60
    ) -> List[Dict]:
        """
        Análise profissional de momentos virais.
        Retorna lista de momentos com score normalizado (0-100).
        """
        logger.info("🔬 Análise Viral Profissional (Modo Offline)")
        logger.info("   📊 Calculando scores multidimensionais...")

        if not segments:
            logger.warning("⚠️ Nenhum segmento para analisar")
            return self._create_fallback(min_duration, max_duration)

        candidates = []

        for i, seg in enumerate(segments):
            text = seg.get('text', '').strip()
            if not text:
                continue

            # Calcular todos os scores
            scores = self._calculate_all_scores(text, i, segments)
            final_score = scores['final']

            # Só considerar se score >= 30
            if final_score >= 30:
                start = seg['start']
                end, full_text = self._expand_segment(
                    segments, i, start, min_duration, max_duration
                )

                if end - start >= min_duration:
                    hook = self._generate_hook(text, scores)

                    candidates.append({
                        'start': round(start, 2),
                        'end': round(end, 2),
                        'duration': round(end - start, 2),
                        'score': round(final_score, 1),
                        'scores_detail': scores,  # Detalhes para debug
                        'hook': hook,
                        'full_text': full_text,
                        'metadata': self._generate_metadata(full_text, hook, final_score)
                    })

        # Fallback se não encontrou
        if not candidates:
            logger.info("   📊 Score médio baixo, usando fallback inteligente")
            return self._create_fallback(min_duration, max_duration, segments)

        # Ordenar e filtrar overlaps
        candidates.sort(key=lambda x: x['score'], reverse=True)
        final = self._remove_overlaps(candidates)

        logger.info(f"✅ {len(final)} momentos virais (scores: {[c['score'] for c in final[:3]]})")
        return final[:5]

    def _calculate_all_scores(self, text: str, idx: int, segments: List[Dict]) -> Dict:
        """
        Calcula todos os scores e retorna score final normalizado.

        Score Final = Média ponderada:
        - Hook (25%), Emotion (25%), Structure (20%), Engagement (15%), Rhythm (15%)
        """
        text_lower = text.lower()

        # Calcular cada dimensão (0-100)
        hook_score = self._calculate_hook_score(text_lower)
        emotion_score = self._calculate_emotion_score(text_lower)
        structure_score = self._calculate_structure_score(text_lower)
        engagement_score = self._calculate_engagement_score(text_lower)
        rhythm_score = self._calculate_rhythm_score(idx, segments)

        # Média ponderada
        final = (
            hook_score * 0.25 +
            emotion_score * 0.25 +
            structure_score * 0.20 +
            engagement_score * 0.15 +
            rhythm_score * 0.15
        )

        # Clamp para 0-100
        final = max(0, min(100, final))

        return {
            'hook': round(hook_score, 1),
            'emotion': round(emotion_score, 1),
            'structure': round(structure_score, 1),
            'engagement': round(engagement_score, 1),
            'rhythm': round(rhythm_score, 1),
            'final': round(final, 1)
        }

    # =========================================================================
    # CALCULADORES DE SCORE INDIVIDUAIS
    # =========================================================================

    def _calculate_hook_score(self, text: str) -> float:
        """Score do gancho (0-100)."""
        score = 0
        max_possible = 60

        # Gatilhos de abertura
        for category, data in self.triggers.items():
            if 'frases' in data:
                for frase in data['frases']:
                    if frase in text:
                        score += data['peso']
                        break  # Uma por categoria
            elif 'patterns' in data:
                for pattern in data['patterns']:
                    if re.search(pattern, text):
                        score += data['peso']
                        break

        # Começa com palavra poderosa
        power_starts = ['você', 'isso', 'atenção', 'cuidado', 'pare', 'nunca', 'o segredo']
        for word in power_starts:
            if text.startswith(word):
                score += 15
                break

        # Normalizar para 0-100
        return min(100, (score / max_possible) * 100)

    def _calculate_emotion_score(self, text: str) -> float:
        """Score de intensidade emocional (0-100)."""
        score = 0
        max_possible = 50

        words = text.split()

        for category, data in self.emotions.items():
            for word in data['words']:
                if word in text:
                    score += data['score']

        # Pontuação emotiva
        exclamations = text.count('!')
        score += min(10, exclamations * 3)

        # Caps lock (enfase)
        caps_words = len([w for w in words if w.isupper() and len(w) > 2])
        score += min(10, caps_words * 5)

        return min(100, (score / max_possible) * 100)

    def _calculate_structure_score(self, text: str) -> float:
        """Score de estrutura viral (0-100)."""
        score = 0
        max_possible = 50

        words = text.split()
        word_count = len(words)

        # Comprimento ideal (8-20 palavras)
        if 8 <= word_count <= 20:
            score += 15
        elif 5 <= word_count <= 25:
            score += 8

        # Tem pergunta
        if '?' in text:
            score += 12

        # Tem número
        if re.search(r'\d+', text):
            score += 8

        # Estrutura de lista
        if re.search(r'^[0-9]+[\.\)]', text):
            score += 10

        # Frases curtas e diretas (sem vírgulas demais)
        comma_ratio = text.count(',') / max(1, word_count)
        if comma_ratio < 0.1:
            score += 5

        return min(100, (score / max_possible) * 100)

    def _calculate_engagement_score(self, text: str) -> float:
        """Score de previsão de engajamento (0-100)."""
        score = 0
        max_possible = 40

        # Pergunta direta ao público
        if '?' in text and any(w in text for w in ['você', 'vocês', 'seu', 'sua']):
            score += 15

        # Call to action
        for kw in self.engagement_patterns['call_to_action']['keywords']:
            if kw in text:
                score += 10
                break

        # Frase curta de impacto
        if len(text.split()) <= 7:
            score += 8

        # Contém promessa de valor
        value_words = ['aprenda', 'descubra', 'ganhe', 'economize', 'resolva', 'melhore']
        for vw in value_words:
            if vw in text:
                score += 7
                break

        return min(100, (score / max_possible) * 100)

    def _calculate_rhythm_score(self, idx: int, segments: List[Dict]) -> float:
        """Score de ritmo e cadência (0-100)."""
        if not segments or len(segments) < 3:
            return 50  # Valor neutro

        score = 50  # Base
        max_possible = 50

        # Analisar variação de duração dos segmentos próximos
        window = segments[max(0, idx-2):min(len(segments), idx+3)]

        if len(window) >= 2:
            durations = []
            for i in range(len(window)):
                dur = window[i].get('end', 0) - window[i].get('start', 0)
                durations.append(dur)

            if durations:
                avg_dur = sum(durations) / len(durations)

                # Ritmo Frenético (TikTok/Reels) = MUITO viral
                if avg_dur < 3:
                    score += 30      # Era 25 (para < 5)
                elif avg_dur < 5:
                    score += 20      # Era 15
                elif avg_dur < 8:
                    score += 10      # Era 5

                # Variação moderada é boa (mantém interesse)
                if len(durations) > 1:
                    variance = sum((d - avg_dur) ** 2 for d in durations) / len(durations)
                    if 1 < variance < 10:
                        score += 10

        return min(100, score)

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def _expand_segment(
        self, segments: List[Dict], start_idx: int,
        start_time: float, min_dur: int, max_dur: int
    ) -> Tuple[float, str]:
        """Expande segmento até duração desejada."""
        end_time = start_time
        content = []

        for j in range(start_idx, len(segments)):
            seg_end = segments[j].get('end', 0)
            seg_text = segments[j].get('text', '')

            if seg_end - start_time <= max_dur:
                end_time = seg_end
                content.append(seg_text)
            else:
                break

        if end_time - start_time < min_dur:
            end_time = start_time + min_dur

        return end_time, ' '.join(content)

    def _generate_hook(self, text: str, scores: Dict) -> str:
        """Gera hook com base no score."""
        hook = text[:60].strip().upper()
        if len(text) > 60:
            hook = hook[:57] + '...'
        return hook

    def _remove_overlaps(self, candidates: List[Dict]) -> List[Dict]:
        """Remove candidatos sobrepostos."""
        final = []
        for cand in candidates:
            overlap = any(abs(cand['start'] - f['start']) < 20 for f in final)
            if not overlap:
                final.append(cand)
        return final

    def _create_fallback(
        self, min_dur: int, max_dur: int,
        segments: List[Dict] = None
    ) -> List[Dict]:
        """Fallback inteligente quando não encontra gatilhos."""
        if not segments:
            return [{
                'start': 0, 'end': min_dur, 'duration': min_dur,
                'score': 50.0, 'hook': 'ASSISTA ATÉ O FINAL!',
                'full_text': '', 'metadata': self._generate_metadata('', 'Momento Viral', 50)
            }]

        total_dur = segments[-1].get('end', 0) - segments[0].get('start', 0)
        clip_dur = (min_dur + max_dur) / 2
        num_clips = max(1, int(total_dur / clip_dur))

        results = []
        for i in range(min(num_clips, 5)):
            start = segments[0].get('start', 0) + (i * clip_dur)
            texts = [s['text'] for s in segments if start <= s.get('start', 0) <= start + clip_dur]

            results.append({
                'start': round(start, 2),
                'end': round(start + clip_dur, 2),
                'duration': round(clip_dur, 2),
                'score': 40.0,
                'hook': f'MOMENTO VIRAL #{i+1}',
                'full_text': ' '.join(texts[:3]),
                'metadata': self._generate_metadata(' '.join(texts), f'Momento {i+1}', 40)
            })

        return results

    def _generate_metadata(self, text: str, hook: str, score: float) -> Dict:
        """Gera metadados com score."""
        words = re.findall(r'\w{5,}', text.lower())
        unique_words = list(set(words))[:3]

        # Emoji baseado no score
        if score >= 80:
            emoji = '🔥'
        elif score >= 60:
            emoji = '⚡'
        elif score >= 40:
            emoji = '💡'
        else:
            emoji = '📹'

        return {
            'title': f"{emoji} {hook}",
            'hashtags': [f"#{w}" for w in unique_words] + ['#viral', '#shorts', '#trending'],
            'description': f"Score: {score}/100 - {text[:100]}..." if text else hook,
            'viral_titles': [
                f"🔥 {hook}",
                f"😱 {hook}",
                f"⚠️ VOCÊ PRECISA VER: {hook[:30]}..."
            ],
            'viral_score': score
        }
