import time
import random
from threading import Lock
from loguru import logger
from xhs_utils.common_util import load_rate_limit_config

class RateLimiter:
    """
    使用令牌桶算法实现的请求速率限制器，带有随机延迟以模拟人类行为
    支持通过环境变量配置和完全禁用
    """
    def __init__(self, max_requests: int = None, time_window: int = None, 
                 min_delay: float = None, max_delay: float = None):
        """
        初始化速率限制器
        所有参数都可选，默认从.env配置文件读取
        如果在.env中设置RATE_LIMIT_ENABLED=false，则完全禁用速率限制
        
        :param max_requests: 在时间窗口内允许的最大请求数，默认从配置文件读取
        :param time_window: 时间窗口大小(秒)，默认从配置文件读取
        :param min_delay: 最小延迟时间(秒)，用于在基础延迟上增加随机波动，默认从配置文件读取
        :param max_delay: 最大延迟时间(秒)，用于在基础延迟上增加随机波动，默认从配置文件读取
        """
        # 加载配置
        config = load_rate_limit_config()
        self.enabled = config['enabled']
        
        # 如果禁用了速率限制，直接返回
        if not self.enabled:
            return
            
        # 从配置文件读取默认值，如果有传入参数则使用传入的值
        self.max_requests = max_requests if max_requests is not None else config['max_requests']
        self.time_window = time_window if time_window is not None else config['time_window']
        self.tokens = self.max_requests
        self.last_update = time.time()
        self.lock = Lock()
        
        # 延迟波动范围
        self.min_delay = min_delay if min_delay is not None else config['min_delay']
        self.max_delay = max_delay if max_delay is not None else config['max_delay']
        
        # 计算基础等待时间（每个请求的标准间隔）
        self.base_wait_time = self.time_window / self.max_requests
    
    def _update_tokens(self):
        """更新令牌数量"""
        if not self.enabled:
            return
            
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = int((time_passed * self.max_requests) / self.time_window)
        if new_tokens > 0:
            self.tokens = min(self.tokens + new_tokens, self.max_requests)
            self.last_update = now

    def _get_random_delay(self, base_time: float = 0) -> float:
        """
        生成一个随机延迟时间
        :param base_time: 基础等待时间，默认为0
        :return: 实际等待时间
        """
        if not self.enabled:
            return 0
            
        # 在基础时间上增加一个随机波动
        # 波动范围是 min_delay 到 max_delay 之间
        random_variation = random.uniform(self.min_delay, self.max_delay)
        total_delay = base_time + random_variation
        
        if total_delay > 0:
            logger.debug(f"Adding delay of {total_delay:.2f} seconds (base: {base_time:.2f}s, variation: {random_variation:.2f}s)")
        
        return total_delay

    def acquire(self, block: bool = True) -> bool:
        """
        获取一个令牌
        :param block: 如果为True，则在没有令牌时阻塞等待；如果为False，则立即返回结果
        :return: 是否成功获取令牌
        """
        # 如果速率限制被禁用，直接返回成功
        if not self.enabled:
            return True
            
        with self.lock:
            self._update_tokens()
            
            if self.tokens > 0:
                self.tokens -= 1
                # 即使有令牌，也添加一个小的随机延迟
                delay = self._get_random_delay()
                if delay > 0:
                    time.sleep(delay)
                return True
            
            if not block:
                return False
            
            # 计算需要等待的时间
            base_wait_time = self.base_wait_time * (1 - self.tokens)
            
            # 在基础等待时间上增加随机波动
            actual_wait_time = self._get_random_delay(base_wait_time)
            time.sleep(actual_wait_time)
            
            self.tokens = self.max_requests - 1
            self.last_update = time.time()
            return True

    def __call__(self, func):
        """装饰器方法，可以直接用于装饰需要限制速率的函数"""
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        return wrapper 