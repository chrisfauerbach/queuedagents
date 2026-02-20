import type { Stats } from "../types";

const cards: { key: keyof Stats; label: string; color: string }[] = [
  { key: "total", label: "Total", color: "bg-gray-100 text-gray-800" },
  { key: "pending", label: "Pending", color: "bg-yellow-100 text-yellow-800" },
  {
    key: "processing",
    label: "Processing",
    color: "bg-blue-100 text-blue-800",
  },
  {
    key: "completed",
    label: "Completed",
    color: "bg-green-100 text-green-800",
  },
  { key: "failed", label: "Failed", color: "bg-red-100 text-red-800" },
];

export default function StatsCards({ stats }: { stats: Stats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
      {cards.map((c) => (
        <div
          key={c.key}
          className={`rounded-lg p-4 ${c.color}`}
        >
          <div className="text-2xl font-bold">{stats[c.key]}</div>
          <div className="text-sm">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
