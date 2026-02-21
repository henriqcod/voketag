-- Create api_keys table (factory-service)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(8) NOT NULL,
    factory_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_factory_id ON api_keys(factory_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(factory_id, created_at) WHERE revoked_at IS NULL;
