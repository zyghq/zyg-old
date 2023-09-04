-- represents the tenant table.
create table tenant(
  tenant_id varchar(255) not null,
  name varchar(512) not null,
  slack_team_ref varchar(255) null,
  
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,

  constraint tenant_idx primary key (tenant_id),
  constraint slack_team_ref_unq unique (slack_team_ref)
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

  constraint slack_event_idx primary key (event_id),
  constraint fk_tenant_id foreign key (tenant_id) references tenant(tenant_id),
  constraint slack_event_ref_unq unique (slack_event_ref)
);

-- represents the synced slack channel
-- create table synced_channel(
--   channel_id varchar(255) not null,
--   tenant_id varchar(255) not null,
--   slack_channel_id varchar(255) not null,
--   context_team_id varchar(255) not null,
--   created bigint not null,
--   creator varchar(255) not null,
--   is_archived boolean not null,
--   is_channel boolean not null,
--   is_ext_shared boolean not null,
--   is_general boolean not null,
--   is_group boolean not null,
--   is_im boolean not null,
--   is_member boolean not null,
--   is_mpim boolean not null,
--   is_org_shared boolean not null,
--   is_pending_ext_shared boolean not null,
--   is_private boolean not null,
--   is_shared boolean not null,
--   name varchar(255) not null,
--   name_normalized varchar(255) not null,
--   updated bigint not null,
--   synced_ts bigint not null,
--   created_at timestamp default current_timestamp,
--   updated_at timestamp default current_timestamp,

--   constraint synced_channel_idx primary key (channel_id),
--   constraint fk_tenant_id foreign key (tenant_id) references tenant(tenant_id)
-- );
