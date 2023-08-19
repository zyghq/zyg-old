-- This table is used to capture Slack events. 
CREATE TABLE slack_event (
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
