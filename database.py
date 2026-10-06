from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

# The application validates this setting during startup.  A placeholder keeps
# imports usable for unit tests that override the database dependency.
engine = create_engine(DATABASE_URL or "sqlite://")

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
