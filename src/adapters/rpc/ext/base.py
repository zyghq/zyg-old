import logging
from typing import Dict, List

from slack_sdk import WebClient
from slack_sdk.errors import SlackClientError

from .exceptions import SlackAPIException, SlackAPIResponseException

logger = logging.getLogger(__name__)


class SlackWebAPI:
    def __init__(self, token: str) -> None:
        self._client = WebClient(token=token)

    def chat_post_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict] | None = None,
        thread_ts: str | None = None,
        metadata: dict | None = None,
    ):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/chat.postMessage
        """
        logger.info(f"invoked `chat_post_message` with args: {channel}")
        try:
            response = self._client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                metadata=metadata,
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def users_list(self, limit=200):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/users.list

        """
        logger.info(f"invoked `users_list` with args: {limit}")
        try:
            response = self._client.users_list(limit=limit)
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def chat_post_ephemeral(
        self,
        channel: str,
        user: str,
        text: str,
        blocks: List[Dict] | None = None,
        metadata=None,
    ):
        logger.info(f"invoked `chat_post_ephemeral` for args: {channel, user}")
        try:
            response = self._client.chat_postEphemeral(
                channel=channel, user=user, text=text, blocks=blocks, metadata=metadata
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def conversation_list(self, types: str = "public_channels"):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.list

        :param types: comma separated list of types to include in the response
        """
        logger.info(f"invoked `conversation_list` for args: {types}")
        try:
            response = self._client.conversations_list(types=types)
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def conversation_history(
        self,
        channel: str,
        inclusive: bool | None = None,
        limit: int | None = None,
        oldest: str | None = None,
    ):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.history

        """
        logger.info(
            "invoked `conversation_history` "
            + f"for args: {channel, inclusive, limit, oldest}"
        )
        try:
            response = self._client.conversations_history(
                channel=channel, oldest=oldest, limit=limit, inclusive=inclusive
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def chat_update(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: List[Dict],
        metadata: dict | None = None,
    ):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/chat.update
        """
        logger.info("invoked `chat_update` " + f"for args: {channel, ts}")
        try:
            response = self._client.chat_update(
                channel=channel, text=text, blocks=blocks, ts=ts, metadata=metadata
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response
