-- This table is used to capture Slack events. 
create table slack_event (
  event_id varchar(255) not null, 
  team_id varchar(255) not null, 
  event jsonb, 
  event_type varchar(255) not null,
  event_ts BIGINT not null,
  metadata jsonb null,
  
  created_at timestamp default current_timestamp, 
  updated_at timestamp default current_timestamp,
  is_ack boolean not null default false,
  
  constraint slack_event_idx primary key (event_id)
);

create table slack_channel (
  channel_id varchar(255) not null,
  name varchar(255) not null,
  channel_type varchar(255) not null,

  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,

  constraint slack_channel_idx primary key (channel_id)
)

create table inbox (
  inbox_id varchar(255) not null,
  name varchar(255) not null,
  description varchar(255) null,

  slack_channel_id varchar(255) null,

  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp,

  constraint inbox_idx primary key (inbox_id),
  constraint fk_slack_channel_id foreign key (slack_channel_id) references slack_channel(slack_channel_id),
  constraint slack_channel_id_unq unique (slack_channel_id)
)