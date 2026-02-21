-- =============================================================================
-- MIGRATION: Admin Features (Audit & Analytics)
-- DATA: 2026-02-21
-- DESCRIÇÃO: Cria tabelas de auditoria e views para o dashboard administrativo
-- =============================================================================

-- 1. Tabela de Auditoria de Segurança (Audit Trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL,          -- ID do admin que fez a ação
    action VARCHAR(100) NOT NULL,    -- Ex: "UPDATE_RISK_LIMIT", "BLOCK_COUNTRY"
    entity_type VARCHAR(50) NOT NULL,-- Ex: "SYSTEM_CONFIG", "USER"
    entity_id VARCHAR(50),           -- ID da entidade afetada (opcional)
    old_value JSONB,                 -- Valor anterior (para diff)
    new_value JSONB,                 -- Novo valor
    ip_address INET,                 -- IP do admin
    user_agent TEXT,                 -- Browser/Device
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance de filtros
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- 2. Views Analíticas para o Dashboard (OLAP Leve)

-- 2.1. Scans por Hora (Últimas 24h)
-- Agrega scans válidos vs inválidos por hora
CREATE OR REPLACE VIEW view_analytics_scans_hourly AS
SELECT 
    date_trunc('hour', created_at) as hour,
    count(*) as total_scans,
    count(*) FILTER (WHERE status = 'valid') as valid_scans,
    count(*) FILTER (WHERE status = 'invalid') as invalid_scans
FROM scans
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1 DESC;

-- 2.2. Mapa de Calor de Fraudes (Últimos 7 dias)
-- Agrupa tentativas de fraude por país
CREATE OR REPLACE VIEW view_analytics_fraud_heatmap AS
SELECT 
    country_code,
    count(*) as fraud_count
FROM scans
WHERE status = 'invalid' 
AND created_at > NOW() - INTERVAL '7 days'
AND country_code IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;

-- 2.3. Taxa de Conversão Global
-- Compara total de produtos fabricados vs total de scans válidos únicos
CREATE OR REPLACE VIEW view_analytics_conversion AS
WITH stats AS (
    SELECT 
        (SELECT count(*) FROM products) as total_products,
        (SELECT count(*) FROM scans WHERE status = 'valid') as valid_scans
)
SELECT 
    total_products,
    valid_scans,
    CASE 
        WHEN total_products > 0 THEN (valid_scans::float / total_products::float) * 100 
        ELSE 0 
    END as conversion_rate
FROM stats;