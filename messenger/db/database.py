import configparser
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from kernel.config import NAME_CONFIG_FILE, DEFAULT_NAME_SERVER_DB, BASE_ENCODING

_CONFIG_FILE = Path(__file__).resolve().parent.parent / NAME_CONFIG_FILE

database_path = DEFAULT_NAME_SERVER_DB
if _CONFIG_FILE.exists():
    config = configparser.ConfigParser()
    config.read(_CONFIG_FILE, encoding=BASE_ENCODING)
    try:
        database_path = config['SETTINGS']['database_path']
    except KeyError:
        pass
    else:
        database_path = Path(database_path).resolve()


DATABASE_URL = f"sqlite:///{database_path}"

engine_server = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

SessionServer = sessionmaker(autocommit=False, autoflush=False, bind=engine_server)

ServerBase = declarative_base()
