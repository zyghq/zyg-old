from pydantic import BaseModel, constr

from .base import CreateIssueCommand


class CreateIssueAPICommand(CreateIssueCommand):
    pass


class FindSlackChannelByRefAPICommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


class FindUserByRefAPICommand(BaseModel):
    tenant_id: str
    slack_user_ref: constr(min_length=3, max_length=255, to_lower=True)


class FindIssueBySlackChannelIdMessageTsAPICommand(BaseModel):
    tenant_id: str
    slack_channel_id: str
    slack_message_ts: str
