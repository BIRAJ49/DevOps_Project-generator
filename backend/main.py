from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.base import Base
from backend.models.database import engine
from backend.routes.auth import router as auth_router
from backend.routes.generator import router as generator_router
from backend.utils.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.archive_directory.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(generator_router, prefix=settings.api_prefix)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

