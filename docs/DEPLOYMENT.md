# 部署文档

## 技术栈

- 后端：Python 3.10、FastAPI、Uvicorn、Pydantic
- 前端：React、TypeScript、Vite
- 存储：本地 JSON 文件
- 容器：Docker、Docker Compose

## 本地开发运行

后端：

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173/
```

## Docker 一键部署

构建并启动：

```bash
docker compose up --build -d
```

或使用脚本：

```bash
sh scripts/docker-up.sh
```

访问：

```text
http://127.0.0.1:8000/
```

停止：

```bash
docker compose down
```

或使用脚本：

```bash
sh scripts/docker-down.sh
```

## 数据持久化

Docker Compose 会把本地 `./datas` 挂载到容器 `/app/datas`。

主要本地数据：

- `datas/accounts.json`：账号 Cookie，本地明文保存，不要提交。
- `datas/operations.json`：运营任务、监控结果、账号快照和操作日志，不要提交。

## 环境变量

- `XHS_WEB_HOST`：服务监听地址，Docker 默认 `0.0.0.0`。
- `XHS_WEB_PORT`：服务端口，Docker 默认 `8000`。
- `XHS_USE_PROXY`：是否保留系统代理。默认 `0`，后端会清理代理环境变量。

## 注意

Docker 部署仍建议只在本机或可信内网使用，不建议暴露到公网。Cookie 是敏感信息，当前版本不做加密存储。
