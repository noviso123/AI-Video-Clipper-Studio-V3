"""
Módulo de Edição de Vídeo Profissional (Visual Upgrades + Audio Fix)
- Speaker-Following otimizado (0.2s sampling)
- Novos efeitos de Zoom (TikTok Punch, Reels Slow)
- Normalização de áudio corrigida (afx)
"""
import logging
import os
import cv2
import numpy as np
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, CompositeVideoClip, vfx, afx, ColorClip
)
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from pydub import AudioSegment
from ..core.config import Config
from ..core.logger import setup_logger
from .captions import DynamicCaptions
from .transcriber import AudioTranscriber
from .narrator import get_narrator
import math
import random
from PIL import Image, ImageDraw, ImageFont

logger = setup_logger(__name__)


class KeyframeAnimator:
    """Sistema de Keyframes profissional para animações suaves."""

    @staticmethod
    def linear(t: float) -> float: return t

    @staticmethod
    def ease_in(t: float) -> float: return t * t

    @staticmethod
    def ease_out(t: float) -> float: return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out(t: float) -> float: return t * t * (3 - 2 * t)

    @staticmethod
    def bounce(t: float) -> float:
        if t < 0.5: return 2 * t * t
        else: return 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def elastic(t: float) -> float:
        if t == 0 or t == 1: return t
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

    @staticmethod
    def get_easing(name: str):
        easings = {
            'linear': KeyframeAnimator.linear,
            'ease_in': KeyframeAnimator.ease_in,
            'ease_out': KeyframeAnimator.ease_out,
            'ease_in_out': KeyframeAnimator.ease_in_out,
            'bounce': KeyframeAnimator.bounce,
            'elastic': KeyframeAnimator.elastic
        }
        return easings.get(name, KeyframeAnimator.ease_in_out)

    def __init__(self):
        self.keyframes = []

    def add_keyframe(self, time: float, values: dict, easing: str = 'ease_in_out'):
        self.keyframes.append({'time': time, 'values': values, 'easing': easing})
        self.keyframes.sort(key=lambda k: k['time'])

    def get_value_at(self, time: float, property_name: str, default: float = 0) -> float:
        if not self.keyframes: return default
        if time <= self.keyframes[0]['time']: return self.keyframes[0]['values'].get(property_name, default)
        if time >= self.keyframes[-1]['time']: return self.keyframes[-1]['values'].get(property_name, default)

        next_kf = self.keyframes[-1]
        prev_kf = self.keyframes[0]

        for kf in self.keyframes:
            if kf['time'] > time:
                next_kf = kf
                break
            prev_kf = kf

        time_range = next_kf['time'] - prev_kf['time']
        if time_range <= 0: return next_kf['values'].get(property_name, default)

        progress = (time - prev_kf['time']) / time_range
        easing_func = self.get_easing(next_kf['easing'])
        eased_progress = easing_func(progress)

        start_val = prev_kf['values'].get(property_name, default)
        end_val = next_kf['values'].get(property_name, default)

        return start_val + (end_val - start_val) * eased_progress


class DynamicSpeakerTracker:
    """Rastreador dinâmico para conteúdo COM rostos (podcasts, entrevistas)."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

    def analyze_video_with_audio(self, video_path: Path, sample_interval: float = 0.5) -> tuple: # OTIMIZADO: 0.5s (2.5x faster)
        logger.info("🔍 Analisando vídeo para faces (High Precision)...")
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sample_frames = max(1, int(fps * sample_interval))

        face_timeline = []
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            if frame_idx % sample_frames == 0:
                timestamp = frame_idx / fps
                faces = self._detect_all_faces(frame)

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

        face_ratio = len(face_timeline) / max(1, frame_idx // sample_frames)
        has_faces = face_ratio > 0.3

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
        # OTIMIZADO: minNeighbors=6, minSize=(40,40)
        for cascade in [self.face_cascade, self.profile_cascade]:
            detected = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))  # OTIMIZADO: velocidade
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
            audio = next((a for a in audio_activity if abs(a['timestamp'] - timestamp) < 0.3), {'is_speaking': True})

            has_left = len(face_data['left_faces']) > 0
            has_right = len(face_data['right_faces']) > 0

            if audio.get('is_speaking', True):
                if has_left and has_right:
                    mode = 'SPLIT_V2'
                    target = {
                        'left': self._get_face_area(face_data['left_faces'][0], width, height),
                        'right': self._get_face_area(face_data['right_faces'][0], width, height)
                    }
                elif (has_left or has_right or len(face_data['center_faces']) > 0) and width > height:
                    # MODO GAMER/REACTION: Vídeo Horizontal + 1 Rosto Detectado
                    mode = 'GAMER_SPLIT'
                    all_faces = face_data['left_faces'] + face_data['right_faces'] + face_data['center_faces']
                    face = all_faces[0]
                    target = {
                        'gameplay': {'center_x': width//2, 'center_y': height//2, 'crop_width': int(height*16/9), 'crop_height': height},
                        'face': self._get_face_area(face, width, height)
                    }
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
            result.append({'timestamp': timestamp, 'mode': mode, 'target_area': target,
                           'frame_width': width, 'frame_height': height})

        return self._smooth_transitions(result)

    def _analyze_audio(self, video_path: Path) -> list:
        try:
            clip = VideoFileClip(str(video_path))
            temp_audio = Path(video_path).parent / "temp_audio.wav"
            clip.audio.write_audiofile(str(temp_audio), logger=None, verbose=False)
            clip.close()
            audio = AudioSegment.from_file(str(temp_audio))
            if temp_audio.exists(): temp_audio.unlink()

            activity = []
            interval = 0.5
            for t in np.arange(0, len(audio)/1000, interval):
                chunk = audio[int(t*1000):int((t+interval)*1000)]
                rms = chunk.rms if len(chunk) > 0 else 0
                activity.append({'timestamp': t, 'is_speaking': rms > 500})
            return activity
        except:
            return []

    def _smooth_transitions(self, timeline, min_duration=1.0):
        if len(timeline) < 3: return timeline
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
        """
        Crop 9:16 seguindo a regra de 1/3 (Eye-level).
        Garante que a cabeça não seja cortada e os olhos fiquem bem posicionados.
        """
        crop_h = height
        crop_w = int(crop_h * 9 / 16)
        if crop_w > width:
            crop_w = width
            crop_h = int(crop_w * 16 / 9)

        # CÁLCULO CINEMATOGRÁFICO:
        # Puxamos o centro do crop para cima para que os olhos fiquem a ~33% do topo
        # Usamos uma margem de segurança de 1.2x a altura da face detectada
        face_center_y = face['center_y']
        
        # Ponto ideal para os olhos no crop vertical: 1/3 da altura do crop
        # Compensamos a posição para que a cabeça tenha 'headroom'
        offset = int(face['height'] * 0.8) 
        target_center_y = max(crop_h // 2, face_center_y - offset)
        target_center_y = min(height - crop_h // 2, target_center_y)

        return {'center_x': face['center_x'], 'center_y': target_center_y,
                'crop_width': crop_w, 'crop_height': crop_h}

    def _get_both_area(self, face_data, width, height):
        all_faces = face_data['left_faces'] + face_data['right_faces'] + face_data['center_faces']
        if len(all_faces) < 2:
            return {'center_x': width//2, 'center_y': height//2, 'crop_width': int(height*9/16), 'crop_height': height}

        min_x = min(f['x'] for f in all_faces)
        max_x = max(f['x'] + f['width'] for f in all_faces)
        center_x = (min_x + max_x) // 2
        center_y = sum(f['center_y'] for f in all_faces) // len(all_faces)

        crop_w = int((max_x - min_x) * 1.5)
        crop_h = int(crop_w * 16 / 9)
        if crop_h > height:
            crop_h = height
            crop_w = int(crop_h * 9 / 16)

        return {'center_x': center_x, 'center_y': center_y, 'crop_width': crop_w, 'crop_height': crop_h}


class ZoomEffects:
    """Efeitos de Zoom otimizados para Shorts/Reels/TikTok."""

    @staticmethod
    def ken_burns(progress: float) -> float:
        return 1.0 + (0.15 * progress) # OTIMIZADO: 0.15

    @staticmethod
    def reverse_zoom(progress: float) -> float:
        return 1.25 - (0.25 * progress)

    @staticmethod
    def highlight_zoom(progress: float) -> float:
        return 1.0 + (0.25 * math.sin(progress * math.pi)) # OTIMIZADO: 0.25

    @staticmethod
    def smooth_zoom(progress: float) -> float:
        return 1.0 + (0.1 * progress)

    @staticmethod
    def dramatic_zoom(progress: float) -> float:
        eased = progress * progress * (3 - 2 * progress)
        return 1.0 + (0.3 * eased) # OTIMIZADO: 0.3

    # === NOVOS EFEITOS ===
    @staticmethod
    def tiktok_punch(progress: float) -> float:
        """Impacto rápido no início."""
        if progress < 0.2: return 1.0 + (0.4 * (progress / 0.2))
        elif progress < 0.4: return 1.4 - (0.2 * ((progress - 0.2) / 0.2))
        else: return 1.2

    @staticmethod
    def reels_slow(progress: float) -> float:
        """Zoom ultra-suave cinematico."""
        return 1.0 + (0.08 * (progress * progress))

    @staticmethod
    def shorts_dynamic(progress: float) -> float:
        """Pulsos dinâmicos."""
        return 1.0 + (0.15 * abs(math.sin(progress * math.pi * 2)))

    @staticmethod
    def get_random_effect():
        effects = [ZoomEffects.ken_burns, ZoomEffects.reverse_zoom, ZoomEffects.highlight_zoom,
                   ZoomEffects.dramatic_zoom, ZoomEffects.tiktok_punch, ZoomEffects.reels_slow, ZoomEffects.shorts_dynamic]
        return random.choice(effects)


class FacelessModeProcessor:
    """Processador para conteúdo FACELESS."""

    def __init__(self, target_w=1080, target_h=1920):
        self.target_w = target_w
        self.target_h = target_h

    def create_faceless_clip(self, clip, start, end, effect='ken_burns'):
        sub_clip = clip.subclip(start, end)
        w, h = sub_clip.size

        if effect == 'ken_burns': return self._apply_ken_burns(sub_clip, w, h)
        return self._apply_static_crop(sub_clip, w, h)

    def _apply_ken_burns(self, clip, w, h):
        duration = clip.duration
        crop_h = h
        crop_w = int(h * 9 / 16)
        if crop_w > w: crop_w = w; crop_h = int(w * 16 / 9)
        center_x, center_y = w // 2, h // 2

        zoom_effect = ZoomEffects.get_random_effect()

        def make_ken_burns_frame(get_frame, t):
            frame = get_frame(t)
            progress = t / duration
            current_zoom = zoom_effect(progress)

            actual_w = int(crop_w / current_zoom)
            actual_h = int(crop_h / current_zoom)

            x1 = max(0, min(w - actual_w, center_x - actual_w // 2))
            y1 = max(0, min(h - actual_h, center_y - actual_h // 2))

            cropped = frame[int(y1):int(y1+actual_h), int(x1):int(x1+actual_w)]
            if cropped.size == 0: return cv2.resize(frame, (self.target_w, self.target_h))
            return cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_AREA)  # OTIMIZADO

        return clip.fl(lambda gf, t: make_ken_burns_frame(gf, t))

    def _apply_static_crop(self, clip, w, h):
        crop_h = h; crop_w = int(h * 9/16)
        if crop_w > w: crop_w = w; crop_h = int(w * 16/9)
        x1 = (w - crop_w) // 2; y1 = (h - crop_h) // 2
        return crop(clip, x1=x1, y1=y1, width=crop_w, height=crop_h).resize((self.target_w, self.target_h))


class VideoEditor:
    """Editor Principal com Otimizações de Cache para CPU."""

    # Cache estático para análise de vídeo (compartilhado entre instâncias)
    _analysis_cache = {}

    def __init__(self):
        self.target_w = 1080
        self.target_h = 1920
        self.tracker = DynamicSpeakerTracker()
        self.faceless = FacelessModeProcessor(self.target_w, self.target_h)

    def create_clip(self, video_path: Path, start: float, end: float, output: Path,
                   thumbnail_path: Path = None, hook_text: str = None, segments: list = None,
                   add_captions: bool = True, **kwargs) -> Path:
        try:
            logger.info(f"🎬 Editando clipe: {start}s -> {end}s")
            original_clip = VideoFileClip(str(video_path))
            safe_end = min(end, original_clip.duration)

            # 0. Cache / Análise (Run once per video)
            cache_key = str(video_path)
            if cache_key in self._analysis_cache:
                logger.info("   ♻️ Usando cache de análise de rostos")
                speaker_data, has_faces = self._analysis_cache[cache_key]
            else:
                logger.info("   🔍 Iniciando análise de rostos (primeira vez)")
                speaker_data, has_faces = self.tracker.analyze_video_with_audio(video_path, sample_interval=0.5)  # OTIMIZADO
                self._analysis_cache[cache_key] = (speaker_data, has_faces)

            clips_sequence = []

            # 1. Thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info("   📸 Adding Thumbnail")
                thumb_clip = ImageClip(str(thumbnail_path)).set_duration(0.1).resize(height=self.target_h).set_position("center")
                clips_sequence.append(thumb_clip)

            # 2. Hook Viral
            hook_duration = 3.0
            content_start = start
            if safe_end - start > hook_duration:
                logger.info("   🎤 Creating VIRAL Hook (3s) with effects")
                hook_clip = self._create_viral_hook(original_clip, start, start + hook_duration, speaker_data, has_faces)
                if hook_clip: clips_sequence.append(hook_clip)
                content_start = start + hook_duration

            # 3. Main Clip
            if has_faces:
                logger.info("   🎥 Modo: Speaker-Following (com rostos)")
                main_clip = self._create_speaker_clip(original_clip, content_start, safe_end, speaker_data)
            else:
                logger.info("   🎥 Modo: Faceless (Ken Burns)")
                main_clip = self.faceless.create_faceless_clip(original_clip, content_start, safe_end, 'ken_burns')
            clips_sequence.append(main_clip)

            # Concatenation with Cinematic Transitions
            if len(clips_sequence) > 1:
                # EFEITO PREMIUM: White Flash entre clips
                final_clips = []
                for i, c in enumerate(clips_sequence):
                    if i > 0:
                        # Adicionar um pequeno flash branco de 0.1s
                        white_flash = ColorClip(size=c.size, color=(255,255,255)).set_duration(0.1).set_opacity(0.8)
                        final_clips.append(white_flash)
                    final_clips.append(c.crossfadein(0.2))
                final = concatenate_videoclips(final_clips, method="compose")
            else:
                final = concatenate_videoclips(clips_sequence, method="compose")

            # Color Grading ULTIMATE (Saturação + Contraste + Brilho)
            logger.info("   🎨 Aplicando Color Grading Professionial...")
            final = (final.fx(vfx.colorx, 1.15)                # Aumento de saturação
                      .fx(vfx.lum_contrast, contrast=0.1, lum=5) # Mais contraste e leve brilho
                      .fx(vfx.gamma_corr, gamma=1.1))          # Gamma para tons de pele melhores

            # 4. Captions
            if add_captions and segments:
                logger.info("   📝 Adicionando legendas...")
                try:
                    transcriber = AudioTranscriber()
                    words = transcriber.get_words_for_clip(segments, start, safe_end)

                    # Adjust offset for crossfades/hooks
                    crossfade_offset = (len(clips_sequence) - 1) * 0.3 if len(clips_sequence) > 1 else 0
                    thumb_offset = 0.1 if (thumbnail_path and os.path.exists(thumbnail_path)) else 0
                    hook_offset = hook_duration if safe_end - start > hook_duration else 0
                    total_offset = thumb_offset + hook_offset - crossfade_offset

                    adjusted_words = [{
                        'word': w['word'], 'start': max(0, w['start'] + total_offset), 'end': max(0, w['end'] + total_offset)
                    } for w in words]

                    captions = DynamicCaptions()
                    captions.pos_y_pct = 0.65
                    captions.font_size = 85
                    final = captions.create_captions(final, adjusted_words)
                except Exception as e: logger.warning(f"Error Captions: {e}")

            # Audio Normalization (CORRIGIDO: afx)
            if final.audio:
                logger.info("   🔊 Normalizando áudio (AFX)...")
                if not hasattr(final.audio, 'fps'):
                    final.audio.fps = 44100

                # Apply normalization to audio track directly
                try:
                    final.audio = final.audio.fx(afx.audio_normalize)
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao normalizar áudio: {e}")

            logger.info(f"   💾 Exportando: {output}")

            # OTIMIZAÇÃO CPU COLAB:
            # - preset='ultrafast' (velocidade máxima)
            # - threads=0 (usar todos os núcleos automaticamente)
            # - audio_fps=44100 (evitar ressampling)

            final.write_videofile(
                str(output),
                fps=30,
                codec="libx264",
                bitrate="5000k",
                audio_codec="aac",
                audio_bitrate="128k",
                threads=0, # Auto-detect all cores
                logger=None,
                preset='ultrafast',
                audio_fps=44100
            )
            return output

        except Exception as e:
            logger.error(f"❌ Erro no editor: {e}")
            return None
        finally:
            if 'original_clip' in locals(): original_clip.close()
            if 'final' in locals():
                try: final.close()
                except: pass

    def _create_speaker_clip(self, original_clip, start, end, speaker_data):
        clip = original_clip.subclip(start, end)
        w, h = clip.size
        clip_data = [d for d in speaker_data if start <= d['timestamp'] <= end]
        if not clip_data:
             # Fallback to faceless if no data for this segment
             return self.faceless.create_faceless_clip(original_clip, start, end, 'center_focus')

        def make_speaker_frame(get_frame, t):
            frame = get_frame(t)
            absolute_t = start + t
            closest = min(clip_data, key=lambda d: abs(d['timestamp'] - absolute_t))

            # Caso ESPECIAL: SPLIT SCREEN (Podcast Mode)
            if closest['mode'] == 'SPLIT_V2':
                # Obter áreas de crop para ambos
                target_top = closest['target_area']['left']
                target_bottom = closest['target_area']['right']

                # Crop Top
                cw1, ch1 = min(target_top['crop_width'], w), min(target_top['crop_height'], h)
                tx1 = max(0, min(w - cw1, target_top['center_x'] - cw1 // 2))
                ty1 = max(0, min(h - ch1, target_top['center_y'] - ch1 // 2))
                top_frame = frame[int(ty1):int(ty1+ch1), int(tx1):int(tx1+cw1)]
                top_frame = cv2.resize(top_frame, (self.target_w, self.target_h // 2), interpolation=cv2.INTER_AREA)

                # Crop Bottom
                cw2, ch2 = min(target_bottom['crop_width'], w), min(target_bottom['crop_height'], h)
                tx2 = max(0, min(w - cw2, target_bottom['center_x'] - cw2 // 2))
                ty2 = max(0, min(h - ch2, target_bottom['center_y'] - ch2 // 2))
                bottom_frame = frame[int(ty2):int(ty2+ch2), int(tx2):int(tx2+cw2)]
                bottom_frame = cv2.resize(bottom_frame, (self.target_w, self.target_h // 2), interpolation=cv2.INTER_AREA)

                # Combinar Verticalmente
                final_frame = np.vstack((top_frame, bottom_frame))
                
                # ADICIONAR DIVISÓRIA PREMIUM (Branco com brilho leve)
                mid_y = self.target_h // 2
                cv2.rectangle(final_frame, (0, mid_y-4), (self.target_w, mid_y+4), (255, 255, 255), -1) # Linha principal
                cv2.line(final_frame, (0, mid_y), (self.target_w, mid_y), (220, 220, 220), 1) # Detalhe interno
                
                return final_frame

            elif closest['mode'] == 'GAMER_SPLIT':
                # Obter áreas de crop (Gameplay Top, Face Bottom)
                target_game = closest['target_area']['gameplay']
                target_face = closest['target_area']['face']

                # 1. Renderizar Gameplay (Top) com SMART FILL (Mais Informação)
                # Em vez de crop 9:16, usamos 16:9 para mostrar o jogo todo e preenchemos o resto com blur
                cw_g, ch_g = w, h # Pegamos o horizonte todo
                game_frame_raw = frame[0:h, 0:w]
                
                # Criar fundo desfocado (1080x960)
                bg_game = cv2.resize(game_frame_raw, (self.target_w, self.target_h // 2), interpolation=cv2.INTER_AREA)
                bg_game = cv2.GaussianBlur(bg_game, (51, 51), 0) # Blur intenso
                
                # Renderizar jogo principal por cima (mantendo proporção para não cortar HUD/Mapa)
                # Redimensionamos o jogo para caber na largura total (1080)
                game_w_target = self.target_w
                game_h_target = int(game_w_target * (h / w))
                game_resized = cv2.resize(game_frame_raw, (game_w_target, game_h_target), interpolation=cv2.INTER_LANCZOS4)
                
                # Centralizar o jogo no fundo desfocado
                start_y = (self.target_h // 2 - game_h_target) // 2
                bg_game[start_y:start_y+game_h_target, 0:game_w_target] = game_resized
                game_frame = bg_game

                # 2. Renderizar Face (Bottom) - Foco Total no Gamer
                cw_f, ch_f = min(target_face['crop_width'], w), min(target_face['crop_height'], h)
                fx1 = max(0, min(w - cw_f, target_face['center_x'] - cw_f // 2))
                fy1 = max(0, min(h - ch_f, target_face['center_y'] - ch_f // 2))
                face_frame = frame[int(fy1):int(fy1+ch_f), int(fx1):int(fx1+cw_f)]
                face_frame = cv2.resize(face_frame, (self.target_w, self.target_h // 2), interpolation=cv2.INTER_AREA)

                # Combinar
                final_frame = np.vstack((game_frame, face_frame))
                
                # Divisória Estilizada com Brilho
                mid_y = self.target_h // 2
                cv2.rectangle(final_frame, (0, mid_y-5), (self.target_w, mid_y+5), (255, 255, 255), -1)
                cv2.rectangle(final_frame, (0, mid_y-2), (self.target_w, mid_y+2), (200, 200, 200), -1)
                return final_frame

            # Caso PADRÃO: Speaker-Following (Single Face)
            future_points = [d for d in clip_data if d['timestamp'] > absolute_t]
            if future_points:
                next_point = min(future_points, key=lambda d: d['timestamp'])
                
                # Garantir que o próximo ponto não seja SPLIT (para evitar erro de dict structure)
                if next_point['mode'] != 'SPLIT_V2' and closest['mode'] != 'SPLIT_V2':
                    time_diff = next_point['timestamp'] - closest['timestamp']
                    if time_diff > 0:
                        progress = min(1.0, (absolute_t - closest['timestamp']) / time_diff)
                        progress = progress * progress * (3 - 2 * progress) # ease-in-out interpolation

                        target_x = closest['target_area']['center_x'] + (next_point['target_area']['center_x'] - closest['target_area']['center_x']) * progress
                        target_y = closest['target_area']['center_y'] + (next_point['target_area']['center_y'] - closest['target_area']['center_y']) * progress

                        target = {
                            'center_x': int(target_x), 'center_y': int(target_y),
                            'crop_width': closest['target_area']['crop_width'], 'crop_height': closest['target_area']['crop_height']
                        }
                    else: target = closest['target_area']
                else: target = closest['target_area']
            else: target = closest['target_area']

            crop_w, crop_h = min(target['crop_width'], w), min(target['crop_height'], h)
            x1 = max(0, min(w - crop_w, target['center_x'] - crop_w // 2))
            y1 = max(0, min(h - crop_h, target['center_y'] - crop_h // 2))

            cropped = frame[int(y1):int(y1+crop_h), int(x1):int(x1+crop_w)]
            if cropped.size == 0: return cv2.resize(frame, (self.target_w, self.target_h))
            return cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_AREA)  # OTIMIZADO

        return clip.fl(lambda gf, t: make_speaker_frame(gf, t))

    def _create_viral_hook(self, original_clip, start, end, speaker_data, has_faces):
        clip = original_clip.subclip(start, end)
        w, h = clip.size
        duration = end - start

        crop_h = h; crop_w = int(h * 9 / 16)
        if crop_w > w: crop_w = w; crop_h = int(w * 16 / 9)

        center_x, center_y = w // 2, h // 2
        if has_faces and speaker_data:
            clip_data = [d for d in speaker_data if start <= d['timestamp'] <= end]
            if clip_data:
                center_x, center_y = clip_data[0]['target_area']['center_x'], clip_data[0]['target_area']['center_y']

        impact_phrases = ["VOCÊ PRECISA VER ISSO!", "OLHA SÓ O QUE ACONTECEU!", "NÃO VAI ACREDITAR!", "ASSISTA ATÉ O FINAL!"]
        impact_text = random.choice(impact_phrases)

        narration_clip = None
        try:
            narrator = get_narrator()
            narration_path = Config.TEMP_DIR / f"hook_narration_{start:.0f}.mp3"
            if narrator.generate_narration(impact_text, narration_path):
                narration_clip = AudioFileClip(str(narration_path))
                if narration_clip.duration > duration: narration_clip = narration_clip.subclip(0, duration)
        except Exception: pass

        def make_viral_hook_frame(get_frame, t):
            frame = get_frame(t)
            progress = t / duration

            # Zoom Punch TikTok Style
            if progress < 0.25: zoom = 1.0 + (0.35 * (progress / 0.25))
            elif progress < 0.5: zoom = 1.35
            else:
                 eased = (progress - 0.5) / 0.5; eased = eased * eased * (3 - 2 * eased)
                 zoom = 1.35 - (0.35 * eased)

            actual_w, actual_h = int(crop_w / zoom), int(crop_h / zoom)
            x1 = max(0, min(w - actual_w, center_x - actual_w // 2))
            y1 = max(0, min(h - actual_h, center_y - actual_h // 2))

            cropped = frame[int(y1):int(y1+actual_h), int(x1):int(x1+actual_w)]
            if cropped.size == 0: result = cv2.resize(frame, (self.target_w, self.target_h))
            else: result = cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_AREA)  # OTIMIZADO

            return self._add_impact_text(result, impact_text, progress)

        hook_clip = clip.fl(lambda gf, t: make_viral_hook_frame(gf, t))

        if narration_clip:
            original_audio = hook_clip.audio.volumex(0.2) if hook_clip.audio else None
            hook_clip = hook_clip.set_audio(CompositeAudioClip([original_audio, narration_clip.volumex(1.2)]))
        else: hook_clip = hook_clip.volumex(0.3)
        return hook_clip

    def _add_impact_text(self, frame, text, progress):
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        font_size = 70

        # Load font Portátil (Assets > Desktop > Fallback)
        base_path = Path(__file__).parent.parent
        font_path = base_path / "assets/fonts/Oswald-Bold.ttf"
        
        try: font = ImageFont.truetype(str(font_path), font_size)
        except:
            try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except: font = ImageFont.load_default()

        if progress < 0.2: alpha = int(255 * (progress / 0.2))
        elif progress > 0.8: alpha = int(255 * ((1.0 - progress) / 0.2))
        else: alpha = 255

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (self.target_w - text_w) // 2, int(self.target_h * 0.15)

        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx*dx + dy*dy <= 16: draw.text((x + dx, y + dy), text, font=font, fill=(0,0,0))
        draw.text((x, y), text, font=font, fill=(255, 200, 0))

        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
