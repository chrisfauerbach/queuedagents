import { useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchComparison } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import StatusBadge from "../components/StatusBadge";
import type { Job } from "../types";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  const normalized =
    dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
  return new Date(normalized).toLocaleString();
}

function JobPanel({ job }: { job: Job }) {
  const isLoading = job.status === "pending" || job.status === "processing";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 min-w-[300px] flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-sm font-medium">{job.model}</span>
        <StatusBadge status={job.status} />
      </div>

      <div className="flex-1">
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-gray-400 py-8 justify-center">
            <svg
              className="animate-spin h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            {job.status === "pending" ? "Waiting..." : "Generating..."}
          </div>
        )}

        {job.result && (
          <pre className="bg-gray-50 rounded p-3 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
            {job.result}
          </pre>
        )}

        {job.error && (
          <pre className="bg-red-50 border border-red-200 rounded p-3 text-sm whitespace-pre-wrap text-red-700">
            {job.error}
          </pre>
        )}
      </div>

      {(job.input_tokens != null || job.generation_time_ms != null) && (
        <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-3 gap-2 text-xs text-gray-500">
          <div>
            <div>Input</div>
            <div className="text-gray-900">
              {job.input_tokens?.toLocaleString() ?? "-"}
            </div>
          </div>
          <div>
            <div>Output</div>
            <div className="text-gray-900">
              {job.output_tokens?.toLocaleString() ?? "-"}
            </div>
          </div>
          <div>
            <div>Time</div>
            <div className="text-gray-900">
              {job.generation_time_ms != null
                ? job.generation_time_ms >= 1000
                  ? `${(job.generation_time_ms / 1000).toFixed(1)}s`
                  : `${job.generation_time_ms}ms`
                : "-"}
              {job.output_tokens != null &&
                job.generation_time_ms != null &&
                job.generation_time_ms > 0 && (
                  <span className="text-gray-400 ml-1">
                    ({(job.output_tokens / (job.generation_time_ms / 1000)).toFixed(1)} t/s)
                  </span>
                )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ComparisonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const fetcher = useCallback(() => fetchComparison(id!), [id]);

  const { data: comparison, loading, error } = usePolling(fetcher, 2000);

  const allDone =
    comparison?.jobs.every(
      (j) => j.status === "completed" || j.status === "failed"
    ) ?? false;

  return (
    <div className="space-y-4">
      <Link
        to="/compare"
        className="text-blue-600 hover:underline text-sm"
      >
        &larr; Back to Comparisons
      </Link>

      {loading && !comparison && (
        <div className="text-gray-400 text-center py-8">Loading...</div>
      )}

      {error && (
        <div className="text-red-600 text-center py-8">Error: {error}</div>
      )}

      {comparison && (
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-lg font-semibold text-gray-900">
                {comparison.name}
              </h1>
              {!allDone && (
                <span className="text-xs text-blue-600">Auto-refreshing...</span>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-3">
              <div>
                <div className="text-gray-500">Models</div>
                <div>{comparison.jobs.length}</div>
              </div>
              <div>
                <div className="text-gray-500">Temperature</div>
                <div>{comparison.temperature}</div>
              </div>
              <div>
                <div className="text-gray-500">Max Tokens</div>
                <div>{comparison.max_tokens}</div>
              </div>
              <div>
                <div className="text-gray-500">Created</div>
                <div>{formatDate(comparison.created_at)}</div>
              </div>
            </div>
            {comparison.system_prompt && (
              <div className="mb-2">
                <div className="text-xs text-gray-500 mb-1">System Prompt</div>
                <pre className="bg-gray-50 rounded p-2 text-sm whitespace-pre-wrap">
                  {comparison.system_prompt}
                </pre>
              </div>
            )}
            <div>
              <div className="text-xs text-gray-500 mb-1">Prompt</div>
              <pre className="bg-gray-50 rounded p-2 text-sm whitespace-pre-wrap">
                {comparison.prompt}
              </pre>
            </div>
          </div>

          <div
            className="grid gap-4"
            style={{
              gridTemplateColumns: `repeat(${Math.min(comparison.jobs.length, 3)}, minmax(300px, 1fr))`,
            }}
          >
            {comparison.jobs.map((job) => (
              <JobPanel key={job.id} job={job} />
            ))}
          </div>
          {comparison.jobs.length > 3 && (
            <div className="overflow-x-auto -mx-4 px-4" />
          )}
        </>
      )}
    </div>
  );
}
