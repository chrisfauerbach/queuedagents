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

export interface OllamaModel {
  name: string;
  size: number;
  family: string | null;
  parameter_size: string | null;
  quantization_level: string | null;
}

export interface Comparison {
  id: string;
  name: string;
  prompt: string;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  created_at: string;
  jobs: Job[];
}

export interface ComparisonCreatePayload {
  name: string;
  prompt: string;
  models: string[];
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface TokenUsagePoint {
  model: string;
  timestamp: string;
  cumulative_input_tokens: number;
  cumulative_output_tokens: number;
  cumulative_total_tokens: number;
  job_count: number;
}

export interface ModelLeaderboardEntry {
  model: string;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  avg_tokens_per_second: number | null;
  avg_generation_time_ms: number | null;
  total_input_tokens: number;
  total_output_tokens: number;
  comparison_wins: number;
  comparison_appearances: number;
  win_rate: number | null;
}

export interface Prompt {
  id: string;
  name: string;
  prompt: string;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface PromptCreatePayload {
  name: string;
  prompt: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface PromptUpdatePayload {
  name?: string;
  prompt?: string;
  system_prompt?: string | null;
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

export interface CatalogVariant {
  tag: string;
  parameter_size: string;
  full_name: string;
  installed: boolean;
}

export interface CatalogModel {
  name: string;
  description: string;
  category: string;
  variants: CatalogVariant[];
}

export interface ModelShowInfo {
  license: string | null;
  modelfile: string | null;
  template: string | null;
  system: string | null;
  parameters: string | null;
  family: string | null;
  parameter_size: string | null;
  quantization_level: string | null;
}

export interface PullProgress {
  status: string;
  digest?: string;
  total?: number;
  completed?: number;
}
