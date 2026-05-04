# 注意事项

## 安全

- Cookie 明文存储在 `datas/accounts.json`。
- 第三方发布 API Key 明文存储在 `datas/operations.json`。
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

- 关键词监控目前是手动执行，尚未实现自动定时调度。
- 账号分析是快照能力，趋势图和对比分析尚未实现。
- 不包含私信。
- 不包含外部后端上传。
- 第三方二维码发布接口要求图片/视频是可公开访问的 HTTPS URL，本地文件不能直接传给该接口。
- 发布页里“直接发布”只支持本地上传文件；“生成二维码”只支持链接媒体。
- 发布历史的“带入发布”只能回填标题、正文、地点、类型和链接媒体；本地文件出于浏览器安全限制需要重新选择。
- 发布流程会自动从正文提取话题，只识别形如 `#话题` 的连续文本，复杂符号或换行会作为话题边界。
- 页面中英文切换第一版覆盖主要导航和新增流程，历史页面文案会逐步补齐。

## 开发约定

- 后端接口都放在 `server/main.py`。
- 本地运营数据读写放在 `server/operation_store.py`。
- 账号数据读写放在 `server/account_store.py`。
- 前端主页面目前集中在 `frontend/src/main.tsx`。
- 前端视觉样式使用 Tailwind CSS，shadcn/ui 配置在 `frontend/components.json`，基础主题在 `frontend/tailwind.config.js` 和 `frontend/src/styles.css`。
- 风控策略维护在 `RISK_CONTROL.md`。
- 测试文档维护在 `docs/TESTING.md`。
- 后续需求或行为变化需要同步更新相关文档和测试。
