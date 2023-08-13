import abc

from pydantic import BaseModel

from domain.models import Issue


class IssueEntity(BaseModel):
    issue_id: str
    title: str
    body: str


class IssueMapper:
    @staticmethod
    def map_to_domain(entity: IssueEntity):
        pass

    @staticmethod
    def map_to_table_entity(issue: Issue):
        pass


class AbstractIssueRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, issue: Issue):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, issue_id: str):
        raise NotImplementedError


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
