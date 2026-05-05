FROM node:20-bookworm-slim AS frontend-builder

ARG NPM_REGISTRY=https://registry.npmmirror.com

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --registry="${NPM_REGISTRY}"

COPY frontend/ ./
RUN npm run build


FROM python:3.10-slim AS runtime

ARG ENABLE_CHINA_MIRRORS=1
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV XHS_WEB_HOST=0.0.0.0
ENV XHS_WEB_PORT=8000

RUN if [ "${ENABLE_CHINA_MIRRORS}" = "1" ]; then \
        sed -i \
            -e 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
            -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
            /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url="${PIP_INDEX_URL}" -r requirements.txt

COPY package*.json ./
RUN npm ci --omit=dev --registry="${NPM_REGISTRY}"

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
