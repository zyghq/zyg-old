from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKeyConstraint,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

metadata = MetaData()


WorkspaceDB = Table(
    "workspace",
    metadata,
    Column("account_id", String(255), nullable=False),
    Column("workspace_id", String(255), primary_key=True),
    Column("slug", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    ForeignKeyConstraint(["account_id"], ["account.account_id"]),
    UniqueConstraint("slug"),
)


SlackWorkspaceDB = Table(
    "slack_workspace",
    metadata,
    Column("workspace_id", String(255), nullable=False),
    Column("ref", String(255), primary_key=True),
    Column("url", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("status", String(127), nullable=False),
    Column("sync_status", String(127), nullable=False),
    Column("synced_at", TIMESTAMP, nullable=True),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    ForeignKeyConstraint(["workspace_id"], ["workspace.workspace_id"]),
    UniqueConstraint("workspace_id"),
)

SlackBotDB = Table(
    "slack_bot",
    metadata,
    Column("slack_workspace_ref", String(255), nullable=False),
    Column("bot_id", String(255), primary_key=True),
    Column("bot_user_ref", String(255), nullable=False),
    Column("bot_ref", String(255), nullable=True),
    Column("app_ref", String(255), nullable=False),
    Column("scope", Text, nullable=False),
    Column("access_token", String(255), nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    ForeignKeyConstraint(["slack_workspace_ref"], ["slack_workspace.ref"]),
    UniqueConstraint("slack_workspace_ref"),
)

SlackChannelDB = Table(
    "slack_channel",
    metadata,
    Column("slack_workspace_ref", String(255), nullable=False),
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
    ForeignKeyConstraint(
        ["slack_workspace_ref"],
        ["slack_workspace.ref"],
        name="slack_channel_slack_workspace_ref_fkey",
    ),
    UniqueConstraint(
        "slack_workspace_ref",
        "channel_ref",
        name="slack_channel_slack_workspace_ref_channel_ref_key",
    ),
)
