import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config import config
from routes.vocabulary import router as vocabulary_router
from routes.telegram import router as telegram_router
from services.vocabulary import make_vocabulary
from services.telegram_bot import set_telegram_webhook

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        await set_telegram_webhook()
    except Exception:
        logger.exception("Failed to set Telegram webhook on startup")

    try:
        make_vocabulary()
    except Exception:
        logger.exception("Failed to build vocabulary cache on startup")
    scheduler.add_job(
        make_vocabulary,
        trigger=CronTrigger.from_crontab(config.cache_cron_schedule),
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Vocabulary Teacher API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def only_known_endpoints(request: Request, call_next):
    if request.url.path == "/vocabulary" and request.method in {"GET", "OPTIONS"}:
        return await call_next(request)
    if request.url.path == "/healthz" and request.method in {"GET", "HEAD"}:
        return await call_next(request)
    if request.url.path == "/telegram/webhook" and request.method == "POST":
        return await call_next(request)
    return JSONResponse({"detail": "Not found"}, status_code=404)


@app.get("/healthz")
@app.head("/healthz")
def healthz():
    return {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allow_origins,
    allow_methods=["GET", "OPTIONS", "HEAD", "POST"],
    allow_headers=["*"],
)

app.include_router(vocabulary_router)
app.include_router(telegram_router)
