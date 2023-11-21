import asyncio
import logging
from typing import Dict

import sqlalchemy as db
from celery import chain

from src.config import engine, worker
from src.db.repository import SlackBotRepository, SlackWorkspaceRepository
from src.db.schema import SlackBotDB, SlackWorkspaceDB
from src.ext.slack import SlackWebAPIConnector
from src.models.account import Account, Workspace
from src.models.slack import SlackBot, SlackWorkspace

logger = logging.getLogger(__name__)


# We can also setup up pipeline for our provisioning Slack workspace tasks
# Reference:
#   https://blog.det.life/replacing-celery-tasks-inside-a-chain-b1328923fb02
#   https://docs.celeryq.dev/en/latest/userguide/canvas.html#chains
#


def pipeline_logger(self):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")


@worker.task(bind=True)
def slack_authenticate(self, context: Dict):
    pipeline_logger(self)

    async def run() -> str:
        account = context["account"]
        workspace = context["workspace"]

        account = Account.from_dict(account)
        workspace = Workspace.from_dict(account, workspace)

        async with engine.begin() as connection:
            query = (
                db.select(
                    SlackWorkspaceDB.c.ref,
                    SlackWorkspaceDB.c.url,
                    SlackWorkspaceDB.c.name,
                    SlackWorkspaceDB.c.status,
                    SlackWorkspaceDB.c.created_at,
                    SlackWorkspaceDB.c.updated_at,
                    SlackBotDB.c.bot_id,
                    SlackBotDB.c.bot_user_ref,
                    SlackBotDB.c.bot_ref,
                    SlackBotDB.c.app_ref,
                    SlackBotDB.c.scope,
                    SlackBotDB.c.access_token,
                )
                .select_from(
                    db.join(
                        SlackWorkspaceDB,
                        SlackBotDB,
                        SlackWorkspaceDB.c.ref == SlackBotDB.c.slack_workspace_ref,
                    )
                )
                .where(SlackWorkspaceDB.c.workspace_id == workspace.workspace_id)
            )
            rows = await connection.execute(query)
            result = rows.mappings().first()

        slack_workspace = SlackWorkspace.from_dict(workspace, result)
        slack_bot = SlackBot.from_dict(slack_workspace, result)

        slack_api = SlackWebAPIConnector(slack_bot)
        response = slack_api.authenticate()

        slack_workspace.url = response.url
        slack_bot.bot_ref = response.bot_id

        async with engine.begin() as connection:
            repo = SlackWorkspaceRepository(connection)
            slack_workspace = await repo.upsert_by_workspace(slack_workspace)
            repo = SlackBotRepository(connection)
            slack_bot = await repo.upsert_by_workspace(slack_bot)

        logger.info(f"Provisioned Slack workspace: {slack_workspace}")
        logger.info(f"Provisioned Slack bot: {slack_bot}")

        result = {
            "workspace_id": workspace.workspace_id,
            "ref": slack_workspace.ref,
            "name": slack_workspace.name,
            "status": slack_workspace.status,
            "slack_bot_bot_id": slack_bot.bot_id,
            "slack_bot_bot_user_ref": slack_bot.bot_user_ref,
            "slack_bot_bot_ref": slack_bot.bot_ref,
            "slack_bot_access_token": slack_bot.access_token,
        }
        return result

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    return result


@worker.task(bind=True)
def slack_ready(self, context: Dict):
    pipeline_logger(self)

    async def run():
        ref = context["ref"]
        query = (
            db.update(SlackWorkspaceDB)
            .where(SlackWorkspaceDB.c.ref == ref)
            .values(
                status=SlackWorkspace.get_status_ready(),
                updated_at=db.func.now(),
            )
        )
        async with engine.begin() as connection:
            await connection.execute(query)
        return True

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    return result


@worker.task(bind=True)
def slack_provision_pipeline(self, context: Dict):
    pipeline_logger(self)

    return chain(
        slack_authenticate.s(context),
        slack_ready.s(),
    ).apply_async()
