CREATE TABLE api_usage_event
(
    id         SERIAL PRIMARY KEY,
    account_id VARCHAR(80)  NOT NULL,
    endpoint   VARCHAR(255) NOT NULL,
    timestamp  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);