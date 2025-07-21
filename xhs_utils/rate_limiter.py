import time
import random
from threading import Lock
from loguru import logger
from config.config import Config

class RateLimiter:
    """
    使用令牌桶算法实现的请求速率限制器，带有随机延迟以模拟人类行为
    支持通过环境变量配置和完全禁用
    """
    def __init__(self):
        config = Config.get_rate_limiter_config()
        self.max_requests = config['max_requests']  # 在时间窗口内允许的最大请求数
        self.time_window = config['time_window']    # 时间窗口大小(秒)
        self.min_delay = config['min_delay']        # 随机延迟的最小值(秒)
        self.max_delay = config['max_delay']        # 随机延迟的最大值(秒)
        self.request_times = []                     # 请求时间列表
        self.enabled = config['enabled']
        
        # 如果禁用了速率限制，直接返回
        if not self.enabled:
            return
            
        self.tokens = self.max_requests
        self.last_update = time.time()
        self.lock = Lock()
        
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

    def _clean_old_requests(self):
        """清理时间窗口外的请求记录"""
        current_time = time.time()
        self.request_times = [t for t in self.request_times 
                            if current_time - t < self.time_window]
        
    def acquire(self):
        """
        获取执行权限
        如果当前请求数超过限制，会等待随机时间
        """
        if not self.enabled:
            return
            
        with self.lock:
            self._clean_old_requests()
            
            while len(self.request_times) >= self.max_requests:
                # 如果请求数达到上限，随机等待一段时间
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.info(f'请求数达到限制，等待 {delay:.2f} 秒')
                time.sleep(delay)
                self._clean_old_requests()
                
            # 记录当前请求时间
            self.request_times.append(time.time())

    def __call__(self, func):
        """装饰器方法，可以直接用于装饰需要限制速率的函数"""
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        return wrapper 