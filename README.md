# AgentSSH 🤖🌐

**AgentSSH** é um agente de infraestrutura inteligente que permite gerenciar e interagir com servidores remotos via SSH usando linguagem natural. Alimentado pelo **Google Gemini API**, ele transforma instruções simples em comandos Bash complexos, executa-os com segurança e analisa os resultados em tempo real.

Além da execução de comandos, o sistema possui um pipeline de observabilidade que coleta métricas de máquinas (via Prometheus), gera embeddings e as armazena em um banco de vetores (**Qdrant**) para consultas semânticas futuras.

---

## 🚀 Funcionalidades Principais

- **🤖 Sistema Multi-Agente**: Utiliza um **Router Agent** para identificar a intenção do usuário e direcionar para o especialista correto:
  - **SSH Agent**: Especialista em execução de comandos e automação Linux (Loop ReAct).
  - **RAG Agent**: Especialista em análise de métricas históricas e saúde da infraestrutura (Retriever de dados do Qdrant).
- **💻 Gestão de Hosts (CRUD)**: Interface completa para cadastrar, editar e remover servidores SSH.
- **🔄 Execução Multi-Step**: O agente pensa (Thought), executa (Action), observa o resultado (Observation) e analisa até concluir a tarefa.
- **📈 Observabilidade e RAG**: Coleta automática de métricas de CPU, RAM e Disco via Celery Beat, com armazenamento vetorial no Qdrant.
- **🛡️ Segurança**: Camada de validação de comandos antes da execução.
- **⚡ Interface Moderna**: Dashboard desenvolvido com Django e HTMX para uma experiência dinâmica sem recarregamento de página.

---

## 🛠️ Stack Tecnológica

- **Backend**: Python 3.11+, Django 5.0
- **AI**: Google Gemini Pro (generative-ai)
- **SSH**: Paramiko
- **Task Queue**: Celery + Redis
- **Banco de Dados**: SQLite (Relacional) + Qdrant (Vetorial)
- **Observability**: Prometheus Node Exporter + Sentence Transformers (Embeddings)
- **Frontend**: HTMX, Vanilla CSS, Semantic HTML

---

## 📦 Estrutura do Projeto

```text
.
├── agent/                  # App principal do Django
│   ├── services/           # Lógica de negócio (Gemini, SSH, Security)
│   ├── models.py           # Definição de Hosts, Sessions e Tasks
│   ├── tasks.py            # Tasks do Celery (Ingestão de Métricas)
│   └── templates/          # Templates HTML/HTMX
├── agent_project/          # Configurações do projeto Django
├── scripts/                # Scripts utilitários
├── docker-compose.yml      # Orquestração de serviços (Web, Worker, Beat, Redis)
└── Makefile                # Atalhos para comandos comuns
```

---

## ⚙️ Instalação e Configuração

### Pré-requisitos
- Docker e Docker Compose V2
- Chave de API do Google Gemini (Google AI Studio)

### 1. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto seguindo o modelo:
```bash
cp .env.example .env
```
Preencha as chaves:
- `GEMINI_API_KEY`: Sua chave do Google AI Studio.
- `SECRET_KEY`: Chave secreta do Django.
- `DEBUG`: True/False.

### 2. Rodando com Docker
O projeto utiliza um `Makefile` para facilitar a gestão dos containers.

```bash
# Constrói e sobe todos os serviços (Web, Redis, Worker, Beat)
make up

# Aplica as migrations do banco de dados
make migrate

# Cria um usuário administrador para o Django
make createsuperuser
```

O sistema estará disponível em: `http://localhost:8000`

---

## ⌨️ Comandos do Makefile

- `make build`: Constrói as imagens Docker.
- `make logs`: Acompanha os logs de todos os serviços.
- `make logs-web`: Logs específicos do servidor Django.
- `make restart`: Reinicia os containers.
- `make task`: Dispara manualmente a task de ingestão de métricas.
- `make clean`: Limpa volumes e imagens não utilizadas.

---

## 📊 Pipeline de Métricas (Homelab)

O AgentSSH está configurado para monitorar nodes específicos via **Prometheus Node Exporter**.

> **Nota de Configuração**: Os endereços das máquinas e do Qdrant estão configurados em `agent/tasks.py`. Certifique-se de ajustar a variável `NODES` e `QDRANT_URL` para o seu ambiente.

1. A cada 10 minutos, o **Celery Beat** dispara a task `ingest_homelab_metrics`.
2. O sistema faz o scrap das métricas em `/metrics`.
3. Transforma o status da máquina em texto legível.
4. Gera um embedding usando o modelo `all-MiniLM-L6-v2`.
5. Salva no **Qdrant** para permitir buscas semânticas (ex: "Quais máquinas estão com pouco espaço em disco?").

---

## 🛡️ Segurança
O sistema implementa uma validação básica de segurança antes de enviar comandos para o servidor remoto. Recomenda-se o uso de usuários com permissões limitadas nos hosts monitorados.

---

## 📄 Licença
Este projeto foi desenvolvido para fins de automação e estudo de agentes inteligentes. Use com responsabilidade.
