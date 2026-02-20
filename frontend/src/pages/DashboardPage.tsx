import { useCallback } from "react";
import { fetchJobs, fetchStats, fetchGpuMetrics } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import StatsCards from "../components/StatsCards";
import JobList from "../components/JobList";
import JobSubmitForm from "../components/JobSubmitForm";
import GpuChart from "../components/GpuChart";

export default function DashboardPage() {
  const statsFetcher = useCallback(() => fetchStats(), []);
  const jobsFetcher = useCallback(() => fetchJobs(), []);
  const gpuFetcher = useCallback(() => fetchGpuMetrics(10), []);

  const { data: stats, loading: statsLoading } = usePolling(statsFetcher, 3000);
  const {
    data: jobs,
    loading: jobsLoading,
    refresh: refreshJobs,
  } = usePolling(jobsFetcher, 3000);
  const { data: gpuMetrics } = usePolling(gpuFetcher, 5000);

  function handleSubmitted() {
    refreshJobs();
  }

  return (
    <div className="space-y-6">
      {stats && <StatsCards stats={stats} />}
      {statsLoading && !stats && (
        <div className="text-gray-400 text-center py-4">Loading stats...</div>
      )}

      {gpuMetrics && <GpuChart metrics={gpuMetrics} />}

      <JobSubmitForm onSubmitted={handleSubmitted} />

      {jobs && <JobList jobs={jobs} />}
      {jobsLoading && !jobs && (
        <div className="text-gray-400 text-center py-4">Loading jobs...</div>
      )}
    </div>
  );
}
