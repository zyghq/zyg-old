from src.domain.models import Inbox, SlackChannel


def test_create_inbox():
    inbox_id = "inbox-1"
    name = "Support Inbox"
    description = "Support Inbox for Willow"
    inbox = Inbox(inbox_id=inbox_id, name=name, description=description)
    assert inbox.inbox_id == inbox_id
    assert inbox.name == name
    assert inbox.description == description


def test_inbox_equality_with_identifier():
    name = "Support Inbox"
    description = "Support Inbox for Willow"
    inbox_id = "inbox-1"

    inbox = Inbox(inbox_id=inbox_id, name=name, description=description)
    inbox2 = Inbox(inbox_id=inbox_id, name=name, description=description)

    is_same = inbox == inbox2
    assert is_same is True


def test_inbox_equality_with_diff_identifier():
    name = "Support Inbox"
    description = "Support Inbox for Willow"
    inbox_id = "inbox-1"
    inbox_id2 = "inbox-2"

    inbox = Inbox(inbox_id=inbox_id, name=name, description=description)
    inbox2 = Inbox(inbox_id=inbox_id2, name=name, description=description)

    is_same = inbox == inbox2
    assert is_same is False


def test_inbox_with_channel():
    inbox_id = "inbox-1"
    name = "Support Inbox"
    description = "Support Inbox for Willow"
    inbox = Inbox(inbox_id=inbox_id, name=name, description=description)

    channel_id = "channel-1"
    slack_channel = SlackChannel(channel_id=channel_id)

    inbox.link_channel(channel=slack_channel)
    assert inbox.slack_channel == slack_channel
