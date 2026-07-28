export type RequestStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED"
  | "FULFILLED";

export type RequestPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export const REQUEST_STATUSES: RequestStatus[] = [
  "PENDING",
  "APPROVED",
  "REJECTED",
  "CANCELLED",
  "FULFILLED",
];

export const REQUEST_PRIORITIES: RequestPriority[] = [
  "LOW",
  "MEDIUM",
  "HIGH",
  "URGENT",
];

export interface TimelineEvent {
  key: string;
  label: string;
  status: "done" | "current" | "upcoming";
  at: string | null;
  actor: string | null;
  detail: string;
}

export interface ApprovalStep {
  id: number;
  step: number;
  approver: number | null;
  approver_email: string | null;
  decision: "PENDING" | "APPROVED" | "REJECTED";
  comments: string;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetRequestListItem {
  id: number;
  request_number: string;
  requested_by: number;
  requested_by_code: string;
  requested_by_email: string;
  department_name: string;
  category: number | null;
  category_name: string | null;
  asset: number | null;
  asset_tag: string | null;
  priority: RequestPriority;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
  fulfilled_at: string | null;
}

export interface AssetRequest extends AssetRequestListItem {
  asset_name: string | null;
  justification: string;
  fulfilled_by: number | null;
  fulfilled_by_email: string | null;
  assignment: number | null;
  approvals: ApprovalStep[];
  timeline: TimelineEvent[];
}

export interface AssetRequestCreatePayload {
  category?: number | null;
  asset?: number | null;
  justification: string;
  priority: RequestPriority;
}

export interface AssetRequestListParams {
  page?: number;
  search?: string;
  status?: RequestStatus | "";
  priority?: RequestPriority | "";
  ordering?: string;
}
