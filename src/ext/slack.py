from pydantic import BaseModel

from src.models.slack import SlackBot

from .base import SlackWebAPI


class AuthenticateResponse(BaseModel):
    """
    {
        "ok": True,
        "url": "https://zyghq.slack.com/",
        "team": "ZygHQ",
        "user": "zyg_dev",
        "team_id": "T03NX4VMCRH",
        "user_id": "U05LDJGBRPX",
        "bot_id": "B05LJVC8PEY",
        "is_enterprise_install": False
    }
    """

    ok: bool
    url: str
    team: str
    user: str
    team_id: str
    user_id: str
    bot_id: str
    is_enterprise_install: bool | None = None
    enterprise_id: str | None = None


class TeamItemResponse(BaseModel):
    id: str
    name: str
    url: str
    domain: str
    email_domain: str
    icon: dict
    avatar_base_url: str
    is_verified: bool


class TeamInfoResponse(BaseModel):
    """
    {
        "ok": True,
        "team": {
            "id": "T03NX4VMCRH",
            "name": "ZygHQ",
            "url": "https://zyghq.slack.com/",
            "domain": "zyghq",
            "email_domain": "",
            "icon": {
                "image_default": True,
                "image_34": "https://...",
                "image_44": "https://...",
                "image_68": "https://...",
                "image_88": "https://...",
                "image_102": "https://...",
                "image_230": "https"//...",
                "image_132": "https://...",
            },
            "avatar_base_url": "https://ca.slack-edge.com/",
            "is_verified": False,
        },
    }
    """

    ok: bool
    team: TeamItemResponse


class SlackWebAPIConnector(SlackWebAPI):
    def __init__(self, bot: SlackBot) -> None:
        self.bot = bot
        super().__init__(bot.access_token)

    def authenticate(self) -> AuthenticateResponse:
        response = self.auth_test()
        return AuthenticateResponse(
            ok=response["ok"],
            url=response["url"],
            team=response["team"],
            user=response["user"],
            team_id=response["team_id"],
            user_id=response["user_id"],
            bot_id=response["bot_id"],
            is_enterprise_install=response.get("is_enterprise_install", None),
            enterprise_id=response.get("enterprise_id", None),
        )

    def get_team_info(self) -> TeamItemResponse:
        response = self.team_info()
        response = TeamInfoResponse(**response)
        return response.team
