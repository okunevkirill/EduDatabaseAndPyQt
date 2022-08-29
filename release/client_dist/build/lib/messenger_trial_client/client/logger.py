import logging
from pathlib import Path

from messenger_trial_client.common.settings import DEFAULT_ENCODING

LOG_DIR = Path(__file__).resolve().parent.parent / 'log'
LOG_FILE_NAME = 'msg_client.log'
FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

if not LOG_DIR.exists():
    LOG_DIR.mkdir()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_DIR / LOG_FILE_NAME, encoding=DEFAULT_ENCODING)
file_handler.setFormatter(FORMATTER)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(FORMATTER)
console_handler.setLevel(logging.INFO)

LOGGER.addHandler(file_handler)
LOGGER.addHandler(console_handler)

if __name__ == '__main__':
    LOGGER.debug('Client: This is debug info')
    LOGGER.info('Client: This is information')
    LOGGER.warning('Client: This is a warning')
    LOGGER.error('Client: This is a error')
    LOGGER.critical('Client: This is critical information')
