import { useCallback } from "react";
import { fetchLeaderboard } from "../api/client";
import { usePolling } from "../hooks/usePolling";

export default function LeaderboardPage() {
  const fetcher = useCallback(() => fetchLeaderboard(), []);
  const { data: entries, loading } = usePolling(fetcher, 10000);

  const totalModels = entries?.length ?? 0;
  const totalTokens = entries
    ? entries.reduce((sum, e) => sum + e.total_input_tokens + e.total_output_tokens, 0)
    : 0;
  const totalJobs = entries
    ? entries.reduce((sum, e) => sum + e.total_jobs, 0)
    : 0;

  function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-gray-900">Model Leaderboard</h1>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs font-medium text-gray-500">Models Tracked</p>
          <p className="text-2xl font-bold text-gray-900">{totalModels}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs font-medium text-gray-500">Total Jobs</p>
          <p className="text-2xl font-bold text-gray-900">{totalJobs}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs font-medium text-gray-500">Total Tokens</p>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(totalTokens)}</p>
        </div>
      </div>

      {loading && !entries && (
        <div className="text-gray-400 text-center py-8">Loading...</div>
      )}

      {entries && entries.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No model data yet. Submit some jobs or comparisons to populate the leaderboard.
        </p>
      )}

      {entries && entries.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Win Rate</th>
                <th className="px-4 py-3">Wins</th>
                <th className="px-4 py-3">Avg Tokens/s</th>
                <th className="px-4 py-3">Avg Time</th>
                <th className="px-4 py-3">Total Tokens</th>
                <th className="px-4 py-3">Jobs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {entries.map((entry, i) => (
                <tr key={entry.model} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400 font-medium">{i + 1}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{entry.model}</td>
                  <td className="px-4 py-3">
                    {entry.win_rate !== null ? (
                      <span className={entry.win_rate >= 0.5 ? "text-green-600 font-medium" : "text-gray-700"}>
                        {(entry.win_rate * 100).toFixed(0)}%
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {entry.comparison_appearances > 0
                      ? `${entry.comparison_wins}/${entry.comparison_appearances}`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {entry.avg_tokens_per_second !== null
                      ? entry.avg_tokens_per_second.toFixed(1)
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {entry.avg_generation_time_ms !== null
                      ? `${(entry.avg_generation_time_ms / 1000).toFixed(1)}s`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {formatNumber(entry.total_input_tokens + entry.total_output_tokens)}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {entry.completed_jobs}/{entry.total_jobs}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
