from src.worker import app
from slack_sdk import WebClient


# @sanchitrk
# read about tasks bounded tasks here
# https://docs.celeryq.dev/en/latest/userguide/tasks.html#bound-tasks
@app.task
def add(x, y):
    print(f"Adding {x} + {y}")
    return x + y


@app.task
def create_in_slack_issue_task(event):
    print("*************** inside task ***************")
    print(event)
    print("*************** inside task ***************")
    return True


@app.task
def sync_channels_by(team):
    print("*************** sync channels by team ***************")
    print(team)
    print("*************** sync channels by team ***************")
    return True
