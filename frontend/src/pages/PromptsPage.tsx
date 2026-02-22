import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  createPrompt,
  updatePrompt,
  deletePrompt,
  fetchPrompts,
  fetchModels,
  createComparison,
} from "../api/client";
import { usePolling } from "../hooks/usePolling";
import type { Prompt, OllamaModel } from "../types";

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

function PromptCard({
  prompt,
  models,
  onRefresh,
}: {
  prompt: Prompt;
  models: OllamaModel[];
  onRefresh: () => void;
}) {
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(prompt.name);
  const [editPrompt, setEditPrompt] = useState(prompt.prompt);
  const [editSystemPrompt, setEditSystemPrompt] = useState(
    prompt.system_prompt || ""
  );
  const [editTemperature, setEditTemperature] = useState(
    String(prompt.temperature)
  );
  const [editMaxTokens, setEditMaxTokens] = useState(
    String(prompt.max_tokens)
  );
  const [saving, setSaving] = useState(false);

  const [showRun, setShowRun] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [running, setRunning] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const deleteTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  function toggleModel(name: string) {
    setSelectedModels((prev) =>
      prev.includes(name) ? prev.filter((m) => m !== name) : [...prev, name]
    );
  }

  async function handleRun() {
    if (selectedModels.length < 2) return;
    setRunning(true);
    try {
      const comparison = await createComparison({
        name: `${prompt.name} - Run`,
        prompt: prompt.prompt,
        models: selectedModels,
        system_prompt: prompt.system_prompt || undefined,
        temperature: prompt.temperature,
        max_tokens: prompt.max_tokens,
      });
      navigate(`/compare/${comparison.id}`);
    } catch {
      setRunning(false);
    }
  }

  function handleUseInCompare() {
    navigate("/compare", {
      state: {
        promptName: prompt.name,
        prompt: prompt.prompt,
        system_prompt: prompt.system_prompt,
        temperature: prompt.temperature,
        max_tokens: prompt.max_tokens,
      },
    });
  }

  async function handleSaveEdit() {
    setSaving(true);
    try {
      await updatePrompt(prompt.id, {
        name: editName,
        prompt: editPrompt,
        system_prompt: editSystemPrompt || null,
        temperature: parseFloat(editTemperature),
        max_tokens: parseInt(editMaxTokens),
      });
      setEditing(false);
      onRefresh();
    } finally {
      setSaving(false);
    }
  }

  function handleDelete() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      deleteTimer.current = setTimeout(() => setConfirmDelete(false), 3000);
      return;
    }
    clearTimeout(deleteTimer.current);
    deletePrompt(prompt.id).then(onRefresh);
  }

  function startEdit() {
    setEditName(prompt.name);
    setEditPrompt(prompt.prompt);
    setEditSystemPrompt(prompt.system_prompt || "");
    setEditTemperature(String(prompt.temperature));
    setEditMaxTokens(String(prompt.max_tokens));
    setEditing(true);
  }

  if (editing) {
    return (
      <div className="bg-white rounded-lg border border-blue-300 p-4 space-y-3">
        <div className="flex gap-3">
          <div className="w-48 flex-shrink-0">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Name
            </label>
            <input
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Prompt
            </label>
            <textarea
              value={editPrompt}
              onChange={(e) => setEditPrompt(e.target.value)}
              rows={2}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full resize-none"
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              System Prompt
            </label>
            <input
              type="text"
              value={editSystemPrompt}
              onChange={(e) => setEditSystemPrompt(e.target.value)}
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
              value={editTemperature}
              onChange={(e) => setEditTemperature(e.target.value)}
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
              value={editMaxTokens}
              onChange={(e) => setEditMaxTokens(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={() => setEditing(false)}
            className="px-3 py-1.5 rounded text-sm text-gray-600 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSaveEdit}
            disabled={saving || !editName.trim() || !editPrompt.trim()}
            className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-gray-900">{prompt.name}</span>
        <span className="text-xs text-gray-400">
          {timeAgo(prompt.updated_at)}
        </span>
      </div>
      <p className="text-sm text-gray-500 truncate mb-2">{prompt.prompt}</p>
      {(prompt.system_prompt ||
        prompt.temperature !== 0.7 ||
        prompt.max_tokens !== 2048) && (
        <div className="flex gap-3 text-xs text-gray-400 mb-3">
          {prompt.system_prompt && (
            <span title={prompt.system_prompt}>
              sys: {prompt.system_prompt.slice(0, 30)}
              {prompt.system_prompt.length > 30 ? "..." : ""}
            </span>
          )}
          {prompt.temperature !== 0.7 && (
            <span>temp: {prompt.temperature}</span>
          )}
          {prompt.max_tokens !== 2048 && (
            <span>max: {prompt.max_tokens}</span>
          )}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            setShowRun(!showRun);
            setSelectedModels([]);
          }}
          className="text-sm px-3 py-1 rounded border border-green-300 text-green-700 hover:bg-green-50"
        >
          Run
        </button>
        <button
          onClick={handleUseInCompare}
          className="text-sm px-3 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50"
        >
          Use in Compare
        </button>
        <button
          onClick={startEdit}
          className="text-sm px-3 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
        >
          Edit
        </button>
        <button
          onClick={handleDelete}
          className={`text-sm px-3 py-1 rounded border ${
            confirmDelete
              ? "border-red-400 bg-red-50 text-red-700"
              : "border-red-300 text-red-600 hover:bg-red-50"
          }`}
        >
          {confirmDelete ? "Confirm?" : "Delete"}
        </button>
      </div>

      {showRun && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <label className="block text-xs font-medium text-gray-500 mb-2">
            Select models (2+)
          </label>
          {models.length > 0 ? (
            <div className="flex flex-wrap gap-2 mb-3">
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
            <p className="text-sm text-gray-400 mb-3">
              No models available. Make sure Ollama is running.
            </p>
          )}
          <button
            onClick={handleRun}
            disabled={running || selectedModels.length < 2}
            className="bg-green-600 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {running ? "Creating..." : "Create Comparison"}
          </button>
        </div>
      )}
    </div>
  );
}

export default function PromptsPage() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState("0.7");
  const [maxTokens, setMaxTokens] = useState("2048");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const promptsFetcher = useCallback(() => fetchPrompts(), []);
  const {
    data: prompts,
    loading,
    refresh,
  } = usePolling(promptsFetcher, 5000);

  useEffect(() => {
    fetchModels()
      .then((list) => setModels(list))
      .catch(() => setModels([]));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createPrompt({
        name,
        prompt,
        system_prompt: systemPrompt || undefined,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
      });
      setName("");
      setPrompt("");
      setSystemPrompt("");
      setTemperature("0.7");
      setMaxTokens("2048");
      setShowAdvanced(false);
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
              placeholder="e.g. Code reviewer"
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
              placeholder="Enter prompt to save..."
            />
          </div>
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
            {submitting ? "Saving..." : "Save Prompt"}
          </button>
        </div>
      </form>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Prompt Library
        </h2>
        {loading && !prompts && (
          <div className="text-gray-400 text-center py-4">Loading...</div>
        )}
        {prompts && prompts.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No saved prompts yet. Create one above.
          </p>
        )}
        {prompts && prompts.length > 0 && (
          <div className="space-y-2">
            {prompts.map((p) => (
              <PromptCard
                key={p.id}
                prompt={p}
                models={models}
                onRefresh={refresh}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
