from fastapi import FastAPI
from sqlalchemy.sql import text

from src.adapters.db import engine
from src.logger import logger

from .routers import channels, events, inbox

app = FastAPI()


app.include_router(
    events.router,
    prefix="/events",
)

app.include_router(
    channels.router,
    prefix="/channels",
)

app.include_router(
    inbox.router,
    prefix="/inbox",
)


@app.get("/")
async def root():
    return {"message": "Hey there! I am willow."}


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
