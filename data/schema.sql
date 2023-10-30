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

-- represents the tenant table.
create table tenant(
  tenant_id varchar(255) not null,
  name varchar(512) not null,
  slack_team_ref varchar(255) null, -- reference to Slack team(id).
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint tenant_tenant_id_pkey primary key (tenant_id),
  constraint tenant_slack_team_ref_key unique (slack_team_ref)
);

-- represents the user table.
create table zyguser(
  user_id varchar(255) not null,
  tenant_id varchar(255) not null, -- reference to tenant.
  slack_user_ref varchar(255) not null, -- reference to Slack user(id).
  name varchar(255) not null,
  role varchar(255) not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint user_user_id_pkey primary key (user_id),
  constraint user_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint user_tenant_id_slack_user_ref_key unique (tenant_id, slack_user_ref)
);


-- represents the slack event table.
-- with reference to a tenant.
create table slack_event(
  event_id varchar(255) not null,
  tenant_id varchar(255) not null, -- reference to tenant.
  slack_event_ref varchar(255) not null,
  inner_event_type varchar(255) not null,
  event_dispatched_ts bigint not null,
  api_app_id varchar(255) null,
  token varchar(255) null,
  payload jsonb,
  is_ack boolean not null default false,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint slack_event_event_id_pkey primary key (event_id),
  constraint slack_event_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint slack_event_slack_event_ref_key unique (slack_event_ref) -- unique across Slack workspaces. As per docs.
);

-- mapped as per raw conversation item from Slack API reponse.
-- with reference to a tenant.
-- fields are mapped as per https://api.slack.com/types/conversation
create table insync_slack_channel(
  tenant_id varchar(255) not null, -- reference to tenant.
  context_team_id varchar(255) not null,
  created bigint not null,
  creator varchar(255) not null,
  id varchar(255) not null, -- reference to Slack channel(id).
  is_archived boolean not null,
  is_channel boolean not null,
  is_ext_shared boolean not null,
  is_general boolean not null,
  is_group boolean not null,
  is_im boolean not null,
  is_member boolean not null,
  is_mpim boolean not null,
  is_org_shared boolean not null,
  is_pending_ext_shared boolean not null,
  is_private boolean not null,
  is_shared boolean not null,
  is_thread_only boolean null,
  name varchar(255) not null,
  name_normalized varchar(255) not null,
  unlinked bigint null,
  updated bigint not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint insync_slack_channel_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id), 
  constraint insync_slack_channel_tenant_id_id_key unique (tenant_id, id)
);

-- represents the linked Slack channel table
-- with reference to a tenant.
create table slack_channel(
  tenant_id varchar(255) not null, -- reference to tenant.
  slack_channel_id varchar(255) not null,
  slack_channel_ref varchar(255) not null, -- reference to Slack channel(id).
  slack_channel_name varchar(255) null, -- reference to Slack channel(name).
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint slack_channel_id_pkey primary key (slack_channel_id),
  constraint slack_channel_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint slack_channel_tenant_id_slack_channel_ref_key unique (tenant_id, slack_channel_ref)
);

-- represents the linked Slack triage channel table
-- with reference to a tenant.
create table slack_triage_channel(
  tenant_id varchar(255) not null, -- reference to tenant.
  alias varchar(255) null,
  slack_channel_id varchar(255) not null,
  slack_channel_ref varchar(255) not null, -- reference to Slack channel(id).
  slack_channel_name varchar(255) null, -- reference to Slack channel(name).
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint slack_triage_channel_id_pkey primary key (slack_channel_id),
  constraint slack_triage_channel_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint slack_triage_channel_tenant_id_slack_channel_ref_key unique (tenant_id, slack_channel_ref)
);

-- represents issue sequence table
-- with reference to a tenant
-- Note: Make sure the query can generate the next sequence number
create table issue_seq(
  seq bigint default 1 not null,
  tenant_id varchar(255) not null, -- reference to tenant.
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint issue_seq_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint issue_seq_tenant_id_key unique (tenant_id)
);

-- represents the issue table
-- with reference to a tenant.
create table issue(
  issue_id varchar(255) not null,
  tenant_id varchar(255) not null, -- reference to tenant.
  issue_number bigint not null,
  slack_channel_id varchar(255) not null, -- reference to slack channel.
  slack_message_ts varchar(255) not null, -- slack message for issue is created.
  body text not null,
  status varchar(127) not null,
  priority smallint not null,
  tags text[] null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint issue_issue_id_pkey primary key (issue_id),
  constraint issue_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint issue_slack_channel_id_fkey foreign key (slack_channel_id) references slack_channel(slack_channel_id),
  constraint issue_tenant_id_issue_number_key unique (tenant_id, issue_number),
  constraint issue_slack_channel_id_slack_message_ts_key unique (slack_channel_id, slack_message_ts)
);

-- mapped as per raw user list item from Slack API reponse.
-- with reference to a tenant.
create table insync_slack_user(
  tenant_id varchar(255) not null, -- reference to tenant.
  id varchar(255) not null,
  is_admin boolean not null,
  is_app_user boolean not null,
  is_bot boolean not null,
  is_email_confirmed boolean not null,
  is_owner boolean not null,
  is_primary_owner boolean not null,
  is_restricted boolean not null,
  is_stranger boolean null,
  is_ultra_restricted boolean not null,
  name varchar(255) not null,
  profile jsonb not null,
  real_name varchar(255) not null,
  team_id varchar(255) not null,
  tz varchar(255) not null,
  tz_label varchar(255) not null,
  tz_offset bigint not null,
  updated bigint not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint insync_slack_user_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint insync_slack_user_tenant_id_id_key unique (tenant_id, id)
);
