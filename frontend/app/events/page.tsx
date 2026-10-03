import Link from "next/link";

import EventsTable from "@/components/EventsTable";
import Shell from "@/components/Shell";
import { apiFetch } from "@/lib/api";
import type { Agent, AuditEvent } from "@/lib/types";

const PAGE_SIZE = 20;
const DECISIONS = ["ALLOW", "BLOCK", "FLAG"];
const RISK_FILTERS = [
  { value: "25", label: "Medium and above" },
  { value: "50", label: "High and above" },
  { value: "75", label: "Critical only" },
];
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function single(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

const selectClass =
  "rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500";

export default async function EventsPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;

  const rawDecision = single(params.decision);
  const decision = rawDecision && DECISIONS.includes(rawDecision) ? rawDecision : undefined;
  const rawRisk = single(params.risk);
  const risk = RISK_FILTERS.some((item) => item.value === rawRisk) ? rawRisk : undefined;
  const rawAgent = single(params.agent);
  const agent = rawAgent && UUID_PATTERN.test(rawAgent) ? rawAgent : undefined;
  const page = Math.min(Math.max(Number.parseInt(single(params.page) ?? "1", 10) || 1, 1), 500);

  const query = new URLSearchParams({
    limit: String(PAGE_SIZE + 1),
    offset: String((page - 1) * PAGE_SIZE),
  });
  if (decision) query.set("decision", decision);
  if (risk) query.set("min_risk_score", risk);
  if (agent) query.set("agent_id", agent);

  const [events, agents] = await Promise.all([
    apiFetch<AuditEvent[]>(`/audit/events?${query.toString()}`),
    apiFetch<Agent[]>("/agents?limit=100"),
  ]);
  const agentNames = Object.fromEntries(agents.map((item) => [item.id, item.name]));
  const hasNext = events.length > PAGE_SIZE;
  const rows = events.slice(0, PAGE_SIZE);

  function pageHref(target: number): string {
    const next = new URLSearchParams();
    if (decision) next.set("decision", decision);
    if (risk) next.set("risk", risk);
    if (agent) next.set("agent", agent);
    next.set("page", String(target));
    return `/events?${next.toString()}`;
  }

  return (
    <Shell>
      <h1 className="text-2xl font-semibold text-white">Security events</h1>
      <p className="mt-1 text-sm text-slate-400">Every decision made by the runtime gateway</p>

      <form method="get" action="/events" className="mt-6 flex flex-wrap items-center gap-3">
        <select name="decision" defaultValue={decision ?? ""} className={selectClass}>
          <option value="">All decisions</option>
          {DECISIONS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select name="risk" defaultValue={risk ?? ""} className={selectClass}>
          <option value="">Any risk</option>
          {RISK_FILTERS.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <select name="agent" defaultValue={agent ?? ""} className={selectClass}>
          <option value="">All agents</option>
          {agents.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <button
          type="submit"
          className="rounded-md bg-emerald-500 px-4 py-1.5 text-sm font-medium text-slate-950 hover:bg-emerald-400"
        >
          Apply
        </button>
        <Link href="/events" className="text-sm text-slate-400 hover:text-white">
          Reset
        </Link>
      </form>

      <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <EventsTable events={rows} agentNames={agentNames} />
      </section>

      <div className="mt-4 flex items-center justify-between text-sm">
        {page > 1 ? (
          <Link href={pageHref(page - 1)} className="text-emerald-400 hover:text-emerald-300">
            &larr; Newer
          </Link>
        ) : (
          <span />
        )}
        <span className="text-slate-500">Page {page}</span>
        {hasNext ? (
          <Link href={pageHref(page + 1)} className="text-emerald-400 hover:text-emerald-300">
            Older &rarr;
          </Link>
        ) : (
          <span />
        )}
      </div>
    </Shell>
  );
}