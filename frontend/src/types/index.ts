export type { User, AuthTokens, LoginCredentials, AuthState } from "./auth";
export type {
  Asset,
  AssetListItem,
  AssetCategory,
  Vendor,
  AssetStatus,
  AssetListParams,
  PaginatedResponse,
  AssetAuditLog,
} from "./assets";
export type {
  AssetRequest,
  AssetRequestListItem,
  RequestStatus,
  RequestPriority,
  TimelineEvent,
} from "./approvals";
export type {
  DashboardSummary,
  DashboardWidgets,
  ChartSlice,
  MonthlyAllocationPoint,
  RecentActivity,
} from "./dashboard";

export interface ApiError {
  message: string;
  status?: number;
  details?: Record<string, string[]>;
}

export interface HealthCheckResponse {
  status: string;
  service?: string;
  app?: string;
}
