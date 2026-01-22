"""
Agente Copywriter Otimizado (Ollama Local)
Geração de títulos e legendas magnéticas em PT-BR.
"""
import os
import json
import logging
import requests
from typing import List, Dict, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)

from agno.agent import Agent
from agno.models.google import Gemini
from ..core.config import config as app_config
from .knowledge_base import get_viral_knowledge_base

class CopywriterAgent:
    def __init__(self):
        self.model = app_config.GEMINI_MODEL
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Obter Knowledge Base (RAG)
        self.knowledge_base = get_viral_knowledge_base()
        
        # Inicializar Agente Agno com RAG (usa GOOGLE_API_KEY do env)
        self.agent = Agent(
            model=Gemini(id=self.model),
            knowledge=self.knowledge_base,
            search_knowledge=True,
            description="Você é um Copywriter expert em marketing viral e ganchos magnéticos para vídeos curtos.",
            instructions=[
                "Sempre responda em Português Brasileiro (PT-BR).",
                "Antes de criar os ganchos, consulte a base de conhecimento sobre melhores práticas de ganchos (Hooks).",
                "Crie ganchos magnéticos potentes para os primeiros 3 segundos de um vídeo.",
                "Use gatilhos mentais: Curiosidade, Urgência ou Medo.",
                "Mantenha os ganchos curtos (máximo 7 palavras).",
                "Retorne os resultados em formato JSON válido."
            ],
            markdown=True
        )

    def generate_hooks(self, text: str, num_variations: int = 3) -> List[Dict]:
        """Gera ganchos magnéticos usando Agno + Gemini"""
        logger.info(f"✍️  Copywriter: Criando ganchos magnéticos (Agno)...")

        prompt = f"""
        Transforme este texto em {num_variations} Ganchos Magnéticos para o início de um vídeo.
        
        TEXTO BASE: {text[:1000]}
        
        Responda EXATAMENTE neste formato JSON:
        [
            {{"hook": "O segredo que nunca te contaram", "score": 9.5}},
            {{"hook": "Pare de fazer isso agora!", "score": 9.2}}
        ]
        """

        try:
            response = self.agent.run(prompt)
            # Limpar markdown se houver
            clean_content = response.content.replace("```json", "").replace("```", "").strip()
            hooks = json.loads(clean_content)
            
            if isinstance(hooks, list):
                return hooks[:num_variations]
            return [hooks]
            
        except Exception as e:
            logger.warning(f"⚠️ Erro no Copywriter (Agno): {e}")

        # Fallback simples em caso de erro
        return [{'hook': text[:40].upper() + "!", 'score': 7.0}]
