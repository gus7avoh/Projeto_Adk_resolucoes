import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import json

# Importa as classes dos agentes
from agentes.contradicao import AgenteContradicao
from agentes.ortografia import AgenteOrtografia
from agentes.ambiguidade import AgenteAmbiguidade
from agentes.adm import AgenteAdm

# Importa apenas as ferramentas que o orquestrador realmente usa
from tools.ferramentas import list_pdfs
from agentes.base import ContextoAnalise

load_dotenv()
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("FluxoAgentes")

def executar_analise_documentos():
    """
    Orquestra a execução sequencial dos agentes. A lógica de processamento
    de documentos agora é delegada para a ferramenta 'obter_dados_processados'
    que será chamada pelo primeiro agente.
    """
    contexto = ContextoAnalise()
    
    # Etapa 1: Apenas verificar se há documentos.
    try:
        documentos = list_pdfs()
        if not documentos:
            raise FileNotFoundError("Nenhum PDF encontrado para análise.")
        
        contexto.documentos = documentos
        contexto.adicionar_log("Sistema", "Verificação Inicial", f"{len(documentos)} documentos encontrados: {documentos}")
        
    except Exception as e:
        contexto.adicionar_log("Sistema", "Erro Fatal na Preparação", f"Falha ao verificar documentos: {e}")
        # Salvar logs e sair se não houver documentos
        salvar_arquivos_finais(contexto)
        return contexto

    # Etapa 2: Instanciar e executar agentes em sequência.
    # O primeiro agente (Contradicao) será responsável por invocar 'obter_dados_processados'.
    agentes_para_executar = [
        AgenteContradicao(),
        AgenteOrtografia(),
        AgenteAmbiguidade(),
        AgenteAdm()
    ]

    for agente_obj in agentes_para_executar:
        try:
            # A lógica de retentativa está dentro do método executar do agente.
            agente_obj.executar(contexto)
        except Exception as e:
            contexto.adicionar_log(agente_obj.nome, "Erro Fatal", f"Agente falhou após todas as tentativas: {e}")
            break # Interrompe o fluxo principal
    
    # Etapa 3: Salvar logs e resultados finais.
    salvar_arquivos_finais(contexto)

    return contexto

def salvar_arquivos_finais(contexto: ContextoAnalise):
    """Função auxiliar para salvar os logs e resultados."""
    try:
        with open("logs/execucao_analise.json", "w", encoding="utf-8") as f:
            json.dump(contexto.logs, f, ensure_ascii=False, indent=2)
        with open("resultados_analise_final.json", "w", encoding="utf-8") as f:
            json.dump(contexto.resultados, f, ensure_ascii=False, indent=2)
        logger.info("Logs e resultados finais foram salvos.")
    except Exception as e:
        logger.warning(f"Não foi possível salvar logs ou resultados: {e}")

# Ponto de entrada
if __name__ == "__main__":
    contexto_final = executar_analise_documentos()
    if "Erro Fatal" in str(contexto_final.logs[-1]):
         print("\n❌ Falha na execução do fluxo de análise.")
    else:
         print("\n✅ Análise concluída com sucesso.")

# Definição do root_agent para compatibilidade com ADK
# O AgenteAdm é o último e consolida tudo, sendo o candidato natural.
agente_adm_final = AgenteAdm()
root_agent = agente_adm_final.adk_agent
