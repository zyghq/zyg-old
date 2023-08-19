from src.worker import app
from src.services import SlackService


# @sanchitrk
# read about tasks bounded tasks here
# https://docs.celeryq.dev/en/latest/userguide/tasks.html#bound-tasks
@app.task
def add(x, y):
    print(f"Adding {x} + {y}")
    return x + y

@app.task
def create_in_slack_issue_task(event):
    print("*************** inside slack_event_issue ***************")
    print(event)
    print('type of event is: ', type(event))
    print("*************** inside slack_event_issue ***************")
    slack_service = SlackService()
    slack_service.send_message(event)
    return event
