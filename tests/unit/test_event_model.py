from src.domain.models import SlackCallbackEvent


def make_slack_event(event_id, team_id):
    return SlackCallbackEvent(
        event_id=event_id,
        team_id=team_id,
        event_type="event_type-1",
        event={
            "text": "Hello world",
        }
    )


def test_slack_event():
    event_id = "event-1"
    team_id = "team-1"
    event_type = "event_type-1"
    event = {
        "text": "Hello world",
        "user": "U12345678",
    }
    slack_event = SlackCallbackEvent(
        event_id=event_id, team_id=team_id, event_type=event_type, event=event
    )
    assert slack_event.event_id == event_id
    assert slack_event.team_id == team_id
    assert slack_event.event_type == event_type
    assert slack_event.event == event


def test_slack_event_equality_with_identifier():
    slack_event = make_slack_event(event_id="event-1", team_id="team-1")
    slack_event2 = make_slack_event(event_id="event-1", team_id="team-1")

    assert slack_event == slack_event2

def test_slack_event_equality_with_diff_identifier():
    slack_event = make_slack_event(event_id="event-1", team_id="team-1")
    slack_event2 = make_slack_event(event_id="event-2", team_id="team-2")

    assert slack_event != slack_event2

def test_slack_event_equality_without_identifier():
    slack_event = make_slack_event(event_id=None, team_id="team-1")
    slack_event2 = make_slack_event(event_id=None, team_id="team-2")

    assert slack_event == slack_event2
