
from app.core.config import settings
from sqlmodel import create_engine

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.SQLALCHEMY_ECHO)
