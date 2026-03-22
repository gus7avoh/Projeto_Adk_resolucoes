# Minha Jornada com Agentes de IA: Projeto de Análise de Resoluções na Arsae-MG

**Autor:** Gustavo Henrique Alves Maciel  
**Data do Relato:** Março de 2026

## Visão Geral
Este projeto foi desenvolvido durante minha trajetória na **Arsae-MG**, com o objetivo de automatizar a fiscalização de resoluções e normativas. A agência produz um alto volume de documentos que orientam os serviços de água e esgoto, e garantir que uma nova norma não entre em conflito com as anteriores é um desafio técnico e jurídico considerável.

## O Desafio
O processo de construção desses documentos é complexo. Era necessário garantir que as novas normativas seguissem o conjunto de normas já existentes, eliminando:
* **Contradições** entre documentos.
* **Ambiguidades** no texto.
* **Erros gramaticais** que pudessem causar interpretações equivocadas.

Fui responsável por desenvolver um sistema de **Agentes de Inteligência Artificial** para atuar como uma camada de fiscalização automatizada.

## Ferramentas e Estrutura
Em junho de 2025, o ecossistema de agentes ainda estava amadurecendo. Após pesquisar diversos frameworks, optei pelo **Google ADK (Agent Development Kit)**, devido à sua documentação robusta e integração com o ecossistema Google.

### Arquitetura do Sistema
A estrutura foi desenhada para ser modular, composta por:
1.  **Ingestão:** Estruturas para recebimento de documentos.
2.  **Pré-processamento:** Conversão de arquivos para formatos interpretáveis.
3.  **Interface:** Saída estruturada para o usuário final.
4.  **Enxame de Agentes (Multi-Agent System):**
    * **Agente de Contradição:** Focado em encontrar conflitos normativos.
    * **Agente de Ambiguidade:** Identifica trechos com múltiplas interpretações.
    * **Agente de Revisão:** Focado em ortografia e gramática.
    * **Agente Controlador (Manager):** Responsável por orquestrar o fluxo, validar o formato da saída e unificar a resposta final.

## Desenvolvimento e MVP
Para o **Mínimo Produto Viável (MVP)**, utilizei a interface de conversa nativa do ADK. 

* **Otimização de Contexto:** Desenvolvi funções para extrair o texto dos PDFs e convertê-los em arquivos `.txt`. Isso reduziu drasticamente o consumo de tokens e melhorou a precisão da análise.
* **Fluxo Inicial:** No teste inicial, o **Agente Gerente** acionava as funções de conversão e passava os dados para o **Agente de Contradição**. O retorno era então formatado pelo Gerente e entregue ao usuário.

### Aprendizados Técnicos
* **Escolha do Modelo:** Após testes comparativos, o **Gemini 2.5 Flash** se destacou pela menor taxa de falhas e eficiência em relação ao GPT-4o na época.
* **Engenharia de Prompt:** Refinei as instruções utilizando **Markdown** dentro dos prompts para dar peso semântico a partes específicas das instruções, garantindo que a LLM compreendesse o contexto jurídico.

## Desafios Encontrados
Apesar do sucesso inicial e do feedback positivo dos superiores, a escala do projeto revelou limitações no framework utilizado:

> * **Paralelismo:** O ADK apresentava dificuldades para executar agentes em paralelo.
> * **Orquestração:** Havia instabilidade na garantia de execução da cadeia de agentes.
> * **Poluição de Contexto:** Ao passar informações entre agentes, o sub-agente muitas vezes perdia o foco de seu papel original devido ao excesso de dados do agente anterior.

## Conclusão e Futuro
Após cerca de 3 meses desenvolvendo esse projeto e alguns outros em paralelo, cheguei à conclusão de que seria melhor tentar outra abordagem e decidi migrar para o n8n, que era outra ferramenta que estava muito bem no mercado.
Essa experiência em meados de junho de 2025 foi o meu primeiro projeto com inteligência artificial. Infelizmente não consegui finalizar a entrega da melhor forma, muito pela falta de uma ferramenta adequada para o que eu precisava fazer, porém consegui aprender muito sobre o desenvolvimento de sistemas como esse. Hoje, com ferramentas mais adequadas como o LangGraph, tenho certeza que conseguiria desenvolver o sistema de uma forma muito mais eficiente.

---
