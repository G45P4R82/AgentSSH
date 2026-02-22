# ─── AgentSSH Makefile ────────────────────────────────────────────────────────
# Uso: make <target>
# Requer: Docker + Docker Compose v2 instalados

COMPOSE = docker compose
APP_SERVICE = web

.DEFAULT_GOAL := help

.PHONY: help build up down restart logs logs-web logs-worker logs-beat \
        shell migrate createsuperuser test check-unit bash ps clean

# ─── Ajuda ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  AgentSSH — comandos disponíveis"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make check-unit       Roda os testes Django dentro do container web"
	@echo "  make build            Constrói (ou reconstrói) as imagens"
	@echo "  make up               Sobe todos os serviços em background"
	@echo "  make down             Para e remove todos os containers"
	@echo "  make restart          down + up"
	@echo "  make ps               Lista containers em execução"
	@echo ""
	@echo "  make logs             Segue logs de todos os serviços"
	@echo "  make logs-web         Logs apenas do Django (runserver)"
	@echo "  make logs-worker      Logs apenas do Celery Worker"
	@echo "  make logs-beat        Logs apenas do Celery Beat"
	@echo ""
	@echo "  make shell            Shell Python do Django (manage.py shell)"
	@echo "  make bash             Bash dentro do container web"
	@echo "  make bash-redis       Redis CLI dentro do container redis"
	@echo ""
	@echo "  make migrate          Aplica migrations do Django"
	@echo "  make createsuperuser  Cria superusuário Django"
	@echo "  make test             Roda os testes Django"
	@echo ""
	@echo "  make task             Dispara a task de ingest manualmente"
	@echo "  make clean            Remove volumes, imagens e containers parados"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo ""

# ─── Docker Compose ───────────────────────────────────────────────────────────
build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart: down up

ps:
	$(COMPOSE) ps

# ─── Logs ─────────────────────────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f

logs-web:
	$(COMPOSE) logs -f web

logs-worker:
	$(COMPOSE) logs -f worker

logs-beat:
	$(COMPOSE) logs -f beat

# ─── Django ──────────────────────────────────────────────────────────────────
shell:
	$(COMPOSE) exec $(APP_SERVICE) python manage.py shell

bash:
	$(COMPOSE) exec $(APP_SERVICE) bash

migrate:
	$(COMPOSE) exec $(APP_SERVICE) python manage.py migrate

createsuperuser:
	$(COMPOSE) exec $(APP_SERVICE) python manage.py createsuperuser

test:
	$(COMPOSE) exec $(APP_SERVICE) python manage.py test

check-unit:
	$(COMPOSE) exec $(APP_SERVICE) python manage.py test agent --keepdb

# ─── Celery ───────────────────────────────────────────────────────────────────
task:
	@echo "📡 Disparando task ingest_homelab_metrics manualmente..."
	$(COMPOSE) exec $(APP_SERVICE) python manage.py shell -c \
		"from agent.tasks import ingest_homelab_metrics; result = ingest_homelab_metrics.delay(); print('Task enfileirada:', result.id)"

# ─── Redis ────────────────────────────────────────────────────────────────────
bash-redis:
	$(COMPOSE) exec redis redis-cli

# ─── Limpeza ──────────────────────────────────────────────────────────────────
clean:
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f
