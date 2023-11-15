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