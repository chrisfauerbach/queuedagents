import { useCallback, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchComparison, setComparisonWinner, clearComparisonWinner } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import StatusBadge from "../components/StatusBadge";
import type { Job } from "../types";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  const normalized =
    dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
  return new Date(normalized).toLocaleString();
}

function ThumbsUpIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth={filled ? 0 : 1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m10.598-9.75H14.25M5.904 18.5c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z"
      />
    </svg>
  );
}

function JobPanel({
  job,
  isWinner,
  allDone,
  onToggleWinner,
}: {
  job: Job;
  isWinner: boolean;
  allDone: boolean;
  onToggleWinner: (jobId: string) => void;
}) {
  const isLoading = job.status === "pending" || job.status === "processing";

  return (
    <div
      className={`bg-white rounded-lg border-2 p-4 min-w-[300px] flex flex-col transition-colors ${
        isWinner
          ? "border-green-400 ring-2 ring-green-100"
          : "border-gray-200"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-sm font-medium">{job.model}</span>
        <div className="flex items-center gap-2">
          {allDone && job.status === "completed" && (
            <button
              onClick={() => onToggleWinner(job.id)}
              className={`p-1 rounded transition-colors ${
                isWinner
                  ? "text-green-600 hover:text-green-700"
                  : "text-gray-300 hover:text-gray-500"
              }`}
              title={isWinner ? "Remove rating" : "Rate as best"}
            >
              <ThumbsUpIcon filled={isWinner} />
            </button>
          )}
          <StatusBadge status={job.status} />
        </div>
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
  const [saving, setSaving] = useState(false);

  const { data: comparison, loading, error, refresh } = usePolling(fetcher, 2000);

  const allDone =
    comparison?.jobs.every(
      (j) => j.status === "completed" || j.status === "failed"
    ) ?? false;

  async function handleToggleWinner(jobId: string) {
    if (!comparison || saving) return;
    setSaving(true);
    try {
      if (comparison.winner_job_id === jobId) {
        await clearComparisonWinner(comparison.id);
      } else {
        await setComparisonWinner(comparison.id, jobId);
      }
      refresh();
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  }

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
              <JobPanel
                key={job.id}
                job={job}
                isWinner={comparison.winner_job_id === job.id}
                allDone={allDone}
                onToggleWinner={handleToggleWinner}
              />
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
