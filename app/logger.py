import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(LOG_LEVEL)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(LOG_LEVEL)

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
if not root_logger.handlers:
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

# Utility to get a module-specific logger
def get_logger(name=None):
    return logging.getLogger(name) 