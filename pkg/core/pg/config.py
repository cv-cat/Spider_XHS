from dataclasses import dataclass
from typing import Optional

@dataclass
class PostgresConfig:
    """PostgreSQL配置类"""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    schema: str = 'public'
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'PostgresConfig':
        """从字典创建配置对象"""
        return cls(
            host=config_dict.get('host', 'localhost'),
            port=config_dict.get('port', 5432),
            database=config_dict.get('database', 'postgres'),
            user=config_dict.get('user', 'postgres'),
            password=config_dict.get('password', ''),
            min_connections=config_dict.get('min_connections', 1),
            max_connections=config_dict.get('max_connections', 10),
            connection_timeout=config_dict.get('connection_timeout', 30),
            schema=config_dict.get('schema', 'public')
        )
        
    def get_dsn(self) -> str:
        """获取数据库连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}" 