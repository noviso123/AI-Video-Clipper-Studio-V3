import os
from pathlib import Path
from agno.knowledge.filesystem import FileSystemKnowledge

# Diretório base
BASE_DIR = Path(__file__).parent.parent.parent

def get_viral_knowledge_base():
    """Retorna a Knowledge Base de diretrizes virais baseada no sistema de arquivos local"""
    knowledge_dir = BASE_DIR / "src" / "agents" / "knowledge"
    
    # Agno 2.x FileSystemKnowledge fornece ferramentas automáticas para o agente (grep, list, get)
    # Isso é ideal para documentos de texto locais sem precisar de banco vetorial externo
    knowledge_base = FileSystemKnowledge(
        base_dir=str(knowledge_dir)
    )
    
    return knowledge_base
    
    # Carregar documentos se o banco estiver vazio
    try:
        knowledge_base.load(recreate=False)
    except Exception as e:
        print(f"⚠️ Erro ao carregar Knowledge Base: {e}")
        
    return knowledge_base
