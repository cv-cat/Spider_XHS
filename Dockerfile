FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN python --version && node --version && npm --version

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

CMD ["python", "main.py"] 
