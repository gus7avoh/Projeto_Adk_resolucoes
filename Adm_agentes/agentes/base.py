from abc import ABC, abstractmethod
from google.adk.agents import Agent # ou LlmAgent, se preferir ser explícito
import time
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("FluxoAgentes")

class AgenteBase(ABC):
    """
    Superclasse abstrata para todos os agentes de análise de documentos.
    """
    def __init__(self, nome: str, descricao: str, output_key: str, tools: list, sub_agents: list = None):
        self.nome = nome
        # A criação do agente permanece a mesma
        self.adk_agent = self._criar_agente_adk(nome, descricao, output_key, tools, sub_agents)

    @abstractmethod
    def _get_instruction(self) -> str:
        """Método que cada subclasse implementa para fornecer seu prompt."""
        pass

    def _criar_agente_adk(self, nome, descricao, output_key, tools, sub_agents) -> Agent:
        """Cria a instância do Agent do Google ADK."""
        # Usando LlmAgent explicitamente para maior clareza, já que é o que o erro indica
        from google.adk.agents import LlmAgent 
        
        agent_params = {
            "model": "gemini-2.5-flash",
            "name": nome,
            "description": descricao,
            "instruction": self._get_instruction(),
            "tools": tools,
        }
        # A classe Agent genérica é usada para orquestração com sub_agents
        # A LlmAgent é para execução direta de prompt.
        if sub_agents:
            from google.adk.agents import Agent
            agent_params["sub_agents"] = sub_agents
            agent_params["output_key"] = output_key
            return Agent(**agent_params)
        else:
            # Para agentes que executam um prompt, usamos LlmAgent
            return LlmAgent(**agent_params)


    def executar(self, contexto, max_retries=3, delay=5):
        """
        Executa o agente com lógica de retentativas, usando a sintaxe de chamada correta.
        """
        retries = 0
        while retries < max_retries:
            try:
                contexto.adicionar_log(self.nome, "iniciando", f"Tentativa {retries + 1}/{max_retries}")
                
                # ===============================================================
                # AQUI ESTÁ A CORREÇÃO CRUCIAL
                # Trocamos .run() por () para invocar o agente
                resultado = self.adk_agent()
                # ===============================================================
                
                contexto.salvar_resultado(self.nome, resultado)
                return resultado # Sucesso, retorna o resultado

            except Exception as e:
                error_message = str(e)
                contexto.adicionar_log(self.nome, "erro", f"Falha na execução: {error_message}")
                
                # A lógica de retentativa continua a mesma
                if "INTERNAL" in error_message and "500" in error_message and retries < max_retries - 1:
                    contexto.adicionar_log(self.nome, "aviso", f"Erro interno (500). Tentando novamente em {delay}s...")
                    time.sleep(delay)
                    retries += 1
                else:
                    # Se não for um erro recuperável, lança a exceção para o orquestrador
                    raise e
        
        # Se o loop terminar, significa que todas as tentativas falharam
        raise Exception(f"Agente {self.nome} falhou após {max_retries} tentativas.")




class ContextoAnalise:
    """Armazena estado compartilhado entre agentes"""
    def __init__(self):
        self.documentos: List[str] = []
        self.resultados: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.status = "iniciado"
    
    def adicionar_log(self, agente: str, acao: str, detalhes: str = ""):
        log = {
            "timestamp": datetime.now().isoformat(),
            "agente": agente,
            "acao": acao,
            "detalhes": detalhes
        }
        self.logs.append(log)
        logger.info(f"[{agente}] {acao} → {detalhes}")
    
    def salvar_resultado(self, agente: str, resultado: Any):
        self.resultados[agente] = resultado
        self.adicionar_log(agente, "análise concluída", f"Resultados armazenados")
    
    def obter_resultado(self, agente: str):
        return self.resultados.get(agente)