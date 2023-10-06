import json

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


def nudge_issue_message_blocks_repr(name: str):
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


def nudge_issue_message_text_repr(name: str):
    return f"""Hi 👋 {name},
    Do you want to open a ticket with the support team?
    In the future, you can react to your support query with a :ticket: emoji
    to immediately open a issue ticket."""
