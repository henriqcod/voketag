-- Add columns to scans table (migration 004)
ALTER TABLE scans 
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ok',
  ADD COLUMN IF NOT EXISTS risk_score INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_risk_score ON scans(risk_score);

-- Create scan_events table (migration 004)
CREATE TABLE IF NOT EXISTS scan_events (
    id UUID PRIMARY KEY,
    tag_id UUID NOT NULL,
    product_id UUID NOT NULL,
    batch_id UUID,
    scanned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    country VARCHAR(2),
    risk_score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_events_tag_id ON scan_events(tag_id);
CREATE INDEX IF NOT EXISTS idx_scan_events_product_id ON scan_events(product_id);
CREATE INDEX IF NOT EXISTS idx_scan_events_scanned_at ON scan_events(scanned_at);
CREATE INDEX IF NOT EXISTS idx_scan_events_country ON scan_events(country);
CREATE INDEX IF NOT EXISTS idx_scan_events_risk_score ON scan_events(risk_score);
