import { useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchJob } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import JobDetail from "../components/JobDetail";

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const fetcher = useCallback(() => fetchJob(id!), [id]);

  const { data: job, loading, error } = usePolling(fetcher, 2000);

  return (
    <div className="space-y-4">
      <Link to="/" className="text-blue-600 hover:underline text-sm">
        &larr; Back to Dashboard
      </Link>

      {loading && !job && (
        <div className="text-gray-400 text-center py-8">Loading...</div>
      )}

      {error && (
        <div className="text-red-600 text-center py-8">Error: {error}</div>
      )}

      {job && <JobDetail job={job} />}
    </div>
  );
}
