const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "/api" : "")).replace(/\/$/, "");

export interface Workspace { id: string; name: string; role: string; created_at?: string; }
export interface User { id: string; email: string; created_at?: string; }
export interface AuthPayload { user: User; workspaces: Workspace[]; }
export interface MissionScope { mode: string; scenario_ids: string[]; entity_ids: string[]; excluded_targets: string[]; }
export interface Mission {
  id: string; objective: string; state: string; version: number; autonomy_tier: string;
  scope: MissionScope; created_at: string; updated_at?: string;
}
export interface WorldEntity {
  id: string; entity_type: string; name: string; environment_id: string; source_class: "synthetic";
  attributes: Record<string, string | number | boolean | null>; created_at?: string;
}
export interface WorldRelationship {
  id: string; from_entity_id: string; to_entity_id: string; relationship_type: string; source_class: "synthetic";
}
export interface Verification {
  id?: string; status: "verified" | "failed" | "disputed" | "inconclusive" | string;
  verifier_version?: string;
  checks?: Array<{ check: string; passed: boolean | null; reason?: string }>;
  reasons?: string[]; discrepancies?: Array<Record<string, unknown>>;
  evidence_ids?: string[]; evidence_fingerprints?: Record<string, string>;
  scope?: string; limitations?: string[]; created_at?: string;
}
export interface VerificationHistory { items: Verification[]; latest: Verification | null; }
export interface Scenario {
  id: string; name: string; category: string; description: string; enabled: boolean;
  fixture_version: string; rule_set_version: string; source_class: "synthetic"; limitations: string[];
}
export interface ScenarioCatalog { items: Scenario[]; catalog_version: string; }
export interface Evidence {
  id: string; evidence_type: string; source_class: "synthetic"; source_ref: string; producer?: string;
  producer_version?: string; content_digest: string; payload: Record<string, unknown>;
  limitations: string[]; created_at?: string;
}
export interface MissionJob {
  id: string; mission_id: string; scenario_id: string; status: string; outcome?: string | null;
}
export interface SimulationRun {
  id: string; mission_id: string; scenario_id: string; outcome: string; status: string;
  started_at?: string; completed_at?: string; baseline_id?: string; fixture_version?: string;
  rule_set_version?: string; input_digest?: string; output_digest?: string;
  result: Record<string, unknown>; evidence: Evidence[];
}

function readCookie(name: string): string {
  if (typeof document === "undefined") return "";
  const prefix = name + "=";
  const value = document.cookie.split("; ").find((part) => part.startsWith(prefix));
  if (!value) return "";
  try { return decodeURIComponent(value.slice(prefix.length)); }
  catch { return value.slice(prefix.length); }
}

async function requestText(path: string, workspaceId: string): Promise<string> {
  const headers = new Headers({ Accept: "text/markdown" });
  headers.set("X-Workspace-ID", workspaceId);
  const response = await fetch(API_BASE + path, { method: "GET", headers, credentials: "include" });
  if (!response.ok) {
    let message = "The request could not be completed.";
    let code = "REQUEST_FAILED";
    try {
      const payload = await response.json();
      message = payload?.error?.message || message;
      code = payload?.error?.code || code;
    } catch { message = response.statusText || message; }
    throw new Error(code + ": " + message);
  }
  return response.text();
}

async function request<T>(path: string, options: {
  method?: string; body?: unknown; workspaceId?: string; idempotencyKey?: string;
} = {}): Promise<T> {
  const method = options.method || "GET";
  const headers = new Headers({ Accept: "application/json" });
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.workspaceId) headers.set("X-Workspace-ID", options.workspaceId);
  if (options.idempotencyKey) headers.set("Idempotency-Key", options.idempotencyKey);
  if (!["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase())) {
    const csrf = readCookie("nexorion_csrf");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(API_BASE + path, {
    method, headers, credentials: "include",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.ok) {
    let message = "The request could not be completed.";
    let code = "REQUEST_FAILED";
    try {
      const payload = await response.json();
      message = payload?.error?.message || message;
      code = payload?.error?.code || code;
    } catch { message = response.statusText || message; }
    throw new Error(code + ": " + message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  me: () => request<AuthPayload>("/v1/auth/me"),
  login: (email: string, password: string) =>
    request<AuthPayload>("/v1/auth/login", { method: "POST", body: { email, password } }),
  register: (email: string, password: string, workspace_name: string) =>
    request<AuthPayload>("/v1/auth/register", { method: "POST", body: { email, password, workspace_name } }),
  logout: () => request<void>("/v1/auth/logout", { method: "POST" }),
  missions: (workspaceId: string) => request<Mission[]>("/v1/missions?limit=100", { workspaceId }),
  createMission: (workspaceId: string, objective: string, scenarioId: string) =>
    request<Mission>("/v1/missions", {
      method: "POST", workspaceId,
      body: { objective, scope: { mode: "synthetic_only", scenario_ids: [scenarioId], entity_ids: [], excluded_targets: ["all real systems and external networks"] }, autonomy_tier: "simulate_synthetic" },
    }),
  entities: (workspaceId: string) => request<WorldEntity[]>("/v1/world/entities?limit=200", { workspaceId }),
  relationships: (workspaceId: string) => request<WorldRelationship[]>("/v1/world/relationships?limit=200", { workspaceId }),
  createEntity: (workspaceId: string, name: string, entity_type: string) =>
    request<WorldEntity>("/v1/world/entities", { method: "POST", workspaceId, body: { name, entity_type, environment_id: "synthetic-lab", attributes: { origin: "user-created synthetic fixture" } } }),
  captureBaseline: (workspaceId: string, missionId: string) =>
    request<unknown>("/v1/missions/" + encodeURIComponent(missionId) + "/baselines", { method: "POST", workspaceId, body: {} }),
  missionCommand: (workspaceId: string, missionId: string, command: string, expectedVersion: number) =>
    request<Mission>("/v1/missions/" + encodeURIComponent(missionId) + "/commands", {
      method: "POST", workspaceId,
      body: { command, expected_version: expectedVersion, reason: "workspace user requested mission workflow step" },
    }),
  enqueueJob: (workspaceId: string, missionId: string, scenarioId: string, idempotencyKey: string) =>
    request<MissionJob>("/v1/missions/" + encodeURIComponent(missionId) + "/jobs", {
      method: "POST", workspaceId, idempotencyKey,
      body: { scenario_id: scenarioId, idempotency_key: idempotencyKey },
    }),
  runs: (workspaceId: string, missionId: string) =>
    request<SimulationRun[]>("/v1/missions/" + encodeURIComponent(missionId) + "/runs?limit=100", { workspaceId }),
  simulate: (workspaceId: string, missionId: string, scenarioId: string, idempotencyKey: string) =>
    request<SimulationRun>("/v1/missions/" + encodeURIComponent(missionId) + "/simulate", { method: "POST", workspaceId, idempotencyKey, body: { scenario_id: scenarioId } }),
  scenarios: () => request<ScenarioCatalog>("/v1/scenarios"),
  verifyRun: (workspaceId: string, missionId: string, runId: string, idempotencyKey: string) =>
    request<Verification>("/v1/missions/" + encodeURIComponent(missionId) + "/runs/" + encodeURIComponent(runId) + "/verify", { method: "POST", workspaceId, idempotencyKey }),
  verificationHistory: (workspaceId: string, missionId: string, runId: string) =>
    request<VerificationHistory>("/v1/missions/" + encodeURIComponent(missionId) + "/runs/" + encodeURIComponent(runId) + "/verification", { workspaceId }),
  missionReport: (workspaceId: string, missionId: string) =>
    request<Record<string, unknown>>("/v1/missions/" + encodeURIComponent(missionId) + "/report", { workspaceId }),
  missionReportMarkdown: (workspaceId: string, missionId: string) =>
    requestText("/v1/missions/" + encodeURIComponent(missionId) + "/report.md", workspaceId),
};