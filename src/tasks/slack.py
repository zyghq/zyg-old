import asyncio
import logging
from datetime import datetime
from typing import Dict

import sqlalchemy as db
from celery import chain

from src.config import engine, worker
from src.db.repository import (
    SlackBotRepository,
    SlackChannelRepository,
    SlackWorkspaceRepository,
)
from src.db.schema import SlackBotDB, SlackWorkspaceDB
from src.ext.slack import SlackWebAPIConnector
from src.models.account import Account, Workspace
from src.models.slack import SlackBot, SlackChannel, SlackWorkspace

logger = logging.getLogger(__name__)


# We can also setup up pipeline for our provisioning Slack workspace tasks
# Reference:
#   https://blog.det.life/replacing-celery-tasks-inside-a-chain-b1328923fb02
#   https://docs.celeryq.dev/en/latest/userguide/canvas.html#chains


@worker.task(bind=True)
def authenticate(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run() -> dict:
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

        slack_workspace = SlackWorkspace.from_dict(
            workspace_id=workspace.workspace_id, values=result
        )
        slack_bot = SlackBot.from_dict(slack_workspace=slack_workspace, values=result)

        slack_api = SlackWebAPIConnector(slack_bot)
        response = slack_api.authenticate()

        slack_workspace.url = response.url
        slack_bot.bot_ref = response.bot_id  # this is from Slack API response

        async with engine.begin() as connection:
            slack_workspace = await SlackWorkspaceRepository(
                connection
            ).upsert_by_workspace(slack_workspace)
            slack_bot = await SlackBotRepository(connection).upsert_by_slack_workspace(
                slack_bot
            )

        logger.info(f"Provisioned Slack workspace: {slack_workspace}")
        logger.info(f"Provisioned Slack bot: {slack_bot}")

        result = {
            "workspace_id": workspace.workspace_id,
            "slack_workspace_ref": slack_workspace.ref,
            "slack_workspace_name": slack_workspace.name,
            "slack_workspace_status": slack_workspace.status,
            "bot_id": slack_bot.bot_id,
            "bot_user_ref": slack_bot.bot_user_ref,
            "bot_ref": slack_bot.bot_ref,
            "bot_access_token": slack_bot.access_token,
        }
        return result

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    return result


@worker.task(bind=True)
def workspace_status_ready(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run():
        ref = context["slack_workspace_ref"]
        query = (
            db.update(SlackWorkspaceDB)
            .where(SlackWorkspaceDB.c.ref == ref)
            .values(
                status=SlackWorkspace.status_ready(),
                updated_at=db.func.now(),
            )
        )
        async with engine.begin() as connection:
            await connection.execute(query)
        return True

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    logger.info(f"set status ready result: {result}")
    return context


@worker.task(bind=True)
def sync_workspace_status_syncing(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run():
        ref = context["slack_workspace_ref"]
        query = (
            db.update(SlackWorkspaceDB)
            .where(SlackWorkspaceDB.c.ref == ref)
            .values(
                sync_status=SlackWorkspace.sync_status_syncing(),
                updated_at=db.func.now(),
            )
        )
        async with engine.begin() as connection:
            await connection.execute(query)
        return True

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    logger.info(f"sync status syncing result: {result}")
    return context


@worker.task(bind=True)
def sync_public_channels(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run() -> dict:
        workspace_id = context["workspace_id"]
        slack_workspace_ref = context["slack_workspace_ref"]
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
                .where(SlackWorkspaceDB.c.ref == slack_workspace_ref)
            )
            rows = await connection.execute(query)
            result = rows.mappings().first()

            slack_workspace = SlackWorkspace.from_dict(
                workspace_id=workspace_id, values=result
            )
            slack_bot = SlackBot.from_dict(
                slack_workspace=slack_workspace, values=result
            )

        slack_api = SlackWebAPIConnector(slack_bot)
        channels = slack_api.get_channels()
        synced_at = datetime.utcnow()

        async with engine.begin() as connection:
            repo = SlackChannelRepository(connection)
            items = []
            for channel in channels:
                slack_channel = await repo.find_by_slack_workspace_channel_ref(
                    slack_workspace=slack_workspace, channel_ref=channel.id
                )
                if not slack_channel:
                    values = channel.model_dump()
                    values["status"] = SlackChannel.status_mute()
                    values["synced_at"] = synced_at
                    slack_channel = SlackChannel.from_dict(
                        slack_workspace=slack_workspace, values=values
                    )
                    slack_channel = await repo.upsert_by_slack_workspace_channel_ref(
                        slack_channel,
                    )
                items.append(slack_channel)
            return items

    loop = asyncio.get_event_loop()
    channels = loop.run_until_complete(run())
    logger.info(f"synced public channels: {len(channels)}")
    return context


@worker.task(bind=True)
def provision_pipeline(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    return chain(
        authenticate.s(context),
        workspace_status_ready.s(),
        sync_workspace_status_syncing.s(),
        sync_public_channels.s(),
    ).apply_async()
