-- Please follow the naming convention for consistency.

-- {tablename}_{columnname(s)}_{suffix}

-- where the suffix is one of the following:

-- pkey for a Primary Key constraint
-- key for a Unique constraint
-- excl for an Exclusion constraint
-- idx for any other kind of index
-- fkey for a Foreign key
-- check for a Check constraint

-- Standard suffix for sequences is
-- seq for all sequences

-- Thanks.
-- --------------------------------------------------

-- Represents the auth account table
CREATE TABLE account (
    account_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL, 
    auth_user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT account_account_id_pkey PRIMARY KEY (account_id),
    CONSTRAINT account_email_key UNIQUE (email),
    CONSTRAINT account_auth_user_id_key UNIQUE (auth_user_id)
);

-- Represents the workspace table
CREATE TABLE workspace (
    account_id VARCHAR(255) NOT NULL,
    workspace_id VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT workspace_workspace_id_pkey PRIMARY KEY (workspace_id),
    CONSTRAINT workspace_account_id_fkey FOREIGN KEY (account_id) REFERENCES account (account_id),
    CONSTRAINT workspace_slug_key UNIQUE (slug)
);

-- Represents the member table
CREATE TABLE member (
    workspace_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    member_id VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT member_member_id_pkey PRIMARY KEY (member_id),
    CONSTRAINT member_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES workspace (workspace_id),
    CONSTRAINT member_account_id_fkey FOREIGN KEY (account_id) REFERENCES account (account_id),
    CONSTRAINT member_workspace_id_account_id_key UNIQUE (workspace_id, account_id),
    CONSTRAINT member_slug_key UNIQUE (slug)
);

-- Represents theh Slack workspace table
-- There is only one Slack workspace per Workspace
CREATE TABLE slack_workspace (
    workspace_id VARCHAR(255) NOT NULL, -- fk to workspace
    ref VARCHAR(255) NOT NULL, -- primary key and reference to Slack workspace or team id
    url VARCHAR(255) NOT NULL, -- Slack workspace url
    name VARCHAR(255) NOT NULL, -- Slack workspace name
    status VARCHAR(127) NOT NULL, -- current status of Slack workspace with respect to Workspace
    sync_status VARCHAR(127) NOT NULL, -- current sync status of Slack workspace
    synced_at TIMESTAMP NULL DEFAULT NULL, -- last time Slack workspace was synced defaults to NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT slack_workspace_ref_pkey PRIMARY KEY (ref),
    CONSTRAINT slack_workspace_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES workspace (workspace_id),
    CONSTRAINT slack_workspace_workspace_id_key UNIQUE (workspace_id)
);

-- Represents the Slack bot table
-- There is only one Slack bot per Slack workspace, indirectly there is only one Slack bot per Workspace
CREATE TABLE slack_bot (
    slack_workspace_ref VARCHAR(255) NOT NULL, -- fk to slack_workspace
    bot_id VARCHAR(255) NOT NULL, -- primary key
    bot_user_ref VARCHAR(255) NOT NULL, -- reference to Slack bot user id
    bot_ref VARCHAR(255) NULL, -- reference to Slack bot id
    app_ref VARCHAR(255) NOT NULL, -- reference to Slack app id
    scope TEXT NOT NULL, -- comma separated list of scopes
    access_token VARCHAR(255) NOT NULL, -- access token for the bot
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT slack_bot_bot_id_pkey PRIMARY KEY (bot_id),
    CONSTRAINT slack_bot_slack_workspace_ref_fkey FOREIGN KEY (slack_workspace_ref) REFERENCES slack_workspace (ref),
    CONSTRAINT slack_bot_slack_workspace_ref_key UNIQUE (slack_workspace_ref)
);

-- Represents the Slack channel table
-- There are many Slack channels per Slack workspace
CREATE TABLE slack_channel (
    slack_workspace_ref VARCHAR(255) NOT NULL, -- fk to slack_workspace
    channel_id VARCHAR(255) NOT NULL, -- primary key
    channel_ref VARCHAR(255) NOT NULL, -- reference to Slack channel id
    is_channel BOOLEAN NOT NULL,
    is_ext_shared BOOLEAN NOT NULL,
    is_general BOOLEAN NOT NULL,
    is_group BOOLEAN NOT NULL,
    is_im BOOLEAN NOT NULL,
    is_member BOOLEAN NOT NULL,
    is_mpim BOOLEAN NOT NULL,
    is_org_shared BOOLEAN NOT NULL,
    is_pending_ext_shared BOOLEAN NOT NULL,
    is_private BOOLEAN NOT NULL,
    is_shared BOOLEAN NOT NULL,
    name VARCHAR(255) NOT NULL, -- Slack channel name
    name_normalized VARCHAR(255) NOT NULL, -- Slack channel name normalized
    created BIGINT NOT NULL,
    updated BIGINT NOT NULL,
    status VARCHAR(127) NOT NULL, -- custom status of Slack channel with respect to Slack workspace
    synced_at TIMESTAMP NULL DEFAULT NULL, -- custom timestamp Slack channel was synced defaults to NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT slack_channel_channel_id_pkey PRIMARY KEY (channel_id),
    CONSTRAINT slack_channel_slack_workspace_ref_fkey FOREIGN KEY (slack_workspace_ref) REFERENCES slack_workspace (ref),
    CONSTRAINT slack_channel_slack_workspace_ref_channel_ref_key UNIQUE (slack_workspace_ref, channel_ref)
);