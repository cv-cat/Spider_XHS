import os
from loguru import logger
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    cookies_str = os.getenv('COOKIES')
    return cookies_str

def init():
    media_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/media_datas'))
    excel_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/excel_datas'))
    for base_path in [media_base_path, excel_base_path]:
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            logger.info(f'创建目录 {base_path}')
    cookies_str = load_env()
    base_path = {
        'media': media_base_path,
        'excel': excel_base_path,
    }
    return cookies_str, base_path

def load_rate_limit_config():
    """
    从.env文件加载速率限制配置
    如果环境变量不存在，返回默认值
    """
    load_dotenv()
    
    # 检查是否启用速率限制
    rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    
    if not rate_limit_enabled:
        return {
            'enabled': False,
            'max_requests': float('inf'),  # 无限制
            'time_window': 1,
            'min_delay': 0,
            'max_delay': 0
        }
    
    return {
        'enabled': True,
        'max_requests': int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '2')),
        'time_window': int(os.getenv('RATE_LIMIT_TIME_WINDOW', '1')),
        'min_delay': float(os.getenv('RATE_LIMIT_MIN_DELAY', '0.2')),  # 默认值改小一些
        'max_delay': float(os.getenv('RATE_LIMIT_MAX_DELAY', '0.5'))   # 默认值改小一些
    }
