CREATE TABLE IF NOT EXISTS scans (
    tag_id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    batch_id UUID NOT NULL,
    first_scan_at TIMESTAMPTZ,
    scan_count INT DEFAULT 0,
    valid BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
