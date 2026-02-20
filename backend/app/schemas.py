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
