import { Ban, CheckCircle2, Flag } from "lucide-react";

import type { AiStatus, Decision, RiskLevel } from "@/lib/types";

const DECISION_STYLES: Record<Decision, string> = {
  ALLOW: "bg-emerald-500/10 text-emerald-300 ring-emerald-500/30",
  BLOCK: "bg-red-500/10 text-red-300 ring-red-500/30",
  FLAG: "bg-amber-500/10 text-amber-300 ring-amber-500/30",
};

const DECISION_ICONS = {
  ALLOW: CheckCircle2,
  BLOCK: Ban,
  FLAG: Flag,
};

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "bg-slate-500/10 text-slate-300 ring-slate-500/30",
  medium: "bg-yellow-500/10 text-yellow-300 ring-yellow-500/30",
  high: "bg-orange-500/10 text-orange-300 ring-orange-500/30",
  critical: "bg-red-500/10 text-red-300 ring-red-500/30",
};

const AI_LABELS: Record<AiStatus, string> = {
  completed: "AI analysis",
  cached: "AI analysis (reused)",
  pending: "Analyzing",
  unavailable: "AI unavailable",
  disabled: "AI off",
  skipped: "Not needed",
};

const BASE = "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset";

export function DecisionBadge({ decision }: { decision: Decision }) {
  const Icon = DECISION_ICONS[decision];
  return (
    <span className={`${BASE} ${DECISION_STYLES[decision]}`}>
      <Icon className="h-3 w-3" />
      {decision}
    </span>
  );
}

export function RiskBadge({ level, score }: { level: RiskLevel; score?: number }) {
  return (
    <span className={`${BASE} ${RISK_STYLES[level]}`}>
      <span className="capitalize">{level}</span>
      {score !== undefined && <span className="opacity-70">{score}</span>}
    </span>
  );
}

export function AiStatusBadge({ status }: { status: AiStatus }) {
  const style =
    status === "completed" || status === "cached"
      ? "bg-violet-500/10 text-violet-300 ring-violet-500/30"
      : "bg-slate-500/10 text-slate-400 ring-slate-500/30";
  return <span className={`${BASE} ${style}`}>{AI_LABELS[status]}</span>;
}