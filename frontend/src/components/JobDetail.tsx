import type { Job } from "../types";
import StatusBadge from "./StatusBadge";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  const normalized = dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
  return new Date(normalized).toLocaleString();
}

export default function JobDetail({ job }: { job: Job }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <StatusBadge status={job.status} />
        <span className="font-mono text-sm text-gray-500">{job.id}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div>
          <div className="text-gray-500">Model</div>
          <div className="font-mono">{job.model}</div>
        </div>
        <div>
          <div className="text-gray-500">Temperature</div>
          <div>{job.temperature}</div>
        </div>
        <div>
          <div className="text-gray-500">Max Tokens</div>
          <div>{job.max_tokens}</div>
        </div>
        <div>
          <div className="text-gray-500">Created</div>
          <div>{formatDate(job.created_at)}</div>
        </div>
      </div>

      {job.system_prompt && (
        <div>
          <div className="text-sm text-gray-500 mb-1">System Prompt</div>
          <pre className="bg-gray-100 rounded p-3 text-sm whitespace-pre-wrap">
            {job.system_prompt}
          </pre>
        </div>
      )}

      <div>
        <div className="text-sm text-gray-500 mb-1">Prompt</div>
        <pre className="bg-gray-100 rounded p-3 text-sm whitespace-pre-wrap">
          {job.prompt}
        </pre>
      </div>

      {job.result && (
        <div>
          <div className="text-sm text-gray-500 mb-1">Result</div>
          <pre className="bg-green-50 border border-green-200 rounded p-3 text-sm whitespace-pre-wrap">
            {job.result}
          </pre>
        </div>
      )}

      {job.error && (
        <div>
          <div className="text-sm text-gray-500 mb-1">Error</div>
          <pre className="bg-red-50 border border-red-200 rounded p-3 text-sm whitespace-pre-wrap text-red-700">
            {job.error}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 text-sm text-gray-500">
        <div>
          <div>Started</div>
          <div className="text-gray-900">{formatDate(job.started_at)}</div>
        </div>
        <div>
          <div>Completed</div>
          <div className="text-gray-900">{formatDate(job.completed_at)}</div>
        </div>
      </div>

      {job.input_tokens != null && (
        <div className="grid grid-cols-3 gap-4 text-sm text-gray-500">
          <div>
            <div>Input Tokens</div>
            <div className="text-gray-900">{job.input_tokens.toLocaleString()}</div>
          </div>
          <div>
            <div>Output Tokens</div>
            <div className="text-gray-900">{job.output_tokens?.toLocaleString() ?? "-"}</div>
          </div>
          <div>
            <div>Generation Time</div>
            <div className="text-gray-900">
              {job.generation_time_ms != null
                ? job.generation_time_ms >= 1000
                  ? `${(job.generation_time_ms / 1000).toFixed(1)}s`
                  : `${job.generation_time_ms}ms`
                : "-"}
              {job.output_tokens != null && job.generation_time_ms != null && job.generation_time_ms > 0 && (
                <span className="text-gray-400 ml-1">
                  ({(job.output_tokens / (job.generation_time_ms / 1000)).toFixed(1)} tok/s)
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
