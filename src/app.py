import logging

from fastapi import FastAPI
from sqlalchemy.sql import text

from src.config import engine
from src.web.routers import accounts, workspaces

app = FastAPI()

logger = logging.getLogger(__name__)


app.include_router(
    accounts.router,
    prefix="/accounts",
)


app.include_router(
    workspaces.router,
    prefix="/workspaces",
)


@app.get("/")
async def root():
    logger.info("Hey there! I am zyg.")
    return {"message": "Hey there! I am zyg."}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        query = text("SELECT NOW()::timestamp AS now")
        rows = await conn.execute(query)
        result = rows.mappings().first()
        logger.info(f"db connected at: {result['now']}")


@app.on_event("shutdown")
async def shutdown():
    logger.warning("cleaning up...")
    await engine.dispose()
