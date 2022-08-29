import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from messenger_trial_server.common.settings import DEFAULT_ENCODING

LOG_DIR = Path(__file__).resolve().parent.parent / 'log'
LOG_FILE_NAME = 'msg_server.log'
FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

if not LOG_DIR.exists():
    LOG_DIR.mkdir()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(LOG_DIR / LOG_FILE_NAME, encoding=DEFAULT_ENCODING, interval=1, when='D')
file_handler.setFormatter(FORMATTER)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(FORMATTER)
console_handler.setLevel(logging.INFO)

LOGGER.addHandler(file_handler)
LOGGER.addHandler(console_handler)

if __name__ == '__main__':
    LOGGER.debug('Server: This is debug info')
    LOGGER.info('Server: This is information')
    LOGGER.warning('Server: This is a warning')
    LOGGER.error('Server: This is a error')
    LOGGER.critical('Server: This is critical information')
