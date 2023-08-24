import pytest

from src.adapters.db.entities import SlackEventDBEntity
from src.services.event import SlackEventService

# from src.domain.models import SlackCallbackEvent
# from src.services.exceptions import SlackCaptureException


def generate_slack_callback_event():
    return dict(
        event_id="Ev12345678",
        team_id="T12345678",
        event_type="event_callback",
        event={
            "type": "message",
            "user": "U12345678",
            "text": "Hello world",
        },
        event_ts=1691953744,
    )


@pytest.mark.asyncio
async def test_service_event_capture():
    slack_event_service = SlackEventService()
    slack_callback_event = generate_slack_callback_event()
    result = await slack_event_service.capture(slack_callback_event)

    assert isinstance(result, SlackEventDBEntity)
    assert result.event_id == slack_callback_event.get("event_id")
    assert result.team_id == slack_callback_event.get("team_id")
    assert result.created_at is not None
    assert result.updated_at is not None


@pytest.mark.asyncio
async def test_service_event_capture_with_scheduled_task():
    slack_event_service = SlackEventService()
    slack_callback_event = generate_slack_callback_event()
    result = await slack_event_service.capture_and_schedule_task_issue(
        slack_callback_event
    )

    assert isinstance(result, SlackEventDBEntity)
    assert result.event_id == slack_callback_event.get("event_id")
    assert result.team_id == slack_callback_event.get("team_id")
    assert result.created_at is not None
    assert result.updated_at is not None


# @pytest.mark.asyncio
# async def test_event_capture_service_with_exception():
#     slack_event_service = SlackEventService()
#     slack_callback_event = generate_slack_callback_event()
#     with pytest.raises(SlackCaptureException) as e:
#         result = await slack_event_service.capture(slack_callback_event)
#         slack_event_service = SlackEventService()
#         assert isinstance(result, SlackEventDbEntity)
#         assert result.event_id == slack_callback_event.event_id
#         assert result.team_id == slack_callback_event.team_id
