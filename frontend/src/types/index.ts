// ---- Auth ----
export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  role_id: number;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ---- Records ----
export interface RecordItem {
  id: number;
  owner_id: number;
  data: Record<string, unknown>;
  version: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ---- Sync operations ----
export type OperationType = "CREATE" | "UPDATE" | "DELETE";
export type SyncStatus = "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED" | "CONFLICT";

export interface SyncOperation {
  id: number;
  operation_id: string;
  record_id: number | null;
  user_id: number;
  operation_type: OperationType;
  base_version: number;
  payload: Record<string, unknown> | null;
  status: SyncStatus;
  attempt_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// Local (client-only) queue entry stored in IndexedDB before it is ever
// acknowledged by the server. Mirrors SyncOperation but tracks local state.
export interface LocalQueueEntry {
  operation_id: string;
  record_id: number | null;
  local_record_id: number | null; // temp negative client-side id for not-yet-created records
  operation_type: OperationType;
  base_version: number;
  payload: Record<string, unknown> | null;
  status: SyncStatus;
  attempt_count: number;
  error_message: string | null;
  created_at: string;
}

// ---- Conflicts ----
export type ResolutionStrategy = "SERVER_WINS" | "CLIENT_WINS" | "LAST_WRITE_WINS" | "MANUAL";

export interface ConflictItem {
  id: number;
  record_id: number;
  user_id: number;
  client_version: number;
  server_version: number;
  client_data: Record<string, unknown> | null;
  server_data: Record<string, unknown> | null;
  resolution_strategy: ResolutionStrategy | null;
  resolution_status: "PENDING" | "RESOLVED";
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
}

// ---- Sync history ----
export interface SyncHistoryItem {
  id: number;
  record_id: number;
  user_id: number;
  operation_type: OperationType;
  sync_status: string;
  conflict_detected: boolean;
  error_message: string | null;
  record_version: number | null;
  created_at: string;
  updated_at: string;
}

// ---- Dashboard ----
export interface SyncDashboard {
  total_records: number;
  total_operations: number;
  pending_operations: number;
  successful_operations: number;
  failed_operations: number;
  conflict_operations: number;
  total_conflicts: number;
  pending_conflicts: number;
  resolved_conflicts: number;
  last_sync_at: string | null;
}

// ---- Users (admin) ----
export interface UserListResponse extends PaginatedResponse<User> {}

export interface ApiError {
  detail: string | { msg: string }[] | Record<string, unknown>;
}

// ---- Audit logs ----
export interface AuditLogItem {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedAuditLogResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
