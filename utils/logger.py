import logging
import sys

def setup_logger(name="AI-Guide"):
    """
    配置并返回一个标准的 logger
    """
    logger = logging.getLogger(name)
    
    # 防止重复添加 handler
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)

    # 创建控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 定义日志格式
    # 格式: [时间] [级别] - 消息
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 使用 TimeManager 的时区逻辑覆盖默认的 time.localtime
    from utils.time_manager import TimeManager
    def time_converter(seconds):
        return TimeManager.get_now().timetuple()
        
    formatter.converter = time_converter
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    
    return logger

# 全局单例 logger
logger = setup_logger()
