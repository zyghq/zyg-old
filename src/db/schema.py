from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

metadata = MetaData()


AccountDb = Table(
    "account",
    metadata,
    Column("account_id", String(255), primary_key=True, nullable=False),
    Column("email", String(255), nullable=False),
    Column("provider", String(255), nullable=False),
    Column("auth_user_id", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("account_id", name="account_account_id_pkey"),
    UniqueConstraint("email", name="account_email_key"),
    UniqueConstraint("auth_user_id", name="account_auth_user_id_key"),
)


WorkspaceDb = Table(
    "workspace",
    metadata,
    Column(
        "account_id",
        String(255),
        ForeignKey("account.account_id", name="workspace_account_id_fkey"),
        nullable=False,
    ),
    Column("workspace_id", String(255), primary_key=True, nullable=False),
    Column("slug", String(255), unique=True, nullable=False),
    Column("name", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("workspace_id", name="workspace_workspace_id_pkey"),
    UniqueConstraint("slug", name="workspace_slug_key"),
)

MemberDb = Table(
    "member",
    metadata,
    Column(
        "workspace_id",
        String(255),
        ForeignKey("workspace.workspace_id", name="member_workspace_id_fkey"),
        nullable=False,
    ),
    Column(
        "account_id",
        String(255),
        ForeignKey("account.account_id", name="member_account_id_fkey"),
        nullable=False,
    ),
    Column("member_id", String(255), primary_key=True, nullable=False),
    Column("slug", String(255), unique=True, nullable=False),
    Column("role", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("member_id", name="member_member_id_pkey"),
    UniqueConstraint(
        "workspace_id", "account_id", name="member_workspace_id_account_id_key"
    ),
    UniqueConstraint("slug", name="member_slug_key"),
)


SlackWorkspaceDb = Table(
    "slack_workspace",
    metadata,
    Column(
        "workspace_id",
        String(255),
        ForeignKey("workspace.workspace_id", name="slack_workspace_workspace_id_fkey"),
        nullable=False,
    ),
    Column("ref", String(255), primary_key=True),
    Column("url", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("status", String(127), nullable=False),
    Column("sync_status", String(127), nullable=False),
    Column("synced_at", TIMESTAMP, nullable=True),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("ref", name="slack_workspace_ref_pkey"),
    UniqueConstraint("workspace_id", name="slack_workspace_workspace_id_key"),
)

SlackBotDb = Table(
    "slack_bot",
    metadata,
    Column(
        "slack_workspace_ref",
        String(255),
        ForeignKey("slack_workspace.ref", name="slack_bot_slack_workspace_ref_fkey"),
        nullable=False,
    ),
    Column("bot_id", String(255), primary_key=True),
    Column("bot_user_ref", String(255), nullable=False),
    Column("bot_ref", String(255), nullable=True),
    Column("app_ref", String(255), nullable=False),
    Column("scope", Text, nullable=False),
    Column("access_token", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("bot_id", name="slack_bot_bot_id_pkey"),
    UniqueConstraint("slack_workspace_ref", name="slack_bot_slack_workspace_ref_key"),
)

SlackChannelDb = Table(
    "slack_channel",
    metadata,
    Column(
        "slack_workspace_ref",
        String(255),
        ForeignKey(
            "slack_workspace.ref", name="slack_channel_slack_workspace_ref_fkey"
        ),
        nullable=False,
    ),
    Column("channel_id", String(255), primary_key=True),
    Column("channel_ref", String(255), nullable=False),
    Column("is_channel", Boolean, nullable=False),
    Column("is_ext_shared", Boolean, nullable=False),
    Column("is_general", Boolean, nullable=False),
    Column("is_group", Boolean, nullable=False),
    Column("is_im", Boolean, nullable=False),
    Column("is_member", Boolean, nullable=False),
    Column("is_mpim", Boolean, nullable=False),
    Column("is_org_shared", Boolean, nullable=False),
    Column("is_pending_ext_shared", Boolean, nullable=False),
    Column("is_private", Boolean, nullable=False),
    Column("is_shared", Boolean, nullable=False),
    Column("name", String(255), nullable=False),
    Column("name_normalized", String(255), nullable=False),
    Column("created", BigInteger, nullable=False),
    Column("updated", BigInteger, nullable=False),
    Column("status", String(127), nullable=False),
    Column("synced_at", TIMESTAMP, nullable=True),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    PrimaryKeyConstraint("channel_id", name="slack_channel_channel_id_pkey"),
    UniqueConstraint(
        "slack_workspace_ref",
        "channel_ref",
        name="slack_channel_slack_workspace_ref_channel_ref_key",
    ),
)
