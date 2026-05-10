import random
import threading
import time

from loguru import logger

REQUEST_TIMEOUT = 15

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

_request_counter = 0
_counter_lock = threading.Lock()


def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def rate_limited_delay(
    min_seconds: float = 5.0,
    max_seconds: float = 15.0,
    cooldown_every: int = 10,
    cooldown_min: float = 60.0,
    cooldown_max: float = 120.0,
) -> None:
    """
    带周期性冷却的请求限速。
    每发送 cooldown_every 次请求后暂停 cooldown_min~cooldown_max 秒，
    其余请求之间随机等待 min_seconds~max_seconds 秒。
    """
    global _request_counter
    with _counter_lock:
        _request_counter += 1
        count = _request_counter

    if count % cooldown_every == 0:
        delay = random.uniform(cooldown_min, cooldown_max)
        logger.info(f'[限速] 已发送 {count} 次请求，触发冷却 {delay:.0f}s')
        time.sleep(delay)
    else:
        # 以 15% 概率插入一次较长停顿，模拟用户阅读
        if random.random() < 0.15:
            delay = random.uniform(max_seconds, max_seconds * 2.5)
            logger.debug(f'[限速] 随机长停顿 {delay:.0f}s')
            time.sleep(delay)
        else:
            time.sleep(random.uniform(min_seconds, max_seconds))


def reset_request_counter() -> None:
    global _request_counter
    with _counter_lock:
        _request_counter = 0


def get_random_user_agent() -> str:
    return random.choice(_USER_AGENTS)
