"""
Módulo de Orquestração de IA Híbrida (Local-First)
Gerencia a alternância inteligente entre análise Local, Gemini e OpenAI.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

class HybridAI:
    """
    Gerenciador Híbrido de IA:
    1. Analisa Localmente (Keyword Matching + Audio Analysis) - PRIORIDADE MÁXIMA
    2. (Gemini e OpenAI removidos para suporte 100% offline)
    4. Mescla ou seleciona o melhor resultado
    """

    def __init__(self):
        # Modificando para garantir Offline
        self.gemini_key = None
        self.openai_key = None
        self.has_gemini = False
        self.has_openai = False
        
        # Clientes (Removidos)
        self._gemini_configured = False
        self._openai_client = None
        
        logger.info("🧠 HybridAI: Modo 100% OFFLINE Ativado")

    def call(
        self,
        local_func: Callable,
        gemini_func: Optional[Callable] = None,
        openai_func: Optional[Callable] = None,
        task_name: str = "AI Task"
    ) -> Any:
        """
        Executa a lógica híbrida.
        Sempre roda o local, e tenta as nuvens se disponíveis.
        """
        logger.info(f"🤖 Iniciando Processamento Híbrido: {task_name}")

        # 1. SEMPRE executar Local primeiro (Motor de Base)
        results = {
            "local": None,
            "gemini": None,
            "openai": None
        }

        try:
            results["local"] = local_func()
            logger.info(f"   🏠 [LOCAL] Processado com sucesso")
        except Exception as e:
            logger.error(f"   ❌ [LOCAL] Falha crítica: {e}")

        # 2. Tentar Gemini se disponível e função fornecida
        if self.has_gemini and gemini_func:
            try:
                results["gemini"] = gemini_func()
                logger.info(f"   ♊ [GEMINI] Processado com sucesso")
            except Exception as e:
                logger.warning(f"   ⚠️ [GEMINI] Falha: {e}")

        # 3. Tentar OpenAI se disponível e função fornecida
        if self.has_openai and openai_func:
            try:
                results["openai"] = openai_func()
                logger.info(f"   🌌 [OPENAI] Processado com sucesso")
            except Exception as e:
                logger.warning(f"   ⚠️ [OPENAI] Falha: {e}")

        # 4. Decisão Inteligente (Mesclagem ou Seleção)
        return self._smart_merge(results, task_name)

    def _smart_merge(self, results: Dict[str, Any], task_name: str) -> Any:
        """
        Decide qual resultado usar ou como mesclar.
        Por padrão: Prioriza Nuvem se disponível (pois são mais 'inteligentes' para texto),
        mas usa Local como fundação inabalável.
        """
        local = results.get("local")
        gemini = results.get("gemini")
        openai = results.get("openai")

        # Se for uma lista de momentos (Curator/Orchestrator highlights)
        if isinstance(local, list):
            # Tenta unificar e remover duplicatas por tempo (aproximado)
            # Para simplificar: Pega o da nuvem se existir, senão local
            if gemini and len(gemini) > 0:
                logger.info(f"   💎 Usando inteligência GEMINI para {task_name}")
                return gemini
            if openai and len(openai) > 0:
                logger.info(f"   💎 Usando inteligência OPENAI para {task_name}")
                return openai
            return local

        # Se for um dicionário (Plano de Edição)
        if isinstance(local, dict):
            # Prioridade Gemini > OpenAI > Local
            if gemini: return gemini
            if openai: return openai
            return local

        # Fallback final
        # Forçar retorno local
        return local
