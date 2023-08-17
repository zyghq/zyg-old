from pydantic import ValidationError
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine as default_engine
from src.adapters.db.exceptions import DBIntegrityException
from src.adapters.db.respositories import SlackEventRepository
from src.logger import logger


class SlackEventService:
    def __init__(self, engine: Engine = default_engine) -> None:
        self.engine = engine

    async def capture(self, event: dict) -> None:
        try:
            slack_event = SlackEventRepository.to_slack_event_entity(event)
        except ValidationError as e:
            return e, None

        try:
            async with self.engine.begin() as conn:
                result = await SlackEventRepository(conn).add(slack_event)
                return None, result
        except DBIntegrityException as e:
            logger.error(e)
            return e, None

    def create_issue(self, event) -> None:
        pass
