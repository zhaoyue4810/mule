import { apiRequest } from "@/services/http";

export interface AdminTestSummary {
  test_code: string;
  title: string;
  category: string;
  is_match_enabled: boolean;
  version_count: number;
}

export interface AdminTestVersionSummary {
  id: number;
  version: number;
  status: string;
  description?: string | null;
  duration_hint?: string | null;
  published_at?: string | null;
  created_at: string;
}

export interface AdminTestDetail {
  test_code: string;
  title: string;
  category: string;
  is_match_enabled: boolean;
  participant_count: number;
  sort_order: number;
  yaml_source?: string | null;
  published_version_id?: number | null;
  published_version?: number | null;
}

export interface AdminDimensionPayload {
  dim_code: string;
  dim_name: string;
  max_score: number;
  sort_order: number;
}

export interface AdminOptionPayload {
  option_code?: string | null;
  seq: number;
  label: string;
  emoji?: string | null;
  value: number;
  score_rules?: Record<string, unknown> | null;
  ext_config?: Record<string, unknown> | null;
}

export interface AdminQuestionPayload {
  question_code?: string | null;
  seq: number;
  question_text: string;
  interaction_type: string;
  emoji?: string | null;
  config?: Record<string, unknown> | null;
  dim_weights: Record<string, unknown>;
  options: AdminOptionPayload[];
}

export interface AdminPersonaPayload {
  persona_key: string;
  persona_name: string;
  emoji?: string | null;
  rarity_percent?: number | null;
  description?: string | null;
  soul_signature?: string | null;
  keywords: string[];
  dim_pattern: Record<string, unknown>;
  capsule_prompt?: string | null;
}

export interface AdminTestVersionContent {
  id: number;
  test_code: string;
  title: string;
  category: string;
  is_match_enabled: boolean;
  participant_count: number;
  sort_order: number;
  version: number;
  status: string;
  description?: string | null;
  duration_hint?: string | null;
  cover_gradient?: string | null;
  report_template_code?: string | null;
  dimensions: AdminDimensionPayload[];
  questions: AdminQuestionPayload[];
  personas: AdminPersonaPayload[];
}

export interface AdminCreateVersionRequest {
  source_version_id?: number | null;
  source_version?: number | null;
  clone_content?: boolean;
  description?: string | null;
}

export interface AdminTestVersionContentUpdateRequest {
  title: string;
  category: string;
  is_match_enabled: boolean;
  participant_count: number;
  sort_order: number;
  description?: string | null;
  duration_hint?: string | null;
  cover_gradient?: string | null;
  report_template_code?: string | null;
  dimensions: AdminDimensionPayload[];
  questions: AdminQuestionPayload[];
  personas: AdminPersonaPayload[];
}

export interface InteractionTypeSummary {
  code: string;
  title: string;
  component: string;
  scoring_method: string;
}

export function loginAdmin(username: string, password: string) {
  return apiRequest<{
    access_token: string;
    token_type: string;
    expires_at: string;
    username: string;
    role: string;
  }>("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function listAdminTests() {
  return apiRequest<AdminTestSummary[]>("/admin/content/tests");
}

export function getAdminTestDetail(testCode: string) {
  return apiRequest<AdminTestDetail>(`/admin/content/tests/${testCode}`);
}

export function listAdminTestVersions(testCode: string) {
  return apiRequest<AdminTestVersionSummary[]>(`/admin/content/tests/${testCode}/versions`);
}

export function createAdminTestVersion(
  testCode: string,
  payload: AdminCreateVersionRequest,
) {
  return apiRequest<AdminTestVersionSummary>(`/admin/content/tests/${testCode}/versions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAdminTestVersionContent(testCode: string, versionId: number) {
  return apiRequest<AdminTestVersionContent>(
    `/admin/content/tests/${testCode}/versions/${versionId}/content`,
  );
}

export function updateAdminTestVersionContent(
  testCode: string,
  versionId: number,
  payload: AdminTestVersionContentUpdateRequest,
) {
  return apiRequest<AdminTestVersionContent>(
    `/admin/content/tests/${testCode}/versions/${versionId}/content`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export function publishAdminTestVersion(
  testCode: string,
  payload: { version_id?: number | null; version?: number | null; note?: string | null },
) {
  return apiRequest<AdminTestVersionSummary>(`/admin/content/tests/${testCode}/publish`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listInteractionTypes() {
  return apiRequest<InteractionTypeSummary[]>("/app/config/interaction-types");
}

export function getAdminAiOverview() {
  return apiRequest<any>("/admin/ai/task/overview");
}

export function getAdminAiMetrics(bucket = "day") {
  return apiRequest<any>(`/admin/ai/task/metrics?bucket=${bucket}`);
}

export function listAdminAiTasks(params = "") {
  return apiRequest<any>(`/admin/ai/task/page${params ? `?${params}` : ""}`);
}

export function getAdminAiTaskDetail(taskId: number) {
  return apiRequest<any>(`/admin/ai/task/${taskId}`);
}

export function retryAdminAiTask(taskId: number) {
  return apiRequest<any>(`/admin/ai/task/${taskId}/retry`, { method: "POST" });
}

export function retryAdminAiFailed() {
  return apiRequest<any>("/admin/ai/task/retry-failed", { method: "POST" });
}

export function listAdminPromptTemplates() {
  return apiRequest<any[]>("/admin/ai/prompt/list");
}

export function getAdminPromptHistory(templateId: number) {
  return apiRequest<any[]>(`/admin/ai/prompt/${templateId}/history`);
}

export function getAdminPromptCompare(templateId: number) {
  return apiRequest<any>(`/admin/ai/prompt/${templateId}/compare`);
}

export function uploadImportFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<any>("/admin/import/upload", {
    method: "POST",
    body: formData,
  });
}

export function listImportTasks(page = 1, size = 20) {
  return apiRequest<{
    items: any[];
    total: number;
    page: number;
    size: number;
  }>(`/admin/import/tasks?page=${page}&size=${size}`);
}

export function getImportPreview(taskId: number) {
  return apiRequest<any>(`/admin/import/${taskId}/preview`);
}

export function approveImport(taskId: number) {
  return apiRequest<any>(`/admin/import/${taskId}/approve`, {
    method: "POST",
    body: JSON.stringify({ note: "approved by admin" }),
  });
}

export function rejectImport(taskId: number, reason: string) {
  return apiRequest<any>(`/admin/import/${taskId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function listAdminBadges() {
  return apiRequest<any[]>("/admin/badges");
}

export function getYamlStatus() {
  return apiRequest<any>("/admin/config/yaml-status");
}

export function reloadYamlConfig() {
  return apiRequest<any>("/admin/config/reload", { method: "POST" });
}

export function listAdminUsers(page = 1, size = 20, keyword = "") {
  return apiRequest<any>(
    `/admin/users?page=${page}&size=${size}&keyword=${encodeURIComponent(keyword)}`,
  );
}

export function getAdminUserDetail(userId: number) {
  return apiRequest<any>(`/admin/users/${userId}`);
}

export function updateAdminUserStatus(userId: number, status: "ENABLED" | "DISABLED") {
  return apiRequest<any>(`/admin/users/${userId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
}

export function getHealthReady() {
  return apiRequest<any>("/app/health/ready");
}
