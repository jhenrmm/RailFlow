import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, validate_settings
from routers import analysis, auth, history

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_settings()
    yield


app = FastAPI(title="Rail Flow", version="1.0.0", lifespan=lifespan)

if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def ready():
    return {"status": "ready"}


app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(history.router)
