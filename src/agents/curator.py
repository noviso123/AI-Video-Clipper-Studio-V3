"""
Agente Curador (Fase 9)
Seleciona os melhores momentos virais combinando análise de texto e emoção
"""
from typing import List, Dict, Optional
from pathlib import Path
from ..modules.analyzer import ViralAnalyzer
from ..modules.audio_analyzer import AudioEmotionAnalyzer
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class CuratorAgent:
    """
    Agente Curador: Busca picos de emoção e seleciona momentos 9/10+

    Responsabilidades:
    - Analisar áudio para detectar picos emocionais
    - Analisar texto para palavras-chave virais
    - Combinar ambas análises
    - Selecionar apenas momentos nota 9/10+
    """

    def __init__(self):
        self.audio_analyzer = AudioEmotionAnalyzer()
        self.viral_analyzer = ViralAnalyzer()
        self.min_score = 8.0  # Apenas momentos de alta qualidade

    def curate_moments(
        self,
        audio_path: Path,
        transcript_segments: List[Dict],
        num_clips: int = 3
    ) -> List[Dict]:
        """
        Curadora principal: seleciona os melhores momentos

        Args:
            audio_path: Caminho do arquivo de áudio
            transcript_segments: Segmentos da transcrição
            num_clips: Número de clipes a selecionar

        Returns:
            Lista dos melhores momentos virais
        """
        logger.info("=" * 50)
        logger.info("🎭 AGENTE CURADOR - Selecionando momentos virais")
        logger.info("=" * 50)

        # 1. Análise de emoção do áudio
        logger.info("\n📊 Etapa 1: Análise Emocional do Áudio")
        emotion_peaks = self.audio_analyzer.detect_emotion_peaks(audio_path)

        # Filtrar apenas picos de alta intensidade
        high_intensity = self.audio_analyzer.get_high_intensity_moments(emotion_peaks)
        logger.info(f"   Picos de alta intensidade: {len(high_intensity)}/{len(emotion_peaks)}")

        # 2. Análise viral da transcrição
        logger.info("\n📝 Etapa 2: Análise Viral da Transcrição")
        viral_moments = self.viral_analyzer.analyze_transcript(
            transcript_segments,
            emotion_peaks
        )

        # 3. Filtrar apenas momentos de alta qualidade (8+)
        top_moments = [m for m in viral_moments if m['score'] >= self.min_score]

        logger.info(f"\n🎯 Momentos de alta qualidade (score >= {self.min_score}): {len(top_moments)}")

        if not top_moments:
            logger.warning("⚠️  Nenhum momento atingiu score 8+. Reduzindo threshold...")
            # Fallback: pegar os melhores mesmo que não sejam 8+
            top_moments = viral_moments[:num_clips] if viral_moments else []

        # 4. Selecionar os N melhores
        selected = top_moments[:num_clips]

        logger.info(f"\n✅ {len(selected)} momentos selecionados para edição:")
        for i, moment in enumerate(selected, 1):
            logger.info(f"   {i}. Score {moment['score']}/10 | {moment['hook']}")
            logger.info(f"      [{self._format_time(moment['start'])} → {self._format_time(moment['end'])}]")
            logger.info(f"      Keywords: {', '.join(moment['keywords'])}")

        logger.info("=" * 50)

        return selected

    def _format_time(self, seconds: float) -> str:
        """Formata segundos como MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


if __name__ == "__main__":
    # Teste rápido
    curator = CuratorAgent()

    # Exemplo (descomente para testar)
    # moments = curator.curate_moments(
    #     Path("temp/audio_test.mp3"),
    #     test_segments,
    #     num_clips=3
    # )
    # print(f"Selecionados: {len(moments)}")
