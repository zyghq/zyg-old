from pydantic import ValidationError
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine as default_engine
from src.adapters.db.entities import SlackEventDbEntity
from src.adapters.db.exceptions import DBIntegrityException
from src.adapters.db.respositories import SlackEventRepository
from src.adapters.tasker.tasks import create_in_slack_issue_task
from src.logger import logger

from .exceptions import SlackCaptureException


class SlackEventService:
    def __init__(self, engine: Engine = default_engine) -> None:
        self.engine = engine

    async def capture(self, event: dict) -> SlackEventDbEntity:
        try:
            new_db_entity = SlackEventDbEntity(
                event_id=event.get("event_id"),
                team_id=event.get("team_id"),
                event=event.get("event"),
                event_type=event.get("event_type"),
                event_ts=event.get("event_ts"),
                metadata=event.get("metadata"),
                created_at=None,
                updated_at=None,
                is_ack=False,
            )
            async with self.engine.begin() as conn:
                result = await SlackEventRepository(conn).add(new_db_entity)
            return result
        except DBIntegrityException as e:
            logger.error(e)
            raise SlackCaptureException("error when capturing slack event.")
        except ValidationError as e:
            logger.error(e)
            raise SlackCaptureException("error when validating slack event.")

    async def capture_and_schedule_task_issue(self, event: dict) -> SlackEventDbEntity:
        try:
            new_db_entity = SlackEventDbEntity(
                event_id=event.get("event_id"),
                team_id=event.get("team_id"),
                event=event.get("event"),
                event_type=event.get("event_type"),
                event_ts=event.get("event_ts"),
                metadata=event.get("metadata"),
                created_at=None,
                updated_at=None,
                is_ack=False,
            )
            async with self.engine.begin() as conn:
                result = await SlackEventRepository(conn).add(new_db_entity)
                task_event_payload = result.model_dump()
                # send the persisted event to the tasker
                # to handle this event asynchronously
                # without blocking the main execution flow
                create_in_slack_issue_task.delay(task_event_payload)
            return result
        except DBIntegrityException as e:
            logger.error(e)
            raise SlackCaptureException("error when capturing slack event.")
        except ValidationError as e:
            logger.error(e)
            raise SlackCaptureException("error when validating slack event.")
