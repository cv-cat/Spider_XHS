from typing import List, Dict, Any, Optional, Union
import asyncpg
from loguru import logger
from .config import PostgresConfig

class PostgresClient:
    """PostgreSQL客户端类"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """创建连接池"""
        if self.pool is not None:
            return
            
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.config.get_dsn(),
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                timeout=self.config.connection_timeout,
                command_timeout=self.config.connection_timeout
            )
            logger.info(f"PostgreSQL连接池创建成功: {self.config.host}:{self.config.port}/{self.config.database}")
        except Exception as e:
            logger.error(f"PostgreSQL连接池创建失败: {str(e)}")
            raise
            
    async def disconnect(self):
        """关闭连接池"""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL连接池已关闭")
            
    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """
        执行SQL语句
        :param query: SQL语句
        :param args: SQL参数
        :param timeout: 超时时间（秒）
        :return: 执行结果
        """
        if self.pool is None:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args, timeout=timeout)
        except Exception as e:
            logger.error(f"SQL执行失败: {query}, 错误: {str(e)}")
            raise
            
    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[asyncpg.Record]:
        """
        执行查询并返回所有结果
        :param query: SQL查询语句
        :param args: SQL参数
        :param timeout: 超时时间（秒）
        :return: 查询结果列表
        """
        if self.pool is None:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args, timeout=timeout)
        except Exception as e:
            logger.error(f"SQL查询失败: {query}, 错误: {str(e)}")
            raise
            
    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """
        执行查询并返回第一行结果
        :param query: SQL查询语句
        :param args: SQL参数
        :param timeout: 超时时间（秒）
        :return: 查询结果（单行）
        """
        if self.pool is None:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args, timeout=timeout)
        except Exception as e:
            logger.error(f"SQL查询失败: {query}, 错误: {str(e)}")
            raise
            
    async def fetchval(self, query: str, *args, timeout: Optional[float] = None) -> Any:
        """
        执行查询并返回第一个值
        :param query: SQL查询语句
        :param args: SQL参数
        :param timeout: 超时时间（秒）
        :return: 查询结果（单个值）
        """
        if self.pool is None:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args, timeout=timeout)
        except Exception as e:
            logger.error(f"SQL查询失败: {query}, 错误: {str(e)}")
            raise
            
    async def transaction(self, timeout: Optional[float] = None):
        """
        创建事务
        :param timeout: 超时时间（秒）
        :return: 事务上下文管理器
        """
        if self.pool is None:
            await self.connect()
            
        return self.pool.acquire(timeout=timeout)
        
    def table_name(self, name: str) -> str:
        """
        获取带前缀的表名
        :param name: 原始表名
        :return: 带前缀的表名
        """
        return f"{name}" 