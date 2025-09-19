import logging
import os
from logging.handlers import RotatingFileHandler

# 1. Ensure log directory exists
log_dir = "/var/log/loginapp"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "throttle.log")

# 2. Create a RotatingFileHandler
handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,  # 5 MB per file
    backupCount=5           # keep last 5 log files
)

# 3. Set formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)

# 4. Get logger and add handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # or DEBUG if needed
logger.addHandler(handler)

# Optional: also print logs to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
