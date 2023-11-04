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

-- represents the account table
create table account (
    account_id varchar(255) not null,
    provider varchar(255) not null,
    auth_user_id varchar(255) not null,
    name varchar(255) not null,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,
    constraint account_account_id_pkey primary key (account_id),
    constraint account_auth_user_id_key unique (auth_user_id)
);

-- represents the workspace table
create table workspace (
    account_id varchar(255) not null,
    workspace_id varchar(255) not null,
    name varchar(255) not null,
    logo_url varchar(255) null,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,
    constraint workspace_workspace_id_pkey primary key (workspace_id),
    constraint workspace_account_id_fkey foreign key (account_id) references account (account_id)
);