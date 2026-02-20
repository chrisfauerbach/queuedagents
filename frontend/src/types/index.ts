export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  model: string;
  prompt: string;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  status: JobStatus;
  result: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  generation_time_ms: number | null;
}

export interface Stats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}

export interface JobCreatePayload {
  model: string;
  prompt: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface GpuMetric {
  id: number;
  gpu_index: number;
  gpu_name: string;
  gpu_utilization: number;
  memory_used_mb: number;
  memory_total_mb: number;
  temperature_c: number;
  power_watts: number;
  recorded_at: string;
}
