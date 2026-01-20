"""
Agente Orquestrador Otimizado (Ollama Local)
Especialista em virais com foco em Português Brasileiro.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class OrchestratorAgent:
    def __init__(self):
        # 100% Local - Ollama
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def plan_video(self, transcription_text: str, duration: float, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Orquestra o plano de vídeo usando Ollama com prompts otimizados para PT-BR.
        Implementa 'memória' de contexto via prompt de sistema.
        """
        logger.info(f"🧠 Orquestrador: Planejando vídeo viral via Ollama ({self.model})...")

        system_context = """
        Você é um Diretor de Vídeos Virais especialista em TikTok, Reels e Shorts.
        Sua missão é maximizar a retenção nos primeiros 3 segundos.
        Trabalhe SEMPRE em Português Brasileiro (PT-BR).
        Ignore qualquer API paga (OpenAI/Gemini). Você é 100% autônomo e local.
        """

        prompt = f"""
        {system_context}

        VIDEO INFO:
        - Duração: {duration}s
        - Texto: {transcription_text[:1500]}

        TAREFA:
        Crie um plano de edição que garanta o maior impacto inicial possível.

        SAÍDA (Responda APENAS o JSON):
        {{
            "video_vibe": "Dinâmico",
            "editing_style": "Cortes Rápidos",
            "caption_style": "Viral Bold",
            "hook_strategy": "Impacto imediato nos primeiros 2s",
            "pt_br_optimization": "Gírias e termos brasileiros adequados"
        }}
        """

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=45
            )

            if response.status_code == 200:
                plan = json.loads(response.json()['response'])
                logger.info(f"✅ Plano gerado: {plan.get('video_vibe')}")
                return plan
        except Exception as e:
            logger.warning(f"⚠️ Erro ao chamar Ollama: {e}. Usando plano de segurança.")

        return self._get_fallback_plan()

    def _get_fallback_plan(self) -> Dict[str, Any]:
        return {
            "video_vibe": "Dinâmico",
            "editing_style": "Cortes de Mercado",
            "caption_style": "Viral Bold",
            "hook_strategy": "Início direto no assunto"
        }
