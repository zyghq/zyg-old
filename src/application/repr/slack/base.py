import json

from jinja2 import Template

from src.domain.models import Issue

from .blocks import CREATE_ISSUE_TEMPLATE_BLOCK


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
    return f"{issue.body}[:128]... with {issue.priority}"
