import type { GpuMetric } from "../types";

interface Props {
  metrics: GpuMetric[];
}

const CHART_W = 700;
const CHART_H = 200;
const PAD = { top: 10, right: 20, bottom: 30, left: 45 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

const LINES: {
  key: string;
  color: string;
  label: string;
  getValue: (m: GpuMetric) => number;
  max: number;
  unit: string;
}[] = [
  {
    key: "util",
    color: "#60a5fa",
    label: "GPU %",
    getValue: (m) => m.gpu_utilization,
    max: 100,
    unit: "%",
  },
  {
    key: "mem",
    color: "#e879f9",
    label: "Mem %",
    getValue: (m) =>
      m.memory_total_mb > 0
        ? Math.round((m.memory_used_mb / m.memory_total_mb) * 100)
        : 0,
    max: 100,
    unit: "%",
  },
  {
    key: "temp",
    color: "#f87171",
    label: "Temp",
    getValue: (m) => m.temperature_c,
    max: 100,
    unit: "°C",
  },
];

function buildPath(
  points: { x: number; y: number }[]
): string {
  if (points.length === 0) return "";
  return points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
}

export default function GpuChart({ metrics }: Props) {
  if (metrics.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 text-gray-400 text-center">
        No GPU metrics yet — waiting for data...
      </div>
    );
  }

  // Group by gpu_index, show chart for GPU 0 (most common single-GPU setup).
  // If multiple GPUs exist, only chart gpu_index 0 for simplicity.
  const gpu0 = metrics.filter((m) => m.gpu_index === 0);
  if (gpu0.length === 0) return null;

  const gpuName = gpu0[gpu0.length - 1].gpu_name;
  const times = gpu0.map((m) => new Date(m.recorded_at).getTime());
  const tMin = times[0];
  const tMax = times[times.length - 1];
  const tRange = tMax - tMin || 1;

  // Y-axis ticks
  const yTicks = [0, 25, 50, 75, 100];

  // Time ticks (5 evenly spaced)
  const timeTicks: number[] = [];
  for (let i = 0; i < 5; i++) {
    timeTicks.push(tMin + (tRange * i) / 4);
  }

  function formatTime(ts: number): string {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  // Latest values for legend
  const latest = gpu0[gpu0.length - 1];

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">GPU Monitor</h2>
        <span className="text-sm text-gray-400">{gpuName}</span>
      </div>

      {/* Legend */}
      <div className="flex gap-6 mb-3 text-sm">
        {LINES.map((line) => {
          const val = line.getValue(latest);
          return (
            <div key={line.key} className="flex items-center gap-1.5">
              <span
                className="inline-block w-3 h-3 rounded-sm"
                style={{ backgroundColor: line.color }}
              />
              <span className="text-gray-300">
                {line.label}: {val}
                {line.unit}
              </span>
            </div>
          );
        })}
        <div className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-green-500" />
          <span className="text-gray-300">
            Power: {latest.power_watts}W
          </span>
        </div>
      </div>

      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full"
        style={{ maxHeight: 240 }}
      >
        {/* Grid lines */}
        {yTicks.map((tick) => {
          const y = PAD.top + INNER_H - (tick / 100) * INNER_H;
          return (
            <g key={tick}>
              <line
                x1={PAD.left}
                x2={PAD.left + INNER_W}
                y1={y}
                y2={y}
                stroke="#374151"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 6}
                y={y + 4}
                textAnchor="end"
                fill="#9ca3af"
                fontSize={10}
              >
                {tick}
              </text>
            </g>
          );
        })}

        {/* Time labels */}
        {timeTicks.map((ts, i) => {
          const x = PAD.left + ((ts - tMin) / tRange) * INNER_W;
          return (
            <text
              key={i}
              x={x}
              y={CHART_H - 6}
              textAnchor="middle"
              fill="#9ca3af"
              fontSize={10}
            >
              {formatTime(ts)}
            </text>
          );
        })}

        {/* Data lines */}
        {LINES.map((line) => {
          const points = gpu0.map((m, i) => ({
            x: PAD.left + ((times[i] - tMin) / tRange) * INNER_W,
            y:
              PAD.top +
              INNER_H -
              (Math.min(line.getValue(m), line.max) / line.max) * INNER_H,
          }));
          return (
            <path
              key={line.key}
              d={buildPath(points)}
              fill="none"
              stroke={line.color}
              strokeWidth={2}
              strokeLinejoin="round"
            />
          );
        })}
      </svg>
    </div>
  );
}
