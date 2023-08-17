from src.worker import app


# @sanchitrk
# read about tasks bounded tasks here
# https://docs.celeryq.dev/en/latest/userguide/tasks.html#bound-tasks
@app.task
def add(x, y):
    print(f"Adding {x} + {y}")
    return x + y

@app.task
def slack_event_issue_task(event):
    print("*************** inside slack_event_issue ***************")
    print(event)
    print("*************** inside slack_event_issue ***************")
    return event
