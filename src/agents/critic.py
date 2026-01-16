"""
Agente Crítico (Fase 10)
Usa Gemini AI para avaliação inteligente de qualidade de clips
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import json
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Tentar importar Gemini
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai não instalado.")


class CriticAgent:
    """
    Agente Crítico: Avalia qualidade de clips usando Gemini AI

    Responsabilidades:
    - Avaliar qualidade geral do clipe (0-10)
    - Identificar problemas específicos
    - Decidir se precisa refazer
    - Sugerir melhorias específicas
    """

    def __init__(self, min_score: float = 7.0, max_iterations: int = 3):
        self.min_score = min_score
        self.max_iterations = max_iterations
        self.gemini_client = None

        api_key = os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("⭐ Agente Crítico: ONLINE (Gemini 1.5 Flash)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao conectar Gemini: {e}")
        else:
            logger.info("⭐ Agente Crítico: Modo Offline (Avaliação Local)")

    def evaluate_clip(self, clip_data: Dict) -> Dict:
        """
        Avalia qualidade de um clipe usando Gemini

        Args:
            clip_data: Dados do clipe (hook, score viral, transcrição, etc)

        Returns:
            Avaliação detalhada com score e sugestões
        """
        logger.info("🔍 AGENTE CRÍTICO - Avaliando qualidade do clipe")

        # Tentar usar Gemini primeiro
        if self.gemini_client:
            try:
                return self._evaluate_with_gemini(clip_data)
            except Exception as e:
                logger.warning(f"⚠️ Gemini falhou: {e}. Usando avaliação local.")

        # Fallback local
        return self._evaluate_locally(clip_data)

    def _evaluate_with_gemini(self, clip_data: Dict) -> Dict:
        """Avaliação usando Gemini AI"""
        logger.info("   🧠 Usando Gemini AI para avaliação profunda...")

        prompt = f"""
Você é um especialista em conteúdo viral para redes sociais (TikTok, Reels, Shorts).

Avalie este clip de vídeo e dê notas de 0-10 para cada critério.

DADOS DO CLIP:
- Hook/Título: {clip_data.get('hook', 'Não definido')}
- Score Viral Inicial: {clip_data.get('viral_score', 0)}
- Duração: {clip_data.get('duration', 0)} segundos
- Keywords: {clip_data.get('keywords', [])}
- Transcrição Preview: {clip_data.get('text_preview', 'Não disponível')[:300]}
- Razão da Seleção: {clip_data.get('reason', 'Não especificada')}

CRITÉRIOS DE AVALIAÇÃO:
1. HOOK (0-10): O título/gancho captura atenção imediatamente?
2. VIRAL_POTENTIAL (0-10): Probabilidade de viralizar nas redes?
3. DURATION (0-10): Duração ideal para a plataforma? (30-60s é ideal)
4. EMOTION (0-10): Causa reação emocional forte?
5. VALUE (0-10): Oferece valor real (entretenimento, aprendizado)?
6. REWATCH (0-10): Pessoas vão querer assistir de novo?

RESPONDA EM JSON (SOMENTE JSON, sem markdown):
{{
    "overall_score": 8.5,
    "approved": true,
    "criteria": {{
        "hook": 9.0,
        "viral_potential": 8.5,
        "duration": 9.0,
        "emotion": 8.0,
        "value": 8.5,
        "rewatch": 7.5
    }},
    "strengths": ["ponto forte 1", "ponto forte 2"],
    "weaknesses": ["ponto fraco 1"],
    "issues": ["problema específico se houver"],
    "suggestions": ["sugestão de melhoria 1", "sugestão 2"],
    "verdict": "APROVADO/REPROVADO - Explicação curta",
    "platform_recommendation": "TikTok/Reels/Shorts/YouTube",
    "best_posting_time": "horário ideal para postar",
    "hashtag_suggestions": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}
"""

        response = self.gemini_client.generate_content(prompt)
        text = response.text.strip()

        # Limpar markdown
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Resposta do Gemini não é JSON válido")
            return self._evaluate_locally(clip_data)

        evaluation = {
            'overall_score': data.get('overall_score', 5.0),
            'approved': data.get('approved', False),
            'criteria': data.get('criteria', {}),
            'issues': data.get('issues', []),
            'suggestions': data.get('suggestions', []),
            'iteration': clip_data.get('iteration', 1),
            'gemini_analysis': True,
            'verdict': data.get('verdict', ''),
            'strengths': data.get('strengths', []),
            'weaknesses': data.get('weaknesses', []),
            'platform_recommendation': data.get('platform_recommendation', 'TikTok'),
            'hashtags': data.get('hashtag_suggestions', [])
        }

        # Override approved based on our min_score
        evaluation['approved'] = evaluation['overall_score'] >= self.min_score

        status = "✅ APROVADO" if evaluation['approved'] else "❌ REJEITADO"
        logger.info(f"   Score Gemini: {evaluation['overall_score']}/10 - {status}")
        logger.info(f"   Veredicto: {evaluation['verdict']}")

        return evaluation

    def _evaluate_locally(self, clip_data: Dict) -> Dict:
        """Avaliação local usando regras fixas"""
        logger.info("   📝 Usando avaliação local...")

        evaluation = {
            'overall_score': 0.0,
            'approved': False,
            'criteria': {},
            'issues': [],
            'suggestions': [],
            'iteration': clip_data.get('iteration', 1),
            'gemini_analysis': False
        }

        # Avaliar hook
        hook_score = self._evaluate_hook(clip_data.get('hook', ''))
        evaluation['criteria']['hook'] = hook_score

        # Avaliar score viral
        viral_score = clip_data.get('viral_score', 0)
        evaluation['criteria']['viral_potential'] = viral_score

        # Avaliar duração
        duration_score = self._evaluate_duration(clip_data.get('duration', 0))
        evaluation['criteria']['duration'] = duration_score

        # Avaliar keywords
        keywords_score = self._evaluate_keywords(clip_data.get('keywords', []))
        evaluation['criteria']['keywords'] = keywords_score

        # Avaliar emoção
        emotion_score = clip_data.get('emotion_intensity', 0) * 10
        evaluation['criteria']['emotion'] = min(emotion_score, 10.0)

        # Calcular score geral
        weights = {
            'hook': 0.25,
            'viral_potential': 0.30,
            'duration': 0.10,
            'keywords': 0.15,
            'emotion': 0.20
        }

        overall = sum(
            evaluation['criteria'].get(k, 5) * weights[k]
            for k in weights.keys()
        )
        evaluation['overall_score'] = round(overall, 1)
        evaluation['approved'] = evaluation['overall_score'] >= self.min_score

        # Identificar problemas
        for criteria, score in evaluation['criteria'].items():
            if score < 6.0:
                evaluation['issues'].append(f"{criteria} fraco (score: {score:.1f})")

        evaluation['suggestions'] = self._generate_suggestions(evaluation)

        status = "✅ APROVADO" if evaluation['approved'] else "❌ REJEITADO"
        logger.info(f"   Score local: {evaluation['overall_score']}/10 - {status}")

        return evaluation

    def _evaluate_hook(self, hook: str) -> float:
        """Avalia qualidade do hook"""
        score = 5.0

        if not hook:
            return 0.0

        if 30 <= len(hook) <= 80:
            score += 1.0

        if any(ord(c) > 127 for c in hook):
            score += 1.0

        impact_words = ['segredo', 'verdade', 'nunca', 'sempre', 'dinheiro', 'sucesso', 'incrível']
        if any(word in hook.lower() for word in impact_words):
            score += 2.0

        if any(c.isdigit() for c in hook):
            score += 1.0

        return min(score, 10.0)

    def _evaluate_duration(self, duration: float) -> float:
        """Avalia se duração é ideal"""
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
        score = 5.0 + min(len(keywords) * 1.5, 5.0)
        return min(score, 10.0)

    def _generate_suggestions(self, evaluation: Dict) -> List[str]:
        """Gera sugestões de melhoria"""
        suggestions = []

        for criteria, score in evaluation['criteria'].items():
            if score < 7.0:
                if criteria == 'hook':
                    suggestions.append("Melhorar hook: adicionar emoji ou número")
                elif criteria == 'viral_potential':
                    suggestions.append("Incluir mais keywords de impacto")
                elif criteria == 'duration':
                    suggestions.append("Ajustar duração para 30-60 segundos")
                elif criteria == 'keywords':
                    suggestions.append("Adicionar mais keywords virais")
                elif criteria == 'emotion':
                    suggestions.append("Selecionar trecho com mais emoção")

        return suggestions

    def should_retry(self, evaluation: Dict) -> Tuple[bool, str]:
        """Decide se deve refazer o clipe"""
        if evaluation['approved']:
            return False, "Clipe aprovado"

        if evaluation['iteration'] >= self.max_iterations:
            return False, f"Limite de {self.max_iterations} iterações"

        if evaluation['overall_score'] < 4.0:
            return False, "Score muito baixo, momento não é viral"

        return True, "Score abaixo do mínimo, tentando melhorar"

    def get_refinement_instructions(self, evaluation: Dict) -> Dict:
        """Gera instruções de refinamento para outros agentes"""
        instructions = {
            'curator': [],
            'copywriter': [],
            'director': []
        }

        for criteria, score in evaluation.get('criteria', {}).items():
            if score < 7.0:
                if criteria == 'hook':
                    instructions['copywriter'].append("Gerar novo hook mais impactante")
                elif criteria == 'viral_potential':
                    instructions['curator'].append("Buscar momento com maior score")
                elif criteria == 'emotion':
                    instructions['curator'].append("Priorizar picos de emoção")
                elif criteria == 'keywords':
                    instructions['director'].append("Destacar keywords nas legendas")

        return instructions

    def batch_evaluate(self, clips: List[Dict]) -> List[Dict]:
        """Avalia múltiplos clips de uma vez"""
        logger.info(f"⭐ Avaliando {len(clips)} clips...")

        evaluations = []
        for i, clip in enumerate(clips):
            logger.info(f"   Clip {i+1}/{len(clips)}...")
            evaluation = self.evaluate_clip(clip)
            evaluation['clip_index'] = i
            evaluations.append(evaluation)

        # Ordenar por score
        evaluations.sort(key=lambda x: x['overall_score'], reverse=True)

        approved_count = sum(1 for e in evaluations if e['approved'])
        logger.info(f"✅ Avaliação concluída: {approved_count}/{len(clips)} aprovados")

        return evaluations
