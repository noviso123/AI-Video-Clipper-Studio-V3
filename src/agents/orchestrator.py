"""
Agente Orquestrador Otimizado (Regras - 100% Offline e Rápido)
Substitui IA generativa por templates de sucesso comprovados.
"""
import logging
from typing import Dict, Any, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class OrchestratorAgent:
    def __init__(self):
        # Nenhuma dependência externa
        pass

    def plan_video(self, transcription_text: str, duration: float, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Orquestrador Inteligente Offline (Simulação de IA).
        Analisa o conteúdo semanticamente para escolher o melhor template.
        """
        logger.info("🧠 Orquestrador: Analisando semântica do conteúdo (Offline Intelligence)...")

        # 1. Análise de Arquétipo do Conteúdo
        archetype = self._analyze_archetype(transcription_text)
        logger.info(f"   📋 Arquétipo Detectado: {archetype['name']}")

        # 2. Seleção de Template Baseado no Arquétipo
        plan = self._get_template_by_archetype(archetype['name'])

        # 3. Ajustes Finos baseados na duração
        if duration < 30:
            plan['editing_style'] += " (Ultra Fast)"
            plan['hook_strategy'] = "Loop Infinito + Hook"

        return plan

    def _analyze_archetype(self, text: str) -> Dict[str, Any]:
        """Classifica o conteúdo baseando-se em palavras-chave e padrões."""
        text = text.lower()

        scores = {
            'MOTIVACIONAL': 0,
            'EDUCATIVO': 0,
            'FRENÉTICO': 0,
            'DARK': 0
        }

        # Dicionários de Palavras-Chave (Intelligence Database)
        keywords = {
            'MOTIVACIONAL': ['sucesso', 'vida', 'sonho', 'dinheiro', 'luta', 'vencer', 'acredite', 'foco', 'deus', 'força'],
            'EDUCATIVO': ['como', 'dica', 'tutorial', 'passo', 'aprenda', 'segredo', 'método', 'ferramenta', 'aula'],
            'FRENÉTICO': ['rápido', 'agora', 'urgente', 'corre', 'imediato', 'insano', 'bizarro', 'top', 'melhor'],
            'DARK': ['erro', 'cuidado', 'perigo', 'medo', 'fracasso', 'nunca', 'evite', 'pare', 'atenção']
        }

        for category, words in keywords.items():
            for word in words:
                scores[category] += text.count(word)

        # Encontrar categoria dominante
        best_match = max(scores, key=scores.get)

        # Se scores muito baixos, default para Frenético (Funciona pra tudo)
        if scores[best_match] < 2:
            best_match = 'FRENÉTICO'

        return {'name': best_match, 'scores': scores}

    def _get_template_by_archetype(self, archetype: str) -> Dict[str, Any]:
        """Retorna templates otimizados para cada estilo."""
        if archetype == 'MOTIVACIONAL':
            return {
                "video_vibe": "Inspirador/Épico",
                "editing_style": "Cinemático (Zoom Lento + Cortes Suaves)",
                "caption_style": "Minimalista Gold (Fonte: Oswald)",
                "hook_strategy": "Frase Filosófica + Imagem Impactante",
                "bg_music": "Inspiring Cinematic",
                "transitions": "Fade Black / Slow Dissolve",
                "visual_notes": "Use B-Rolls de luxo ou natureza se disponível"
            }
        elif archetype == 'EDUCATIVO':
            return {
                "video_vibe": "Autoridade/Clareza",
                "editing_style": "Cortes Precisos (Jump Cuts nos silêncios)",
                "caption_style": "Highlight Green (Destaque palavras-chave)",
                "hook_strategy": "Promessa de Resultado ('Você vai aprender...')",
                "bg_music": "Lo-Fi Focus",
                "transitions": "Slide / Push",
                "visual_notes": "Zoom explicativo quando falar termos técnicos"
            }
        elif archetype == 'DARK':
            return {
                "video_vibe": "Tensão/Mistério",
                "editing_style": "Cortes Secos + Efeitos Glitch",
                "caption_style": "Alert Red (Fonte: Impact)",
                "hook_strategy": "Alerta de Perigo ('Pare de fazer isso')",
                "bg_music": "Dark Suspense / Trap Deep",
                "transitions": "Glitch / Noise",
                "visual_notes": "Diminuir saturação, aumentar contraste"
            }
        else: # FRENÉTICO / PADRÃO
            return {
                "video_vibe": "Alta Energia/Viral",
                "editing_style": "Cortes Rápidos (A cada 2s máx)",
                "caption_style": "Viral Bold Colorido",
                "hook_strategy": "Pergunta Provocativa + Zoom Punch",
                "bg_music": "Trending Phonk / Upbeat",
                "transitions": "Whip / Zoom Blur",
                "visual_notes": "Muitos emojis e stickers"
            }

    def _get_fallback_plan(self) -> Dict[str, Any]:
        return self.plan_video("", 0)
