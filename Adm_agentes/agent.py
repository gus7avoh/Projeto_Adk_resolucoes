# Imports corretos para Google ADK
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import os
import PyPDF2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OpenAi_model = LiteLlm(
    model = "gpt-4o", 
    api_key = os.getenv('OPENAI_API_KEY')
)

# Configuração dos caminhos
BASE_PATH = r"D:\cod\Arsae\Adk\teste_mult_agent\Adminstrador_resolucoes\documentos"

def read_pdf(filename: str) -> str:
    """Read PDF content and extract text."""
    document_path = os.path.join(BASE_PATH, filename)
    
    if not os.path.exists(document_path):
        return f"Arquivo {filename} não encontrado."
    
    try:    
        with open(document_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            texto_completo = ""
            
            for pagina in pdf_reader.pages:
                texto_completo += pagina.extract_text() + "\n"
            
        return texto_completo.strip()
    
    except Exception as e:
        return f"Erro ao ler PDF {filename}: {str(e)}"

def list_pdfs() -> list:
    """List all available PDF files."""
    try:
        if not os.path.exists(BASE_PATH):
            return []
        
        pdfs = [f for f in os.listdir(BASE_PATH) if f.lower().endswith('.pdf')]
        return pdfs
    
    except Exception as e:
        return [f"Erro ao listar arquivos: {str(e)}"]

def read_all_pdfs() -> dict:
    """Read all PDFs and return content dictionary."""
    resolucoes_disponiveis = list_pdfs()
    conteudos = {}
    
    for resolucao in resolucoes_disponiveis:
        try:
            conteudo = read_pdf(resolucao)
            conteudos[resolucao] = conteudo
        except Exception as e:
            conteudos[resolucao] = f"Erro ao ler: {str(e)}"
    
    return conteudos

# Funções com nomes em português como wrapper (para manter compatibilidade)
def Ler_PDF(nome_arquivo: str) -> str:
    """Wrapper para read_pdf mantendo compatibilidade."""
    return read_pdf(nome_arquivo)

def Listar_PDFs() -> list:
    """Wrapper para list_pdfs mantendo compatibilidade."""
    return list_pdfs()

def Ler_todos_PDFs() -> dict:
    """Wrapper para read_all_pdfs mantendo compatibilidade."""
    return read_all_pdfs()

Contradicao = LlmAgent(
    model=OpenAi_model,
    name="Contradicao",
    description="Agente responsável por verificar contradições em documentos PDF de resoluções.",
    instruction=f"""
    Você é um especialista em encontrar contradições em documentos.
    
    DOCUMENTOS DISPONÍVEIS: {', '.join(list_pdfs())}
    
    FUNÇÕES DISPONÍVEIS:
    - read_pdf(filename) - Lê um PDF específico
    - list_pdfs() - Lista todos os PDFs
    - read_all_pdfs() - Lê todos os PDFs
    
    INSTRUÇÕES:
    1. Analise os PDFs buscando contradições entre resoluções
    2. Uma contradição é quando uma resolução diz algo e outra diz o oposto
    3. Cite trechos específicos dos documentos
    4. Não aponte erros de gramática, apenas contradições de conteúdo
    
    FORMATO DE RESPOSTA:
    ----------------------------------------------------------------------------------------------------------------
    ANÁLISE DE CONTRADIÇÕES:
    
    - Documentos analisados: [lista]
    - Número de contradições: [número]
    
    Para cada contradição encontrada:
    - Contradição [número]:
        - Documento 1: [nome] - [trecho]
        - Documento 2: [nome] - [trecho]
        - Explicação: [detalhes da contradição]
    ----------------------------------------------------------------------------------------------------------------
    """,
    tools=[read_pdf, list_pdfs, read_all_pdfs],
    output_key="analise_contradicoes"
)

Adm_agentes = LlmAgent(
    model=OpenAi_model,
    name="Adm_agentes",
    description="Agente supervisor responsável por validar o trabalho dos outros agentes.",
    instruction="""
    Você é o supervisor responsável por validar o trabalho dos agentes.
    
    IMPORTANTE: Acesse a análise anterior através do estado 'analise_contradicoes'.
    
    INSTRUÇÕES:
    1. Verifique se o trabalho do agente Contradição está correto
    2. Valide se as contradições encontradas são reais
    3. Aponte erros caso existam
    
    FORMATO DE RESPOSTA:
    ----------------------------------------------------------------------------------------------------------------
    VALIDAÇÃO DO TRABALHO:
    - Trabalho desenvolvido corretamente: [Sim/Não]
    
    Se NÃO:
    - Agente: [nome]
    - Erro encontrado: [descrição]
    - Trecho incorreto: [citação]
    ----------------------------------------------------------------------------------------------------------------
    """,
    sub_agents=[Contradicao],
    output_key="validacao_final"
)

# Variável que o ADK procura para o agente raiz
root_agent = Adm_agentes