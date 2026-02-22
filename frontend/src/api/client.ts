import type { Job, Stats, JobCreatePayload, GpuMetric, OllamaModel, Comparison, ComparisonCreatePayload, TokenUsagePoint, ModelLeaderboardEntry, Prompt, PromptCreatePayload, PromptUpdatePayload, CatalogModel, ModelShowInfo, PullProgress } from "../types";

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

export function fetchCatalog(): Promise<CatalogModel[]> {
  return request<CatalogModel[]>("/models/catalog");
}

export function showModel(name: string): Promise<ModelShowInfo> {
  return request<ModelShowInfo>("/models/show", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function deleteModel(name: string): Promise<void> {
  return request<void>("/models", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function pullModel(
  name: string,
  onProgress: (progress: PullProgress) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/models/pull`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
    signal,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.trim()) {
        try {
          onProgress(JSON.parse(line));
        } catch {
          // skip malformed lines
        }
      }
    }
  }
  if (buffer.trim()) {
    try {
      onProgress(JSON.parse(buffer));
    } catch {
      // skip
    }
  }
}
