import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_name='personal_health.log', level=logging.INFO):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, log_name)

    # Create a custom logger
    logger = logging.getLogger('personal_health')
    
    # Only configure the logger if it hasn't been configured already
    if not logger.handlers:
        logger.setLevel(level)

        # Create handlers
        file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)  # 10MB per file, keep 5 backups
        console_handler = logging.StreamHandler()

        # Create formatters and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger