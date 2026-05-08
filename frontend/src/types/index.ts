export type ConnectionType = 'postgres' | 'mongodb' | 'mysql';
export type MaskingStrategyType = 'substitution' | 'hashing' | 'redaction' | 'nullification' | 'fpe' | 'perturbation';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Connection {
  id: string;
  name: string;
  type: ConnectionType;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export interface ConnectionCreate {
  name: string;
  type: ConnectionType;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export interface MaskingRule {
  id: string;
  name: string;
  connection_id: string;
  target_table: string;
  target_column: string;
  strategy: MaskingStrategyType;
  strategy_options: Record<string, unknown>;
}

export interface RuleCreate {
  name: string;
  connection_id: string;
  target_table: string;
  target_column: string;
  strategy: MaskingStrategyType;
  strategy_options?: Record<string, unknown>;
}

export interface MaskingJob {
  id: string;
  connection_id: string;
  rule_ids: string[];
  status: JobStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  records_processed: number;
  owner_id: string;
  shared_with: string[];
}

export interface JobCreate {
  connection_id: string;
  rule_ids: string[];
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  picture?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Summary {
  total_connections: number;
  total_rules: number;
  total_jobs: number;
  total_records_processed: number;
}

export interface DynamicQueryResponse {
  data: Record<string, unknown>[];
  total_records: number;
  is_masked: boolean;
}

export interface ShareJobRequest {
  email: string;
}

export interface AuditLogEntry {
  id: string;
  job_id: string;
  user_id: string;
  user_email: string;
  user_role: string;
  action: string;
  is_masked: boolean;
  timestamp: string;
}
