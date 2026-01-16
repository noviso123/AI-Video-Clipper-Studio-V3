"""
Agente Copywriter (Fase 9)
Cria hooks e títulos virais para os clipes
Integrado com Gemini AI para geração inteligente
"""
from typing import List, Dict, Optional
import re
import os
import json
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Tentar importar Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai não instalado. Usando fallback local.")


class CopywriterAgent:
    """
    Agente Copywriter: Cria hooks e títulos virais
    Usa Gemini AI quando disponível para geração inteligente

    Responsabilidades:
    - Gerar múltiplas variações de hooks
    - Criar títulos chamativos
    - Otimizar para cada plataforma
    """

    # Templates de hooks virais (fallback)
    HOOK_TEMPLATES = {
        'curiosidade': [
            "Você não vai acreditar {topic}...",
            "O que ninguém te conta sobre {topic}",
            "A verdade sobre {topic} que choca",
            "Descubra por que {topic}",
        ],
        'urgencia': [
            "🚨 {topic} - Veja agora!",
            "⚠️ URGENTE: {topic}",
            "Pare tudo e veja {topic}",
            "Você precisa saber {topic} HOJE",
        ],
        'beneficio': [
            "Como {topic} em 30 dias",
            "O segredo para {topic}",
            "{topic}: Guia definitivo",
            "A fórmula exata para {topic}",
        ],
        'polêmica': [
            "A mentira sobre {topic}",
            "Por que {topic} está errado",
            "O erro fatal sobre {topic}",
            "Chocante: {topic}",
        ],
        'numero': [
            "3 formas de {topic}",
            "5 erros sobre {topic}",
            "7 segredos de {topic}",
            "10 dicas sobre {topic}",
        ]
    }

    # Emojis por categoria
    EMOJIS = {
        'dinheiro': ['💰', '💵', '🤑', '💎'],
        'sucesso': ['🏆', '🎯', '⭐', '✨'],
        'alerta': ['🚨', '⚠️', '❗', '🔴'],
        'segredo': ['🔥', '💡', '🤫', '👀'],
        'pergunta': ['❓', '🤔', '💭', '❔'],
        'positivo': ['✅', '👍', '💪', '🚀'],
        'negativo': ['❌', '⛔', '🛑', '💔']
    }

    def __init__(self):
        self.gemini_client = None
        api_key = os.getenv("GEMINI_API_KEY")

        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✍️ Copywriter Agent: ONLINE (Gemini 1.5 Flash)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao conectar Gemini: {e}. Usando fallback.")
        else:
            logger.info("✍️ Copywriter Agent: Modo Offline (Templates Locais)")

    def generate_hooks(self, text: str, num_variations: int = 3) -> List[Dict]:
        """
        Gera múltiplas variações de hooks usando abordagem Híbrida.
        """
        from ..core.hybrid_ai import HybridAI
        hybrid = HybridAI()

        return hybrid.call(
            local_func=lambda: self._generate_hooks_local(text, num_variations),
            gemini_func=lambda: self._generate_hooks_gemini(text, num_variations) if self.gemini_client else None,
            task_name="Hook Generation"
        )

    def _generate_hooks_gemini(self, text: str, num_variations: int) -> List[Dict]:
        """Gera hooks usando Gemini AI"""
        prompt = f"""
        Você é um especialista em marketing viral para TikTok/Reels.

        Dado este texto de um vídeo:
        "{text[:500]}"

        Crie {num_variations} hooks SUPER virais em português brasileiro.
        Cada hook deve:
        - Ter no máximo 10 palavras
        - Gerar URGÊNCIA ou CURIOSIDADE
        - Usar emojis estrategicamente

        Responda APENAS em JSON:
        [
            {{"hook": "texto do hook", "score": 8.5, "style": "curiosidade"}},
            ...
        ]
        """

        response = self.gemini_client.generate_content(prompt)

        # Extrair JSON da resposta
        try:
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                hooks = json.loads(json_match.group())
                logger.info(f"   ✨ Gemini gerou {len(hooks)} hooks virais")
                return hooks
        except:
            pass

        return self._generate_hooks_local(text, num_variations)

    def _generate_hooks_local(self, text: str, num_variations: int) -> List[Dict]:
        """Fallback: Gera hooks usando templates locais"""

        logger.info("✍️  AGENTE COPYWRITER - Gerando hooks virais")

        # Extrair tópico principal
        topic = self._extract_topic(text)

        hooks = []

        # Gerar hooks de cada categoria
        for category, templates in self.HOOK_TEMPLATES.items():
            for template in templates[:1]:  # 1 de cada categoria
                hook = template.format(topic=topic)
                emoji = self._get_best_emoji(text, category)

                hooks.append({
                    'hook': f"{emoji} {hook}",
                    'category': category,
                    'score': self._calculate_hook_score(hook, text)
                })

        # Ordenar por score
        hooks.sort(key=lambda x: x['score'], reverse=True)

        # Retornar top N
        selected = hooks[:num_variations]

        logger.info(f"   Gerados {len(selected)} hooks:")
        for i, hook in enumerate(selected, 1):
            logger.info(f"      {i}. {hook['hook']} (Score: {hook['score']:.1f})")

        return selected

    def _extract_topic(self, text: str) -> str:
        """Extrai o tópico principal do texto"""
        # Pegar primeira frase ou primeiros 50 caracteres
        sentences = text.split('.')
        if sentences:
            topic = sentences[0].strip()
            if len(topic) > 50:
                topic = topic[:50] + '...'
            return topic.lower()
        return text[:50].lower()

    def _get_best_emoji(self, text: str, category: str) -> str:
        """Seleciona o melhor emoji para o contexto"""
        text_lower = text.lower()

        # Detectar categoria pelo texto
        if any(w in text_lower for w in ['dinheiro', 'mil', 'lucro', 'ganhar']):
            return self.EMOJIS['dinheiro'][0]
        elif any(w in text_lower for w in ['segredo', 'verdade', 'ninguém']):
            return self.EMOJIS['segredo'][0]
        elif any(w in text_lower for w in ['cuidado', 'erro', 'falha']):
            return self.EMOJIS['alerta'][0]
        elif any(w in text_lower for w in ['sucesso', 'vitória', 'conquista']):
            return self.EMOJIS['sucesso'][0]
        elif '?' in text:
            return self.EMOJIS['pergunta'][0]
        else:
            return self.EMOJIS['positivo'][0]

    def _calculate_hook_score(self, hook: str, original_text: str) -> float:
        """Calcula score de viralidade do hook"""
        score = 5.0
        hook_lower = hook.lower()

        # Contém números específicos
        if re.search(r'\d+', hook):
            score += 1.0

        # Tem emoji
        if any(ord(c) > 127 for c in hook):
            score += 0.5

        # Palavras de urgência
        if any(w in hook_lower for w in ['urgente', 'agora', 'hoje', 'pare']):
            score += 1.0

        # Palavras de curiosidade
        if any(w in hook_lower for w in ['segredo', 'verdade', 'descubra', 'ninguém']):
            score += 1.0

        # Comprimento ideal (50-80 caracteres)
        if 50 <= len(hook) <= 80:
            score += 0.5

        return min(score, 10.0)

    def optimize_for_platform(self, hook: str, platform: str = 'tiktok') -> str:
        """
        Otimiza hook para plataforma específica

        Args:
            hook: Hook original
            platform: Plataforma alvo (tiktok, reels, shorts)
        """
        if platform == 'tiktok':
            # TikTok: mais emojis, mais informal
            if not any(ord(c) > 127 for c in hook):
                hook = '🔥 ' + hook
            return hook[:100]  # Limite de 100 chars

        elif platform == 'reels':
            # Reels: mais clean, hashtags
            return hook[:125]

        elif platform == 'shorts':
            # Shorts: mais direto
            return hook[:70]

        return hook


if __name__ == "__main__":
    # Teste rápido
    copywriter = CopywriterAgent()

    test_text = "O segredo para ganhar dinheiro rápido que ninguém te conta"
    hooks = copywriter.generate_hooks(test_text, num_variations=3)

    for hook in hooks:
        print(f"Hook: {hook['hook']}")
        print(f"Score: {hook['score']}")
        print()
