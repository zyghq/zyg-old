-- This table is used to capture Slack events. 
CREATE TABLE slack_event (
  event_id varchar(255) not null, 
  token varchar(255) not null, 
  team_id varchar(255) not null, 
  api_app_id varchar(255) not null, 
  event jsonb, 
  type varchar(255) not null, 
  event_context varchar(255) not null, 
  event_time BIGINT not null, 
  
  created_at timestamp default current_timestamp, 
  updated_at timestamp default current_timestamp,

  is_ack boolean not null default false,
  
  constraint slack_event_idx primary key (event_id)
);
