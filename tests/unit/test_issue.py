from src.domain.models import Issue, Requester, Assignee


def create_issue(title, body):
    requester = Requester("requester-1", "requester@zyg.ai")
    return Issue(requester=requester, title=title, body=body)


def test_create_issue_by_requester():
    title = "I, am having an issue with the login."
    body = "I tried loggging into the app, but I am not able to. Please help."
    issue = create_issue(title=title, body=body)

    assert issue.title == title
    assert issue.body == body


def test_create_issue_with_agent_assignment():
    title = "oops! something went wrong!"
    body = "I cannot send emails. Please help."
    issue = create_issue(title=title, body=body)

    agent_email = "sanchit@zyg.ai"
    agent = Assignee("assignee-1", agent_email)
    issue.assign(assignee=agent)

    assert issue.assignee.email == agent_email


def test_issue_equality_without_identifier():
    title = "oops"
    body = "something went wrong"
    issue = create_issue(title=title, body=body)
    issue2 = create_issue(title=title, body=body)

    is_same = issue == issue2
    assert is_same is False
