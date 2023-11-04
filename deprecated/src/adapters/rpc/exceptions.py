class SlackAPIException(Exception):
    pass


class SlackAPIResponseException(SlackAPIException):
    pass


class CreateIssueAPIError(Exception):
    pass


class UserNotFoundAPIError(Exception):
    pass


class FindIssueAPIError(Exception):
    pass


class FindSlackChannelAPIError(Exception):
    pass


class SlackChannelNotFoundAPIError(Exception):
    pass


class FindUserAPIError(Exception):
    pass


class IssueNotFoundAPIError(Exception):
    pass
