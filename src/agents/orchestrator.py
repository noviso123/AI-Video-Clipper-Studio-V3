"""
Agente Orquestrador (Fase 16)
O 'Cérebro' do sistema V2.
Analisa a transcrição e define o plano de edição (Vibe, Foco, Cortes).
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o Orquestrador.
        Se api_key não for fornecida, tenta pegar do ambiente.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("🧠 Agente Orquestrador: ONLINE (OpenAI Conectado)")
            except Exception as e:
                logger.error(f"❌ Erro ao conectar OpenAI: {e}")
        else:
            logger.warning("⚠️ Agente Orquestrador: MODO OFFLINE (Sem API Key)")

    def plan_video(self, transcription_text: str, duration: float, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Gera um plano de edição completo baseado no conteúdo usando abordagem Híbrida.
        """
        from ..core.hybrid_ai import HybridAI
        hybrid = HybridAI()

        return hybrid.call(
            local_func=self._get_fallback_plan,
            openai_func=lambda: self._call_openai_plan(transcription_text, duration, user_preferences) if self.client else None,
            task_name="Editing Plan"
        )

    def _call_openai_plan(self, text: str, duration: float, prefs: Optional[Dict]) -> Dict[str, Any]:
        """Chamada real para OpenAI"""
        logger.info("🧠 Orquestrador: Analisando conteúdo para gerar plano de edição via OpenAI...")
        prompt = self._build_prompt(text, duration, prefs)
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional Video Editor Director. Output ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        content = response.choices[0].message.content
        plan = json.loads(content)
        logger.info(f"🧠 Plano gerado via OpenAI: Vibe={plan.get('video_vibe')} | Style={plan.get('editing_style')}")
        return plan

    def _build_prompt(self, text: str, duration: float, prefs: Optional[Dict]) -> str:
        """Cria o prompt para a IA"""
        prefs_str = json.dumps(prefs) if prefs else "None"

        return f"""
        Analyze this video transcript and create an Editing Plan.

        VIDEO INFO:
        - Duration: {duration} seconds
        - User Preferences: {prefs_str}

        TRANSCRIPT SAMPLE (First 2000 chars):
        {text[:2000]}...

        TASK:
        Determine the 'Vibe', 'Editing Style', and 'Highlight Moments'.

        OUTPUT JSON FORMAT:
        {{
            "video_vibe": "Motivational" | "Funny" | "Serious" | "Educational",
            "editing_style": "Fast Paced" | "Slow & Emotional" | "Dynamic",
            "color_grading": "Warm" | "Cold" | "Vibrant" | "Black & White",
            "music_mood": "Epic" | "Lo-fi" | "Upbeat",
            "caption_style": "Hormozi" | "Minimalist" | "Typewriter",
            "narration_needed": true | false,
            "narration_script": "Short intro script specific to this video content if needed (Portuguese)",
            "highlight_moments": [
                {{"start_inc": 0, "end_inc": 10, "reason": "Intro hook", "focus": "Speaker"}},
                {{"start_inc": 50, "end_inc": 60, "reason": "Emotional peak", "focus": "Zoom In"}}
            ],
            "viral_score_prediction": 0-10,
            "title_ideas": ["Title 1", "Title 2"],
            "description_hashtags": ["#tag1", "#tag2"]
        }}
        """

    def _get_fallback_plan(self) -> Dict[str, Any]:
        """Plano padrão caso a IA falhe"""
        return {
            "video_vibe": "General",
            "editing_style": "Normal",
            "color_grading": "Vibrant",
            "music_mood": "Upbeat",
            "caption_style": "Hormozi",
            "highlight_moments": [],
            "viral_score_prediction": 5,
            "title_ideas": [],
            "description_hashtags": []
        }
