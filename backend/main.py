from typing import Union
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from routers import cookie, xhs
from loguru import logger
import sys

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", 
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

OPENAPI_URL = "/api/openapi.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("🚀 小红书API服务启动成功")
    logger.info("📖 API文档: http://localhost:8000/docs")
    logger.info("📊 Scalar文档: http://localhost:8000/scalar")
    logger.info("🍪 Cookie管理服务已就绪")
    
    yield
    
    # 关闭时执行
    logger.info("👋 小红书API服务已关闭")
    logger.info("🧹 清理资源完成")


# 创建FastAPI应用
app = FastAPI(
    title="小红书API服务",
    description="提供小红书数据采集和Cookie管理的HTTP API服务",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=OPENAPI_URL,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(cookie.router)
app.include_router(xhs.router)

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Scalar API文档界面"""
    return get_scalar_api_reference(
        openapi_url=OPENAPI_URL,
        title=app.title,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)