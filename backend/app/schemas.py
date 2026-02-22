from datetime import datetime

from pydantic import BaseModel, Field

from shared.models import JobStatus


class JobCreate(BaseModel):
    model: str = Field(..., max_length=100, examples=["gemma3:12b"])
    prompt: str = Field(..., min_length=1)
    system_prompt: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=128000)


class JobResponse(BaseModel):
    id: str
    model: str
    prompt: str
    system_prompt: str | None
    temperature: float
    max_tokens: int
    status: JobStatus
    result: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    input_tokens: int | None
    output_tokens: int | None
    generation_time_ms: int | None

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    total: int


class OllamaModelResponse(BaseModel):
    name: str
    size: int
    family: str | None = None
    parameter_size: str | None = None
    quantization_level: str | None = None


class ComparisonCreate(BaseModel):
    name: str = Field(..., max_length=200)
    prompt: str = Field(..., min_length=1)
    models: list[str] = Field(..., min_length=1)
    system_prompt: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=128000)


class ComparisonResponse(BaseModel):
    id: str
    name: str
    prompt: str
    system_prompt: str | None
    temperature: float
    max_tokens: int
    created_at: datetime
    jobs: list[JobResponse]

    model_config = {"from_attributes": True}


class PromptCreate(BaseModel):
    name: str = Field(..., max_length=200)
    prompt: str = Field(..., min_length=1)
    system_prompt: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=128000)


class PromptUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    prompt: str | None = Field(None, min_length=1)
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=128000)


class PromptResponse(BaseModel):
    id: str
    name: str
    prompt: str
    system_prompt: str | None
    temperature: float
    max_tokens: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenUsagePoint(BaseModel):
    model: str
    timestamp: datetime
    cumulative_input_tokens: int
    cumulative_output_tokens: int
    cumulative_total_tokens: int
    job_count: int


class ModelLeaderboardEntry(BaseModel):
    model: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    avg_tokens_per_second: float | None
    avg_generation_time_ms: float | None
    total_input_tokens: int
    total_output_tokens: int
    comparison_wins: int
    comparison_appearances: int
    win_rate: float | None


class GpuMetricResponse(BaseModel):
    id: int
    gpu_index: int
    gpu_name: str
    gpu_utilization: int
    memory_used_mb: int
    memory_total_mb: int
    temperature_c: int
    power_watts: float
    recorded_at: datetime

    model_config = {"from_attributes": True}
