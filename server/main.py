import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config import config
from routes.vocabulary import router as vocabulary_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="Vocabulary Teacher API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def only_vocabulary_endpoint(request: Request, call_next):
    if request.url.path == "/vocabulary" and request.method in {"GET", "OPTIONS"}:
        return await call_next(request)
    if request.url.path == "/healthz" and request.method in {"GET", "HEAD"}:
        return await call_next(request)
    return JSONResponse({"detail": "Not found"}, status_code=404)


@app.get("/healthz")
@app.head("/healthz")
def healthz():
    logger.info("I'm healthy")
    return {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allow_origins,
    allow_methods=["GET", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

app.include_router(vocabulary_router)
