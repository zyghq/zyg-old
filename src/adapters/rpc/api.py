import logging
from http import HTTPStatus

import httpx
from httpx import Response

from src.application.commands import (
    CreateIssueCommand,
    GetSlackChannelByRefCommand,
    GetUserByRefCommand,
)
from src.config import ZYG_BASE_URL
from src.domain.models import TenantContext

from .exceptions import (
    CreateIssueAPIException,
    SlackChannelAPIException,
    SlackChannelNotFoundResponseException,
    UserAPIException,
    UserNotFoundResponseException,
    WebAPIException,
)

logger = logging.getLogger(__name__)


class WebAPIBaseConnector:
    def respond(self, response: Response):
        if response.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            return response.json()
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            raise WebAPIException(HTTPStatus.UNAUTHORIZED.name)
        elif response.status_code == HTTPStatus.BAD_REQUEST:
            raise WebAPIException(HTTPStatus.BAD_REQUEST.name)
        elif response.status_code == HTTPStatus.NOT_FOUND:
            raise WebAPIException(HTTPStatus.NOT_FOUND.name)
        elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            raise WebAPIException(HTTPStatus.INTERNAL_SERVER_ERROR.name)
        else:
            raise WebAPIException("API response error - something went wrong.")


class ZygWebAPIConnector(WebAPIBaseConnector):
    def __init__(self, tenant_context: TenantContext, base_url=ZYG_BASE_URL) -> None:
        self.tenant_context = tenant_context
        self.base_url = base_url

    async def create_issue(self, command: CreateIssueCommand) -> dict:
        try:
            response = httpx.post(
                f"{self.base_url}/issues/",
                headers={
                    "content-type": "application/json",
                },
                json={
                    "tenant_id": command.tenant_id,
                    "slack_channel_id": command.slack_channel_id,
                    "slack_message_ts": command.slack_message_ts,
                    "body": command.body,
                    "status": command.status,
                    "priority": command.priority,
                    "tags": command.tags,
                },
            )
            return self.respond(response)
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
            raise CreateIssueAPIException(
                "Request failed to create issue at HTTP level"
            ) from exc
        except WebAPIException as e:
            logger.error(f"Web API Exception for {e}")
            raise CreateIssueAPIException("Request failed to create issue") from e

    async def find_slack_channel_by_ref(
        self, command: GetSlackChannelByRefCommand
    ) -> dict | None:
        """
        With find we dont raise an error we just return None if not found.
        Unlike get we raise an error if not found.
        """
        try:
            response = httpx.post(
                f"{self.base_url}/tenants/channels/linked/:search/",
                headers={
                    "content-type": "application/json",
                },
                json={
                    "slack_channel_ref": command.slack_channel_ref,
                },
            )
            items = self.respond(response)
            if len(items) == 0:
                return None
            return items[0]
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
            raise SlackChannelAPIException(
                "Request failed to get slack channel by reference at HTTP level"
            ) from exc
        except WebAPIException as exc:
            logger.error(f"Web API Exception for {exc}")
            raise SlackChannelAPIException(
                "Request failed to get slack channel by reference"
            ) from exc

    async def get_slack_channel_by_ref(
        self, command: GetSlackChannelByRefCommand
    ) -> dict:
        """
        With get we raise an error if not found.
        Unlike find we just return None if not found.
        """
        item = await self.find_slack_channel_by_ref(command)
        if item is None:
            raise SlackChannelNotFoundResponseException(
                "No slack channel found for the reference"
            )
        return item

    async def find_user_by_slack_ref(self, command: GetUserByRefCommand) -> dict | None:
        """
        With find we dont raise an error we just return None if not found.
        Unlike get we raise an error if not found.
        """
        try:
            response = httpx.post(
                f"{self.base_url}/tenants/users/:search/",
                headers={
                    "content-type": "application/json",
                },
                json={
                    "slack_user_ref": command.slack_user_ref,
                },
            )
            items = self.respond(response)
            if len(items) == 0:
                return None
            return items[0]
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
            raise UserAPIException(
                "Request failed to get user by reference at HTTP level"
            ) from exc
        except WebAPIException as e:
            logger.error(f"Web API Exception for {e}")
            raise UserAPIException("Request failed to get user by reference") from e

    async def get_user_by_slack_ref(self, command: GetUserByRefCommand) -> dict:
        """
        With get we raise an error if not found.
        Unlike find we just return None if not found.
        """
        item = await self.find_user_by_slack_ref(command)
        if item is None:
            raise UserNotFoundResponseException("No user found for the reference")
        return item
