import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.api.routes.products import router as product_router
from app.api.routes.categories import router as category_router
from app.services.ingestion_service import IngestionService

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Bootstrapping data...")
    db = SessionLocal()
    try:
        IngestionService.bootstrap_data(db)
    finally:
        db.close()

    logger.info("Application startup completed.")
    yield
    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(category_router)
app.include_router(product_router)