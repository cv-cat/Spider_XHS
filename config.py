"""
Rate limiter configuration settings
"""

RATE_LIMITER = {
    # 在时间窗口内允许的最大请求数
    'max_requests': 2,
    
    # 时间窗口大小(秒)
    'time_window': 1,
    
    # 随机延迟的最小值(秒)
    'min_delay': 0.5,
    
    # 随机延迟的最大值(秒)
    'max_delay': 2.0,
} 