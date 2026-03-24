#!/usr/bin/env python3
"""
调试日志记录
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

# 导入API的日志配置
import api.main


def test_logging():
    # 获取所有日志记录器
    root_logger = logging.getLogger()

    # 打印所有日志记录器的名称
    print("所有日志记录器:")
    for name in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(name)
        print(f"  {name}: level={logger.level}, handlers={len(logger.handlers)}")

    # 检查特定的日志记录器
    print("\n检查特定日志记录器:")
    for name in ["logging", "uvicorn", "fastapi", "surrealdb"]:
        logger = logging.getLogger(name)
        print(f"  {name}: level={logger.level}, handlers={len(logger.handlers)}")
        for handler in logger.handlers:
            print(f"    Handler: {type(handler).__name__}")


if __name__ == "__main__":
    test_logging()
