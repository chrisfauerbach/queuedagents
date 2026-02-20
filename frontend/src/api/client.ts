import type { Job, Stats, JobCreatePayload, GpuMetric, OllamaModel, Comparison, ComparisonCreatePayload } from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
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
