import { useState } from "react";
import { createJob } from "../api/client";

export default function JobSubmitForm({
  onSubmitted,
}: {
  onSubmitted: () => void;
}) {
  const [model, setModel] = useState("gemma3:12b");
  const [prompt, setPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState("0.7");
  const [maxTokens, setMaxTokens] = useState("2048");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createJob({
        model,
        prompt,
        system_prompt: systemPrompt || undefined,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
      });
      setPrompt("");
      onSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Model
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm w-40"
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
            placeholder="Enter your prompt..."
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
          disabled={submitting || !prompt.trim()}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "Submitting..." : "Submit Job"}
        </button>
      </div>
    </form>
  );
}
