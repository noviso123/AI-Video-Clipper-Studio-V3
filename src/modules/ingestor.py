"""
Módulo de Ingestão de Conteúdo (Cérebro)
Usa Microsoft MarkItDown para converter arquivos (PDF, DOCX, XLSX, etc) em Markdown.
"""
import os
from pathlib import Path
from markitdown import MarkItDown
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class ContentIngestor:
    """Consome arquivos locais e transforma em texto estruturado (Markdown)"""

    def __init__(self):
        # MarkItDown pode usar LLMs para decifrar imagens se configurado,
        # mas aqui usaremos a versão puramente local para rapidez.
        self.md = MarkItDown()
        self.temp_dir = os.path.join(os.getcwd(), 'temp', 'ingestion')
        os.makedirs(self.temp_dir, exist_ok=True)

    def convert_file(self, file_path: str) -> str:
        """Converte qualquer arquivo suportado para Markdown"""
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return ""

        try:
            logger.info(f"📄 Convertendo arquivo: {os.path.basename(file_path)}")
            result = self.md.convert(file_path)
            markdown_content = result.text_content

            logger.info(f"✅ Conversão concluída. Tamanho: {len(markdown_content)} caracteres.")
            return markdown_content
        except Exception as e:
            logger.error(f"❌ Erro ao converter arquivo: {e}")
            return f"Erro na ingestão: {str(e)}"

    def save_markdown(self, content: str, original_filename: str) -> str:
        """Salva o conteúdo convertido para persistência"""
        name = Path(original_filename).stem
        output_path = os.path.join(self.temp_dir, f"{name}.md")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

# Singleton
ingestor = None
def get_ingestor() -> ContentIngestor:
    global ingestor
    if ingestor is None:
        ingestor = ContentIngestor()
    return ingestor
