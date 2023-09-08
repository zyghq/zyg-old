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
  slack_team_ref varchar(255) null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint tenant_tenant_id_pkey primary key (tenant_id),
  constraint tenant_slack_team_ref_key unique (slack_team_ref)
);


-- represents the slack event table.
create table slack_event(
  event_id varchar(255) not null,
  tenant_id varchar(255) not null,
  slack_event_ref varchar(255) not null,
  inner_event_type varchar(255) not null,
  event jsonb,
  event_ts bigint not null,
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
-- with reference to tenant.
create table insync_slack_channel(
  tenant_id varchar(255) not null, -- reference to tenant.
  context_team_id varchar(255) not null,
  created bigint not null,
  creator varchar(255) not null,
  id varchar(255) not null,
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
  name varchar(255) not null,
  name_normalized varchar(255) not null,
  num_members bigint not null,
  parent_conversation varchar(255) null,
  pending_connected_team_ids text[] null,
  pending_shared text[] null,
  previous_names text[] null,
  purpose jsonb null,
  shared_team_ids text[] null,
  topic jsonb null,
  unlinked bigint null,
  updated bigint not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint insync_slack_channel_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id), 
  constraint insync_slack_channel_tenant_id_id_key unique (tenant_id, id)
);

create table linked_slack_channel(
  tenant_id varchar(255) not null, -- reference to tenant.
  linked_slack_channel_id varchar(255) not null,
  slack_channel_ref varchar(255) not null, -- reference to Slack channel(id).
  slack_channel_name varchar(255) null, -- reference to Slack channel(name).
  triage_slack_channel_ref varchar(255) not null, -- reference to Slack channel(id).
  triage_slack_channel_name varchar(255) null, -- reference to Slack channel(name).
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,
  constraint linked_slack_channel_id_pkey primary key (linked_slack_channel_id),
  constraint linked_slack_channel_tenant_id_fkey foreign key (tenant_id) references tenant(tenant_id),
  constraint linked_slack_channel_tenant_id_slack_channel_ref_key unique (tenant_id, slack_channel_ref)
);