import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchModels,
  fetchCatalog,
  pullModel,
  deleteModel,
} from "../api/client";
import { usePolling } from "../hooks/usePolling";
import type { OllamaModel, CatalogModel, PullProgress } from "../types";

function formatSize(bytes: number): string {
  const gb = bytes / (1024 * 1024 * 1024);
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(0)} MB`;
}

interface ActiveDownload {
  name: string;
  status: string;
  total: number;
  completed: number;
  done: boolean;
  error: string | null;
}

function PullProgressBar({
  name,
  onComplete,
  onError,
}: {
  name: string;
  onComplete: () => void;
  onError: (err: string) => void;
}) {
  const [progress, setProgress] = useState<ActiveDownload>({
    name,
    status: "starting...",
    total: 0,
    completed: 0,
    done: false,
    error: null,
  });
  const controllerRef = useRef<AbortController | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;

    pullModel(
      name,
      (p: PullProgress) => {
        setProgress((prev) => ({
          ...prev,
          status: p.status,
          total: p.total ?? prev.total,
          completed: p.completed ?? prev.completed,
        }));
      },
      controller.signal,
    )
      .then(() => {
        setProgress((prev) => ({ ...prev, done: true, status: "complete" }));
        onCompleteRef.current();
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        const msg = err instanceof Error ? err.message : String(err);
        setProgress((prev) => ({ ...prev, error: msg, status: "failed" }));
        onErrorRef.current(msg);
      });

    return () => {
      controller.abort();
    };
  }, [name]);

  const pct =
    progress.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : 0;

  return (
    <div className="bg-white rounded-lg border border-blue-200 p-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-medium text-sm text-gray-900">{name}</span>
        {progress.error ? (
          <span className="text-xs text-red-600">{progress.error}</span>
        ) : progress.done ? (
          <span className="text-xs text-green-600">Complete</span>
        ) : (
          <span className="text-xs text-gray-500">{progress.status}</span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            progress.error
              ? "bg-red-500"
              : progress.done
                ? "bg-green-500"
                : "bg-blue-500"
          }`}
          style={{ width: `${progress.done ? 100 : pct}%` }}
        />
      </div>
      {progress.total > 0 && !progress.done && !progress.error && (
        <div className="text-xs text-gray-400 mt-1">
          {formatSize(progress.completed)} / {formatSize(progress.total)} ({pct}
          %)
        </div>
      )}
    </div>
  );
}

function InstalledModelRow({
  model,
  onDeleted,
}: {
  model: OllamaModel;
  onDeleted: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const deleteTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  function handleDelete() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      deleteTimer.current = setTimeout(() => setConfirmDelete(false), 3000);
      return;
    }
    clearTimeout(deleteTimer.current);
    setDeleting(true);
    deleteModel(model.name)
      .then(onDeleted)
      .catch(() => setDeleting(false));
  }

  return (
    <tr className="border-b border-gray-100 last:border-b-0">
      <td className="py-2 px-4 font-medium text-sm text-gray-900">
        {model.name}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {formatSize(model.size)}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {model.family || "-"}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {model.parameter_size || "-"}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {model.quantization_level || "-"}
      </td>
      <td className="py-2 px-4 text-right">
        <button
          onClick={handleDelete}
          disabled={deleting}
          className={`text-sm px-3 py-1 rounded border ${
            confirmDelete
              ? "border-red-400 bg-red-50 text-red-700"
              : "border-red-300 text-red-600 hover:bg-red-50"
          } disabled:opacity-50`}
        >
          {deleting ? "Deleting..." : confirmDelete ? "Confirm?" : "Delete"}
        </button>
      </td>
    </tr>
  );
}

export default function ModelsPage() {
  const modelsFetcher = useCallback(() => fetchModels(), []);
  const {
    data: models,
    loading: modelsLoading,
    refresh: refreshModels,
  } = usePolling(modelsFetcher, 5000);

  const [catalog, setCatalog] = useState<CatalogModel[] | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const [downloads, setDownloads] = useState<string[]>([]);
  const [customName, setCustomName] = useState("");

  const loadCatalog = useCallback(() => {
    setCatalogLoading(true);
    fetchCatalog()
      .then(setCatalog)
      .catch(() => setCatalog([]))
      .finally(() => setCatalogLoading(false));
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  function startPull(name: string) {
    if (downloads.includes(name)) return;
    setDownloads((prev) => [...prev, name]);
  }

  function handlePullComplete(name: string) {
    setDownloads((prev) => prev.filter((d) => d !== name));
    refreshModels();
    loadCatalog();
  }

  function handlePullError(name: string) {
    // Keep in list briefly so user sees error, then remove
    setTimeout(() => {
      setDownloads((prev) => prev.filter((d) => d !== name));
    }, 5000);
  }

  function handleCustomPull(e: React.FormEvent) {
    e.preventDefault();
    const name = customName.trim();
    if (!name) return;
    startPull(name);
    setCustomName("");
  }

  const totalSize = models
    ? models.reduce((sum, m) => sum + m.size, 0)
    : 0;

  const categories = catalog
    ? [...new Set(catalog.map((m) => m.category))]
    : [];

  const filteredCatalog = catalog
    ? activeCategory
      ? catalog.filter((m) => m.category === activeCategory)
      : catalog
    : [];

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-gray-900">
            {models ? models.length : "-"}
          </div>
          <div className="text-sm text-gray-500">Installed Models</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-gray-900">
            {models ? formatSize(totalSize) : "-"}
          </div>
          <div className="text-sm text-gray-500">Total Disk Usage</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-blue-600">
            {downloads.length}
          </div>
          <div className="text-sm text-gray-500">Active Downloads</div>
        </div>
      </div>

      {/* Active downloads */}
      {downloads.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Active Downloads
          </h2>
          <div className="space-y-2">
            {downloads.map((name) => (
              <PullProgressBar
                key={name}
                name={name}
                onComplete={() => handlePullComplete(name)}
                onError={() => handlePullError(name)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom pull form */}
      <form
        onSubmit={handleCustomPull}
        className="bg-white rounded-lg border border-gray-200 p-4"
      >
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Pull a model by name
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            placeholder="e.g. llama3.1:8b"
            className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1"
          />
          <button
            type="submit"
            disabled={!customName.trim()}
            className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Pull
          </button>
        </div>
      </form>

      {/* Installed models table */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Installed Models
        </h2>
        {modelsLoading && !models && (
          <div className="text-gray-400 text-center py-4">Loading...</div>
        )}
        {models && models.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No models installed. Pull one from the catalog below or enter a
            custom name above.
          </p>
        )}
        {models && models.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-4 text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="text-left py-2 px-4 text-xs font-medium text-gray-500 uppercase">
                    Size
                  </th>
                  <th className="text-left py-2 px-4 text-xs font-medium text-gray-500 uppercase">
                    Family
                  </th>
                  <th className="text-left py-2 px-4 text-xs font-medium text-gray-500 uppercase">
                    Parameters
                  </th>
                  <th className="text-left py-2 px-4 text-xs font-medium text-gray-500 uppercase">
                    Quantization
                  </th>
                  <th className="py-2 px-4"></th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <InstalledModelRow
                    key={m.name}
                    model={m}
                    onDeleted={() => {
                      refreshModels();
                      loadCatalog();
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model catalog */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Model Catalog
        </h2>

        {catalogLoading && (
          <div className="text-gray-400 text-center py-4">Loading...</div>
        )}

        {!catalogLoading && catalog && (
          <>
            {/* Category filter pills */}
            <div className="flex flex-wrap gap-2 mb-4">
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-3 py-1 rounded-full text-sm border ${
                  activeCategory === null
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}
              >
                All
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() =>
                    setActiveCategory(cat === activeCategory ? null : cat)
                  }
                  className={`px-3 py-1 rounded-full text-sm border ${
                    activeCategory === cat
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Model cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredCatalog.map((model) => (
                <div
                  key={model.name}
                  className="bg-white rounded-lg border border-gray-200 p-4"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900">
                      {model.name}
                    </span>
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {model.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mb-3">
                    {model.description}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {model.variants.map((v) =>
                      v.installed ? (
                        <span
                          key={v.tag}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-green-300 bg-green-50 text-green-700 text-xs"
                        >
                          {v.parameter_size}
                          <svg
                            className="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        </span>
                      ) : (
                        <button
                          key={v.tag}
                          onClick={() => startPull(v.full_name)}
                          disabled={downloads.includes(v.full_name)}
                          className="px-2.5 py-1 rounded border border-gray-300 text-gray-600 text-xs hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {downloads.includes(v.full_name)
                            ? "Pulling..."
                            : v.parameter_size}
                        </button>
                      ),
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
