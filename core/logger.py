import logging
from logging.handlers import RotatingFileHandler
import os

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("naukri_automation")
logger.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# ----------------------------------------------
# FILE HANDLER (logs to logs/automation.log)
# ----------------------------------------------
file_handler = RotatingFileHandler(
    "logs/automation.log",
    maxBytes=2_000_000,
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ----------------------------------------------
# CONSOLE HANDLER (logs to terminal)
# ----------------------------------------------
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
