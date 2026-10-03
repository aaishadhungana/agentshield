import Link from "next/link";

import { DecisionBadge, RiskBadge } from "@/components/Badges";
import { timeAgo } from "@/lib/format";
import type { AuditEvent } from "@/lib/types";

export default function EventsTable({
  events,
  agentNames,
}: {
  events: AuditEvent[];
  agentNames: Record<string, string>;
}) {
  if (events.length === 0) {
    return <p className="py-6 text-center text-sm text-slate-500">No events match.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>
            <th className="pb-2 pr-4 font-medium">Time</th>
            <th className="pb-2 pr-4 font-medium">Agent</th>
            <th className="pb-2 pr-4 font-medium">Action</th>
            <th className="pb-2 pr-4 font-medium">Decision</th>
            <th className="pb-2 font-medium">Risk</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {events.map((event) => (
            <tr key={event.id} className="hover:bg-slate-800/40">
              <td className="whitespace-nowrap py-3 pr-4 text-slate-400">{timeAgo(event.created_at)}</td>
              <td className="py-3 pr-4 text-slate-300">
                {event.agent_id ? (agentNames[event.agent_id] ?? "Unknown agent") : "Deleted agent"}
              </td>
              <td className="py-3 pr-4">
                <Link
                  href={`/investigate?id=${event.id}`}
                  className="font-mono text-xs text-slate-200 hover:text-emerald-300"
                >
                  {event.tool}.{event.action} &rarr; {event.resource}
                </Link>
              </td>
              <td className="py-3 pr-4">
                <DecisionBadge decision={event.decision} />
              </td>
              <td className="py-3">
                <RiskBadge level={event.risk_level} score={event.risk_score} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}