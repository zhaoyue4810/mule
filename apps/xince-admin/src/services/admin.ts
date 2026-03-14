import { apiRequest } from "@/services/http";

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
