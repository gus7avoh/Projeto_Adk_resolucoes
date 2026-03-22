# Imports corretos para Google ADK
#from google.adk.agents import LlmAgent
from google.adk.agents import Agent
#$from google.adk.models.lite_llm import LiteLlm
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, List
import logging
import json
import time # Importar para usar time.sleep

from . import ferramentas

load_dotenv()

BASE_PATH = os.getenv("DOCUMENTS_PATH", r"D:\cod\Arsae\Adk\Projeto_Adk_resolucoes\Adm_agentes\documentos")
# Criar diretório de logs se não existir
Path("logs").mkdir(exist_ok=True)


# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("FluxoAgentes")

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
    
def executar_analise_documentos():
    """
    Orquestra a execução sequencial dos agentes com logs, validação e contexto.
    """
    contexto = ContextoAnalise()
    
    # Etapa 1: Listar documentos
    try:
        documentos = ferramentas.list_pdfs()
        contexto.documentos = documentos
        contexto.adicionar_log("Sistema", "list_pdfs", f"{len(documentos)} documentos encontrados: {documentos}")
        
        if not documentos:
            contexto.adicionar_log("Sistema", "erro", "Nenhum PDF encontrado para análise")
            return None
    except Exception as e:
        contexto.adicionar_log("Sistema", "erro", f"Falha ao listar PDFs: {str(e)}")
        return None

    # Etapa 2: Processar todos os PDFs uma única vez
    try:
        ferramentas.obter_dados_processados()
        contexto.adicionar_log("Sistema", "processar_pdf", "Todos os PDFs foram processados com sucesso")
    except Exception as e:
        contexto.adicionar_log("Sistema", "erro", f"Falha ao processar PDFs: {str(e)}")
        return None

    # Etapa 3: Executar agentes em sequência com retentativa
    agentes = [
        ("Contradicao", Contradicao),
        ("Ambiguidade", Ambiguidade),
    ]

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

    for nome, agente in agentes:
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                contexto.adicionar_log(nome, "iniciando", f"Agente ativado (Tentativa {retries + 1}/{MAX_RETRIES + 1})")
                
                # Executa o agente
                resultado = agente.adk_agent.run_async(contexto.documentos)

                # Salva o resultado
                contexto.salvar_resultado(nome, resultado)
                
                # Verifica se houve erro no formato (opcional)
                if hasattr(resultado, "status_analise") and resultado.status_analise == "Necessita Correção":
                    contexto.adicionar_log(nome, "alerta", "Análise precisa de correção")
                break  # Sai do loop de retentativa se o agente for bem-sucedido

            except Exception as e:
                error_message = str(e)
                if "INTERNAL" in error_message and "500" in error_message:
                    contexto.adicionar_log(nome, "erro", f"Erro INTERNO (500) na execução: {error_message}. Tentando novamente em {RETRY_DELAY_SECONDS} segundos...")
                    retries += 1
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    contexto.adicionar_log(nome, "erro", f"Falha na execução: {error_message}")
                    break  # Interrompe se for um erro diferente de INTERNAL ou se exceder as retentativas
        else:
            contexto.adicionar_log(nome, "erro", f"Agente {nome} falhou após {MAX_RETRIES + 1} tentativas devido a erro INTERNO (500).")
            break # Interrompe o fluxo principal se o agente falhar após todas as retentativas

    # Etapa 4: Salvar log completo e resultados finais em arquivo JSON
    try:
        # Salvar logs
        with open(r"logs/execucao_analise.json", "w", encoding="utf-8") as f:
            json.dump(contexto.logs, f, ensure_ascii=False, indent=2)
        logger.info("Logs salvos em logs/execucao_analise.json")

        # Salvar resultados finais
        with open(r"resultados_analise_final.json", "w", encoding="utf-8") as f:
            json.dump(contexto.resultados, f, ensure_ascii=False, indent=2)
        logger.info("Resultados finais salvos em resultados_analise_final.json")

    except Exception as e:
        logger.warning(f"Não foi possível salvar logs ou resultados finais: {e}")

    # Etapa 5: Retornar contexto final (para auditoria ou UI)
    return contexto

# Agent para análise de contradições
Contradicao = Agent(
    model="gemini-2.5-flash",
    name="Contradicao",
    description="Agent responsible for analyzing contradictions in resolutions.",
    instruction=f"""
    You are a specialist in finding contradictions in documents.
    
    Functions available for you to use:
    - ferramentas.list_pdfs() -> list - List all available PDF files
    - ferramentas.obter_dados_processados() -> dict - Get processed data for analysis
  
    INSTRUCTIONS:

    calm down, you don\\'t need to rush, you have all the time in the world to analyze the documents.

    1. Use obter_dados_processados() to get all document content processed
    2. Analyze the extracted text looking for contradictions between resolutions
        ANALYSIS METHODOLOGY:
        1. Group texts by similar themes/subjects
        2. Compare statements within each group
        3. Identify conflicting statements
        4. Check if the context is really comparable
        5. Document contradictions found
    
    3. Contradictions can be within one document or across multiple documents
    4. Check all resolutions between all processed documents
    
    5. What is a contradiction?
        In the context of document analysis by AI models, a contradiction occurs when two or more documents (or resolutions) make directly opposing claims about the same subject or topic within a comparable context.
        Key considerations for contradiction detection:
        Contextual alignment is essential: The AI must evaluate the semantic context, not just perform keyword matching.
        Topic consistency: Both statements must refer to the same topic or entity. Differences across unrelated subjects do not constitute a contradiction.
        Temporal and conditional scope: Dates, conditions, and specific circumstances must also align. Contradictions only exist when both statements apply to the same time frame and scenario.
        Example scenario for AI contradiction detection:
        Document A: \\"The water tariff will increase in July 2025.\\"
        Document B: \\"The water tariff will decrease in July 2025.\\"
        → This represents a clear contradiction: same topic, same time frame, opposite claims.
        Non-contradiction example (different topics):
        Document A: \\"The water tariff will increase in July 2025.\\"
        Document B: \\"Wastewater treatment charges will decrease in July 2025.\\"
        → No contradiction: different topics.

    6. Cite the specific excerpts from the documents where contradictions occur
    7. Focus only on content contradictions, not grammar errors or formatting issues
    8. If no contradictions are found, clearly state that no contradictions were detected
    9. Be objective and clear in your responses
    10. When activated, perform your analysis without waiting for additional instructions
    11. Save your analysis results in the output for validation by Adm_agentes
    12. When you finish your job, transfer to OrtografiaGramatica 

    RESPONSE FORMAT (JSON):
    {{
      \\"contradicao\\": true|false,
      \\"documentos_analisados\\": [\\"arquivo1.pdf\\", \\"arquivo2.pdf\\", ...],
      \\"numero_contradicoes\\": 0|1|2|...,
      \\"contradicoes\\": [
        {{
          \\"documento_1\\": \\"nome_do_documento_1.pdf\\",
          \\"localizacao_1\\": \\"Seção 3, Parágrafo 2\\",
          \\"trecho_1\\": \\"O valor será reduzido a partir de janeiro de 2025.\\",
          \\"documento_2\\": \\"nome_do_documento_2.pdf\\",
          \\"localizacao_2\\": \\"Cláusula 5, Item B\\",
          \\"trecho_2\\": \\"O valor será aumentado a partir de janeiro de 2025.\\",
          \\"explicacao\\": \\"Ambos os documentos tratam do mesmo valor e período, mas indicam direções opostas (redução vs aumento), caracterizando uma contradição direta.\\"
        }}
      ],
      \\"observacao\\": \\"Nenhuma contradição foi encontrada entre os documentos analisados.\\" (apenas se contradicao == false)
    }}

    IMPORTANT:
    - Respond ONLY in valid JSON format, strictly adhering to the structure above.
    - DO NOT include any additional text, explanations, markdown, or formatting outside the JSON.
    - When contradicao is false, include \\\'observacao\\\' explaining no contradictions were found.
    - Always call obter_dados_processados() first to get the processed data
    - Thoroughly analyze all available text content
    - Save your complete analysis for validation by Adm_agentes
    - After generating the JSON, transfer to Ambiguidade
    """,
    tools=[ferramentas.list_pdfs, ferramentas.obter_dados_processados],
    output_key="analise_contradicoes"
)

Ambiguidade = Agent(
    model="gemini-2.5-flash",
    name="Ambiguidade",
    description="Agent responsible for identifying ambiguous phrases in resolutions.",
    instruction=f"""
    You are a specialist in identifying ambiguities in technical and legal documents.

    Functions available for you to use:
    - ferramentas.list_pdfs() -> list - List all available PDF files
    - ferramentas.processar_pdf() -> dict - Process all PDF files to extract content in a dictionary format
    - ferramentas.obter_dados_processados() -> dict - Get processed data for analysis

    INSTRUCTIONS:

    calm down, you don\\'t need to rush, you have all the time in the world to analyze the documents.

    1. Use obter_dados_processados() to get all document content processed
    2. Analyze the extracted text looking for ambiguous expressions that may cause interpretation issues

    🔍 ANALYSIS METHODOLOGY:
        1. Read the text carefully, sentence by sentence
        2. Identify phrases or expressions that may have **more than one possible meaning**
        3. Evaluate whether the ambiguity arises from:
           - Lexical ambiguity (word with multiple meanings)
           - Syntactic ambiguity (unclear sentence structure)
           - Referential ambiguity (unclear pronoun or subject reference)
           - Scope ambiguity (unclear which part of the sentence an element applies to)
           - Implicit assumptions or missing information
        4. Suggest how the sentence could be rewritten to eliminate ambiguity
        5. Be precise and objective

    📘 WHAT IS AN AMBIGUITY?

    Ambiguity occurs when a sentence or phrase allows **two or more possible interpretations**, causing uncertainty or confusion. It is problematic in legal, technical, and regulatory documents because it can lead to **misinterpretations, legal loopholes, or conflicting understandings**.

    🔁 Types of ambiguity:
    - **Lexical ambiguity:** \\"banco\\" (could be a financial institution or a bench)
    - **Syntactic ambiguity:** \\"O gerente demitiu o funcionário com problemas\\" → Who has the problems? The manager or the employee?
    - **Referential ambiguity:** \\"Foi decidido que ele será o responsável.\\" → Who is \\"ele\\"?
    - **Scope ambiguity:** \\"Todos os usuários não precisam preencher o formulário.\\" → Does it mean no user or only some?

    ✅ Non-ambiguous example:
    \\"O gerente demitiu o funcionário que causava problemas técnicos.\\"  
    → Specific and clear.

    🚫 Ambiguous example:
    \\"O engenheiro relatou ao chefe que ele estava com dificuldades.\\"  
    → \\"Ele\\" refers to who? The engineer or the boss?\\"

    6. Focus only on **ambiguity of meaning**, not grammar or contradiction
    7. If no ambiguity is found, clearly state that no ambiguous expressions were detected
    8. Be objective and clear in your explanations
    9. When finished, transfer your results to Adm_agentes for validation

    RESPONSE FORMAT (JSON):
    {{
      \\"ambiguidade\\": true|false,
      \\"documentos_analisados\\": [\\"arquivo1.pdf\\", \\"arquivo2.pdf\\"],
      \\"numero_ambiguidades\\": 0|1|2|...,
      \\"ambiguidades\\": [
        {{
          \\"documento\\": \\"resolucao_2025.pdf\\",
          \\"localizacao\\": \\"Artigo 5, Parágrafo 2\\",
          \\"trecho\\": \\"O responsável deverá entregar o relatório ao diretor com urgência.\\",
          \\"tipo\\": \\"Referencial\\",
          \\"explicacao\\": \\"Não está claro se \\\\'urgência\\\\' se aplica ao responsável ou ao diretor.\\",
          \\"sugestao_reescrita\\": \\"O responsável deverá entregar com urgência o relatório ao diretor.\\"
        }}
      ],
      \\"observacao\\": \\"Nenhuma ambiguidade foi identificada nos documentos analisados.\\" (apenas se ambiguidade == false)
    }}

    IMPORTANT:
    - Respond ONLY in valid JSON format, strictly adhering to the structure above.
    - DO NOT include any additional text, mark
    (Content truncated due to size limit. Use line ranges to read in chunks)""",
    tools=[ferramentas.list_pdfs, ferramentas.obter_dados_processados],
    output_key="analise_ambiguidade"
)

Adm_agentes = Agent(
    model="gemini-2.5-flash",
    name="Adm_agentes",
    description="Agent responsible for managing and validating the work of other agents.",
    instruction= """
    You are responsible for coordinating the analysis process and validating results.

    Functions available for you to use:
    - ferramentas.list_pdfs() -> list - List all available PDF files
    - ferramentas.processar_pdf() -> dict - Process all PDF files to extract content
    - ferramentas.obter_dados_processados() -> dict - Get processed data for analysis

    INSTRUCTIONS:
    1. When the analysis starts, coordinate with the Contradicao agent to perform document analysis
    2. Access the analysis results through the \\\'analise_contradicoes\\\' output
    3. Validate if the contradictions found are real and meaningful
    4. Check if the agent properly processed all available documents
    5. Verify that the analysis format follows the specified structure
    6. Point out any errors or inconsistencies if they exist
    7. Provide a comprehensive summary of the entire analysis process
    8. Save the final validation result

    📌 Additional responsibilities for ambiguity detection:

    16. Coordinate with the Ambiguidade agent to analyze ambiguous language
    17. Access the analysis results through the \\\'analise_ambiguidade\\\' output
    18. Validate whether each ambiguity identified is truly open to multiple interpretations
    19. Check if the ambiguity type (lexical, syntactic, referential, scope) was correctly classified
    20. Verify that the rewriting suggestions resolve the ambiguity clearly
    21. Ensure that the agent followed the required response format strictly
    22. If no ambiguities were found, confirm that this conclusion is supported by the analysis
    23. If any ambiguity is misclassified or unjustified, report and suggest corrections

    RESPONSE FORMAT (JSON):
    {
      \\"status_analise\\": \\"Aprovada\\" | \\"Necessita Correção\\",
      \\"resumo_processo\\": {
        \\"arquivos_pdf_encontrados\\": 3,
        \\"arquivos_processados_com_sucesso\\": 3,
        \\"contradicoes_validadas\\": 2,
        \\"ambiguidades_validadas\\": 3
      },
      \\"detalhes_validacao\\": \\"Todos os agentes processaram os documentos corretamente. A análise de contradições foi consistente com os trechos extraídos.
        {
          \\"erro\\": \\"Sugestão incorreta para \\\\'pára\\\\' → \\\\'para\\\\' em contexto verbal\\",
          \\"sugestao\\": \\"Verificar se \\\\'pára\\\\' está no sentido de verbo \\\\'parar\\\\'\\", o que mantém acento\\"
        }
      ],
      \\"conclusao\\": \\"A análise geral foi satisfatória, com alto nível de acurácia. Um ajuste é necessário no agente de ortografia para casos de verbos acentuados. Após correção, o conjunto de documentos pode ser considerado validado.\\"
    }

    IMPORTANT:
    - Respond ONLY in valid JSON format, strictly adhering to the structure above.
    - DO NOT include any additional text, markdown, or explanations outside the JSON.
    - If no problems were found, keep \\\'problemas_identificados\\\' as an empty list [].
    - Always ensure the final output is a single, valid JSON object.
    - After validation, finalize the process and confirm completion.
    """,
    sub_agents=[Contradicao, Ambiguidade],
    tools=[ferramentas.list_pdfs, ferramentas.obter_dados_processados],
    output_key="validacao_final"
)

# Variável que o ADK procura para o agente raiz
root_agent = Adm_agentes

if __name__ == "__main__":
    contexto_final = executar_analise_documentos()
    if contexto_final:
         print("\n✅ Análise concluída. Último resultado:")
         print(json.dumps(contexto_final.resultados.get("Adm_agentes", {}), ensure_ascii=False, indent=2))
    else:
         print("\n❌ Falha na execução do fluxo de análise.")


