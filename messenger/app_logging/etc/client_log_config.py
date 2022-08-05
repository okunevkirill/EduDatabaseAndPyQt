import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / 'log'
LOG_FILE_NAME = 'msg_client.log'
FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

if not LOG_DIR.exists():
    LOG_DIR.mkdir()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_DIR / LOG_FILE_NAME, encoding='utf-8')
file_handler.setFormatter(FORMATTER)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(FORMATTER)
console_handler.setLevel(logging.INFO)

LOGGER.addHandler(file_handler)
LOGGER.addHandler(console_handler)

if __name__ == '__main__':
    LOGGER.debug('This is debug info')
    LOGGER.info('This is information')
    LOGGER.warning('This is a warning')
    LOGGER.error('This is a error')
    LOGGER.critical('This is critical information')
