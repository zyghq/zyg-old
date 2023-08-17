import abc
import json

from pydantic import BaseModel
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql import text

from src.domain.models import Issue

from .entities import SlackEventEntity


class AbstractSlackEventRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, slack_event: SlackEventEntity):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, event_id: str):
        raise NotImplementedError


class SlackEventRepository(AbstractSlackEventRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    async def add(self, slack_event: SlackEventEntity):
        query = f"""
        insert into slack_event (event_id, token, team_id, api_app_id,
            event, type, event_context, event_time)
        values (:event_id, :token, :team_id, :api_app_id,
            :event, :type, :event_context, :event_time)
        returning event_id, token, team_id, 
            api_app_id, event, type, 
            event_context, event_time,
            created_at, updated_at, is_ack
        """
        values = slack_event.model_dump()
        if isinstance(values["event"], dict):
            values["event"] = json.dumps(values["event"])

        try:
            async with self.engine.begin() as conn:
                rows = await conn.execute(
                    statement=text(query),
                    parameters=values,
                )
                result = rows.mappings().first()
            return None, result
        except Exception as e:
            return e, None

    async def get(self, event_id: str):
        pass


# below code needs to be worked on


# todo: work in progress
class IssueEntity(BaseModel):
    issue_id: str
    title: str
    body: str


# todo: work in progress
class IssueMapper:
    @staticmethod
    def map_to_domain(entity: IssueEntity):
        pass

    @staticmethod
    def map_to_table_entity(issue: Issue):
        pass


# todo: work in progress
class AbstractIssueRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, issue: Issue):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, issue_id: str):
        raise NotImplementedError


# todo: work in progress
class IssueRepository(AbstractIssueRepository):
    def __init__(self, database) -> None:
        self.database = database

    async def add(self, issue: Issue):
        await self.database.connect()
        result = await self.database.execute(
            query=(
                "INSERT INTO issue (issue_id, title, body) "
                "VALUES (:issue_id, :title, :body)"
            ),
            values=dict(issue_id=issue.issue_id, title=issue.title, body=issue.body),
        )
        return result

    async def get(self, issue_id: str):
        await self.database.connect()
        results = await self.database.fetch_all(query="SELECT * FROM issue")
        return results[0]
