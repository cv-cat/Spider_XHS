import os
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env():
    load_dotenv(REPO_ROOT / '.env')
    load_dotenv(REPO_ROOT / '.env.local', override=True)
    cookies_str = os.getenv('XHS_COOKIE') or os.getenv('COOKIES')
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
