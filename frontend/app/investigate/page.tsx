import { ArrowLeft, Sparkles } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import AutoRefresh from "@/components/AutoRefresh";
import { AiStatusBadge, DecisionBadge, RiskBadge } from "@/components/Badges";
import Shell from "@/components/Shell";
import { apiFetch, apiFetchOrNull } from "@/lib/api";
import { formatDateTime, labelize } from "@/lib/format";
import type { Agent, AuditEvent, Decision } from "@/lib/types";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const FALLBACK_GUIDANCE: Record<Decision, string> = {
  ALLOW:
    "No action is required unless the risk signals above look unexpected for this agent.",
  BLOCK:
    "The request was denied and nothing was executed. Check whether the agent's permissions need to change, or whether this agent is behaving unexpectedly.",
  FLAG:
    "Review this request before treating it as safe, and confirm with the agent's owner that it was intended.",
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">{title}</h2>
      {children}
    </section>
  );
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-0.5 break-all text-sm text-slate-200">{value}</dd>
    </div>
  );
}

export default async function InvestigatePage({
  searchParams,
}: {
  searchParams: Promise<{ id?: string }>;
}) {
  const { id } = await searchParams;
  if (!id || !UUID_PATTERN.test(id)) {
    notFound();
  }

  const event = await apiFetch<AuditEvent>(`/audit/events/${id}`);
  const agent = event.agent_id ? await apiFetchOrNull<Agent>(`/agents/${event.agent_id}`) : null;
  const agentName = agent?.name ?? "A deleted or inaccessible agent";
  const analysis = event.ai_analysis;
  const escalated = event.policy_decision !== null && event.policy_decision !== event.decision;

  return (
    <Shell>
      {event.ai_status === "pending" && <AutoRefresh />}

      <Link
        href="/events"
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        All events
      </Link>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">Event investigation</h1>
        <DecisionBadge decision={event.decision} />
        <RiskBadge level={event.risk_level} score={event.risk_score} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="What happened?">
          <p className="text-sm leading-6 text-slate-300">
            <span className="font-medium text-white">{agentName}</span> requested{" "}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">{event.action}</code> using{" "}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">{event.tool}</code> on{" "}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">{event.resource}</code>.
          </p>
          <p className="mt-3 text-xs text-slate-500">Parameters (secrets are redacted before storage)</p>
          <pre className="mt-1 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-300">
            {Object.keys(event.parameters).length > 0
              ? JSON.stringify(event.parameters, null, 2)
              : "No parameters"}
          </pre>
        </Section>

        <Section title="Who performed it, and what was targeted?">
          <dl className="grid grid-cols-2 gap-4">
            <Fact
              label="Agent"
              value={
                event.agent_id ? (
                  <Link
                    href={`/events?agent=${event.agent_id}`}
                    className="text-emerald-400 hover:text-emerald-300"
                  >
                    {agentName}
                  </Link>
                ) : (
                  agentName
                )
              }
            />
            <Fact label="Source IP" value={event.ip_address ?? "Unknown"} />
            <Fact label="Tool" value={event.tool} />
            <Fact label="Action" value={event.action} />
            <Fact label="Resource" value={event.resource} />
            <Fact label="Time" value={formatDateTime(event.created_at)} />
            <Fact label="Request ID" value={event.request_id} />
            <Fact label="Event ID" value={event.id} />
          </dl>
        </Section>

        <Section title="Why was it considered risky?">
          <div className="mb-4">
            <div className="mb-1 flex justify-between text-sm">
              <span className="text-slate-300">Risk score</span>
              <span className="text-slate-400">{event.risk_score} / 100</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className={`h-full ${
                  event.risk_score >= 75
                    ? "bg-red-500"
                    : event.risk_score >= 50
                      ? "bg-orange-500"
                      : event.risk_score >= 25
                        ? "bg-yellow-500"
                        : "bg-slate-500"
                }`}
                style={{ width: `${event.risk_score}%` }}
              />
            </div>
          </div>
          {event.risk_signals.length === 0 ? (
            <p className="text-sm text-slate-500">No risk signals were raised for this request.</p>
          ) : (
            <ul className="space-y-3">
              {event.risk_signals.map((signal) => (
                <li key={signal.code} className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{labelize(signal.code)}</p>
                    <p className="text-xs text-slate-400">{signal.detail}</p>
                  </div>
                  <span className="shrink-0 text-xs text-slate-500">+{signal.points}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="What decision was made?">
          <div className="flex flex-wrap items-center gap-3">
            <DecisionBadge decision={event.decision} />
            <span className="font-mono text-xs text-slate-400">{event.reason_code}</span>
          </div>
          <p className="mt-3 text-sm text-slate-300">{event.reason}</p>
          {escalated && event.policy_decision && (
            <p className="mt-3 rounded-md bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
              The permission policy said {event.policy_decision}, but the risk engine changed the
              outcome to {event.decision}.
            </p>
          )}
        </Section>

        <Section title="What did Gemini identify?">
          <div className="mb-3">
            <AiStatusBadge status={event.ai_status} />
          </div>
          {analysis ? (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Sparkles className="h-4 w-4 text-violet-300" />
                <span className="text-sm font-medium text-white">{labelize(analysis.category)}</span>
                <RiskBadge level={analysis.risk_level} />
              </div>
              <p className="text-sm leading-6 text-slate-300">{analysis.reason}</p>
              <p className="text-xs text-slate-500">
                AI output is advisory. The decision above came from the deterministic policy and risk
                engines.
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-400">
              {event.ai_status === "pending" && "The analysis is running and this page will update."}
              {event.ai_status === "unavailable" &&
                "The AI service could not analyze this event. The decision was not affected."}
              {event.ai_status === "disabled" &&
                "AI analysis is turned off because no Gemini API key is configured."}
              {event.ai_status === "skipped" &&
                "This event scored low enough that AI analysis was not needed."}
            </p>
          )}
        </Section>

        <Section title="What should be done?">
          <p className="text-sm leading-6 text-slate-300">
            {analysis?.recommendation ?? FALLBACK_GUIDANCE[event.decision]}
          </p>
        </Section>
      </div>
    </Shell>
  );
}