"""
日志配置
"""
import os
from pathlib import Path
from utils.config_loader import get_config

config = get_config()

# Logging
LOG_LEVEL = config.get("logging.level", os.getenv("LOG_LEVEL", "INFO"))
LOG_DIR = Path(os.getenv("LOG_DIR", config.get("logging.dir", "logs")))
LOG_FILE = str(LOG_DIR / "app.log")
