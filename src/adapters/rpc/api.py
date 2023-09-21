import logging
from http import HTTPStatus

import httpx
from httpx import Response

from src.application.commands import CreateIssueCommand
from src.config import ZYG_BASE_URL
from src.domain.models import TenantContext

from .exceptions import CreateIssueResponseException, WebAPIResponseException

logger = logging.getLogger(__name__)


class WebAPIBaseConnector:
    def respond(self, response: Response):
        if response.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            return response.json()
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            raise WebAPIResponseException(HTTPStatus.UNAUTHORIZED.name)
        elif response.status_code == HTTPStatus.BAD_REQUEST:
            raise WebAPIResponseException(HTTPStatus.BAD_REQUEST.name)
        elif response.status_code == HTTPStatus.NOT_FOUND:
            raise WebAPIResponseException(HTTPStatus.NOT_FOUND.name)
        elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            raise WebAPIResponseException(HTTPStatus.INTERNAL_SERVER_ERROR.name)
        else:
            raise WebAPIResponseException("API response error - something went wrong.")


class ZygWebAPIConnector(WebAPIBaseConnector):
    def __init__(self, tenant_context: TenantContext, base_url=ZYG_BASE_URL) -> None:
        self.tenant_context = tenant_context
        self.base_url = base_url

    async def create_issue(self, command: CreateIssueCommand) -> dict:
        try:
            response = httpx.post(
                f"{self.base_url}/issues/",
                headers={
                    "content-type": "application/json",
                },
                json={
                    "tenant_id": command.tenant_id,
                    "body": command.body,
                    "status": command.status,
                    "priority": command.priority,
                    "tags": command.tags,
                },
            )
            return self.respond(response)
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
            raise CreateIssueResponseException(
                "Request failed to create issue at HTTP level"
            ) from exc
        except WebAPIResponseException as e:
            logger.error(f"Web API Exception for {e}")
            raise CreateIssueResponseException("Request failed to create issue") from e
        except Exception as e:
            logger.error(f"Exception for {e}")
            raise CreateIssueResponseException("Request failed to create issue") from e
