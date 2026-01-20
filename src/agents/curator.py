"""
Agente Curador Simplificado
Seleciona os melhores momentos virais da transcrição.
"""
import logging
from typing import List, Dict
from pathlib import Path
from ..modules.analyzer import ViralAnalyzer
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class CuratorAgent:
    """Curador minimalista focado em texto."""

    def __init__(self):
        self.analyzer = ViralAnalyzer()

    def curate_moments(
        self,
        audio_path: Path, # Mantido por compatibilidade de assinatura
        transcript_segments: List[Dict],
        num_clips: int = 3,
        min_duration: int = 30,
        max_duration: int = 60
    ) -> List[Dict]:
        """Seleciona os melhores momentos baseado no texto."""
        logger.info("🎭 Iniciando Curadoria Simplificada...")

        # Chama o analisador (agora simplificado e sem dependências de áudio)
        moments = self.analyzer.analyze_transcript(
            transcript_segments,
            min_duration=min_duration,
            max_duration=max_duration
        )

        # Seleciona os N melhores
        selected = moments[:num_clips]

        logger.info(f"✅ {len(selected)} momentos selecionados.")
        return selected
