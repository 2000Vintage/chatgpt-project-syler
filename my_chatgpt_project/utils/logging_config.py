import logging
from aiologger import Logger
import os

log_dir = "logs"

# 创建日志目录（如果不存在）
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def configure_sync_logging():
    """
    配置同步日志记录
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/server.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("sync_logger")

def configure_async_logging():
    """
    配置异步日志记录
    """
    return Logger.with_default_handlers(name="async_logger", level=logging.INFO)

