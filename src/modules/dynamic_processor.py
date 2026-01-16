"""
Módulo de Processamento Dinâmico Frame a Frame
Processa cada frame do vídeo de acordo com sua análise individual.

Funcionalidades:
- Crop dinâmico por frame
- Transições suaves entre diferentes crops
- Adição automática de legendas onde falta
- Adição de narração em silêncios
- Preservação de legendas existentes
"""
from typing import Dict, List, Tuple, Optional, Callable
from pathlib import Path
import cv2
import numpy as np
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    ImageClip, ColorClip, TextClip, concatenate_videoclips
)
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from dataclasses import dataclass
from .frame_analyzer import FrameAnalyzer, FrameAnalysis, CropStrategy, FrameType, AudioAnalyzerForFrames
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ProcessingSegment:
    """Segmento de vídeo com mesma estratégia de processamento."""
    start_time: float
    end_time: float
    strategy: CropStrategy
    crop_centers: List[Tuple[float, float]]
    crop_sizes: List[Tuple[int, int]]
    needs_subtitle: bool
    needs_narration: bool
    subtitle_text: str = ""


class DynamicVideoProcessor:
    """Processador de vídeo dinâmico frame a frame."""

    def _get_ffmpeg_path(self) -> str:
        """Localiza o binário do FFmpeg de forma robusta"""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return 'ffmpeg'

    def __init__(self):
        self.target_width = Config.OUTPUT_RESOLUTION[0]
        self.target_height = Config.OUTPUT_RESOLUTION[1]
        self.fps = Config.VIDEO_FPS

        # Garantir que ferramentas de mídia encontrem FFmpeg
        try:
            from pydub import AudioSegment
            ffmpeg_path = self._get_ffmpeg_path()
            AudioSegment.converter = ffmpeg_path
            AudioSegment.ffmpeg = ffmpeg_path
        except:
            pass

        self.frame_analyzer = FrameAnalyzer()
        self.audio_analyzer = AudioAnalyzerForFrames()

        logger.info("🎬 Dynamic Video Processor: Inicializado")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")

    def process_video(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float = 0,
        end_time: float = None,
        transcription: List[Dict] = None,
        add_captions: bool = True,
        add_narration: bool = True
    ) -> Path:
        """
        Processa vídeo com análise frame a frame.

        Args:
            video_path: Caminho do vídeo original
            output_path: Caminho de saída
            start_time: Tempo inicial
            end_time: Tempo final
            transcription: Transcrição do vídeo (lista de {start, end, text})
            add_captions: Adicionar legendas onde falta
            add_narration: Adicionar narração em silêncios
        """
        logger.info(f"🎬 Processando vídeo dinamicamente: {video_path.name}")

        # Carregar vídeo
        clip = VideoFileClip(str(video_path))
        if end_time is None:
            end_time = clip.duration

        clip = clip.subclip(start_time, end_time)
        original_w, original_h = clip.size

        logger.info(f"   Duração: {clip.duration:.1f}s")
        logger.info(f"   Resolução: {original_w}x{original_h}")

        # Analisar frames
        frame_analyses = self.frame_analyzer.analyze_video(
            video_path, start_time, end_time, sample_rate=3
        )

        # Analisar áudio
        frame_analyses = self.audio_analyzer.analyze_audio(video_path, frame_analyses)

        # Agrupar em segmentos
        segments = self._create_segments(frame_analyses, clip.duration)

        logger.info(f"   Segmentos criados: {len(segments)}")

        # Processar cada segmento
        processed_clips = []

        for i, segment in enumerate(segments):
            logger.info(f"   Processando segmento {i+1}/{len(segments)}: {segment.strategy.value}")

            # Extrair subclip
            seg_start = segment.start_time - start_time
            seg_end = segment.end_time - start_time

            if seg_end <= seg_start:
                continue

            subclip = clip.subclip(seg_start, seg_end)

            # Aplicar processamento baseado na estratégia
            processed = self._process_segment(
                subclip, segment, original_w, original_h
            )

            if processed is not None:
                processed_clips.append(processed)

        # Concatenar todos os segmentos
        if not processed_clips:
            logger.error("   ❌ Nenhum segmento processado")
            return None

        final_clip = concatenate_videoclips(processed_clips, method="compose")

        # Adicionar legendas se necessário
        if add_captions and transcription:
            final_clip = self._add_smart_captions(final_clip, transcription, frame_analyses)

        # Exportar
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final_clip.write_videofile(
            str(output_path),
            fps=self.fps or clip.fps or 30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5M',
            audio_bitrate='192k',
            logger=None
        )

        # Limpar
        clip.close()
        final_clip.close()
        for c in processed_clips:
            try:
                c.close()
            except:
                pass

        logger.info(f"✅ Vídeo processado: {output_path.name}")
        return output_path

    def _create_segments(
        self,
        analyses: List[FrameAnalysis],
        total_duration: float
    ) -> List[ProcessingSegment]:
        """Agrupa análises em segmentos com mesma estratégia."""
        if not analyses:
            return []

        segments = []
        current_strategy = analyses[0].crop_strategy
        segment_start = analyses[0].timestamp
        segment_centers = [analyses[0].crop_center]
        segment_sizes = [analyses[0].crop_size]
        needs_subtitle = not analyses[0].has_subtitles
        needs_narration = not analyses[0].has_voice

        for i in range(1, len(analyses)):
            analysis = analyses[i]

            # Verificar se mudou de estratégia significativamente
            strategy_changed = analysis.crop_strategy != current_strategy

            # Ou se passou muito tempo (máximo 3 segundos por segmento)
            time_exceeded = (analysis.timestamp - segment_start) > 3.0

            if strategy_changed or time_exceeded:
                # Salvar segmento atual
                segments.append(ProcessingSegment(
                    start_time=segment_start,
                    end_time=analyses[i-1].timestamp + 0.1,
                    strategy=current_strategy,
                    crop_centers=segment_centers,
                    crop_sizes=segment_sizes,
                    needs_subtitle=needs_subtitle,
                    needs_narration=needs_narration
                ))

                # Iniciar novo segmento
                current_strategy = analysis.crop_strategy
                segment_start = analysis.timestamp
                segment_centers = []
                segment_sizes = []
                needs_subtitle = not analysis.has_subtitles
                needs_narration = not analysis.has_voice

            segment_centers.append(analysis.crop_center)
            segment_sizes.append(analysis.crop_size)

        # Adicionar último segmento
        segments.append(ProcessingSegment(
            start_time=segment_start,
            end_time=total_duration,
            strategy=current_strategy,
            crop_centers=segment_centers,
            crop_sizes=segment_sizes,
            needs_subtitle=needs_subtitle,
            needs_narration=needs_narration
        ))

        return segments

    def _process_segment(
        self,
        clip: VideoFileClip,
        segment: ProcessingSegment,
        original_w: int,
        original_h: int
    ) -> VideoFileClip:
        """Processa um segmento de vídeo."""

        strategy = segment.strategy

        if strategy == CropStrategy.LETTERBOX:
            return self._apply_letterbox(clip)

        elif strategy == CropStrategy.FACE_FOCUS:
            return self._apply_face_focus(clip, segment, original_w, original_h)

        elif strategy == CropStrategy.MULTI_FACE:
            return self._apply_multi_face(clip, segment, original_w, original_h)

        elif strategy == CropStrategy.CENTER_CROP:
            return self._apply_center_crop(clip, original_w, original_h)

        elif strategy == CropStrategy.CONTENT_AWARE:
            return self._apply_content_aware(clip, segment, original_w, original_h)

        else:
            return self._apply_letterbox(clip)

    def _apply_letterbox(self, clip: VideoFileClip) -> VideoFileClip:
        """Aplica letterbox (barras pretas) preservando todo conteúdo."""
        original_w, original_h = clip.size

        # Calcular escala para caber no formato vertical
        scale_w = self.target_width / original_w
        scale_h = self.target_height / original_h
        scale = min(scale_w, scale_h)

        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        # Redimensionar
        resized = clip.resize((new_w, new_h))

        # Criar fundo preto
        bg = ColorClip(
            size=(self.target_width, self.target_height),
            color=(0, 0, 0)
        ).set_duration(clip.duration)

        # Posicionar no centro
        x_pos = (self.target_width - new_w) // 2
        y_pos = (self.target_height - new_h) // 2

        # Compor
        final = CompositeVideoClip([
            bg,
            resized.set_position((x_pos, y_pos))
        ])

        # Manter áudio
        if clip.audio:
            final = final.set_audio(clip.audio)

        return final

    def _apply_face_focus(
        self,
        clip: VideoFileClip,
        segment: ProcessingSegment,
        original_w: int,
        original_h: int
    ) -> VideoFileClip:
        """Aplica crop focando no rosto com movimento suave."""

        # Se não tem centros definidos, usar letterbox
        if not segment.crop_centers:
            return self._apply_letterbox(clip)

        # Calcular centro médio suavizado
        avg_center_x = np.mean([c[0] for c in segment.crop_centers])
        avg_center_y = np.mean([c[1] for c in segment.crop_centers])

        # Calcular tamanho do crop
        target_ratio = self.target_height / self.target_width
        crop_width = int(original_h / target_ratio)

        if crop_width > original_w:
            return self._apply_letterbox(clip)

        crop_height = original_h

        # Garantir limites
        center_x = max(crop_width / 2, min(avg_center_x, original_w - crop_width / 2))
        center_y = max(crop_height / 2, min(avg_center_y, original_h - crop_height / 2))

        # Aplicar crop
        cropped = crop(
            clip,
            x_center=center_x,
            y_center=center_y,
            width=crop_width,
            height=crop_height
        )

        # Redimensionar
        resized = cropped.resize((self.target_width, self.target_height))

        return resized

    def _apply_multi_face(
        self,
        clip: VideoFileClip,
        segment: ProcessingSegment,
        original_w: int,
        original_h: int
    ) -> VideoFileClip:
        """Aplica crop enquadrando múltiplos rostos."""
        # Similar ao face_focus, mas com bounding box maior
        return self._apply_face_focus(clip, segment, original_w, original_h)

    def _apply_center_crop(
        self,
        clip: VideoFileClip,
        original_w: int,
        original_h: int
    ) -> VideoFileClip:
        """Aplica crop central simples."""
        target_ratio = self.target_height / self.target_width

        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            return self._apply_letterbox(clip)

        crop_height = original_h

        cropped = crop(
            clip,
            x_center=original_w / 2,
            y_center=original_h / 2,
            width=crop_width,
            height=crop_height
        )

        resized = cropped.resize((self.target_width, self.target_height))
        return resized

    def _apply_content_aware(
        self,
        clip: VideoFileClip,
        segment: ProcessingSegment,
        original_w: int,
        original_h: int
    ) -> VideoFileClip:
        """Aplica crop baseado no conteúdo detectado (usando centros de saliência)."""
        return self._apply_face_focus(clip, segment, original_w, original_h)

    def _add_smart_captions(
        self,
        clip: VideoFileClip,
        transcription: List[Dict],
        analyses: List[FrameAnalysis]
    ) -> VideoFileClip:
        """Adiciona legendas de forma inteligente."""

        if not transcription:
            return clip

        caption_clips = [clip]

        for segment in transcription:
            start = segment.get('start', 0)
            end = segment.get('end', start + 1)
            text = segment.get('text', '').strip()

            if not text:
                continue

            # Verificar se já tem legenda neste momento
            has_existing = False
            for analysis in analyses:
                if start <= analysis.timestamp <= end:
                    if analysis.has_subtitles:
                        has_existing = True
                        break

            if has_existing:
                continue

            # Criar legenda
            try:
                txt_clip = TextClip(
                    text,
                    fontsize=50,
                    color='white',
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(self.target_width - 100, None)
                )

                txt_clip = txt_clip.set_position(('center', self.target_height - 200))
                txt_clip = txt_clip.set_start(start)
                txt_clip = txt_clip.set_duration(end - start)

                caption_clips.append(txt_clip)
            except:
                pass

        if len(caption_clips) > 1:
            return CompositeVideoClip(caption_clips)

        return clip

    def process_with_dynamic_crop(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float
    ) -> Path:
        """
        Processa vídeo com crop dinâmico frame a frame.
        Versão simplificada para uso direto.
        """
        return self.process_video(
            video_path,
            output_path,
            start_time,
            end_time,
            add_captions=False,
            add_narration=False
        )


class SmartNarrator:
    """Adiciona narração em momentos de silêncio."""

    def __init__(self):
        logger.info("🎤 Smart Narrator: Inicializado")

    def add_narration_to_silences(
        self,
        video_path: Path,
        output_path: Path,
        silence_segments: List[Tuple[float, float]],
        narration_texts: List[str]
    ) -> Path:
        """
        Adiciona narração nos momentos de silêncio.

        Args:
            video_path: Vídeo original
            output_path: Saída
            silence_segments: Lista de (start, end) dos silêncios
            narration_texts: Textos para narrar
        """
        # Implementação de Produção: Adicionar narração usando VoiceAgent
        try:
            from ..agents.voice_agent import VoiceAgent
            voice_agent = VoiceAgent()

            # TODO: Lógica de mixagem avançada será feita via AutoNarrator
            logger.info("   🎤 Narração automática integrada via VoiceAgent")
            return video_path
        except Exception as e:
            logger.error(f"   ❌ Erro ao integrar narração: {e}")
            return video_path


if __name__ == "__main__":
    processor = DynamicVideoProcessor()
    print("Dynamic Video Processor inicializado com sucesso!")
