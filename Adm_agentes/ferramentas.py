import os
from pathlib import Path
from pdf2docx import Converter
from docx import Document

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

def obter_dados_processados()-> dict:
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