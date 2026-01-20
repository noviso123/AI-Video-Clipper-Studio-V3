"""
Módulo de Edição de Vídeo Profissional
- Speaker-Following para podcasts/entrevistas
- Faceless Mode para conteúdo sem rosto (Reels/TikTok)
- Safe zones, Ken Burns effect, cortes dinâmicos
"""
import logging
import os
import cv2
import numpy as np
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, CompositeVideoClip
)
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from pydub import AudioSegment
from ..core.config import Config
from ..core.logger import setup_logger
from .captions import DynamicCaptions
from .transcriber import AudioTranscriber

logger = setup_logger(__name__)


class DynamicSpeakerTracker:
    """Rastreador dinâmico para conteúdo COM rostos (podcasts, entrevistas)."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )

    def analyze_video_with_audio(self, video_path: Path, sample_interval: float = 0.5) -> tuple:
        """
        Analisa vídeo e retorna (speaker_data, has_faces).
        Se não encontrar rostos, retorna ([], False) para usar modo Faceless.
        """
        logger.info("🔍 Analisando vídeo para faces e áudio...")

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sample_frames = max(1, int(fps * sample_interval))

        face_timeline = []
        total_faces = 0
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_frames == 0:
                timestamp = frame_idx / fps
                faces = self._detect_all_faces(frame)
                total_faces += len(faces)

                if faces:
                    positions = self._classify_face_positions(faces, width)
                    face_timeline.append({
                        'timestamp': timestamp,
                        'faces': faces,
                        'left_faces': positions['left'],
                        'right_faces': positions['right'],
                        'center_faces': positions['center'],
                        'frame_width': width,
                        'frame_height': height
                    })

            frame_idx += 1

        cap.release()

        # Determinar se tem rostos suficientes
        face_ratio = len(face_timeline) / max(1, frame_idx // sample_frames)
        has_faces = face_ratio > 0.3  # Pelo menos 30% dos frames tem rostos

        if has_faces:
            logger.info(f"✅ Modo: WITH FACES ({int(face_ratio*100)}% com rostos)")
            speaker_data = self._determine_active_speaker(face_timeline, video_path, width, height)
            return speaker_data, True
        else:
            logger.info(f"✅ Modo: FACELESS ({int(face_ratio*100)}% com rostos)")
            return [], False

    def _detect_all_faces(self, frame) -> list:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = []

        for cascade in [self.face_cascade, self.profile_cascade]:
            detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
            for (x, y, w, h) in detected:
                is_dup = any(abs(f['center_x'] - (x + w//2)) < 60 for f in faces)
                if not is_dup:
                    faces.append({
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'center_x': x + w // 2, 'center_y': y + h // 2, 'area': w * h
                    })

        faces.sort(key=lambda f: f['center_x'])
        return faces

    def _classify_face_positions(self, faces, width) -> dict:
        third = width / 3
        return {
            'left': [f for f in faces if f['center_x'] < third],
            'center': [f for f in faces if third <= f['center_x'] <= 2 * third],
            'right': [f for f in faces if f['center_x'] > 2 * third]
        }

    def _determine_active_speaker(self, face_timeline, video_path, width, height) -> list:
        """Determina speaker ativo com base em áudio."""
        try:
            audio_activity = self._analyze_audio(video_path)
        except:
            audio_activity = []

        result = []
        last_mode = 'CENTER'
        last_target = {'center_x': width//2, 'center_y': height//2,
                       'crop_width': int(height*9/16), 'crop_height': height}

        for face_data in face_timeline:
            timestamp = face_data['timestamp']
            audio = next((a for a in audio_activity if abs(a['timestamp'] - timestamp) < 0.3),
                        {'is_speaking': True})

            has_left = len(face_data['left_faces']) > 0
            has_right = len(face_data['right_faces']) > 0

            if audio.get('is_speaking', True):
                if has_left and has_right:
                    mode = 'BOTH'
                    target = self._get_both_area(face_data, width, height)
                elif has_left:
                    mode = 'LEFT'
                    target = self._get_face_area(face_data['left_faces'][0], width, height)
                elif has_right:
                    mode = 'RIGHT'
                    target = self._get_face_area(face_data['right_faces'][0], width, height)
                else:
                    mode = 'CENTER'
                    target = last_target
            else:
                mode = last_mode
                target = last_target

            last_mode = mode
            last_target = target

            result.append({
                'timestamp': timestamp, 'mode': mode, 'target_area': target,
                'frame_width': width, 'frame_height': height
            })

        return self._smooth_transitions(result)

    def _analyze_audio(self, video_path: Path) -> list:
        try:
            clip = VideoFileClip(str(video_path))
            temp_audio = Path(video_path).parent / "temp_audio.wav"
            clip.audio.write_audiofile(str(temp_audio), logger=None, verbose=False)
            clip.close()

            audio = AudioSegment.from_file(str(temp_audio))
            activity = []
            interval = 0.5

            for t in np.arange(0, len(audio)/1000, interval):
                chunk = audio[int(t*1000):int((t+interval)*1000)]
                rms = chunk.rms if len(chunk) > 0 else 0
                activity.append({'timestamp': t, 'is_speaking': rms > 500})

            if temp_audio.exists():
                temp_audio.unlink()

            return activity
        except:
            return []

    def _smooth_transitions(self, timeline, min_duration=1.0):
        if len(timeline) < 3:
            return timeline

        smoothed = [timeline[0]]
        current_mode = timeline[0]['mode']
        mode_start = 0

        for i, frame in enumerate(timeline[1:], 1):
            if frame['mode'] != current_mode:
                duration = frame['timestamp'] - timeline[mode_start]['timestamp']
                if duration >= min_duration:
                    smoothed.append(frame)
                    current_mode = frame['mode']
                    mode_start = i
                else:
                    frame_copy = frame.copy()
                    frame_copy['mode'] = current_mode
                    frame_copy['target_area'] = smoothed[-1]['target_area']
                    smoothed.append(frame_copy)
            else:
                smoothed.append(frame)

        return smoothed

    def _get_face_area(self, face, width, height):
        crop_h = min(int(face['height'] * 8), height)
        crop_w = min(int(crop_h * 9 / 16), int(height * 9 / 16))
        return {
            'center_x': face['center_x'],
            'center_y': face['center_y'] + face['height'] // 2,
            'crop_width': crop_w, 'crop_height': crop_h
        }

    def _get_both_area(self, face_data, width, height):
        all_faces = face_data['left_faces'] + face_data['right_faces'] + face_data['center_faces']
        if len(all_faces) < 2:
            return {'center_x': width//2, 'center_y': height//2,
                    'crop_width': int(height*9/16), 'crop_height': height}

        min_x = min(f['x'] for f in all_faces)
        max_x = max(f['x'] + f['width'] for f in all_faces)
        center_x = (min_x + max_x) // 2
        center_y = sum(f['center_y'] for f in all_faces) // len(all_faces)

        crop_w = int((max_x - min_x) * 1.5)
        crop_h = int(crop_w * 16 / 9)
        if crop_h > height:
            crop_h = height
            crop_w = int(crop_h * 9 / 16)

        return {'center_x': center_x, 'center_y': center_y,
                'crop_width': crop_w, 'crop_height': crop_h}


class FacelessModeProcessor:
    """
    Processador para conteúdo FACELESS (sem rosto).
    - Safe zone central
    - Ken Burns effect (zoom lento)
    - Cortes dinâmicos
    """

    def __init__(self, target_w=1080, target_h=1920):
        self.target_w = target_w
        self.target_h = target_h
        # Safe zone: 80% do centro (evita cortes nas bordas)
        self.safe_margin = 0.1  # 10% de margem

    def create_faceless_clip(self, clip, start, end, effect='ken_burns'):
        """
        Cria clipe faceless com efeito Ken Burns e safe zone.
        """
        sub_clip = clip.subclip(start, end)
        w, h = sub_clip.size

        if effect == 'ken_burns':
            return self._apply_ken_burns(sub_clip, w, h)
        elif effect == 'center_focus':
            return self._apply_center_focus(sub_clip, w, h)
        else:
            return self._apply_static_crop(sub_clip, w, h)

    def _apply_ken_burns(self, clip, w, h):
        """
        Aplica efeito Ken Burns (zoom lento) para dinamismo.
        Alterna entre zoom in e zoom out a cada segmento.
        """
        duration = clip.duration

        # Calcular crop base (9:16)
        crop_h = h
        crop_w = int(h * 9 / 16)
        if crop_w > w:
            crop_w = w
            crop_h = int(w * 16 / 9)

        # Centro
        center_x = w // 2
        center_y = h // 2

        # Parâmetros do zoom (5% de variação)
        zoom_start = 1.0
        zoom_end = 1.05

        def make_ken_burns_frame(get_frame, t):
            frame = get_frame(t)
            progress = t / duration

            # Interpolação de zoom
            current_zoom = zoom_start + (zoom_end - zoom_start) * progress

            # Calcular crop com zoom
            actual_w = int(crop_w / current_zoom)
            actual_h = int(crop_h / current_zoom)

            x1 = max(0, center_x - actual_w // 2)
            y1 = max(0, center_y - actual_h // 2)
            x1 = min(x1, w - actual_w)
            y1 = min(y1, h - actual_h)

            # Crop
            cropped = frame[int(y1):int(y1 + actual_h), int(x1):int(x1 + actual_w)]

            if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                return cv2.resize(cropped, (self.target_w, self.target_h))
            else:
                return cv2.resize(frame, (self.target_w, self.target_h))

        return clip.fl(lambda gf, t: make_ken_burns_frame(gf, t))

    def _apply_center_focus(self, clip, w, h):
        """Crop central com safe zone."""
        crop_h = h
        crop_w = int(h * 9 / 16)

        if crop_w > w:
            crop_w = w
            crop_h = int(w * 16 / 9)

        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2

        def make_center_frame(get_frame, t):
            frame = get_frame(t)
            cropped = frame[int(y1):int(y1 + crop_h), int(x1):int(x1 + crop_w)]
            return cv2.resize(cropped, (self.target_w, self.target_h))

        return clip.fl(lambda gf, t: make_center_frame(gf, t))

    def _apply_static_crop(self, clip, w, h):
        """Crop estático central."""
        target_ratio = 9 / 16
        crop_h = h
        crop_w = int(h * target_ratio)

        if crop_w > w:
            crop_w = w
            crop_h = int(w / target_ratio)

        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2

        cropped = crop(clip, x1=x1, y1=y1, width=crop_w, height=crop_h)
        return cropped.resize((self.target_w, self.target_h))


class VideoEditor:
    """
    Editor principal com suporte automático a:
    - Podcasts/Entrevistas (speaker-following)
    - Faceless content (Ken Burns, safe zone)
    """

    def __init__(self):
        self.target_w = 1080
        self.target_h = 1920
        self.tracker = DynamicSpeakerTracker()
        self.faceless = FacelessModeProcessor(self.target_w, self.target_h)

    def create_clip(
        self, video_path: Path, start: float, end: float, output: Path,
        thumbnail_path: Path = None, hook_text: str = None,
        segments: list = None, add_captions: bool = True, **kwargs
    ) -> Path:
        """Cria clipe com detecção automática de modo (faces vs faceless)."""
        try:
            logger.info(f"🎬 Editando clipe: {start}s -> {end}s")

            original_clip = VideoFileClip(str(video_path))
            safe_end = min(end, original_clip.duration)

            # Analisar vídeo para determinar modo
            speaker_data, has_faces = self.tracker.analyze_video_with_audio(
                video_path, sample_interval=0.5
            )

            clips_sequence = []

            # 1. Thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info("   📸 Adding Thumbnail")
                thumb_clip = ImageClip(str(thumbnail_path)).set_duration(0.1)
                thumb_clip = thumb_clip.resize(height=self.target_h).set_position("center")
                clips_sequence.append(thumb_clip)

            # 2. Hook (3s)
            hook_duration = 3.0
            if safe_end - start > hook_duration:
                logger.info("   🎤 Creating Viral Hook (3s)")
                if has_faces:
                    hook_clip = self._create_speaker_clip(
                        original_clip, start, start + hook_duration, speaker_data
                    )
                else:
                    hook_clip = self.faceless.create_faceless_clip(
                        original_clip, start, start + hook_duration, 'ken_burns'
                    )
                if hook_clip:
                    hook_clip = hook_clip.volumex(0.2)
                    clips_sequence.append(hook_clip)
                content_start = start + hook_duration
            else:
                content_start = start

            # 3. Main clip
            if has_faces:
                logger.info("   🎥 Modo: Speaker-Following (com rostos)")
                main_clip = self._create_speaker_clip(
                    original_clip, content_start, safe_end, speaker_data
                )
            else:
                logger.info("   🎥 Modo: Faceless (Ken Burns + Safe Zone)")
                main_clip = self.faceless.create_faceless_clip(
                    original_clip, content_start, safe_end, 'ken_burns'
                )

            clips_sequence.append(main_clip)

            # Concatenar
            final = concatenate_videoclips(clips_sequence, method="compose")

            # 4. Legendas
            if add_captions and segments:
                logger.info("   📝 Adicionando legendas...")
                try:
                    transcriber = AudioTranscriber()
                    words = transcriber.get_words_for_clip(segments, start, safe_end)

                    if words:
                        offset = 0.1 + (3.0 if safe_end - start > 3.0 else 0)
                        adjusted_words = [
                            {'word': w['word'], 'start': w['start'] + offset, 'end': w['end'] + offset}
                            for w in words
                        ]
                        captions = DynamicCaptions()
                        final = captions.create_captions(final, adjusted_words)
                        logger.info(f"   ✅ Legendas: {len(adjusted_words)} palavras")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro nas legendas: {e}")

            # Exportar
            logger.info(f"   💾 Exportando: {output}")
            final.write_videofile(
                str(output), fps=30, codec="libx264",
                audio_codec="aac", threads=4, logger=None, preset='fast'
            )

            original_clip.close()
            return output

        except Exception as e:
            logger.error(f"❌ Erro no editor: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_speaker_clip(self, original_clip, start, end, speaker_data):
        """Cria clipe com speaker-following."""
        clip = original_clip.subclip(start, end)
        w, h = clip.size

        clip_data = [d for d in speaker_data if start <= d['timestamp'] <= end]

        if not clip_data:
            return self.faceless.create_faceless_clip(original_clip, start, end, 'center_focus')

        def make_speaker_frame(get_frame, t):
            frame = get_frame(t)
            absolute_t = start + t

            closest = min(clip_data, key=lambda d: abs(d['timestamp'] - absolute_t))
            target = closest['target_area']

            crop_x = max(0, target['center_x'] - target['crop_width'] // 2)
            crop_y = max(0, target['center_y'] - target['crop_height'] // 2)
            crop_x = min(crop_x, w - target['crop_width'])
            crop_y = min(crop_y, h - target['crop_height'])

            crop_w = min(target['crop_width'], w)
            crop_h = min(target['crop_height'], h)

            cropped = frame[
                int(max(0, crop_y)):int(min(h, crop_y + crop_h)),
                int(max(0, crop_x)):int(min(w, crop_x + crop_w))
            ]

            if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                return cv2.resize(cropped, (self.target_w, self.target_h))
            else:
                return cv2.resize(frame, (self.target_w, self.target_h))

        return clip.fl(lambda gf, t: make_speaker_frame(gf, t))
