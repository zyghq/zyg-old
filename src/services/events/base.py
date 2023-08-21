from pydantic import ValidationError
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine as default_engine
from src.adapters.db.entities import SlackEventDbEntity
from src.adapters.db.exceptions import DBIntegrityException
from src.adapters.db.respositories import SlackEventRepository
from src.logger import logger

from .exceptions import SlackEventEntityValidation, SlackEventDBException


class SlackEventCaptureService:
    def __init__(self, engine: Engine = default_engine) -> None:
        self.engine = engine

    async def capture(self, event: dict, override=False) -> SlackEventDbEntity:
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
                if override:
                    logger.warning(
                        f"override slack event for event_id: `{event.get('event_id')}`"
                    )
                    result = await SlackEventRepository(conn).upsert(new_db_entity)
                else:
                    result = await SlackEventRepository(conn).add(new_db_entity)
            return result
        except DBIntegrityException as e:
            logger.error(e)
            raise SlackEventDBException("error when capturing slack event.")
        except ValidationError as e:
            logger.error(e)
            raise SlackEventEntityValidation("error when validating slack event.")
