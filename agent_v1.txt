# Imports corretos para Google ADK
from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os
from pathlib import Path
from dotenv import load_dotenv
from pdf2docx import Converter
from docx import Document

load_dotenv()

OpenAi_model = LiteLlm(
    model="gpt-4o", 
    api_key=os.getenv('OPENAI_API_KEY')
)

# Configuração dos caminhos - usando variáveis de ambiente para flexibilidade
BASE_PATH = os.getenv('DOCUMENTS_PATH', r"D:\cod\Arsae\Adk\Projeto_Adk_resolucoes\Adm_agentes\documentos")

# Verificar e criar diretórios se necessário
def ensure_directories():
    """Garante que os diretórios necessários existam."""
    try:
        os.makedirs(BASE_PATH, exist_ok=True)
        return True
    except Exception as e:
        print(f"Erro ao criar diretórios: {str(e)}")
        return False

def list_pdfs() -> list:
    """Lista todos os arquivos PDF disponíveis."""
    try:
        if not os.path.exists(BASE_PATH):
            print(f"Diretório {BASE_PATH} não existe.")
            return []
        
        pdfs = [f for f in os.listdir(BASE_PATH) if f.lower().endswith('.pdf')]
        return pdfs
    
    except Exception as e:
        print(f"Erro ao listar arquivos: {str(e)}")
        return []

def converter_pdf_para_docx(pdf_path: str, docx_path: str) -> bool:
    """
    Converte um arquivo PDF para DOCX.
    
    Args:
        pdf_path (str): Caminho completo para o arquivo PDF
        docx_path (str): Caminho completo para o arquivo DOCX de saída
    
    Returns:
        bool: True se a conversão foi bem-sucedida, False caso contrário
    """
    try:
        if not os.path.exists(pdf_path):
            print(f"Arquivo PDF não encontrado: {pdf_path}")
            return False
            
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        print(f"PDF convertido com sucesso: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"Erro ao converter PDF para DOCX ({os.path.basename(pdf_path)}): {str(e)}")
        return False

def analisar_texto_riscado(docx_path: str) -> dict:
    """
    Analisa o documento DOCX procurando por texto riscado.
    
    Args:
        docx_path (str): Caminho para o arquivo DOCX
    
    Returns:
        dict: Dicionário com textos riscados e normais
    """
    try:
        if not os.path.exists(docx_path):
            print(f"Arquivo DOCX não encontrado: {docx_path}")
            return {"textos_riscados": [], "textos_normais": [], "erro": "Arquivo não encontrado"}
        
        doc = Document(docx_path)
        textos_riscados = []
        textos_normais = []

        for paragraph in doc.paragraphs:
            texto = paragraph.text.strip()
            if not texto:
                continue

            tem_risco = False
            for run in paragraph.runs:
                if run.font.strike:
                    tem_risco = True
                    break

            if tem_risco:
                textos_riscados.append(texto)
                print(f"Texto riscado encontrado: {texto[:50]}...")
            else:
                textos_normais.append(texto)

        print(f"Análise completa - Textos riscados: {len(textos_riscados)}, Textos normais: {len(textos_normais)}")
        
        return {
            #"textos_riscados": textos_riscados,
            "textos_normais": textos_normais,
            "total_paragrafos": len(textos_riscados) + len(textos_normais)
        }

    except Exception as e:
        print(f"Erro ao analisar documento DOCX: {str(e)}")
        return {"textos_riscados": [], "textos_normais": [], "erro": str(e)}

def processar_pdf() -> dict:
    """
    Processa todos os PDFs convertendo para DOCX e analisando o texto riscado.
    
    Returns:
        dict: Dicionário com resultados do processamento de cada arquivo
    """
    # Garantir que os diretórios existam
    if not ensure_directories():
        return {"erro": "Não foi possível criar/acessar os diretórios necessários"}
    
    resultados = {}
    arquivos_pdf = list_pdfs()
    
    if not arquivos_pdf:
        return {"erro": "Nenhum arquivo PDF encontrado", "arquivos_processados": 0}
    
    print(f"Encontrados {len(arquivos_pdf)} arquivos PDF para processar")
    
    for arquivo_pdf in arquivos_pdf:
        print(f"\nProcessando: {arquivo_pdf}")
        
        # Construir caminhos completos
        pdf_path = os.path.join(BASE_PATH, arquivo_pdf)
        nome_base = os.path.splitext(arquivo_pdf)[0]
        docx_path = os.path.join(BASE_PATH, f"{nome_base}.docx")
        
        # Converter PDF para DOCX
        sucesso_conversao = converter_pdf_para_docx(pdf_path, docx_path)
        
        if sucesso_conversao:
            # Analisar texto riscado
            resultado_analise = analisar_texto_riscado(docx_path)
            resultados[arquivo_pdf] = {
                "convertido": True,
                "caminho_docx": docx_path,
                "analise": resultado_analise
            }
        else:
            resultados[arquivo_pdf] = {
                "convertido": False,
                "erro": "Falha na conversão",
                "analise": None
            }
    
    print(f"\nProcessamento concluído. {len(resultados)} arquivos processados.")
    return {
        "arquivos_processados": len(resultados),
        "resultados": resultados,
        "sucesso": True
    }

def obter_dados_processados() -> dict:
    """
    Obtém os dados processados para análise.
    Esta função pode ser expandida para incluir cache ou armazenamento persistente.
    """
    return processar_pdf()

# Agent para análise de contradições
Contradicao = Agent(
    model = "gemini-2.0-flash",
    name="Contradicao",
    description="Agent responsible for analyzing contradictions in resolutions.",
    instruction=f"""
    You are a specialist in finding contradictions in documents.
    
    Functions available for you to use:
    - list_pdfs() -> list - List all available PDF files
    - processar_pdf() -> dict - Process all PDF files to extract content in a dictionary format
    - obter_dados_processados() -> dict - Get processed data for analysis
  
    INSTRUCTIONS:

    calm down, you don't need to rush, you have all the time in the world to analyze the documents.

    1. Use obter_dados_processados() to get all document content processed
    2. Analyze the extracted text looking for contradictions between resolutions
    3. Contradictions can be within one document or across multiple documents
    4. Check all resolutions between all processed documents
    
    5. What is a contradiction?
        In the context of document analysis by AI models, a contradiction occurs when two or more documents (or resolutions) make directly opposing claims about the same subject or topic within a comparable context.
        Key considerations for contradiction detection:
        Contextual alignment is essential: The AI must evaluate the semantic context, not just perform keyword matching.
        Topic consistency: Both statements must refer to the same topic or entity. Differences across unrelated subjects do not constitute a contradiction.
        Temporal and conditional scope: Dates, conditions, and specific circumstances must also align. Contradictions only exist when both statements apply to the same time frame and scenario.
        Example scenario for AI contradiction detection:
        Document A: "The water tariff will increase in July 2025."
        Document B: "The water tariff will decrease in July 2025."
        → This represents a clear contradiction: same topic, same time frame, opposite claims.
        Non-contradiction example (different topics):
        Document A: "The water tariff will increase in July 2025."
        Document B: "Wastewater treatment charges will decrease in July 2025."
        → No contradiction: different topics.

    6. Cite the specific excerpts from the documents where contradictions occur
    7. Focus only on content contradictions, not grammar errors or formatting issues
    8. If no contradictions are found, clearly state that no contradictions were detected
    9. Be objective and clear in your responses
    10. When activated, perform your analysis without waiting for additional instructions
    11. Save your analysis results in the output for validation by Adm_agentes
    12. When you finish your job, transfer to Adm_agentes for validation

    RESPONSE FORMAT:
    ----------------------------------------------------------------------------------------------------------------
    ANÁLISE DE CONTRADIÇÕES:
    
    - Documentos analisados: [lista dos arquivos processados]
    - Número de contradições encontradas: [número]
    
    Para cada contradição encontrada, use o seguinte formato:
    
    Contradição [número]:
    
    📄 Documento: [nome do documento 1]
    📍 Localização: [parágrafo/seção específica]
    📝 Trecho: "[trecho exato do texto]"
    
    📄 Documento: [nome do documento 2]  
    📍 Localização: [parágrafo/seção específica]
    📝 Trecho: "[trecho exato do texto]"
    
    🔍 Explicação da Contradição:
    [Detalhes claros sobre como os trechos se contradizem]
    
    ----------------------------------------------------------------------------------------------------------------

    IMPORTANT:
    - When you finish your job, transfer to Adm_agentes for validation
    - Always call obter_dados_processados() first to get the processed data
    - Thoroughly analyze all available text content
    - Save your complete analysis for validation by Adm_agentes
    """,
    tools=[list_pdfs, processar_pdf, obter_dados_processados],
    output_key="analise_contradicoes"
)

# Agent administrador para validação
Adm_agentes = Agent(
    model = "gemini-2.0-flash", 
    name="Adm_agentes",
    description="Agent responsible for managing and validating the work of other agents.",
    instruction="""
    You are responsible for coordinating the analysis process and validating results.

    Functions available for you to use:
    - list_pdfs() -> list - List all available PDF files
    - processar_pdf() -> dict - Process all PDF files to extract content
    - obter_dados_processados() -> dict - Get processed data for analysis

    INSTRUCTIONS:
    1. When the analysis starts, coordinate with the Contradicao agent to perform document analysis
    2. Access the analysis results through the 'analise_contradicoes' output
    3. Validate if the contradictions found are real and meaningful
    4. Check if the agent properly processed all available documents
    5. Verify that the analysis format follows the specified structure
    6. Point out any errors or inconsistencies if they exist
    7. Provide a comprehensive summary of the entire analysis process
    8. Save the final validation result

    RESPONSE FORMAT:
    ----------------------------------------------------------------------------------------------------------------
    VALIDAÇÃO E RESUMO FINAL:
    
    ✅ Status da Análise: [Aprovada/Necessita Correção]
    📊 Resumo do Processo:
    - Arquivos PDF encontrados: [número]
    - Arquivos processados com sucesso: [número]
    - Contradições validadas: [número]
    
    📝 Detalhes da Validação:
    [Descrição detalhada da validação realizada]
    
    Se houver erros para correção:
    ❌ Problemas Identificados:
    - Agente: [nome]
    - Erro: [descrição do erro]
    - Sugestão: [como corrigir]
    
    📋 Conclusão:
    [Resumo final dos resultados e recomendações]
    ----------------------------------------------------------------------------------------------------------------

    IMPORTANT:
     1. When the analysis starts, coordinate with the Contradicao agent to perform document analysis
    """,
    sub_agents=[Contradicao],
    tools=[list_pdfs, processar_pdf, obter_dados_processados],
    output_key="validacao_final"
)

# Variável que o ADK procura para o agente raiz
root_agent = Adm_agentes
