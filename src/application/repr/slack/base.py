import json

# TODO: non required once we have integrated the datetime attributes from Issue model.
from datetime import datetime

import pytz
from jinja2 import Template

from src.domain.models import Issue

from .blocks import CREATE_ISSUE_TEMPLATE_BLOCK  # TODO: move away from jinja.


class BlockBuilder:
    def __init__(self) -> None:
        self._blocks = []

    def section(self, text: dict):
        item = {
            "type": "section",
            "text": text,
        }
        self._blocks.append(item)

    def divider(self):
        self._blocks.append({"type": "divider"})

    def actions(self, elements: list):
        self._blocks.append({"type": "actions", "elements": elements})

    @staticmethod
    def text(text: str, type: str = "mrkdwn", emoji: bool = True):
        return {"type": type, "text": text}

    @property
    def blocks(self) -> list:
        return self._blocks


def issue_message_blocks_repr(issue: Issue):
    template = Template(CREATE_ISSUE_TEMPLATE_BLOCK)
    rendered_template = template.render(
        status=issue.status_display_name,
        issue_number=issue.issue_number,
        text=issue.body,
        priority=issue.priority_display_name,
    )

    rendered = json.loads(rendered_template, strict=False)
    return rendered["blocks"]


def issue_message_text_repr(issue: Issue):
    return f"{issue.body[:512]}..."


def nudge_issue_text_repr(name: str):
    return f"""Hi 👋 {name},
    Do you want to open a ticket with the support team?
    In the future, you can react to your support query with a :ticket: emoji
    to immediately open a issue ticket."""


def nudge_issue_blocks_repr(name: str):
    block = BlockBuilder()
    block.section(
        BlockBuilder.text(
            text=f"Hi :wave: {name},",
        )
    )
    block.section(
        BlockBuilder.text(
            text="Do you want to open a ticket with the support team?",
        )
    )
    block.section(
        BlockBuilder.text(
            text="In the future you can react to your support query with a "
            + ":ticket: emoji to immediately open a ticket.",
        )
    )
    return block.blocks


def issue_opened_reply_text_repr(slack_user_ref: str):
    # TODO:  get the timezone info from the Tenant or the User.
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    formatted = now.strftime("%d %b %Y at %I:%M %p")
    return f"""<@{slack_user_ref}> has opened an issue ticket On {formatted}"""


def issue_opened_reply_blocks_repr(slack_user_ref: str, issue_number: int):
    # TODO:  get the timezone info from the Tenant or the User.
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    formatted = now.strftime("%d %b %Y at %I:%M %p")
    block = BlockBuilder()
    block.section(
        BlockBuilder.text(
            text=f"<@{slack_user_ref}> has opened an issue ticket.",
        )
    )
    block.section(
        BlockBuilder.text(
            text=f":ticket: *Issue #{issue_number}* | _{formatted}_",
        )
    )
    elements = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Close Issue", "emoji": True},
            "value": "click_close_issue",
            "action_id": "action_close_issue",
        }
    ]
    block.actions(elements=elements)
    return block.blocks


def issue_closed_reply_text_repr(slack_user_ref: str):
    # TODO:  get the timezone info from the Tenant or the User.
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    formatted = now.strftime("%d %b %Y at %I:%M %p")
    return f"""<@{slack_user_ref}> has closed the issue On {formatted}"""


def issue_closed_reply_blocks_repr(slack_user_ref: str, issue_number: int):
    # TODO:  get the timezone info from the Tenant or the User.
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    formatted = now.strftime("%d %b %Y at %I:%M %p")
    block = BlockBuilder()
    block.section(
        BlockBuilder.text(
            text=f"<@{slack_user_ref}> has closed the issue.",
        )
    )
    block.section(
        BlockBuilder.text(
            text=f":ticket: *Issue #{issue_number}* | _{formatted}_",
        )
    )
    elements = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Reopen Issue", "emoji": True},
            "value": "click_reopen_issue",
            "action_id": "action_reopen_issue",
        }
    ]
    block.actions(elements=elements)
    return block.blocks
