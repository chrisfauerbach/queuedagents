import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { createComparison, fetchComparisons, fetchModels } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import type { OllamaModel } from "../types";

function formatSize(bytes: number): string {
  const gb = bytes / (1024 * 1024 * 1024);
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(0)} MB`;
}

function timeAgo(dateStr: string): string {
  const normalized =
    dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
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

export default function ComparePage() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState("0.7");
  const [maxTokens, setMaxTokens] = useState("2048");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const comparisonsFetcher = useCallback(() => fetchComparisons(), []);
  const {
    data: comparisons,
    loading,
    refresh,
  } = usePolling(comparisonsFetcher, 5000);

  useEffect(() => {
    fetchModels()
      .then((list) => setModels(list))
      .catch(() => setModels([]));
  }, []);

  function toggleModel(modelName: string) {
    setSelectedModels((prev) =>
      prev.includes(modelName)
        ? prev.filter((m) => m !== modelName)
        : [...prev, modelName]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (selectedModels.length < 2) {
      setError("Select at least 2 models to compare");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createComparison({
        name,
        prompt,
        models: selectedModels,
        system_prompt: systemPrompt || undefined,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
      });
      setName("");
      setPrompt("");
      setSelectedModels([]);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg border border-gray-200 p-4 space-y-3"
      >
        <div className="flex gap-3">
          <div className="w-48 flex-shrink-0">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
              placeholder="e.g. Recursion test"
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={2}
              required
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full resize-none"
              placeholder="Enter prompt to compare across models..."
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">
            Models (select 2+)
          </label>
          {models.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {models.map((m) => (
                <label
                  key={m.name}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded border text-sm cursor-pointer transition-colors ${
                    selectedModels.includes(m.name)
                      ? "bg-blue-50 border-blue-300 text-blue-700"
                      : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(m.name)}
                    onChange={() => toggleModel(m.name)}
                    className="sr-only"
                  />
                  {m.name}
                  <span className="text-xs text-gray-400">
                    ({formatSize(m.size)})
                  </span>
                </label>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              No models available. Make sure Ollama is running.
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          {showAdvanced ? "Hide" : "Show"} advanced options
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                System Prompt
              </label>
              <input
                type="text"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Temperature
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Max Tokens
              </label>
              <input
                type="number"
                min="1"
                max="128000"
                value={maxTokens}
                onChange={(e) => setMaxTokens(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
              />
            </div>
          </div>
        )}

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting || !prompt.trim() || !name.trim()}
            className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Creating..." : "Compare Models"}
          </button>
        </div>
      </form>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Past Comparisons
        </h2>
        {loading && !comparisons && (
          <div className="text-gray-400 text-center py-4">Loading...</div>
        )}
        {comparisons && comparisons.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No comparisons yet. Create one above.
          </p>
        )}
        {comparisons && comparisons.length > 0 && (
          <div className="space-y-2">
            {comparisons.map((c) => {
              const allDone = c.jobs.every(
                (j) => j.status === "completed" || j.status === "failed"
              );
              const completed = c.jobs.filter(
                (j) => j.status === "completed"
              ).length;
              const failed = c.jobs.filter(
                (j) => j.status === "failed"
              ).length;
              return (
                <Link
                  key={c.id}
                  to={`/compare/${c.id}`}
                  className="block bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900">{c.name}</span>
                    <span className="text-xs text-gray-400">
                      {timeAgo(c.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 truncate mb-2">
                    {c.prompt}
                  </p>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-gray-500">
                      {c.jobs.length} model{c.jobs.length !== 1 ? "s" : ""}
                    </span>
                    {allDone ? (
                      <span className="text-green-600">
                        {completed} completed
                        {failed > 0 && `, ${failed} failed`}
                      </span>
                    ) : (
                      <span className="text-blue-600">In progress...</span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
