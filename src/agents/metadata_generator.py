"""
Gerador Inteligente de Metadados Virais
Usa Ollama para criar títulos, descrições e hashtags otimizados por plataforma.
"""
import os
import json
import requests
from typing import Dict, List, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)

from agno.agent import Agent
from agno.models.google import Gemini
from ..core.config import config as app_config
from .knowledge_base import get_viral_knowledge_base

class MetadataGenerator:
    """Gera metadados virais e otimizados usando Agno + Gemini + RAG"""
    
    def __init__(self):
        self.model = app_config.GEMINI_MODEL
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.language = os.getenv("METADATA_LANGUAGE", "pt-BR")
        self.tone = os.getenv("METADATA_TONE", "casual")
        
        # Obter Knowledge Base (RAG)
        self.knowledge_base = get_viral_knowledge_base()
        
        # Inicializar Agente Agno com RAG (usa GOOGLE_API_KEY do env)
        self.agent = Agent(
            model=Gemini(id=self.model),
            knowledge=self.knowledge_base,
            search_knowledge=True,
            description="Você é um especialista em SEO e marketing viral para redes sociais (TikTok, YouTube, Instagram).",
            instructions=[
                f"Sempre responda em {self.language}.",
                f"Use um tom {self.tone}.",
                "Antes de responder, pesquise na sua base de conhecimento por diretrizes específicas da plataforma.",
                "Crie títulos magnéticos e descrições otimizadas para engajamento.",
                "Não use aspas nos títulos ou hashtags."
            ],
            markdown=True
        )
        
        # Configurações por plataforma
        self.platform_configs = {
            "tiktok": {
                "title_max_length": 150,
                "description_max_length": 2200,
                "hashtag_count": 15,
                "style": "casual e direto"
            },
            "youtube": {
                "title_max_length": 90,
                "description_max_length": 5000,
                "hashtag_count": 15,
                "style": "profissional mas acessível"
            },
            "instagram": {
                "title_max_length": 100,
                "description_max_length": 2200,
                "hashtag_count": 20,
                "style": "engajador e visual"
            }
        }
    
    def generate_metadata(
        self, 
        transcript: str, 
        viral_moment: dict, 
        platform: str = "all"
    ) -> Dict[str, Dict]:
        """Gera metadados virais usando Agno Agent"""
        logger.info(f"🧠 Gerando metadados virais com Agno ({platform})...")
        
        platforms_to_generate = (
            ["tiktok", "youtube", "instagram"] if platform == "all" 
            else [platform]
        )
        
        results = {}
        for plat in platforms_to_generate:
            try:
                prompt = self._build_platform_prompt(plat, transcript, viral_moment)
                response = self.agent.run(prompt)
                
                # O Agno retorna a resposta em formato texto/markdown
                # Precisamos garantir que conseguimos extrair os dados.
                # Aqui simplificamos a extração para este exemplo, no futuro podemos usar Structured Output
                results[plat] = self._parse_agent_response(response.content, plat, viral_moment)
                logger.info(f"   ✅ {plat.capitalize()}: \"{results[plat]['title'][:50]}...\"")
            except Exception as e:
                logger.error(f"   ❌ Erro ao gerar metadados para {plat}: {e}")
                results[plat] = self._get_fallback_metadata(plat, viral_moment.get('hook', ''), transcript[:200])
        
        return results

    def _build_platform_prompt(self, platform: str, transcript: str, viral_moment: dict) -> str:
        config = self.platform_configs[platform]
        return f"""
        Gere metadados para {platform.upper()}.
        
        CONTEXTO DO VÍDEO: {viral_moment.get('context', transcript[:500])}
        GANCHO DETECTADO: {viral_moment.get('hook', '')}
        
        REGRAS PARA {platform.upper()}:
        - Estilo: {config['style']}
        - Título: Máx {config['title_max_length']} chars. Use gatilhos mentais.
        - Descrição: Máx {config['description_max_length']} chars. CTA engajador.
        - Hashtags: Exatamente {config['hashtag_count']} hashtags relevantes.
        
        Responda EXATAMENTE neste formato JSON:
        {{
            "title": "Seu título aqui",
            "description": "Sua descrição aqui",
            "hashtags": ["#tag1", "#tag2", ...]
        }}
        """

    def _parse_agent_response(self, content: str, platform: str, viral_moment: dict) -> Dict:
        """Tenta extrair JSON da resposta do agente"""
        try:
            # Limpar markdown se houver
            clean_content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_content)
            return data
        except:
            logger.warning("⚠️ Falha ao parsear JSON do Agno, usando fallback parcial")
            return self._get_fallback_metadata(platform, viral_moment.get('hook', ''), content[:200])
    
    def _get_fallback_metadata(
        self, 
        platform: str, 
        hook: str, 
        context: str
    ) -> Dict:
        """Metadados de fallback se IA falhar"""
        hashtags = self._get_default_hashtags(platform)
        title = (hook or context[:50]).upper() + "! 🔥"
        description = f"{hook}\n\n{context[:300]}...\n\n" + " ".join(hashtags)
        
        return {
            "title": title,
            "description": description,
            "hashtags": hashtags
        }
    
    def _get_default_hashtags(self, platform: str) -> List[str]:
        """Hashtags padrão por plataforma"""
        defaults = {
            "tiktok": [
                "#viral", "#fyp", "#foryou", "#foryoupage", "#trending",
                "#brasil", "#shorts", "#viralvideo", "#tiktokviral",
                "#explore", "#videovirais", "#conteudo", "#braziltiktok"
            ],
            "youtube": [
                "#Shorts", "#YouTubeShorts", "#Viral", "#Trending",
                "#Brasil", "#Portuguese", "#ViralShorts", "#ShortsFeed",
                "#Explore", "#Recommended", "#BrasilYouTube"
            ],
            "instagram": [
                "#reels", "#reelsinstagram", "#reelsviral", "#viral",
                "#trending", "#explorepage", "#explore", "#instagood",
                "#brasil", "#instabrasil", "#reelsbrasil", "#viralreels",
                "#foryou", "#fyp", "#instadaily"
            ]
        }
        return defaults.get(platform, defaults["tiktok"])
    
    def validate_metadata(self, metadata: dict, platform: str) -> bool:
        """Valida se metadados atendem requisitos da plataforma"""
        config = self.platform_configs[platform]
        
        checks = [
            len(metadata['title']) <= config['title_max_length'],
            len(metadata['description']) <= config['description_max_length'],
            len(metadata['hashtags']) > 0,
            all(tag.startswith('#') for tag in metadata['hashtags'])
        ]
        
        return all(checks)
