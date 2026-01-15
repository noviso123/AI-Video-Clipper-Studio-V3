"""
Agente de Metadados e Viralidade (Fase 20)
Gera títulos, descrições e hashtags otimizados para alta conversão (CTR).
"""
import logging
import json
import os
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

class MetadataAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            logger.info("📈 Metadata Agent: Inicializado")
        else:
            self.client = None
            logger.warning("📈 Metadata Agent: OFFLINE (Sem API Key)")

    def generate_metadata(self, transcript: str, vibe: str) -> dict:
        """
        Gera metadados virais baseados na transcrição e vibe.
        """
        if not self.client:
            logger.warning("   ⚠️ MetadataAgent offline - retornando None")
            return None

        try:
            logger.info("   📈 Gerando Títulos e Descrições Virais...")

            prompt = f"""
            You are a world-class YouTube & TikTok Strategist (MrBeast style).

            Analyze the following video transcript segment and generate high-CTR metadata.

            CONTEXT:
            Video Vibe: {vibe}
            Transcript: "{transcript[:4000]}..." (truncated)

            TASK:
            1. Generate 5 Viral Titles (mix of Clickbait, Curiosity, and Benefit-driven).
            2. Generate a Description optimized for SEO (first 2 lines are hook).
            3. Generate 15 relevant Hashtags.
            4. Predict a "Virality Score" (0-100) based on the hook strength.

            OUTPUT JSON FORMAT:
            {{
                "viral_titles": [
                    "Title 1 (Curiosity)",
                    "Title 2 (Shocking)",
                    "Title 3 (Benefit)"
                ],
                "description": "Full description text...",
                "hashtags": ["#tag1", "#tag2"],
                "virality_score": 85,
                "reasoning": "Why this will go viral..."
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Viral Content Expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            logger.info(f"   🔥 Score de Viralidade: {result.get('virality_score')}/100")

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao gerar metadados: {e}")
            return None

    def save_metadata(self, metadata: dict, output_path: Path):
        """Salva metadados em arquivo de texto/JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Criar versão TXT legível para o usuário copiar
            txt_path = output_path.with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== TÍTULOS VIRAIS ===\n")
                for t in metadata.get('viral_titles', []):
                    f.write(f"- {t}\n")

                f.write("\n=== DESCRIÇÃO ===\n")
                f.write(metadata.get('description', ''))

                f.write("\n\n=== HASHTAGS ===\n")
                f.write(" ".join(metadata.get('hashtags', [])))

        except Exception as e:
            logger.error(f"❌ Erro ao salvar metadados: {e}")
