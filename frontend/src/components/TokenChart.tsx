import type { TokenUsagePoint } from "../types";

interface Props {
  data: TokenUsagePoint[];
}

const CHART_W = 700;
const CHART_H = 200;
const PAD = { top: 10, right: 20, bottom: 30, left: 55 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

const COLORS = [
  "#22d3ee", // cyan
  "#a78bfa", // violet
  "#f97316", // orange
  "#34d399", // emerald
  "#f472b6", // pink
  "#facc15", // yellow
  "#60a5fa", // blue
  "#fb7185", // rose
  "#4ade80", // green
  "#e879f9", // fuchsia
  "#38bdf8", // sky
  "#f87171", // red
  "#a3e635", // lime
  "#2dd4bf", // teal
  "#c084fc", // purple
  "#fbbf24", // amber
];

function buildPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  return points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
}

function formatYLabel(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

export default function TokenChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 text-gray-400 text-center">
        No token usage data yet
      </div>
    );
  }

  // Group by model
  const models = [...new Set(data.map((d) => d.model))];
  const byModel = new Map<string, TokenUsagePoint[]>();
  for (const d of data) {
    if (!byModel.has(d.model)) byModel.set(d.model, []);
    byModel.get(d.model)!.push(d);
  }

  // Time range across all points
  const allTimes = data.map((d) => new Date(d.timestamp).getTime());
  const tMin = Math.min(...allTimes);
  const tMax = Math.max(...allTimes);
  const tRange = tMax - tMin || 1;

  // Y range — max cumulative total across all models
  const yMax = Math.max(...data.map((d) => d.cumulative_total_tokens), 1);

  // Y-axis ticks (5 evenly spaced)
  const yTicks: number[] = [];
  for (let i = 0; i <= 4; i++) {
    yTicks.push(Math.round((yMax * i) / 4));
  }

  // Time ticks (5 evenly spaced)
  const timeTicks: number[] = [];
  for (let i = 0; i < 5; i++) {
    timeTicks.push(tMin + (tRange * i) / 4);
  }

  function formatTime(ts: number): string {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-4">Token Usage</h2>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-3 text-sm">
        {models.map((model, i) => {
          const points = byModel.get(model)!;
          const latest = points[points.length - 1];
          return (
            <div key={model} className="flex items-center gap-1.5">
              <span
                className="inline-block w-3 h-3 rounded-sm"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}
              />
              <span className="text-gray-300">
                {model}: {latest.cumulative_total_tokens.toLocaleString()} tokens
              </span>
            </div>
          );
        })}
      </div>

      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full"
        style={{ maxHeight: 240 }}
      >
        {/* Grid lines + Y labels */}
        {yTicks.map((tick) => {
          const y = PAD.top + INNER_H - (tick / yMax) * INNER_H;
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
                {formatYLabel(tick)}
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

        {/* Data lines — one per model */}
        {models.map((model, i) => {
          const modelPoints = byModel.get(model)!;
          const points = modelPoints.map((d) => ({
            x: PAD.left + ((new Date(d.timestamp).getTime() - tMin) / tRange) * INNER_W,
            y: PAD.top + INNER_H - (d.cumulative_total_tokens / yMax) * INNER_H,
          }));
          return (
            <path
              key={model}
              d={buildPath(points)}
              fill="none"
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              strokeLinejoin="round"
            />
          );
        })}
      </svg>
    </div>
  );
}
