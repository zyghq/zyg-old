import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr

from src.application.commands import TenantProvisionCommand
from src.application.exceptions import SlackTeamReferenceException
from src.application.repr.api import TenantRepr
from src.services.tenant import TenantProvisionService

logger = logging.getLogger(__name__)

router = APIRouter()


class ProvisionTenantRequestBody(BaseModel):
    name: constr(min_length=3)
    slack_team_ref: str


@router.post("/tenants/")
async def tenant(request_body: ProvisionTenantRequestBody):
    command = TenantProvisionCommand(
        name=request_body.name,
        slack_team_ref=request_body.slack_team_ref,
    )

    try:
        tenant_provision_service = TenantProvisionService()
        tenant = await tenant_provision_service.provision(command)
    except SlackTeamReferenceException as e:
        logger.warning(
            f"slack team ref `{command.slack_team_ref}` "
            f"is already mapped to a tenant {e}"
        )
        return JSONResponse(
            status_code=409,
            content={
                "errors": [
                    {
                        "status": 409,
                        "title": "Conflict",
                        "detail": "slack team ref is already mapped to a tenant.",
                    }
                ]
            },
        )
    except Exception as e:
        logger.error(f"error provisioning tenant {e}")
        return JSONResponse(
            status_code=503,
            content={
                "errors": [
                    {
                        "status": 503,
                        "title": "Service Unavailable",
                        "detail": "unable to provision tenant.",
                    }
                ]
            },
        )

    response = TenantRepr(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slack_team_ref=tenant.slack_team_ref,
    )

    return response
