"""
Agente Crítico (Fase 10)
Avalia qualidade do vídeo e decide se precisa refazer
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class CriticAgent:
    """
    Agente Crítico: Avalia qualidade e implementa loop de feedback

    Responsabilidades:
    - Avaliar qualidade geral do clipe (0-10)
    - Identificar problemas específicos
    - Decidir se precisa refazer
    - Sugerir melhorias específicas
    """

    def __init__(self, min_score: float = 8.0, max_iterations: int = 3):
        """
        Inicializa o agente crítico

        Args:
            min_score: Score mínimo para aprovar (0-10)
            max_iterations: Máximo de iterações de refinamento
        """
        self.min_score = min_score
        self.max_iterations = max_iterations

    def evaluate_clip(self, clip_data: Dict) -> Dict:
        """
        Avalia qualidade de um clipe

        Args:
            clip_data: Dados do clipe incluindo momento, hook, score viral

        Returns:
            Avaliação detalhada com score e sugestões
        """
        logger.info("🔍 AGENTE CRÍTICO - Avaliando qualidade do clipe")

        evaluation = {
            'overall_score': 0.0,
            'approved': False,
            'criteria': {},
            'issues': [],
            'suggestions': [],
            'iteration': clip_data.get('iteration', 1)
        }

        # 1. Avaliar hook
        hook_score = self._evaluate_hook(clip_data.get('hook', ''))
        evaluation['criteria']['hook'] = hook_score

        # 2. Avaliar score viral
        viral_score = clip_data.get('viral_score', 0)
        evaluation['criteria']['viral_potential'] = viral_score

        # 3. Avaliar duração
        duration_score = self._evaluate_duration(clip_data.get('duration', 0))
        evaluation['criteria']['duration'] = duration_score

        # 4. Avaliar keywords
        keywords_score = self._evaluate_keywords(clip_data.get('keywords', []))
        evaluation['criteria']['keywords'] = keywords_score

        # 5. Avaliar emoção
        emotion_score = clip_data.get('emotion_intensity', 0) * 10
        evaluation['criteria']['emotion'] = min(emotion_score, 10.0)

        # Calcular score geral (média ponderada)
        weights = {
            'hook': 0.25,
            'viral_potential': 0.30,
            'duration': 0.10,
            'keywords': 0.15,
            'emotion': 0.20
        }

        overall = sum(
            evaluation['criteria'][k] * weights[k]
            for k in weights.keys()
        )
        evaluation['overall_score'] = round(overall, 1)

        # Determinar se aprovado
        evaluation['approved'] = evaluation['overall_score'] >= self.min_score

        # Identificar problemas
        for criteria, score in evaluation['criteria'].items():
            if score < 6.0:
                evaluation['issues'].append(f"{criteria} fraco (score: {score:.1f})")

        # Gerar sugestões
        evaluation['suggestions'] = self._generate_suggestions(evaluation)

        # Log resultado
        status = "✅ APROVADO" if evaluation['approved'] else "❌ REJEITADO"
        logger.info(f"   Score geral: {evaluation['overall_score']}/10 - {status}")

        if evaluation['issues']:
            logger.info(f"   Problemas: {', '.join(evaluation['issues'])}")

        return evaluation

    def _evaluate_hook(self, hook: str) -> float:
        """Avalia qualidade do hook"""
        score = 5.0

        if not hook:
            return 0.0

        # Comprimento ideal
        if 30 <= len(hook) <= 80:
            score += 1.0

        # Tem emoji
        if any(ord(c) > 127 for c in hook):
            score += 1.0

        # Palavras de impacto
        impact_words = ['segredo', 'verdade', 'nunca', 'sempre', 'dinheiro', 'sucesso']
        if any(word in hook.lower() for word in impact_words):
            score += 2.0

        # Contém número
        if any(c.isdigit() for c in hook):
            score += 1.0

        return min(score, 10.0)

    def _evaluate_duration(self, duration: float) -> float:
        """Avalia se duração é ideal"""
        # Duração ideal: 30-60 segundos
        if 30 <= duration <= 60:
            return 10.0
        elif 20 <= duration < 30 or 60 < duration <= 90:
            return 7.0
        elif 15 <= duration < 20 or 90 < duration <= 120:
            return 5.0
        else:
            return 3.0

    def _evaluate_keywords(self, keywords: List[str]) -> float:
        """Avalia presença de keywords virais"""
        if not keywords:
            return 5.0

        # Mais keywords = melhor
        score = 5.0 + min(len(keywords) * 1.5, 5.0)
        return min(score, 10.0)

    def _generate_suggestions(self, evaluation: Dict) -> List[str]:
        """Gera sugestões de melhoria"""
        suggestions = []

        for criteria, score in evaluation['criteria'].items():
            if score < 7.0:
                if criteria == 'hook':
                    suggestions.append("Melhorar hook: adicionar emoji ou número específico")
                elif criteria == 'viral_potential':
                    suggestions.append("Aumentar potencial viral: incluir mais keywords de impacto")
                elif criteria == 'duration':
                    suggestions.append("Ajustar duração para 30-60 segundos")
                elif criteria == 'keywords':
                    suggestions.append("Adicionar mais keywords virais ao trecho")
                elif criteria == 'emotion':
                    suggestions.append("Selecionar trecho com mais picos de emoção")

        return suggestions

    def should_retry(self, evaluation: Dict) -> Tuple[bool, str]:
        """
        Decide se deve refazer o clipe

        Returns:
            Tupla (deve_refazer, razão)
        """
        if evaluation['approved']:
            return False, "Clipe aprovado"

        if evaluation['iteration'] >= self.max_iterations:
            return False, f"Limite de {self.max_iterations} iterações atingido"

        if evaluation['overall_score'] < 4.0:
            return False, "Score muito baixo, provavelmente momento não é viral"

        return True, "Score abaixo do mínimo, tentando melhorar"

    def get_refinement_instructions(self, evaluation: Dict) -> Dict:
        """
        Gera instruções de refinamento para outros agentes

        Returns:
            Instruções para Curador, Copywriter e Diretor
        """
        instructions = {
            'curator': [],
            'copywriter': [],
            'director': []
        }

        for criteria, score in evaluation['criteria'].items():
            if score < 7.0:
                if criteria == 'hook':
                    instructions['copywriter'].append("Gerar novo hook mais impactante")
                elif criteria == 'viral_potential':
                    instructions['curator'].append("Buscar momento com maior score viral")
                elif criteria == 'emotion':
                    instructions['curator'].append("Priorizar momentos com picos de emoção")
                elif criteria == 'keywords':
                    instructions['director'].append("Destacar keywords existentes nas legendas")

        return instructions


if __name__ == "__main__":
    # Teste rápido
    critic = CriticAgent()

    test_clip = {
        'hook': '💰 O segredo para ganhar dinheiro rápido',
        'viral_score': 8.5,
        'duration': 45,
        'keywords': ['dinheiro', 'segredo', 'rápido'],
        'emotion_intensity': 0.8,
        'iteration': 1
    }

    evaluation = critic.evaluate_clip(test_clip)
    print(f"Score: {evaluation['overall_score']}")
    print(f"Aprovado: {evaluation['approved']}")
