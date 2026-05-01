FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.10-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV XHS_WEB_HOST=0.0.0.0
ENV XHS_WEB_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apis ./apis
COPY server ./server
COPY static ./static
COPY xhs_utils ./xhs_utils
COPY spider ./spider
COPY RISK_CONTROL.md README.md ./
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/datas

EXPOSE 8000

CMD ["sh", "-c", "uvicorn server.main:app --host ${XHS_WEB_HOST:-0.0.0.0} --port ${XHS_WEB_PORT:-8000}"]
