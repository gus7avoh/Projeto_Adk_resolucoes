# Imports corretos para Google ADK
from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os
import PyPDF2
import fitz  # PyMuPDF
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OpenAi_model = LiteLlm(
    model = "gpt-4o", 
    api_key = os.getenv('OPENAI_API_KEY')
)


#model : "gemini-2.0-flash",	 
#api_key : os.getenv('GEMINI_API_KEY')


# Configuração dos caminhos
BASE_PATH = r"D:\cod\Arsae\Adk\Projeto_Adk_resolucoes\Adm_agentes\documentos"

def read_pdf_visual_detection(filename: str) -> str:
    """Try to detect strikethrough by visual elements."""
    document_path = os.path.join(BASE_PATH, filename)
    
    try:
        doc = fitz.open(document_path)
        texto_completo = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Busca por linhas horizontais (possíveis riscos)
            drawings = page.get_drawings()
            strike_lines = []
            
            for drawing in drawings:
                # Verifica se é uma linha horizontal
                if drawing.get("type") == "l":  # linha
                    rect = drawing.get("rect")
                    if rect and abs(rect[3] - rect[1]) < 2:  # Linha muito fina (horizontal)
                        strike_lines.append(fitz.Rect(rect))
            
            # Extrai texto e verifica sobreposição com linhas
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            span_rect = fitz.Rect(span["bbox"])
                            
                            # Verifica se há linha passando pelo meio do texto
                            is_struck = False
                            for strike_line in strike_lines:
                                if (strike_line.y0 > span_rect.y0 and 
                                    strike_line.y0 < span_rect.y1 and
                                    strike_line.intersects(span_rect)):
                                    is_struck = True
                                    break
                            
                            if is_struck:
                                texto_completo += f"<RISCADO>{text}</RISCADO>"
                            else:
                                texto_completo += text
                        texto_completo += "\n"
        
        doc.close()
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


#Contradicao = LlmAgent(
Contradicao = Agent(
    model = "gemini-2.0-flash",	 
    name="Contradicao",
    description="Agent responsible for analyzing contradictions in resolutions.",
    instruction=f"""
    You are a specialist in finding contradictions in documents.
    
    Start by reading the available PDFs in the directory and writing their names with that format:

    DOCUMENTOS DISPONÍVEIS: {', '.join(list_pdfs())}
    
  
    Functions available for you to use:
    - read_pdf(filename: str) -> str - Read PDF content from a file and extract text in a string format
    - read_all_pdfs() -> dict - Read all PDFs and return a dictionary with their content
    - list_pdfs() -> list - List all available PDF files in the directory

    INSTRUCTIONS:

    1- Analyze the PDFs looking for contradictions between resolutions, this contradictions can be in a one or more documents,
       you need to check all resolutions between all documents 
    2- A contradiction is when one resolution says something and another says the opposite
    3- You must to ignore strikethrough phases this will stay between <RISCADO> tags, you must to ignore this tags and the text inside them
    4- Cite the specific excerpts from the documents where the contradictions occur
    5- Do not point out grammar errors, or say anything other than what was requested - only content contradictions
    6- If you don't find contradictions, inform that there are no contradictions - this is a valid response
    7- Use the available documents for your analysis
    8- Be objective and clear in your responses
    9- When activated, you must perform your analysis without waiting for additional instructions
    10- after you finish your analysis, you must to pass to the Adm_agentes agent for validation

    RESPONSE FORMAT:
    ----------------------------------------------------------------------------------------------------------------
    ANÁLISE DE CONTRADIÇÕES:
    
    - Documentos analisados: [lista]
    - Número de contradições: [número]
    
    for each contradiction found, use the following format:
    - Contradição [número]:

        -  [nome do documento]
            Número do artigo: [número do artigo] (ex: Art. 1)

            - [trecho]


        -  [nome do documento]
            Número do artigo: [número do artigo] (ex: Art. 1)

            - [trecho]

        - Explicação:
        
        [detalhes da contradição]
    ----------------------------------------------------------------------------------------------------------------
    """,
    tools=[read_pdf, list_pdfs, read_all_pdfs],
    output_key="analise_contradicoes"
)

#Adm_agentes = LlmAgent(
Adm_agentes = Agent(
    model = "gemini-2.0-flash",	 
    name="Adm_agentes",
    description="Agent responsible for managing and validating the work of other agents.",
    instruction="""
    Your task is to ensure that the Contradicao agent has performed its work correctly and that the contradictions found are valid.

    IMPORTANT: Access the previous analysis through the state 'analise_contradicoes'.

    INSTRUCTIONS:
    1. Check if the work of the Contradicao agent is correct
    2. Validate if the contradictions found are real
    3. Point out errors if they exist
    4. after all agents have finished their work, you must validate the final result
    5. When the chat starts, you must to pass to the conversation for the Contradicao agent to perform its analysis

    RESPONSE FORMAT:
    ----------------------------------------------------------------------------------------------------------------
    VALIDAÇÃO DO TRABALHO:
    - Trabalho desenvolvido corretamente: [Sim/Não]
    
    If not correct:
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