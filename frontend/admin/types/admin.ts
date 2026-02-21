export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  risk_score?: number;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  role: string;
}

export interface DashboardStats {
  total_users?: number;
  total_products?: number;
  total_scans?: number;
  total_batches?: number;
  total_anchors?: number;
  [key: string]: unknown;
}

export interface ServiceStatus {
  service: string;
  url?: string;
  status: string;
}

export interface SystemStatusResponse {
  services: ServiceStatus[];
}

export interface SystemConfigResponse {
  environment?: string;
  factory_service_url?: string;
  blockchain_service_url?: string;
  database_pool_size?: number;
  cors_origins?: string[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: string;
}

export interface AuditLog {
  id?: string;
  entity_type?: string;
  entity_id?: string;
  action?: string;
  user_id?: string;
  changes?: Record<string, unknown>;
  ip_address?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface FraudAnalytics {
  suspicious_count?: number;
  high_risk_scans?: unknown[];
  [key: string]: unknown;
}

export interface GeographicAnalytics {
  by_country?: Record<string, number>;
  by_region?: Record<string, number>;
  [key: string]: unknown;
}

export interface TrendAnalytics {
  by_day?: Array<{ date: string; count: number }>;
  [key: string]: unknown;
}
