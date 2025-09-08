# Usar imagem base oficial do Python na mesma versão do desenvolvimento
FROM python:3.12.3-slim

# Evitar arquivos .pyc e usar log sem buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Criar pasta de trabalho
WORKDIR /app

# Copiar arquivos de dependências primeiro para aproveitar cache de build
COPY requirements.txt /app/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . /app/

# Instalar dependências do Venom Bot
WORKDIR /app/whatsapp_bot
RUN npm install

# Voltar para a pasta principal do app
WORKDIR /app

# Expõe a porta do Flask
EXPOSE 5000

# Comando padrão para rodar a aplicação
CMD ["python", "app.py"]
