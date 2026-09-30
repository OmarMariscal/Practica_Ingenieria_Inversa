from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config, models  # noqa: F401  (models registra las tablas)
from app.api import router
from app.database import Base, engine
from app.errors import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="API de artículos (reimplementación)", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse({"errors": exc.errors}, status_code=exc.status)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    errors: dict[str, list[str]] = {}
    for err in exc.errors():
        parts = [str(p) for p in err["loc"][1:]]
        if len(parts) > 1 and parts[0] in ("article", "user"):
            parts = parts[1:]
        errors.setdefault(".".join(parts) or "body", []).append(err["msg"])
    return JSONResponse({"errors": errors}, status_code=422)
