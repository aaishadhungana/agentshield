import type { LucideIcon } from "lucide-react";
import Link from "next/link";

import type { AgentActivity, RiskLevel } from "@/lib/types";

const TONES = {
  neutral: "bg-slate-800 text-slate-300",
  green: "bg-emerald-500/10 text-emerald-300",
  red: "bg-red-500/10 text-red-300",
  amber: "bg-amber-500/10 text-amber-300",
  orange: "bg-orange-500/10 text-orange-300",
};

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "neutral",
}: {
  label: string;
  value: number;
  hint?: string;
  icon: LucideIcon;
  tone?: keyof typeof TONES;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <span className={`rounded-md p-2 ${TONES[tone]}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

const LEVELS: { level: RiskLevel; bar: string }[] = [
  { level: "low", bar: "bg-slate-500" },
  { level: "medium", bar: "bg-yellow-500" },
  { level: "high", bar: "bg-orange-500" },
  { level: "critical", bar: "bg-red-500" },
];

export function RiskDistribution({ distribution }: { distribution: Record<RiskLevel, number> }) {
  const total = LEVELS.reduce((sum, item) => sum + distribution[item.level], 0);
  if (total === 0) {
    return <p className="text-sm text-slate-500">No events in this period.</p>;
  }
  return (
    <div className="space-y-4">
      {LEVELS.map(({ level, bar }) => {
        const count = distribution[level];
        const percent = Math.round((count / total) * 100);
        return (
          <div key={level}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="capitalize text-slate-300">{level}</span>
              <span className="text-slate-500">
                {count} ({percent}%)
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800">
              <div className={`h-full ${bar}`} style={{ width: `${percent}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function AgentActivityTable({ rows }: { rows: AgentActivity[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">No agent activity in this period.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>
            <th className="pb-2 pr-3 font-medium">Agent</th>
            <th className="pb-2 pr-3 text-right font-medium">Total</th>
            <th className="pb-2 pr-3 text-right font-medium">Allow</th>
            <th className="pb-2 pr-3 text-right font-medium">Block</th>
            <th className="pb-2 pr-3 text-right font-medium">Flag</th>
            <th className="pb-2 text-right font-medium">Max risk</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((row) => (
            <tr key={row.agent_id ?? "deleted"}>
              <td className="py-2 pr-3">
                {row.agent_id ? (
                  <Link href={`/events?agent=${row.agent_id}`} className="text-slate-200 hover:text-emerald-300">
                    {row.agent_name ?? "Unknown agent"}
                  </Link>
                ) : (
                  <span className="text-slate-500">Deleted agent</span>
                )}
              </td>
              <td className="py-2 pr-3 text-right text-slate-300">{row.total}</td>
              <td className="py-2 pr-3 text-right text-emerald-300">{row.allowed}</td>
              <td className="py-2 pr-3 text-right text-red-300">{row.blocked}</td>
              <td className="py-2 pr-3 text-right text-amber-300">{row.flagged}</td>
              <td className="py-2 text-right text-slate-300">{row.max_risk_score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}