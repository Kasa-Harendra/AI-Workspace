from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from settings import settings

engine = create_engine(url=(settings.DATABASE_URL + settings.DATABASE_NAME), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def get_db():
    try:
        with SessionLocal() as db:
            yield db
    except Exception as e:
        raise e 
    
