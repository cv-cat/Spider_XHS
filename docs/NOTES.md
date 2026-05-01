# 注意事项

## 安全

- Cookie 明文存储在 `datas/accounts.json`。
- 不要提交 `datas/accounts.json`、`datas/operations.json`、`.env`。
- 不建议公网部署。
- 前端不会展示完整 Cookie。

## 风控

- 默认按需加载详情，不自动批量拉取。
- 同一账号请求串行，并带随机间隔。
- 连续失败后进入冷却。
- 新增任何批量功能前，必须先设计暂停、取消、限速和失败处理。

## 运行

- 开发模式前端端口是 `5173`。
- Docker 模式统一访问后端端口 `8000`，FastAPI 会托管前端构建产物。
- 如果本机 8000 端口被占用，可以修改 `docker-compose.yml` 的端口映射。

## 当前限制

- 发布任务目前是记录和管理，尚未实现从任务列表直接执行发布。
- 关键词监控目前是手动执行，尚未实现自动定时调度。
- 账号分析是快照能力，趋势图和对比分析尚未实现。
- 不包含私信。
- 不包含外部后端上传。

## 开发约定

- 后端接口都放在 `server/main.py`。
- 本地运营数据读写放在 `server/operation_store.py`。
- 账号数据读写放在 `server/account_store.py`。
- 前端主页面目前集中在 `frontend/src/main.tsx`。
- 风控策略维护在 `RISK_CONTROL.md`。
