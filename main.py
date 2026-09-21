from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import Base, engine
from models import User

app = FastAPI()

@app.on_event("startup")
def startup():
    return Base.metadata.create_all(bind=engine)