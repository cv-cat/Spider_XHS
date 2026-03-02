"""
请求延时管理模块
提供统一的延时控制机制,支持固定延时和随机波动延时

本模块通过环境变量配置,RequestDelayManager实例化时会执行load_dotenv
"""
import time
import os
import random
from loguru import logger
from dotenv import load_dotenv


class RequestDelayManager:
    """请求延时管理器"""

    def __init__(self):
        load_dotenv()
        self.base_delay = float(os.getenv('REQUEST_DELAY', '0'))
        self.enable_random = os.getenv('ENABLE_RANDOM_DELAY', 'false').lower() == 'true'
        self.random_range = float(os.getenv('RANDOM_DELAY_RANGE', '0.5'))

    def get_delay(self) -> float:
        """
        获取当前的延时时间(秒)
        如果启用了随机延时,会在基础延时上添加随机波动
        """
        if self.base_delay <= 0:
            return 0

        delay = self.base_delay

        if self.enable_random:
            # 添加随机波动: ±random_range 范围内的随机值
            fluctuation = random.uniform(-self.random_range, self.random_range)
            delay = max(0, delay + fluctuation)  # 确保延时不会为负数

        return delay

    def apply_delay(self):
        """应用延时"""
        delay = self.get_delay()
        if delay > 0:
            logger.debug(f"请求延时: {delay:.2f}秒")
            time.sleep(delay)

    def update_config(self, base_delay=None, enable_random=None, random_range=None):
        """
        动态更新延时配置
        :param base_delay: 基础延时(秒)
        :param enable_random: 是否启用随机延时
        :param random_range: 随机波动范围(秒)
        """
        if base_delay is not None:
            self.base_delay = float(base_delay)
            os.environ['REQUEST_DELAY'] = str(base_delay)

        if enable_random is not None:
            self.enable_random = enable_random
            os.environ['ENABLE_RANDOM_DELAY'] = str(enable_random).lower()

        if random_range is not None:
            self.random_range = float(random_range)
            os.environ['RANDOM_DELAY_RANGE'] = str(random_range)


# 全局延时管理器实例
delay_manager = RequestDelayManager()

