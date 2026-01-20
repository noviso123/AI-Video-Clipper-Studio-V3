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

class CopywriterAgent:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def generate_hooks(self, text: str, num_variations: int = 3) -> List[Dict]:
        """Gera ganchos magnéticos usando Ollama em PT-BR."""
        logger.info(f"✍️  Copywriter: Criando ganchos magnéticos (Ollama)...")

        prompt = f"""
        Você é um Copywriter viral. Transforme este texto em {num_variations} Ganchos Magnéticos para os primeiros 3 segundos de um vídeo.

        REGRAS:
        - Idioma: Português Brasileiro (PT-BR).
        - Use Gatilhos: Curiosidade, Urgência ou Medo.
        - Curto: Máximo 7 palavras.

        TEXTO BASE: {text[:500]}

        SAÍDA (Apenas JSON):
        [
            {{"hook": "O segredo que nunca te contaram", "score": 9.5}},
            ...
        ]
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
                timeout=30
            )

            if response.status_code == 200:
                hooks = json.loads(response.json()['response'])
                return hooks if isinstance(hooks, list) else [hooks]
        except Exception as e:
            logger.warning(f"⚠️ Erro no Copywriter (Ollama): {e}")

        return [{'hook': text[:40].upper() + "!", 'score': 7.0}]
