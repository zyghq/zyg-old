from pydantic import BaseModel

from src.models.slack import SlackBot
from typing import List

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


class SlackConversationItemResponse(BaseModel):
    """
    {
        'context_team_id': 'T03NX4VMCRH',
        'created': 1657381542,
        'creator': 'U03NZJWKEF6',
        'id': 'C03PLUZDY2U',
        'is_archived': False,
        'is_channel': True,
        'is_ext_shared': False,
        'is_general': True,
        'is_group': False,
        'is_im': False,
        'is_member': True,
        'is_mpim': False,
        'is_org_shared': False,
        'is_pending_ext_shared': False,
        'is_private': False,
        'is_shared': False,
        'name': 'general',
        'name_normalized': 'general',
        'num_members': 4,
        'parent_conversation': None,
        'pending_connected_team_ids': [],
        'pending_shared': [],
        'previous_names': [],
        'purpose': {'creator': 'U03NZJWKEF6',
                    'last_set': 1657381542,
                    'value': '...'
                            '...'
                            '...'},
        'shared_team_ids': ['T03NX4VMCRH'],
        'topic': {'creator': '', 'last_set': 0, 'value': ''},
        'unlinked': 0,
        'updated': 1681220308327
    }
    """

    context_team_id: str
    created: int
    creator: str
    id: str
    is_archived: bool
    is_channel: bool
    is_ext_shared: bool
    is_general: bool
    is_group: bool
    is_im: bool
    is_member: bool
    is_mpim: bool
    is_org_shared: bool
    is_pending_ext_shared: bool
    is_private: bool
    is_shared: bool
    name: str
    name_normalized: str
    num_members: int
    parent_conversation: str | None
    pending_connected_team_ids: List[str]
    pending_shared: List[str]
    previous_names: List[str]
    purpose: dict
    shared_team_ids: List[str]
    topic: dict
    unlinked: int
    updated: int


class SlackConversationListResponse(BaseModel):
    ok: bool
    channels: List[SlackConversationItemResponse]
    response_metadata: dict | None = None


class SlackWebAPIConnector(SlackWebAPI):
    def __init__(self, access_token: str) -> None:
        super().__init__(access_token)

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
        # TODO: needs testing, not using it for now.
        response = self.team_info()
        response = TeamInfoResponse(**response.data)
        return response.team

    def get_channels(
        self, types: str = "public_channel"
    ) -> List[SlackConversationItemResponse]:
        response = self.conversation_list(types=types)
        response = SlackConversationListResponse(**response.data)
        return response.channels
