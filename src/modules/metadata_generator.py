"""
Módulo de Geração de Metadados Virais
Usa LLM (Gemini) para criar Títulos, Descrições e Tags otimizados para cada plataforma.
"""
import os
import json
import logging
from typing import Dict, List, Optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ..core.logger import setup_logger

logger = setup_logger(__name__)

class MetadataGenerator:
    """Gera metadados virais (Título, Descrição, Tags) para redes sociais"""
    
    def __init__(self):
        self.gemini_client = None
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("🧠 Metadata Generator: ONLINE (Gemini 1.5 Flash)")
            except Exception as e:
                logger.error(f"❌ Erro ao conectar Gemini: {e}")
        else:
            logger.warning("⚠️ Metadata Generator: Gemini não disponível ou API Key ausente.")

    def generate_metadata(self, transcription_text: str, duration: float, platform: str = "all") -> Dict:
        """
        Gera metadados otimizados com base na transcrição do vídeo.
        Returns:
            Dict: {
                "title": "Hook Viral",
                "description": "Texto curto...",
                "hashtags": ["#tag1", "#tag2"],
                "viral_score": 9.0,
                "platform_specific": { ... }
            }
        """
        if not self.gemini_client:
            return self._fallback_metadata()

        prompt = f"""
        Atue como um Especialista em SEO e Viralidade para Redes Sociais (TikTok, Shorts, Reels).
        
        Analise esta transcrição de um vídeo curto ({duration}s):
        "{transcription_text[:2000]}..." [truncado se necessário]
        
        Gere metadados EXTREMAMENTE VIRAIS.
        
        REGRAS:
        1. Título (Hook): Máximo 50 caracteres. Deve ser impossível de ignorar. Use 1 emoji.
        2. Descrição: Máximo 3 linhas. Direta e instigante. Com Call to Action (CTA).
        3. Hashtags: 5-7 tags misturando nicho (ex: #marketing) e virais (ex: #fyp).
        4. Viral Score: 0-10 baseado no potencial do conteúdo.
        
        Retorne APENAS um JSON:
        {{
            "title": "O Segredo que Ninguém Te Conta 🤫",
            "description": "Você sabia disso? Comente abaixo! 👇\\n\\nIsso mudou meu jogo.",
            "hashtags": ["#segredo", "#dicas", "#viral", "#foryou"],
            "viral_score": 8.5,
            "explanation": "O hook desperta curiosidade imediata..."
        }}
        """
        
        try:
            response = self.gemini_client.generate_content(prompt)
            data = self._parse_json(response.text)
            return data
        except Exception as e:
            logger.error(f"Erro na geração de metadados: {e}")
            return self._fallback_metadata()

    def _parse_json(self, text: str) -> Dict:
        try:
            text = text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            return json.loads(text.strip())
        except:
            return self._fallback_metadata()

    def _fallback_metadata(self) -> Dict:
        return {
            "title": "Confira este vídeo incrível! 🎬",
            "description": "Assista até o final! #shorts",
            "hashtags": ["#viral", "#foryou", "#trending"],
            "viral_score": 5.0,
            "explanation": "Fallback generation (Error or Offline)"
        }
