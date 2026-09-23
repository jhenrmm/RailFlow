from fastapi import FastAPI

from database import Base, engine
from routers import analysis, auth, history

app = FastAPI(title="Transito AI")


@app.on_event("startup")
def startup():
    return Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(history.router)