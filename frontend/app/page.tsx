import { Activity, Ban, Bot, CheckCircle2, Flag, ShieldAlert } from "lucide-react";
import Link from "next/link";

import EventsTable from "@/components/EventsTable";
import Shell from "@/components/Shell";
import { AgentActivityTable, RiskDistribution, StatCard } from "@/components/Widgets";
import { apiFetch } from "@/lib/api";
import type { Agent, AuditEvent, DashboardSummary } from "@/lib/types";

export default async function DashboardPage() {
  const [summary, events, agents] = await Promise.all([
    apiFetch<DashboardSummary>("/dashboard/summary?days=7"),
    apiFetch<AuditEvent[]>("/audit/events?limit=8"),
    apiFetch<Agent[]>("/agents?limit=100"),
  ]);
  const agentNames = Object.fromEntries(agents.map((agent) => [agent.id, agent.name]));

  return (
    <Shell>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Security overview</h1>
        <p className="mt-1 text-sm text-slate-400">
          Agent activity over the last {summary.window_days} days
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Agents"
          value={summary.total_agents}
          hint={`${summary.active_agents} active`}
          icon={Bot}
        />
        <StatCard label="Allowed" value={summary.decisions.allow} icon={CheckCircle2} tone="green" />
        <StatCard label="Blocked" value={summary.decisions.block} icon={Ban} tone="red" />
        <StatCard
          label="Flagged for review"
          value={summary.decisions.flag}
          icon={Flag}
          tone="amber"
        />
        <StatCard
          label="High-risk events"
          value={summary.high_risk_events}
          hint="High and critical"
          icon={ShieldAlert}
          tone="orange"
        />
        <StatCard label="Total events" value={summary.total_events} icon={Activity} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="mb-4 font-medium text-white">Risk distribution</h2>
          <RiskDistribution distribution={summary.risk_distribution} />
        </section>
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="mb-4 font-medium text-white">Agent activity</h2>
          <AgentActivityTable rows={summary.agent_activity} />
        </section>
      </div>

      <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium text-white">Recent security events</h2>
          <Link href="/events" className="text-sm text-emerald-400 hover:text-emerald-300">
            View all
          </Link>
        </div>
        <EventsTable events={events} agentNames={agentNames} />
      </section>
    </Shell>
  );
}