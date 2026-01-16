"""
Multi-Agent System for Viral Content Generation
Uses CrewAI to orchestrate autonomous research and copywriting.
"""
import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Configuration
config = Config()

def get_llm(force_local=False):
    """Retorna o LLM usando abordagem Híbrida (Prioridade: OpenAI -> Local)"""
    from ..core.hybrid_ai import HybridAI
    hybrid = HybridAI()

    # Se temos OpenAI e não estamos forçando local
    if hybrid.has_openai and not force_local:
        return ChatOpenAI(model="gpt-4o", temperature=0.7)

    # Fallback/Padrão: Ollama (Local)
    return ChatOllama(model="llama3", base_url="http://127.0.0.1:11434")

class ContentAgents:
    """Definição de Agentes Especialistas em Viralização"""

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"🤖 Agentes CrewAI inicializados com: {type(self.llm).__name__}")

    def researcher(self):
        return Agent(
            role='Pesquisador de Tendências e Fatos',
            goal='Extrair os pontos mais impactantes e factuais de um conteúdo bruto',
            backstory='Você é um mestre em encontrar a "agulha no palheiro". Sua missão é ler documentos ou sites e extrair dados, curiosidades e ganchos que prendam a atenção.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def scriptwriter(self):
        return Agent(
            role='Copywriter Viral de Reels e TikTok',
            goal='Escrever roteiros com Retenção Altíssima (Hook, Body, CTA) em Português do Brasil',
            backstory='Você é um estrategista de conteúdo com 10 anos de experiência em vídeos curtos. Você sabe que os primeiros 3 segundos são tudo. Seus roteiros são rápidos, magnéticos e emocionais.',
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def director(self):
        return Agent(
            role='Diretor de Arte e Edição',
            goal='Definir o ritmo visual e as instruções de edição para o roteiro',
            backstory='Você entende de psicologia visual. Você decide onde entram legendas dinâmicas, b-rolls e cortes rápidos para manter a energia do vídeo no topo.',
            llm=self.llm,
            verbose=True
        )

    def producer(self):
        return Agent(
            role='Produtor Executivo',
            goal='Garantir a qualidade final, coesão e viabilidade técnica do projeto',
            backstory='Você é o responsável final pelo controle de qualidade. Você revisa se o roteiro está em PT-BR, se as vozes estão marcadas corretamente e se as instruções visuais fazem sentido.',
            llm=self.llm,
            verbose=True
        )

class ContentTasks:
    """Definição de Tarefas para a Crew"""

    def research_task(self, agent, context):
        return Task(
            description=f"Analise o seguinte conteúdo e extraia os 5 pontos mais 'compartilháveis' e interessantes: {context}",
            expected_output="Uma lista estruturada com ganchos (hooks) e fatos principais.",
            agent=agent
        )

    def script_task(self, agent):
        return Task(
            description=(
                "Com base na pesquisa, escreva um roteiro de vídeo de 60 segundos. "
                "REQUISITO CRÍTICO: O roteiro deve ser inteiramente em PORTUGUÊS DO BRASIL, "
                "mesmo que o conteúdo original seja em inglês ou outro idioma. "
                "Use marcadores de voz para diferentes falantes se houver diálogos ou mudança de tom. "
                "Vozes disponíveis: [VOICE: michael] (Masculino), [VOICE: bella] (Feminino), [VOICE: sarah] (Feminino Suave). "
                "Formato: [VOICE: michael] Texto aqui... [VOICE: bella] Resposta aqui..."
            ),
            expected_output="Roteiro completo em PT-BR com marcadores de voz [VOICE: nome] e seções [GANCHO], [CONTEÚDO], [ENCERRAMENTO].",
            agent=agent
        )

    def visual_task(self, agent):
        return Task(
            description=(
                "Adicione instruções de edição visual ao roteiro. "
                "Garanta que as instruções não interfiram nos marcadores [VOICE: ...]. "
                "Instruções: [Corte Rápido], [B-Roll: termo], [Legenda: texto]."
            ),
            expected_output="O roteiro com marcações visuais inteligentes adicionadas.",
            agent=agent
        )

    def review_task(self, agent):
        return Task(
            description=(
                "REVISÃO FINAL CRÍTICA: Verifique se o roteiro está 100% em Português do Brasil. "
                "Certifique-se de que todos os [VOICE: ...] e [B-Roll: ...] estão formatados corretamente. "
                "Melhore a fluidez do texto para que soe natural ao ser falado."
            ),
            expected_output="O roteiro final, revisado, polido e pronto para produção imediata.",
            agent=agent
        )
