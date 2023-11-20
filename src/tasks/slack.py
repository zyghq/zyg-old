import asyncio
import logging
from typing import Dict

import sqlalchemy as db

from src.config import engine, worker
from src.db.repository import SlackBotRepository, SlackWorkspaceRepository
from src.db.schema import SlackBotDB, SlackWorkspaceDB
from src.ext.slack import SlackWebAPIConnector
from src.models.account import Account, Workspace
from src.models.slack import SlackBot, SlackWorkspace

logger = logging.getLogger(__name__)


@worker.task(bind=True, name="zyg.provision_slack_workspace")
def provision_slack_workspace(self, context: Dict):
    async def run():
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
            slack_workspace = await repo.upsert(slack_workspace)
            repo = SlackBotRepository(connection)
            slack_bot = await repo.upsert_by_workspace(slack_bot)

        logger.info(f"Provisioned Slack workspace: {slack_workspace}")
        logger.info(f"Provisioned Slack bot: {slack_bot}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    return True
