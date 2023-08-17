from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import POSTGRES_URI

engine: Engine = create_async_engine(
    POSTGRES_URI,
    future=True,
    echo=True,
)
