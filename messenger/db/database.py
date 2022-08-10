from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///server_db.db3"

engine_server = create_engine(DATABASE_URL)

SessionServer = sessionmaker(autocommit=False, autoflush=False, bind=engine_server)

ServerBase = declarative_base()
