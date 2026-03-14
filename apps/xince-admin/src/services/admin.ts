import { apiRequest } from "@/services/http";

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
  return apiRequest<any[]>("/admin/content/tests");
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
