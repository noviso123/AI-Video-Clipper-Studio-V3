"""
Módulo de Legendas Dinâmicas (Fase 7) - VERSÃO 2.0
Cria legendas word-level animadas estilo Hormozi

MELHORIAS V2:
- Detecta legendas existentes e evita sobreposição
- Posicionamento inteligente baseado no conteúdo do vídeo
- Suporte a múltiplas posições dinâmicas
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from moviepy.editor import VideoClip, TextClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import numpy as np
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Import opcional do detector de legendas
try:
    from .subtitle_detector import SubtitleDetector
    SUBTITLE_DETECTOR_AVAILABLE = True
except ImportError:
    SUBTITLE_DETECTOR_AVAILABLE = False


class DynamicCaptions:
    """Cria legendas dinâmicas word-level com posicionamento inteligente"""

    # Estilos de legenda predefinidos
    STYLES = {
        'hormozi': {
            'fontsize': 70,
            'font': 'Arial-Bold',
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 3,
            'method': 'caption',
            'align': 'center'
        },
        'modern': {
            'fontsize': 75,
            'font': 'Roboto-Bold', 
            'color': '#FFFFFF', # Branco
            'stroke_color': '#000000', # Preto
            'stroke_width': 4,
            'highlight_color': '#00FF00', # Verde Neon
            'highlight_stroke': '#000000',
            'method': 'caption',
            'align': 'center'
        },
        'neon': {
            'fontsize': 80,
            'font': 'Impact',
            'color': '#00FFFF', # Ciano
            'stroke_color': '#000000',
            'stroke_width': 4,
            'highlight_color': '#FF00FF', # Magenta
            'highlight_stroke': '#FFFFFF',
            'method': 'caption',
            'align': 'center',
            'shadow_color': 'black',
            'shadow_offset': (5, 5)
        },
        'bold_pro': {
            'fontsize': 65,
            'font': 'Verdana-Bold',
            'color': '#FFD700', # Ouro
            'stroke_color': '#000000',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center',
            'bg_color': 'rgba(0,0,0,0.6)' # Fundo semi-transparente
        },
        'karaoke_modern': {
            'fontsize': 60,                # Tamanho equilibrado
            'font': 'Arial-Bold',          # Fonte limpa e universal
            'color': '#FFFFFF',            # Branco puro (padrão TV)
            'stroke_color': '#000000',     # Stroke preto
            'stroke_width': 3,             # Contraste alto
            'highlight_color': '#FFD700',  # Ouro sutil para palavra atual (Karaokê)
            'highlight_stroke': '#000000', 
            'method': 'caption',
            'align': 'center',
            'uppercase': False             # Manter case original (mais formal)
        }
    }
    
    # Posições Y em porcentagem da altura do vídeo
    POSITIONS = {
        'top': 0.12,
        'upper': 0.25,
        'center': 0.50,
        'lower': 0.65,
        'bottom': 0.75  # AUMENTADO MARGEM DE SEGURANÇA (era 0.82). Evita sobrepor UI do TikTok.
    }

    def __init__(self, style: str = 'hormozi'):
        """
        Inicializa o criador de legendas

        Args:
            style: Estilo de legenda ('hormozi', 'mr_beast', 'minimal', 'tiktok')
        """
        self.style_name = style
        self.style = self.STYLES.get(style, self.STYLES['hormozi'])
        
        # Inicializar detector de legendas
        self.subtitle_detector = None
        if SUBTITLE_DETECTOR_AVAILABLE:
            self.subtitle_detector = SubtitleDetector()
        
        logger.info(f"📝 Dynamic Captions inicializado (estilo: {style})")
        logger.info(f"   Detecção de legendas existentes: {'Ativo' if self.subtitle_detector else 'Inativo'}")

    def create_captions(
        self,
        video_clip: VideoClip,
        words: List[Dict],
        position: str = 'auto',
        video_path: Path = None
    ) -> VideoClip:
        """
        Adiciona legendas dinâmicas ao vídeo com posicionamento inteligente

        Args:
            video_clip: Clip de vídeo original
            words: Lista de palavras com timestamps
            position: Posição das legendas ('auto', 'top', 'center', 'bottom')
            video_path: Caminho do vídeo (para detectar legendas existentes)

        Returns:
            Vídeo com legendas
        """
        logger.info(f"📝 Criando legendas dinâmicas (estilo: {self.style_name})")
        logger.info(f"   Total de palavras: {len(words)}")

        if not words:
            logger.warning("   Nenhuma palavra fornecida, retornando vídeo sem legendas")
            return video_clip

        # Determinar posição ideal
        actual_position = self._determine_optimal_position(
            position, video_path, video_clip.size
        )
        
        logger.info(f"   Posição das legendas: {actual_position}")

        try:
            # Criar clips de texto para cada palavra
            text_clips = []

            # Agrupar palavras em frases curtas (Smart Grouping)
            grouped_words = self._group_words(words, max_chars=25, max_duration=3.0)
            
            for group in grouped_words:
                # Usar nova lógica de Karaoke (PIL-based para alinhamento perfeito)
                karaoke_clips = self._create_karaoke_group(
                    group,
                    video_clip.size,
                    actual_position
                )
                text_clips.extend(karaoke_clips)

            if not text_clips:
                logger.warning("   Nenhum clip de texto criado")
                return video_clip

            # Combinar vídeo + legendas
            final_video = CompositeVideoClip([video_clip] + text_clips)

            logger.info(f"✅ {len(text_clips)} legendas adicionadas")

            return final_video

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def _determine_optimal_position(
        self,
        requested_position: str,
        video_path: Path,
        video_size: Tuple[int, int]
    ) -> str:
        """
        Determina a posição ideal para as legendas.
        
        Se 'auto', detecta legendas existentes e escolhe posição que evita sobreposição.
        """
        if requested_position != 'auto':
            return requested_position
        
        # Tentar detectar legendas existentes
        if self.subtitle_detector and video_path:
            try:
                result = self.subtitle_detector.detect_subtitle_regions(video_path, sample_count=5)
                
                if result.get('has_subtitles'):
                    existing_pos = result.get('subtitle_position')
                    suggested = result.get('suggested_new_position', 'bottom')
                    
                    logger.info(f"   🔍 Legendas existentes detectadas em: {existing_pos}")
                    logger.info(f"   📍 Usando posição alternativa: {suggested}")
                    
                    return suggested
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao detectar legendas existentes: {e}")
        
        # Padrão: bottom para vídeos verticais, center para horizontais
        video_w, video_h = video_size
        if video_h > video_w:  # Vertical
            return 'bottom'
        else:  # Horizontal
            return 'lower'

    def _create_word_clip(
        self,
        word: str,
        start: float,
        end: float,
        video_size: Tuple[int, int],
        position: str
    ) -> Optional[TextClip]:
        """
        Cria clip de texto para uma palavra

        Args:
            word: Palavra a exibir
            start: Tempo de início
            end: Tempo de fim
            video_size: Tamanho do vídeo (largura, altura)
            position: Posição da legenda

        Returns:
            TextClip ou None se houver erro
        """
        try:
            # Lógica de Highlight (se a palavra for chave)
            if word.lower() in ['dinheiro', 'sucesso', 'agora', 'atenção', 'segredo', 'você', 'eu', 'nós']:
                 color = self.style.get('highlight_color', self.style['color'])
                 stroke_color = self.style.get('highlight_stroke', self.style['stroke_color'])
            else:
                 color = self.style['color']
                 stroke_color = self.style['stroke_color']

            # Criar texto
            txt_clip = TextClip(
                word,
                fontsize=self.style['fontsize'],
                font=self.style['font'],
                color=color,
                stroke_color=stroke_color,
                stroke_width=self.style['stroke_width'],
                method=self.style['method'],
                size=(video_size[0] * 0.9, None) if len(word) > 10 else None # Wrap se for frase longa
            )

            # Definir duração e posição temporal
            txt_clip = txt_clip.set_start(start).set_duration(end - start)

            # Calcular posição na tela
            video_w, video_h = video_size
            y_pct = self.POSITIONS.get(position, self.POSITIONS['bottom'])
            y_pos = video_h * y_pct

            txt_clip = txt_clip.set_position(('center', y_pos))

            # Adicionar animação de entrada (Pop ou Fade)
            if self.style_name in ['modern', 'neon']:
                 # Pop effect (scale up) - Simulado com resize (custoso) ou apenas fade rapido
                 txt_clip = fadein(txt_clip, 0.1)
            else:
                 fade_duration = min(0.1, (end - start) / 2)
                 txt_clip = fadein(txt_clip, fade_duration)
                 txt_clip = fadeout(txt_clip, fade_duration)

            return txt_clip

        except Exception as e:
            # Tentar fallback com PIL se o erro for de ImageMagick
            if "ImageMagick" in str(e) or "WinError 2" in str(e):
                logger.warning(f"   ⚠️ ImageMagick não encontrado. Usando fallback PIL para '{word}'")
                return self._create_word_clip_pil(word, start, end, video_size, position)

            logger.warning(f"   Erro ao criar clip para '{word}': {e}")
            return None

    def _create_word_clip_pil(
        self,
        word: str,
        start: float,
        end: float,
        video_size: Tuple[int, int],
        position: str
    ) -> Optional[VideoClip]:
        """Fallback: Cria clip de texto usando PIL (sem ImageMagick)"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            from moviepy.editor import ImageClip

            # Configurações básicas
            fontsize = self.style['fontsize']
            
            # Tentar carregar fonte
            font = self._get_pil_font(fontsize)

            # Criar imagem transparente
            img_w, img_h = 1080, 200  # Tamanho fixo para o container do texto
            img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Cor e Stroke (Produção)
            fill_color = self.style['color']
            stroke_color = self.style['stroke_color']
            stroke_width = self.style.get('stroke_width', 0)

            # Desenhar stroke manualmente
            x = img_w // 2
            y = img_h // 2

            if stroke_width > 0:
                for off_x in range(-stroke_width, stroke_width + 1):
                    for off_y in range(-stroke_width, stroke_width + 1):
                        draw.text((x + off_x, y + off_y), word, font=font, fill=stroke_color, anchor="mm")

            # Desenhar texto principal
            draw.text((x, y), word, font=font, fill=fill_color, anchor="mm")

            # Converter para numpy array
            img_np = np.array(img)

            # Criar ImageClip
            txt_clip = ImageClip(img_np)
            txt_clip = txt_clip.set_start(start).set_duration(end - start)

            # Calcular posição
            video_w, video_h = video_size
            y_pct = self.POSITIONS.get(position, self.POSITIONS['bottom'])
            y_pos = video_h * y_pct

            txt_clip = txt_clip.set_position(('center', y_pos))

            return txt_clip

        except Exception as e:
            logger.error(f"   ❌ Falha fatal no fallback PIL: {e}")
            return None

    def _create_karaoke_group(self, group: Dict, video_size: Tuple[int, int], position: str) -> List[VideoClip]:
        """
        Cria UM clip por frase usando make_frame para renderizar Karaokê dinamicamente.
        Isso evita criar centenas de ImageClips que travam o MoviePy.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            from moviepy.editor import VideoClip
            
            words = group['words']
            if not words: return []

            start_time = group['start']
            end_time = group['end']
            duration = end_time - start_time
            
            # 1. Configurar Fonte e Dimensões (Calculados uma vez)
            fontsize = self.style['fontsize']
            font = self._get_pil_font(fontsize)
            
            video_w, video_h = video_size
            img_w, img_h = video_w, int(video_h * 0.25) # Área de texto um pouco maior
            
            # Posição Y
            y_pct = self.POSITIONS.get(position, self.POSITIONS['bottom'])
            y_pos_video = video_h * y_pct
            
            full_text = group['text']
            
            # Calcular geometria (uma vez)
            draw_temp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
            total_text_w = draw_temp.textlength(full_text, font=font)
            start_x = (img_w - total_text_w) // 2
            center_y = img_h // 2
            
            # Cores
            base_color = self.style['color']
            stroke_color = self.style['stroke_color']
            stroke_width = self.style.get('stroke_width', 2)
            highlight_color = self.style.get('highlight_color', '#00FF00')
            highlight_stroke = self.style.get('highlight_stroke', stroke_color) # Stroke do highlight

            # Pré-calcular posições das palavras para não recalcular a cada frame
            word_positions = []
            curr_x = start_x
            space_w = draw_temp.textlength(" ", font=font)
            
            for w in words:
                w_len = draw_temp.textlength(w['word'], font=font)
                word_positions.append({
                    'word': w['word'],
                    'x': curr_x,
                    'width': w_len,
                    'start_rel': w['start'] - start_time,
                    'end_rel': w['end'] - start_time
                })
                curr_x += w_len + space_w

            # FUNÇÃO GERADORA DE FRAMES (Executa a cada frame do vídeo)
            def make_frame(t):
                # t é relativo ao inicio do clip (0 a duration)
                
                # Criar imagem transparente base
                img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Desenhar cada palavra
                for i, wp in enumerate(word_positions):
                    # Verificar se esta palavra deve estar iluminada no tempo t
                    is_active = wp['start_rel'] <= t <= wp['end_rel']
                    
                    fill = highlight_color if is_active else base_color
                    stroke = highlight_stroke if is_active else stroke_color
                    
                    # Desenhar (com stroke manual pois PIL é limitado)
                    x, y = wp['x'], center_y
                    
                    # Stroke
                    if stroke_width > 0:
                        for off_x in range(-stroke_width, stroke_width + 1):
                            for off_y in range(-stroke_width, stroke_width + 1):
                                draw.text((x + off_x, y + off_y), wp['word'], font=font, fill=stroke, anchor="lm")
                    
                    # Fill
                    draw.text((x, y), wp['word'], font=font, fill=fill, anchor="lm")
                
                # Convert RGBA to RGB with proper alpha handling
                arr = np.array(img)
                # Return only RGB (3 channels), not RGBA (4 channels)
                rgb = arr[:, :, :3]
                return rgb
            
            # Função para gerar máscara de transparência
            def make_mask(t):
                img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                for i, wp in enumerate(word_positions):
                    is_active = wp['start_rel'] <= t <= wp['end_rel']
                    fill = highlight_color if is_active else base_color
                    stroke = highlight_stroke if is_active else stroke_color
                    x, y = wp['x'], center_y
                    
                    if stroke_width > 0:
                        for off_x in range(-stroke_width, stroke_width + 1):
                            for off_y in range(-stroke_width, stroke_width + 1):
                                draw.text((x + off_x, y + off_y), wp['word'], font=font, fill=stroke, anchor="lm")
                    draw.text((x, y), wp['word'], font=font, fill=fill, anchor="lm")
                
                arr = np.array(img)
                # Return alpha channel normalized to 0-1
                return arr[:, :, 3] / 255.0

            # Criar VideoClip Customizado com máscara
            clip = VideoClip(make_frame, duration=duration)
            mask_clip = VideoClip(make_mask, ismask=True, duration=duration)
            clip = clip.set_mask(mask_clip)
            clip = clip.set_start(start_time).set_position((0, y_pos_video))
            
            return [clip] # Retorna lista com 1 único clip, compatível com lógica anterior

        except Exception as e:
            logger.error(f"Erro no Karaoke Generator: {e}")
            return []

    def _draw_text_pil(self, draw, pos, text, font, fill, stroke, width):
        """Helper para desenhar texto com stroke"""
        x, y = pos
        # Stroke
        if width > 0:
            for off_x in range(-width, width + 1):
                for off_y in range(-width, width + 1):
                    draw.text((x + off_x, y + off_y), text, font=font, fill=stroke, anchor="lm")
        # Fill
        draw.text((x, y), text, font=font, fill=fill, anchor="lm")

    def _get_pil_font(self, size: int):
        """Obtém uma fonte PIL com fallbacks."""
        from PIL import ImageFont
        import os
        
        font_paths = [
            # Linux (Ubuntu/Debian)
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            # Linux (Fedora/Bazzite)
            '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf',
            '/usr/share/fonts/google-noto/NotoSans-Bold.ttf',
            # Windows
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/impact.ttf',
            # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial Bold.ttf',
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()

    def create_sentence_captions(
        self,
        video_clip: VideoClip,
        segments: List[Dict],
        position: str = 'auto',
        video_path: Path = None
    ) -> VideoClip:
        """
        Cria legendas por frase (fallback se word-level não disponível)
        """
        try:
            if not segments:
                return video_clip
            
            # Determinar posição ideal
            actual_position = self._determine_optimal_position(
                position, video_path, video_clip.size
            )
            
            text_clips = []
            for segment in segments:
                text_clip = self._create_word_clip(
                    segment.get('text', ''),
                    segment.get('start', 0),
                    segment.get('end', 1),
                    video_clip.size,
                    actual_position
                )
                if text_clip:
                    text_clips.append(text_clip)
            
            if text_clips:
                return CompositeVideoClip([video_clip] + text_clips)
            return video_clip
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def get_available_positions(self) -> Dict[str, float]:
        """Retorna as posições disponíveis para legendas."""
        return self.POSITIONS.copy()

    def set_custom_position(self, name: str, y_percentage: float):
        """
        Define uma posição customizada para legendas.
        
        Args:
            name: Nome da posição
            y_percentage: Posição Y em porcentagem (0.0 = topo, 1.0 = base)
        """
        self.POSITIONS[name] = max(0.05, min(0.95, y_percentage))
        logger.info(f"   📍 Posição customizada '{name}' definida em {y_percentage:.0%}")

    def _group_words(self, words: List[Dict], max_chars: int = 25, max_duration: float = 2.5) -> List[Dict]:
        """Agrupa palavras em frases curtas (Smart Grouping)"""
        if not words:
            return []
            
        groups = []
        current_group = []
        current_chars = 0
        current_start = words[0]['start']
        
        for i, word in enumerate(words):
            w_len = len(word['word'])
            w_end = word['end']
            
            # Condições para quebrar o grupo:
            # 1. Muito longo (caracteres)
            # 2. Muito longo (tempo)
            # 3. Pausa grande antes desta palavra (silêncio)
            
            time_gap = word['start'] - (words[i-1]['end'] if i > 0 else word['start'])
            
            if (current_chars + w_len > max_chars) or \
               (w_end - current_start > max_duration) or \
               (time_gap > 0.5): # Pausa de 0.5s = nova frase
                
                # Fechar grupo anterior
                if current_group:
                    groups.append({
                        'text': ' '.join([w['word'] for w in current_group]),
                        'start': current_group[0]['start'],
                        'end': current_group[-1]['end'],
                        'words': current_group
                    })
                
                # Iniciar novo grupo
                current_group = [word]
                current_chars = w_len
                current_start = word['start']
            else:
                current_group.append(word)
                current_chars += w_len + 1 # +1 para o espaço
                
        # Adicionar último grupo
        if current_group:
            groups.append({
                'text': ' '.join([w['word'] for w in current_group]),
                'start': current_group[0]['start'],
                'end': current_group[-1]['end'],
                'words': current_group
            })
            
        return groups
if __name__ == "__main__":
    # Teste rápido
    captions = DynamicCaptions(style='hormozi')
    print("Dynamic Captions inicializado com sucesso!")
    print(f"Posições disponíveis: {captions.get_available_positions()}")
