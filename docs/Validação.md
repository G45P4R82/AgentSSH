

## ⚠️ Ameaças à Validade: AgentSSH

### 1. Validade Interna (Internal Validity)

Refere-se a fatores que podem influenciar os resultados sem que o pesquisador saiba.

* **Viés de Seleção de Prompts:** Se os testes usarem apenas comandos simples que o LLM já conhece bem, a eficácia do Router pode parecer maior do que é na realidade.
* **Latência da Rede:** Instabilidades na conexão SSH podem ser interpretadas como falhas do Agente ReAct, quando na verdade são problemas de infraestrutura externa.

### 2. Validade de Construto (Construct Validity)

Refere-se a se a métrica realmente mede o que deveria medir.

* **Definição de "Sucesso":** O agente pode retornar um comando Bash válido, mas que não atende à intenção semântica do usuário. Medir apenas "sucesso de execução" (exit code 0) pode mascarar falhas de lógica da IA.
* **Limitação da Blacklist:** A segurança é medida pela interceptação de comandos proibidos. Se a blacklist for incompleta, a validade do construto "Segurança" fica comprometida.

### 3. Validade Externa (External Validity)

Refere-se à capacidade de generalizar os resultados.

* **Especificidade do SO:** O AgentSSH é focado em ambientes Linux. Os resultados podem não se aplicar a servidores Windows (PowerShell) ou ambientes de rede restritos (firewalls agressivos).
* **Dependência do Modelo:** Os resultados obtidos com o **Gemini 1.5 Flash** podem variar drasticamente se o modelo for trocado (ex: GPT-4 ou modelos locais Llama), limitando a generalização da arquitetura.

### 4. Validade de Conclusão (Conclusion Validity)

Refere-se à relação estatística entre o tratamento e o resultado.

* **Tamanho da Amostra:** Rodar apenas 5 ou 10 testes não oferece suporte estatístico para afirmar que a arquitetura multi-agente é superior.
* **Confiabilidade (Reliability):** A natureza estocástica dos LLMs pode fazer com que o mesmo prompt gere resultados diferentes em execuções distintas.
