export type Decision = "ALLOW" | "BLOCK" | "FLAG";
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type AiStatus =
  | "skipped"
  | "disabled"
  | "pending"
  | "completed"
  | "cached"
  | "unavailable";

export interface RiskSignal {
  code: string;
  points: number;
  detail: string;
}

export interface AiAnalysis {
  risk_level: RiskLevel;
  category: string;
  reason: string;
  recommendation: string;
}

export interface AuditEvent {
  id: string;
  request_id: string;
  agent_id: string | null;
  owner_id: string | null;
  tool: string;
  action: string;
  resource: string;
  parameters: Record<string, unknown>;
  ip_address: string | null;
  decision: Decision;
  policy_decision: Decision | null;
  reason_code: string;
  reason: string;
  risk_score: number;
  risk_level: RiskLevel;
  risk_signals: RiskSignal[];
  ai_status: AiStatus;
  ai_analysis: AiAnalysis | null;
  created_at: string;
}

export interface Agent {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
}

export interface AgentActivity {
  agent_id: string | null;
  agent_name: string | null;
  total: number;
  allowed: number;
  blocked: number;
  flagged: number;
  max_risk_score: number;
}

export interface DashboardSummary {
  window_days: number;
  total_agents: number;
  active_agents: number;
  total_events: number;
  decisions: { allow: number; block: number; flag: number };
  high_risk_events: number;
  risk_distribution: Record<RiskLevel, number>;
  agent_activity: AgentActivity[];
}