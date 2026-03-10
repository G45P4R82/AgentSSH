

## 🎯 Definição do Objetivo (Template GQM)

Para formalizar o experimento com o **AgentSSH**, preenchemos o modelo da seguinte forma:

* **Objeto de Estudo:** O sistema de orquestração multi-agente AgentSSH (especificamente os agentes Router, SSH e RAG).
* **Propósito:** **Avaliar** a eficácia e a confiabilidade e **comparar** com abordagens de agente único (Single Agent).
* **Foco:** A **capacidade de detecção/prevenção de falhas** (segurança) e a **acurácia na execução** de comandos complexos via linguagem natural.
* **Ponto de Vista:** Do **administrador de sistemas/SRE** que busca automatizar tarefas sem perder o controle de segurança.
* **Contexto:** Um ambiente de infraestrutura híbrida com múltiplos servidores remotos e coleta de métricas em tempo real (NodeExporter + Qdrant).

---

## 📋 Desdobramento: Questões e Métricas

Seguindo a hierarquia do GQM, transformamos o objetivo em perguntas mensuráveis:

### 1. Eficácia do Roteamento (Router Agent)

* **Questão:** O Router direciona corretamente as intenções de "Métricas" vs. "Ações SSH"?
* **Métrica:** Taxa de acerto do Router (Precision/Recall) em um dataset de 50 prompts variados.

### 2. Confiabilidade e Segurança (Blacklist & ReAct)

* **Questão:** O loop ReAct consegue recuperar erros de execução sem violar a `blacklist` de segurança?
* **Métrica:** Percentual de comandos bloqueados corretamente vs. comandos que falharam por erro de sintaxe mas foram corrigidos pelo agente.

### 3. Utilidade do Contexto RAG

* **Questão:** A busca semântica no Qdrant melhora a análise de tendências em comparação a uma consulta simples de "status atual"?
* **Métrica:** Tempo de resposta para identificar anomalias históricas vs. análise manual de logs.

---

## 🔬 Transformação em Hipótese Formal

Como sugere a parte inferior da sua imagem, podemos transformar isso em uma hipótese testável:

> **Hipótese:** "O uso de uma arquitetura multi-agente com um Router especializado reduz em **X%** a execução de comandos inválidos no terminal em comparação a um agente LLM genérico, mantendo uma acurácia de **Y%** na recuperação de métricas históricas via RAG."

**Variáveis Independentes:** Arquitetura do Agente (Multi-agente vs Single-agent).
**Variáveis Dependentes:** Taxa de erro de execução, tempo de resposta, conformidade com a blacklist de segurança.


