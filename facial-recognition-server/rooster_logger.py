"""
    Setup a logger for the server
    usage:
    from rooster_logger import logger 
    logger.info("Start Server")
"""

import logging
from logging.handlers import RotatingFileHandler
import os

os.chdir(os.path.dirname(__file__))

# Create a logger
logger = logging.getLogger('rooster_server')
logger.setLevel(logging.INFO)

# Create a handler that writes log messages to a file, with a maximum
# log file size of 5MB and keeping backup logs (e.g., 3 old log files).
handler = RotatingFileHandler('rooster_server.log', maxBytes=5*1024*1024, backupCount=15)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)