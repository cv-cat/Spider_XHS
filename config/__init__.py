import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """加载配置文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    example_env_path = project_root / '.env.example'
    
    # 如果配置文件不存在，复制示例文件
    if not env_path.exists() and example_env_path.exists():
        import shutil
        shutil.copy(str(example_env_path), str(env_path))
    
    # 加载环境变量
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("警告: 配置文件不存在，将使用默认配置")
        
# 在导入时自动加载配置
load_config() 