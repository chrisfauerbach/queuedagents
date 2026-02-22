import type { Job, Stats, JobCreatePayload, GpuMetric, OllamaModel, Comparison, ComparisonCreatePayload, TokenUsagePoint, ModelLeaderboardEntry, Prompt, PromptCreatePayload, PromptUpdatePayload } from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function fetchJobs(): Promise<Job[]> {
  return request<Job[]>("/jobs");
}

export function fetchJob(id: string): Promise<Job> {
  return request<Job>(`/jobs/${id}`);
}

export function fetchStats(): Promise<Stats> {
  return request<Stats>("/stats");
}

export function createJob(payload: JobCreatePayload): Promise<Job> {
  return request<Job>("/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchModels(): Promise<OllamaModel[]> {
  return request<OllamaModel[]>("/models");
}

export function fetchGpuMetrics(minutes: number = 10): Promise<GpuMetric[]> {
  return request<GpuMetric[]>(`/gpu/metrics?minutes=${minutes}`);
}

export function createComparison(payload: ComparisonCreatePayload): Promise<Comparison> {
  return request<Comparison>("/comparisons", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchComparisons(): Promise<Comparison[]> {
  return request<Comparison[]>("/comparisons");
}

export function fetchComparison(id: string): Promise<Comparison> {
  return request<Comparison>(`/comparisons/${id}`);
}

export function fetchTokenUsage(hours: number = 24): Promise<TokenUsagePoint[]> {
  return request<TokenUsagePoint[]>(`/token-usage?hours=${hours}`);
}

export function fetchLeaderboard(): Promise<ModelLeaderboardEntry[]> {
  return request<ModelLeaderboardEntry[]>("/leaderboard");
}

export function fetchPrompts(): Promise<Prompt[]> {
  return request<Prompt[]>("/prompts");
}

export function fetchPrompt(id: string): Promise<Prompt> {
  return request<Prompt>(`/prompts/${id}`);
}

export function createPrompt(payload: PromptCreatePayload): Promise<Prompt> {
  return request<Prompt>("/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updatePrompt(id: string, payload: PromptUpdatePayload): Promise<Prompt> {
  return request<Prompt>(`/prompts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deletePrompt(id: string): Promise<void> {
  return request<void>(`/prompts/${id}`, { method: "DELETE" });
}
