import { Link } from "react-router-dom";
import type { Job } from "../types";
import StatusBadge from "./StatusBadge";

function timeAgo(dateStr: string): string {
  const normalized = dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
  const seconds = Math.floor(
    (Date.now() - new Date(normalized).getTime()) / 1000
  );
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function JobList({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8">
        No jobs yet. Submit one above.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-gray-500">
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Model</th>
            <th className="py-2 pr-4">Prompt</th>
            <th className="py-2 pr-4">Tokens</th>
            <th className="py-2 pr-4">Created</th>
            <th className="py-2" />
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2 pr-4">
                <StatusBadge status={job.status} />
              </td>
              <td className="py-2 pr-4 font-mono text-xs">{job.model}</td>
              <td className="py-2 pr-4 max-w-xs truncate">{job.prompt}</td>
              <td className="py-2 pr-4 text-gray-500 font-mono text-xs whitespace-nowrap">
                {job.input_tokens != null
                  ? `${job.input_tokens}/${job.output_tokens ?? 0}`
                  : "-"}
              </td>
              <td className="py-2 pr-4 text-gray-500">
                {timeAgo(job.created_at)}
              </td>
              <td className="py-2">
                <Link
                  to={`/jobs/${job.id}`}
                  className="text-blue-600 hover:underline"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
