#!/usr/bin/env python3
"""
测试日志过滤
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


# 模拟一个会产生callHandlers日志的操作
def test_logging():
    # 创建一个logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    # 添加一个处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # 产生一些日志
    logger.debug("This is a test debug message")
    logger.info("This is a test info message")

    # 模拟一个会产生callHandlers日志的操作
    def inner_function():
        logger.debug("This is from inner function")

    inner_function()


if __name__ == "__main__":
    test_logging()
