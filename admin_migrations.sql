-- Create scans table (migration 002)
CREATE TABLE IF NOT EXISTS scans (
    tag_id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    batch_id UUID NOT NULL,
    first_scan_at TIMESTAMP,
    scan_count INTEGER NOT NULL DEFAULT 0,
    valid BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scans_product_id ON scans(product_id);
CREATE INDEX IF NOT EXISTS idx_scans_batch_id ON scans(batch_id);
CREATE INDEX IF NOT EXISTS idx_scans_first_scan_at ON scans(first_scan_at);
CREATE INDEX IF NOT EXISTS idx_scans_updated_at ON scans(updated_at);

-- Create admin_login_logs table (migration 003)
CREATE TABLE IF NOT EXISTS admin_login_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_logs_user_id ON admin_login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_login_logs_created ON admin_login_logs(created_at);
