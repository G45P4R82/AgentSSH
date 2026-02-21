FROM python:3.12-slim

# Evita .pyc e faz o stdout/stderr ir direto pro terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema necessárias para algumas libs Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte
COPY . .

# Porta padrão do Django runserver
EXPOSE 8000

# Comando padrão — sobrescrito por cada serviço no docker-compose.yml
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
