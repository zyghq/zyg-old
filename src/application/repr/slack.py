from src.domain.models import Issue


def issue_message_repr(issue: Issue):
    body = issue.body
    issue_id = issue.issue_id
    issue_number = issue.issue_number
    message = f"{body} with issue_id: {issue_id} issue_number: {issue_number}"  # XXX: wip # noqa
    return message
