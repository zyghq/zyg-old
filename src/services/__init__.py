from pydantic import ValidationError
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine as default_engine
from src.adapters.db.exceptions import DBIntegrityException
from src.adapters.db.respositories import SlackEventRepository
from src.adapters.tasker.tasks import slack_event_issue_task
from src.logger import logger


class SlackEventService:
    def __init__(self, engine: Engine = default_engine) -> None:
        self.engine = engine

    async def capture(self, event: dict) -> None:
        try:
            slack_event = SlackEventRepository.to_entity(event)
        except ValidationError as e:
            logger.error(e)
            return e, None
        try:
            async with self.engine.begin() as conn:
                result = await SlackEventRepository(conn).add(slack_event)
                return None, result
        except DBIntegrityException as e:
            logger.error(e)
            return e, None

    async def capture_with_async_issue(self, event) -> None:
        try:
            slack_event = SlackEventRepository.to_entity(event)
        except ValidationError as e:
            logger.error(e)
            return e, None

        try:
            async with self.engine.begin() as conn:
                result = await SlackEventRepository(conn).add(slack_event)
                slack_event_issue_task.delay(event)
                return None, result
        except DBIntegrityException as e:
            logger.error(e)
            return e, None
