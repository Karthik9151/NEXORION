import {
  Activity, AlertTriangle, Archive, ArrowUpRight, BadgeCheck, Check, CheckCircle2,
  ChevronDown, ChevronRight, CircleHelp, Clock3, Command, Compass, Database, Download,
  FileCheck2, FileJson, FileText, Filter, Fingerprint, FlaskConical, GitBranch, Globe2,
  LayoutDashboard, LockKeyhole, LogOut, Menu, Moon, MoreHorizontal, Network, Plus, Radar,
  RefreshCw, Search, Server, Settings2, Shield, ShieldAlert, ShieldCheck, Sun, Users, X,
  type LucideIcon,
} from "lucide-react";
import {
  Background, Controls, MiniMap, ReactFlow, type Edge as FlowEdge, type Node as FlowNode,
} from "@xyflow/react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api, type AuthPayload, type Evidence, type Mission, type SimulationRun, type User, type Workspace, type WorldEntity, type WorldRelationship } from "./api";

type Screen = "missions" | "world" | "simulation" | "evidence" | "reports" | "settings";
type Theme = "obsidian" | "polar";
type ApiStatus = "checking" | "online" | "offline" | "sample";

const NAV: Array<{ id: Screen; label: string; icon: LucideIcon; group: string }> = [
  { id: "missions", label: "Mission Center", icon: LayoutDashboard, group: "WORKSPACE" },
  { id: "world", label: "Digital World", icon: Network, group: "WORKSPACE" },
  { id: "simulation", label: "Simulation Lab", icon: FlaskConical, group: "OPERATIONS" },
  { id: "evidence", label: "Evidence & Origo", icon: FileCheck2, group: "OPERATIONS" },
  { id: "reports", label: "Reports", icon: FileText, group: "INTELLIGENCE" },
  { id: "settings", label: "Settings", icon: Settings2, group: "SYSTEM" },
];

const SCENARIOS = [
  { id: "scenario-auth-failure-v1", name: "Authentication Failure Pattern", category: "IDENTITY", description: "Five synthetic failures followed by a success inside the fixed rule window.", enabled: true, icon: LockKeyhole },
  { id: "scenario-auth-benign-control-v1", name: "Benign Control Sequence", category: "CONTROL", description: "A registered control fixture with repeated failures and no following success.", enabled: true, icon: ShieldCheck },
  { id: "scenario-lateral-movement-planned", name: "Lateral Movement", category: "NETWORK", description: "Scenario catalog placeholder. No executable fixture is registered yet.", enabled: false, icon: GitBranch },
  { id: "scenario-data-exfiltration-planned", name: "Data Exfiltration", category: "DATA", description: "Scenario catalog placeholder. No executable fixture is registered yet.", enabled: false, icon: Database },
];

const DEMO_MISSIONS: Mission[] = [
  {
    id: "sample-mission-01",
    objective: "Investigate synthetic authentication-failure sequence",
    state: "active",
    version: 2,
    autonomy_tier: "simulate_synthetic",
    scope: { mode: "synthetic_only", scenario_ids: ["scenario-auth-failure-v1"], entity_ids: [], excluded_targets: ["all real systems and external networks"] },
    created_at: "2026-10-10T09:15:00Z",
  },
  {
    id: "sample-mission-02",
    objective: "Validate baseline integrity and fixture provenance",
    state: "succeeded",
    version: 4,
    autonomy_tier: "observe_explain",
    scope: { mode: "synthetic_only", scenario_ids: ["scenario-auth-benign-control-v1"], entity_ids: [], excluded_targets: ["all real systems and external networks"] },
    created_at: "2026-10-09T14:35:00Z",
  },
  {
    id: "sample-mission-03",
    objective: "Map service dependencies in the synthetic application",
    state: "draft",
    version: 1,
    autonomy_tier: "plan",
    scope: { mode: "synthetic_only", scenario_ids: ["scenario-auth-benign-control-v1"], entity_ids: [], excluded_targets: ["all real systems and external networks"] },
    created_at: "2026-10-08T11:20:00Z",
  },
];

const DEMO_ENTITIES: WorldEntity[] = [
  { id: "asset-identity", entity_type: "identity", name: "Synthetic User", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { trust: "test identity", zone: "lab-a" } },
  { id: "asset-app", entity_type: "host", name: "Web Application", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { role: "fictional application", exposure: "simulated" } },
  { id: "asset-auth", entity_type: "service", name: "Auth Service", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { version: "fixture-1.0", controls: "teaching rule" } },
  { id: "asset-db", entity_type: "dataset", name: "Synthetic User Store", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { data_class: "fictional", records: 1200 } },
  { id: "asset-log", entity_type: "log_source", name: "Auth Event Stream", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { producer: "fixture", source: "local data only" } },
  { id: "asset-policy", entity_type: "control", name: "Session Policy", environment_id: "synthetic-lab", source_class: "synthetic", attributes: { baseline: "captured", version: "v1" } },
];

const DEMO_RELATIONSHIPS: WorldRelationship[] = [
  { id: "rel-1", from_entity_id: "asset-identity", to_entity_id: "asset-app", relationship_type: "authenticates_to", source_class: "synthetic" },
  { id: "rel-2", from_entity_id: "asset-app", to_entity_id: "asset-auth", relationship_type: "depends_on", source_class: "synthetic" },
  { id: "rel-3", from_entity_id: "asset-auth", to_entity_id: "asset-db", relationship_type: "authenticates_to", source_class: "synthetic" },
  { id: "rel-4", from_entity_id: "asset-auth", to_entity_id: "asset-log", relationship_type: "emits", source_class: "synthetic" },
  { id: "rel-5", from_entity_id: "asset-policy", to_entity_id: "asset-auth", relationship_type: "belongs_to", source_class: "synthetic" },
];

const SAMPLE_DIGEST = "6bc9a22c4f9f0f7b2e4c0f7a9fd2e83d8b4d8bdbb6a3b7ec4c2ed7f621aa9a10";
const DEMO_EVIDENCE: Evidence = {
  id: "sample-evidence-001",
  evidence_type: "synthetic_auth_event_cluster",
  source_class: "synthetic",
  source_ref: "fixture://auth-failure/sequence-a",
  producer: "nexorion-synthetic-simulator",
  producer_version: "0.1.0",
  content_digest: SAMPLE_DIGEST,
  payload: { scenario_id: "scenario-auth-failure-v1", outcome: "suspicious_auth_pattern", supporting_event_ids: ["E1", "E2", "E3", "E4", "E5", "E6"], event_count: 6 },
  limitations: ["Synthetic fixture only.", "Teaching threshold is not calibrated for real-world detection."],
  created_at: "2026-10-10T09:32:00Z",
};

const DEMO_RUNS: SimulationRun[] = [
  {
    id: "sample-run-001",
    mission_id: "sample-mission-02",
    scenario_id: "scenario-auth-benign-control-v1",
    outcome: "repeated_auth_failures",
    status: "completed",
    started_at: "2026-10-09T14:48:00Z",
    completed_at: "2026-10-09T14:48:01Z",
    fixture_version: "1.0.0",
    rule_set_version: "auth-failure-rules-v1",
    input_digest: "10f4b8bcaf12e064b02b4be2d6806cbbf75bbf8349159790935bc5f9847a6d10",
    output_digest: SAMPLE_DIGEST,
    result: {
      summary: "Repeated synthetic authentication failures were recorded without the required success-after-threshold pattern.",
      source_class: "synthetic",
      verification: {
        status: "verified",
        scope: "deterministic fixture assertions only",
        checks: [
          { check: "registered_fixture_only", passed: true },
          { check: "synthetic_source_label", passed: true },
          { check: "fixture_event_count", passed: true },
          { check: "expected_fixture_outcome", passed: true },
          { check: "evidence_references_resolve", passed: true },
        ],
        limitations: ["This is a sample UI record, not a live backend result."],
      },
    },
    evidence: [DEMO_EVIDENCE],
  },
];

function timeAgo(value?: string): string {
  if (!value) return "—";
  const elapsed = Math.max(0, Date.now() - new Date(value).getTime());
  const mins = Math.floor(elapsed / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + "m ago";
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + "h ago";
  return Math.floor(hours / 24) + "d ago";
}

function formatDate(value?: string): string {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, { year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function StatusTag({ value }: { value: string }) {
  const key = value.toLowerCase().replace(/[\s_-]+/g, "-");
  let tone = "neutral";
  if (["active", "succeeded", "completed", "verified", "cleaned", "safe", "online", "passed", "registered", "ready", "authenticated", "enforced", "available"].includes(key)) tone = "success";
  else if (["running", "warning", "suspicious", "review-required", "pending", "inconclusive", "sample", "bounded", "captured", "on-run"].includes(key)) tone = "warning";
  else if (["failed", "malicious", "high-risk", "disputed", "unauthorized", "unavailable"].includes(key)) tone = "danger";
  else if (["draft", "planned", "not-started", "offline"].includes(key)) tone = "muted";
  return <span className={"status-tag " + tone}><span className="tag-dot" />{value.replace(/-/g, " ")}</span>;
}

function LogoMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48" className="brand-mark">
      <path d="M24 4 44 42H4L24 4Z" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinejoin="round" />
      <path d="M24 13 34 34H14L24 13Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M24 13V34M14 34l10-8 10 8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function MetricCard({ label, value, hint, icon: Icon, trend }: { label: string; value: string | number; hint: string; icon: LucideIcon; trend?: string }) {
  return (
    <div className="metric-card">
      <div className="metric-top"><span className="metric-label">{label}</span><span className="metric-icon"><Icon size={17} /></span></div>
      <div className="metric-value">{value}</div>
      <div className="metric-foot"><span>{hint}</span>{trend && <span className="metric-trend"><ArrowUpRight size={12} />{trend}</span>}</div>
    </div>
  );
}

function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    try { return (localStorage.getItem("nexorion-theme") as Theme) || "obsidian"; } catch { return "obsidian"; }
  });
  const [screen, setScreen] = useState<Screen>("missions");
  const [booting, setBooting] = useState(true);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [demoMode, setDemoMode] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [missions, setMissions] = useState<Mission[]>(DEMO_MISSIONS);
  const [entities, setEntities] = useState<WorldEntity[]>(DEMO_ENTITIES);
  const [relationships, setRelationships] = useState<WorldRelationship[]>(DEMO_RELATIONSHIPS);
  const [runs, setRuns] = useState<SimulationRun[]>(DEMO_RUNS);
  const [selectedMissionId, setSelectedMissionId] = useState("sample-mission-01");
  const [selectedScenarioId, setSelectedScenarioId] = useState(SCENARIOS[0].id);
  const [selectedEntity, setSelectedEntity] = useState<WorldEntity | null>(DEMO_ENTITIES[1]);
  const [searchText, setSearchText] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("Research Workspace");
  const [authBusy, setAuthBusy] = useState(false);
  const [showMissionModal, setShowMissionModal] = useState(false);
  const [missionObjective, setMissionObjective] = useState("Investigate a synthetic authentication-failure sequence");
  const [missionScenario, setMissionScenario] = useState(SCENARIOS[0].id);
  const [showEntityModal, setShowEntityModal] = useState(false);
  const [entityName, setEntityName] = useState("Synthetic service");
  const [entityType, setEntityType] = useState("service");
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [evidenceFilter, setEvidenceFilter] = useState("all");

  const isSample = demoMode || apiStatus === "sample" || (!user && apiStatus === "offline");
  const selectedMission = missions.find((item) => item.id === selectedMissionId) || missions[0];
  const selectedScenario = SCENARIOS.find((item) => item.id === selectedScenarioId) || SCENARIOS[0];
  const registeredScenarios = SCENARIOS.filter((item) => item.enabled);

  const notify = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 4200);
  }, []);

  const refreshWorkspace = useCallback(async (id: string) => {
    if (!id) return;
    try {
      const [nextMissions, nextEntities, nextRelationships] = await Promise.all([
        api.missions(id), api.entities(id), api.relationships(id),
      ]);
      setMissions(nextMissions);
      setEntities(nextEntities);
      setRelationships(nextRelationships);
      setSelectedMissionId((current) => nextMissions.some((mission) => mission.id === current) ? current : (nextMissions[0]?.id || ""));
      if (nextMissions[0]) {
        const nextRuns = await api.runs(id, nextMissions[0].id).catch(() => []);
        setRuns(nextRuns);
      } else {
        setRuns([]);
      }
      setApiStatus("online");
    } catch {
      setApiStatus("offline");
      notify("API unavailable. Your session is kept, but writes are paused until the API reconnects.");
    }
  }, [notify]);

  useEffect(() => {
    let cancelled = false;
    api.me().then(async (payload: AuthPayload) => {
      if (cancelled) return;
      setUser(payload.user);
      setWorkspaces(payload.workspaces);
      setWorkspaceId(payload.workspaces[0]?.id || "");
      setDemoMode(false);
      if (payload.workspaces[0]) await refreshWorkspace(payload.workspaces[0].id);
    }).catch(() => {
      if (!cancelled) setApiStatus("offline");
    }).finally(() => {
      if (!cancelled) setBooting(false);
    });
    return () => { cancelled = true; };
  }, [refreshWorkspace]);

  useEffect(() => {
    try { localStorage.setItem("nexorion-theme", theme); } catch { /* storage is optional */ }
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (!user || !workspaceId || demoMode || !selectedMission) return;
    let cancelled = false;
    api.runs(workspaceId, selectedMission.id).then((items) => {
      if (!cancelled) setRuns((current) => {
        const retained = current.filter((run) => run.mission_id !== selectedMission.id);
        return [...retained, ...items].sort((a, b) => (b.started_at || "").localeCompare(a.started_at || ""));
      });
    }).catch(() => { if (!cancelled) setRuns([]); });
    return () => { cancelled = true; };
  }, [user, workspaceId, demoMode, selectedMission?.id]);

  const visibleMissions = missions.filter((mission) => {
    const query = searchText.trim().toLowerCase();
    return !query || mission.objective.toLowerCase().includes(query) || mission.id.toLowerCase().includes(query);
  });

  const missionRuns = selectedMission ? runs.filter((run) => run.mission_id === selectedMission.id) : [];
  const allEvidence = runs.flatMap((run) => run.evidence.map((item) => ({ ...item, mission_id: run.mission_id, run_id: run.id, outcome: run.outcome })));
  const visibleEvidence = allEvidence.filter((item) => evidenceFilter === "all" || item.evidence_type.toLowerCase().includes(evidenceFilter));
  const verifiedRuns = runs.filter((run) => ((run.result.verification as { status?: string } | undefined)?.status || "") === "verified").length;
  const activeCount = missions.filter((mission) => ["active", "running", "verifying"].includes(mission.state)).length;
  const completedCount = missions.filter((mission) => ["completed", "succeeded"].includes(mission.state)).length;

  const graphNodes: FlowNode[] = useMemo(() => {
    const positions = [
      { x: 360, y: 80 }, { x: 115, y: 210 }, { x: 360, y: 220 },
      { x: 590, y: 210 }, { x: 225, y: 395 }, { x: 480, y: 390 },
      { x: 680, y: 390 }, { x: 80, y: 390 },
    ];
    return entities.map((entity, index) => ({
      id: entity.id,
      position: positions[index % positions.length],
      data: { label: entity.name, entity },
      style: {
        borderRadius: 12,
        border: "1px solid var(--border-strong)",
        background: theme === "obsidian" ? "#1b1b20" : "#ffffff",
        color: "var(--text-primary)",
        boxShadow: "0 8px 22px rgba(0,0,0,.14)",
        fontSize: 12,
        fontWeight: 600,
        minWidth: 132,
        padding: "11px 13px",
      },
    }));
  }, [entities, theme]);

  const graphEdges: FlowEdge[] = useMemo(() => relationships
    .filter((relationship) => entities.some((entity) => entity.id === relationship.from_entity_id) && entities.some((entity) => entity.id === relationship.to_entity_id))
    .map((relationship) => ({
      id: relationship.id,
      source: relationship.from_entity_id,
      target: relationship.to_entity_id,
      label: relationship.relationship_type.replace(/_/g, " "),
      type: "smoothstep",
      animated: false,
      style: { stroke: theme === "obsidian" ? "#9d8136" : "#748197", strokeWidth: 1.35 },
      labelStyle: { fill: "var(--text-secondary)", fontSize: 9 },
      labelBgStyle: { fill: "var(--panel)", fillOpacity: 0.92 },
    })), [relationships, entities, theme]);

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    try {
      const payload = authMode === "login"
        ? await api.login(authEmail.trim(), authPassword)
        : await api.register(authEmail.trim(), authPassword, workspaceName.trim() || "Research Workspace");
      setUser(payload.user);
      setWorkspaces(payload.workspaces);
      setWorkspaceId(payload.workspaces[0]?.id || "");
      setDemoMode(false);
      setApiStatus("online");
      if (payload.workspaces[0]) await refreshWorkspace(payload.workspaces[0].id);
      setScreen("missions");
      notify(authMode === "login" ? "Session established." : "Workspace created. Welcome to NEXORION.");
    } catch (error) {
      notify(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setAuthBusy(false);
    }
  }

  function enterDemo() {
    setUser(null);
    setDemoMode(true);
    setApiStatus("sample");
    setWorkspaces([]);
    setMissions(DEMO_MISSIONS);
    setEntities(DEMO_ENTITIES);
    setRelationships(DEMO_RELATIONSHIPS);
    setRuns(DEMO_RUNS);
    setSelectedMissionId(DEMO_MISSIONS[0].id);
    setScreen("missions");
  }

  async function handleLogout() {
    try { await api.logout(); } catch { /* clear local view even if API is unavailable */ }
    setUser(null);
    setDemoMode(false);
    setWorkspaces([]);
    setWorkspaceId("");
    setApiStatus("offline");
    notify("Signed out of the workspace.");
  }

  async function createMission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const objective = missionObjective.trim();
    if (objective.length < 10) {
      notify("Write a mission objective with at least 10 characters.");
      return;
    }
    setBusy(true);
    try {
      if (demoMode) {
        const created: Mission = {
          id: "sample-mission-" + Date.now(),
          objective,
          state: "draft",
          version: 1,
          autonomy_tier: "simulate_synthetic",
          scope: { mode: "synthetic_only", scenario_ids: [missionScenario], entity_ids: [], excluded_targets: ["all real systems and external networks"] },
          created_at: new Date().toISOString(),
        };
        setMissions((current) => [created, ...current]);
        setSelectedMissionId(created.id);
        notify("Sample mission created in this browser session only.");
      } else {
        if (!user || apiStatus !== "online" || !workspaceId) throw new Error("Connect to a workspace before creating a persistent mission.");
        const created = await api.createMission(workspaceId, objective, missionScenario);
        setMissions((current) => [created, ...current]);
        setSelectedMissionId(created.id);
        notify("Mission saved to the selected workspace.");
      }
      setShowMissionModal(false);
      setScreen("simulation");
    } catch (error) {
      notify(error instanceof Error ? error.message : "Could not create the mission.");
    } finally {
      setBusy(false);
    }
  }

  async function createEntity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!entityName.trim()) return;
    setBusy(true);
    try {
      if (demoMode) {
        const created: WorldEntity = {
          id: "sample-asset-" + Date.now(),
          entity_type: entityType,
          name: entityName.trim(),
          environment_id: "synthetic-lab",
          source_class: "synthetic",
          attributes: { origin: "browser-session sample" },
        };
        setEntities((current) => [...current, created]);
        setSelectedEntity(created);
        notify("Sample entity added in this browser session only.");
      } else {
        if (!user || apiStatus !== "online" || !workspaceId) throw new Error("Connect to a workspace before adding a persistent entity.");
        const created = await api.createEntity(workspaceId, entityName.trim(), entityType);
        setEntities((current) => [...current, created]);
        setSelectedEntity(created);
        notify("Synthetic entity saved.");
      }
      setShowEntityModal(false);
    } catch (error) {
      notify(error instanceof Error ? error.message : "Could not create the entity.");
    } finally {
      setBusy(false);
    }
  }

  async function runScenario() {
    const selectedScenario = SCENARIOS.find((item) => item.id === selectedScenarioId) || SCENARIOS[0];
    if (!selectedScenario.enabled) {
      notify("This scenario is a catalog placeholder; its registered fixture is not implemented.");
      return;
    }
    if (!selectedMission) {
      notify("Create a synthetic mission before running a fixture.");
      setShowMissionModal(true);
      return;
    }
    setBusy(true);
    try {
      if (demoMode) {
        const suspicious = selectedScenario.id === "scenario-auth-failure-v1";
        const now = new Date().toISOString();
        const sampleRun: SimulationRun = {
          id: "sample-run-" + Date.now(),
          mission_id: selectedMission.id,
          scenario_id: selectedScenario.id,
          outcome: suspicious ? "suspicious_auth_pattern" : "repeated_auth_failures",
          status: "completed",
          started_at: now,
          completed_at: now,
          fixture_version: "1.0.0",
          rule_set_version: "auth-failure-rules-v1",
          input_digest: SAMPLE_DIGEST,
          output_digest: SAMPLE_DIGEST,
          result: {
            summary: suspicious
              ? "A synthetic success followed at least five matching failures inside the configured window."
              : "Repeated synthetic authentication failures were recorded without the required success-after-threshold pattern.",
            source_class: "synthetic",
            verification: {
              status: "verified",
              scope: "sample UI fixture only",
              checks: [{ check: "registered_fixture_only", passed: true }, { check: "synthetic_source_label", passed: true }, { check: "fixture_event_count", passed: true }, { check: "expected_fixture_outcome", passed: true }, { check: "evidence_references_resolve", passed: true }],
              limitations: ["Sample data only; not generated by the backend."],
            },
          },
          evidence: [{ ...DEMO_EVIDENCE, id: "sample-evidence-" + Date.now(), payload: { ...DEMO_EVIDENCE.payload, scenario_id: selectedScenario.id, outcome: suspicious ? "suspicious_auth_pattern" : "repeated_auth_failures" }, created_at: now }],
        };
        setRuns((current) => [sampleRun, ...current]);
        setMissions((current) => current.map((mission) => mission.id === selectedMission.id ? { ...mission, state: "succeeded", version: mission.version + 1 } : mission));
        notify("Sample simulation complete. Results are illustrative and not persisted.");
      } else {
        if (!user || apiStatus !== "online" || !workspaceId) throw new Error("The API is unavailable. Reconnect before running a simulation.");
        if (selectedMission.state !== "draft") throw new Error("This backend allows one run per draft mission. Create a new mission for another run.");
        if (selectedMission.autonomy_tier !== "simulate_synthetic") throw new Error("This mission does not have the simulate_synthetic autonomy tier.");
        await api.captureBaseline(workspaceId, selectedMission.id);
        const idempotencyKey = "nexorion-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 12);
        const result = await api.simulate(workspaceId, selectedMission.id, selectedScenario.id, idempotencyKey);
        setRuns((current) => [result, ...current.filter((run) => run.id !== result.id)]);
        setMissions((current) => current.map((mission) => mission.id === selectedMission.id ? { ...mission, state: "succeeded", version: mission.version + 1 } : mission));
        notify("Registered synthetic fixture completed and returned by the API.");
      }
      setScreen("evidence");
    } catch (error) {
      notify(error instanceof Error ? error.message : "Simulation could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  function exportReport(run: SimulationRun, format: "json" | "md") {
    const report = {
      platform: "NEXORION",
      environment: "SYNTHETIC (ISOLATED)",
      report_scope: "Registered synthetic fixture and bounded deterministic checks only",
      mission_id: run.mission_id,
      run_id: run.id,
      scenario_id: run.scenario_id,
      outcome: run.outcome,
      verification: run.result.verification || { status: "not supplied" },
      evidence: run.evidence,
      result: run.result,
      input_digest: run.input_digest,
      output_digest: run.output_digest,
      limitations: ["Synthetic data only.", "This output does not describe a real environment.", "Fixture consistency checks are not a full independent verifier."],
    };
    let content = "";
    let filename = "";
    if (format === "json") {
      content = JSON.stringify(report, null, 2);
      filename = "nexorion-report-" + run.id + ".json";
    } else {
      content = [
        "# NEXORION Synthetic Mission Report", "",
        "- Environment: SYNTHETIC (ISOLATED)",
        "- Mission: " + run.mission_id,
        "- Run: " + run.id,
        "- Scenario: " + run.scenario_id,
        "- Outcome: " + run.outcome,
        "- Verification: " + String((run.result.verification as { status?: string } | undefined)?.status || "not supplied"),
        "", "## Summary", "", String(run.result.summary || "No summary was returned."),
        "", "## Evidence", "",
        ...run.evidence.map((item) => "- " + item.evidence_type + " · " + item.source_ref + " · SHA-256 " + item.content_digest),
        "", "## Limitations", "",
        "- Synthetic fixture only; not a real-world observation.",
        "- The registered fixture verifier checks deterministic consistency, not a real system.",
      ].join("\n");
      filename = "nexorion-report-" + run.id + ".md";
    }
    const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
    notify("Report export prepared as " + format.toUpperCase() + ".");
  }

  const changeScreen = (next: Screen) => {
    setScreen(next);
    setMobileMenuOpen(false);
  };

  if (booting) {
    return <div className="boot-screen"><LogoMark /><div className="boot-title">NEXORION</div><div className="loader-line" /><span>Establishing workspace session…</span></div>;
  }

  if (!user && !demoMode) {
    return (
      <div className="auth-shell" data-theme={theme}>
        <div className="auth-aside">
          <div className="brand brand-large"><LogoMark /><div><div className="brand-name">NEXORION</div><div className="brand-subtitle">SYNTHETIC CYBER RESEARCH PLATFORM</div></div></div>
          <div className="auth-hero">
            <div className="eyebrow"><span className="pulse-dot" /> RESEARCH ENVIRONMENT · ISOLATED</div>
            <h1>Model the world.<br /><em>Verify every result.</em></h1>
            <p>Explore synthetic systems, run reproducible security fixtures, and preserve the evidence trail in one governed research workspace.</p>
            <div className="auth-feature"><span><Network size={17} /></span><div><strong>Persistent digital world</strong><small>Typed entities, relationships, and versioned baselines</small></div></div>
            <div className="auth-feature"><span><Fingerprint size={17} /></span><div><strong>Evidence by design</strong><small>Provenance, digests, bounded checks, and limitations</small></div></div>
            <div className="auth-feature"><span><ShieldCheck size={17} /></span><div><strong>Synthetic by default</strong><small>No live target execution or real credential operations</small></div></div>
          </div>
          <div className="auth-footer">RESEARCH · INTELLIGENCE · A SAFER DIGITAL FUTURE</div>
        </div>
        <div className="auth-main">
          <div className="auth-topline"><span>WORKSPACE ACCESS</span><button className="icon-button" aria-label="Toggle theme" onClick={() => setTheme(theme === "obsidian" ? "polar" : "obsidian")}>{theme === "obsidian" ? <Sun size={17} /> : <Moon size={17} />}</button></div>
          <form className="auth-card" onSubmit={handleAuth}>
            <div className="section-kicker">NEXORION IDENTITY</div>
            <h2>{authMode === "login" ? "Welcome back" : "Create a workspace"}</h2>
            <p>{authMode === "login" ? "Sign in to continue your research session." : "Register to create a private workspace for synthetic research."}</p>
            {authMode === "register" && <label className="field-label">Workspace name<input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} minLength={2} maxLength={100} placeholder="Research Workspace" required /></label>}
            <label className="field-label">Email address<input type="email" autoComplete="email" value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} placeholder="analyst@example.com" required /></label>
            <label className="field-label">Password<input type="password" autoComplete={authMode === "login" ? "current-password" : "new-password"} value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} minLength={authMode === "register" ? 12 : 1} maxLength={128} placeholder={authMode === "register" ? "At least 12 characters" : "Enter your password"} required /></label>
            <button className="button button-primary button-wide" disabled={authBusy} type="submit">{authBusy ? "Connecting…" : authMode === "login" ? "Sign in securely" : "Create workspace"}<ChevronRight size={16} /></button>
            <div className="auth-switch">{authMode === "login" ? "New to NEXORION?" : "Already have a workspace?"}<button type="button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create account" : "Sign in"}</button></div>
            <div className="auth-divider"><span>OR</span></div>
            <button className="button button-secondary button-wide" type="button" onClick={enterDemo}><Compass size={16} /> Explore sample environment</button>
            <div className="auth-note"><Shield size={14} /> Demo actions remain in this browser session and are not sent to the API.</div>
          </form>
          <div className="auth-legal">By continuing, use only synthetic data and workspaces you are authorized to access.</div>
        </div>
        {toast && <div className="toast" role="status">{toast}</div>}
      </div>
    );
  }

  return (
    <div className={"app-shell theme-" + theme} data-theme={theme}>
      <header className="topbar">
        <div className="brand"><LogoMark /><div><div className="brand-name">NEXORION</div><div className="brand-subtitle">SYNTHETIC CYBER RESEARCH PLATFORM</div></div></div>
        <nav className="top-links" aria-label="Primary sections">
          <button onClick={() => changeScreen("world")} className={screen === "world" ? "selected" : ""}>Explore</button><span>·</span>
          <button onClick={() => changeScreen("simulation")} className={screen === "simulation" ? "selected" : ""}>Simulate</button><span>·</span>
          <button onClick={() => changeScreen("evidence")} className={screen === "evidence" ? "selected" : ""}>Verify</button><span>·</span>
          <button onClick={() => changeScreen("reports")} className={screen === "reports" ? "selected" : ""}>Defend</button>
        </nav>
        <div className="top-context"><span>AI-DRIVEN INTELLIGENCE</span><i /> <span>SYNTHETIC ENVIRONMENT</span><i /> <span>RESEARCH AT SCALE</span></div>
        <button className="mobile-menu-button icon-button" aria-label="Open navigation" onClick={() => setMobileMenuOpen((value) => !value)}><Menu size={19} /></button>
      </header>

      <div className="environment-strip">
        <span className="env-indicator"><span className="env-ring"><Shield size={12} /></span> ENV: SYNTHETIC (ISOLATED)</span>
        <span className="environment-copy">{demoMode ? "SAMPLE WORKSPACE · BROWSER SESSION ONLY" : user ? "WORKSPACE SCOPED · AUTHENTICATED" : "API CONNECTION REQUIRED"}</span>
        <span className={"connection-state " + (apiStatus === "online" ? "connected" : apiStatus === "sample" ? "sample" : "disconnected")}><span className="tag-dot" />{apiStatus === "online" ? "API CONNECTED" : apiStatus === "sample" ? "SAMPLE DATA" : "API OFFLINE"}</span>
      </div>

      <div className="app-layout">
        <aside className={"sidebar " + (mobileMenuOpen ? "sidebar-open" : "")}>
          <div className="sidebar-workspace"><div className="workspace-avatar"><Command size={17} /></div><div className="workspace-copy"><strong>{demoMode ? "Research Sandbox" : workspaces[0]?.name || "My Workspace"}</strong><small>{demoMode ? "Sample environment" : workspaces[0]?.role ? workspaces[0].role + " workspace" : "Workspace"}</small></div><ChevronDown size={14} /></div>
          {(["WORKSPACE", "OPERATIONS", "INTELLIGENCE", "SYSTEM"] as const).map((group) => (
            <div className="nav-group" key={group}>
              <div className="nav-group-label">{group}</div>
              {NAV.filter((item) => item.group === group).map((item) => {
                const Icon = item.icon;
                return <button key={item.id} className={"nav-item " + (screen === item.id ? "active" : "")} onClick={() => changeScreen(item.id)}><Icon size={17} strokeWidth={1.8} /><span>{item.label}</span>{screen === item.id && <span className="nav-selected-mark" />}</button>;
              })}
            </div>
          ))}
          <div className="sidebar-spacer" />
          <div className="sidebar-safety"><div className="safety-icon"><ShieldCheck size={17} /></div><div><strong>Safety boundary active</strong><small>Registered fixtures only</small></div><span className="live-dot" /></div>
          <div className="sidebar-user"><div className="user-avatar">{user?.email?.slice(0, 1).toUpperCase() || "S"}</div><div className="user-details"><strong>{user?.email || "Sample Analyst"}</strong><small>{demoMode ? "Read-only sample profile" : "Research analyst"}</small></div><button className="icon-button tiny" aria-label={user ? "Sign out" : "Exit demo"} onClick={user ? handleLogout : () => { setDemoMode(false); setApiStatus("offline"); }}><LogOut size={15} /></button></div>
        </aside>

        <main className="main-area">
          <div className="page-heading">
            <div className="page-heading-left">
              <div className="breadcrumbs"><span>WORKSPACE</span><ChevronRight size={12} /><span>{NAV.find((item) => item.id === screen)?.label.toUpperCase()}</span></div>
              <h1>{screen === "missions" ? "Mission Center" : screen === "world" ? "Digital World Explorer" : screen === "simulation" ? "Simulation Lab" : screen === "evidence" ? "Evidence & Origo Verification" : screen === "reports" ? "Mission Reports" : "Workspace Settings"}</h1>
              <p>{screen === "missions" ? "Manage bounded research missions and monitor their lifecycle." : screen === "world" ? "Explore typed synthetic entities, relationships, and selected asset context." : screen === "simulation" ? "Execute registered deterministic fixtures inside the isolated environment." : screen === "evidence" ? "Inspect evidence provenance, content digests, and fixture verification checks." : screen === "reports" ? "Review reproducible outcomes and export auditable research records." : "Manage presentation preferences and inspect workspace connectivity."}</p>
            </div>
            <div className="heading-actions">
              <button className="icon-button" aria-label="Toggle theme" title="Toggle theme" onClick={() => setTheme(theme === "obsidian" ? "polar" : "obsidian")}>{theme === "obsidian" ? <Sun size={17} /> : <Moon size={17} />}</button>
              <button className="button button-primary" onClick={() => { setMissionObjective("Investigate a synthetic authentication-failure sequence"); setMissionScenario(SCENARIOS[0].id); setShowMissionModal(true); }}><Plus size={16} /> New mission</button>
            </div>
          </div>

          {isSample && <div className="sample-notice"><CircleHelp size={15} /><span><strong>Sample environment.</strong> Displayed records are illustrative; changes stay in this browser session and do not reach the backend.</span><button onClick={() => { setDemoMode(false); setScreen("settings"); }}>Connection settings <ChevronRight size={14} /></button></div>}
          {user && apiStatus === "offline" && <div className="warning-notice"><AlertTriangle size={16} /><span>API not reachable. Persistent writes are paused; retry from Settings after confirming the API URL and development proxy.</span><button onClick={() => refreshWorkspace(workspaceId)}><RefreshCw size={14} /> Retry</button></div>}

          {screen === "missions" && (
            <section className="screen-stack">
              <div className="metric-grid">
                <MetricCard label="TOTAL MISSIONS" value={missions.length.toString().padStart(2, "0")} hint="In this workspace" icon={LayoutDashboard} trend="+12%" />
                <MetricCard label="ACTIVE MISSIONS" value={activeCount.toString().padStart(2, "0")} hint="Currently in progress" icon={Activity} />
                <MetricCard label="COMPLETED" value={completedCount.toString().padStart(2, "0")} hint="Terminal outcomes" icon={BadgeCheck} />
                <MetricCard label="VERIFIED RUNS" value={verifiedRuns.toString().padStart(2, "0")} hint="Fixture checks passed" icon={ShieldCheck} />
              </div>
              <div className="content-grid mission-grid">
                <section className="panel mission-list-panel">
                  <div className="panel-heading"><div><div className="section-kicker">RESEARCH PIPELINE</div><h2>Mission register</h2><p>Scope, status, and the most recent activity</p></div><button className="button button-secondary button-small" onClick={() => refreshWorkspace(workspaceId)} disabled={!user || apiStatus !== "online"}><RefreshCw size={14} /> Refresh</button></div>
                  <div className="table-toolbar"><label className="search-field"><Search size={15} /><input value={searchText} onChange={(event) => setSearchText(event.target.value)} placeholder="Search missions, IDs…" /></label><button className="button button-secondary button-small" onClick={() => notify("Showing all mission lifecycle states.")}><Filter size={14} /> All states <ChevronDown size={13} /></button></div>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead><tr><th>MISSION</th><th>MODE</th><th>STATUS</th><th>LAST ACTIVITY</th><th>VERSION</th><th /></tr></thead>
                      <tbody>
                        {visibleMissions.map((mission) => <tr key={mission.id} className={selectedMission?.id === mission.id ? "row-selected" : ""} onClick={() => setSelectedMissionId(mission.id)}>
                          <td><div className="mission-cell"><span className="mission-symbol"><Radar size={15} /></span><span><strong>{mission.objective}</strong><small>{mission.id.slice(0, 14)}</small></span></div></td>
                          <td><span className="type-pill">Synthetic</span></td><td><StatusTag value={mission.state} /></td><td>{timeAgo(mission.updated_at || mission.created_at)}</td><td className="mono">v{mission.version}</td><td><button className="icon-button tiny" aria-label="Open mission" onClick={(event) => { event.stopPropagation(); setSelectedMissionId(mission.id); setScreen("simulation"); }}><ChevronRight size={15} /></button></td>
                        </tr>)}
                        {visibleMissions.length === 0 && <tr><td colSpan={6}><div className="empty-state"><Archive size={22} /><strong>No matching missions</strong><span>Adjust the search or create a new mission.</span></div></td></tr>}
                      </tbody>
                    </table>
                  </div>
                  <div className="panel-foot"><span>Showing {visibleMissions.length} of {missions.length} missions</span><span className="foot-right"><span className="tiny-pulse" /> Scope isolation enforced</span></div>
                </section>
                <section className="panel readiness-panel">
                  <div className="panel-heading"><div><div className="section-kicker">SELECTED CONTEXT</div><h2>Mission readiness</h2><p>Pre-run governance checks</p></div><span className="panel-icon"><ShieldCheck size={18} /></span></div>
                  {selectedMission ? <>
                    <div className="readiness-title"><div className="readiness-avatar"><FlaskConical size={19} /></div><div><strong>{selectedMission.objective}</strong><small>{selectedMission.id}</small></div></div>
                    <div className="readiness-score"><div><span>Scope assurance</span><strong>Bounded</strong></div><span className="assurance-line"><i /></span></div>
                    <div className="check-list">
                      <div className="check-row"><CheckCircle2 size={16} /><span>Synthetic-only scope</span><StatusTag value="Verified" /></div>
                      <div className="check-row"><CheckCircle2 size={16} /><span>Excluded target boundary</span><StatusTag value="Active" /></div>
                      <div className="check-row"><CheckCircle2 size={16} /><span>Registered scenario</span><StatusTag value={selectedMission.scope?.scenario_ids?.[0] ? "Verified" : "Review Required"} /></div>
                      <div className="check-row"><Clock3 size={16} /><span>Baseline snapshot</span><StatusTag value={missionRuns.length ? "Captured" : "On run"} /></div>
                    </div>
                    <button className="button button-primary button-wide" onClick={() => setScreen("simulation")}>Open mission workspace <ArrowUpRight size={15} /></button>
                    <div className="subtle-disclaimer">Readiness reflects the selected scope and registered fixture path, not a guarantee about real systems.</div>
                  </> : <div className="empty-state"><CircleHelp size={22} /><strong>Select a mission</strong><span>Mission details appear here.</span></div>}
                </section>
              </div>
              <div className="panel activity-panel">
                <div className="panel-heading compact"><div><div className="section-kicker">RECENT ACTIVITY</div><h2>Execution timeline</h2></div><button className="text-button" onClick={() => setScreen("reports")}>View reports <ChevronRight size={14} /></button></div>
                <div className="timeline-row">
                  <div className="timeline-icon success"><Check size={15} /></div><div className="timeline-copy"><strong>Fixture consistency check completed</strong><span>Deterministic assertions returned a bounded verification result.</span></div><span className="timeline-time">{timeAgo(runs[0]?.completed_at)}</span>
                </div>
                <div className="timeline-row">
                  <div className="timeline-icon gold"><GitBranch size={15} /></div><div className="timeline-copy"><strong>World graph available for exploration</strong><span>{entities.length} synthetic entities · {relationships.length} typed relationships in the current view.</span></div><span className="timeline-time">Current</span>
                </div>
                <div className="timeline-row">
                  <div className="timeline-icon muted"><Fingerprint size={15} /></div><div className="timeline-copy"><strong>Evidence digest recorded</strong><span>Source class and fixture limitations remain attached to the evidence record.</span></div><span className="timeline-time">{timeAgo(runs[0]?.started_at)}</span>
                </div>
              </div>
            </section>
          )}

          {screen === "world" && (
            <section className="screen-stack">
              <div className="world-summary">
                <div className="world-summary-title"><div className="world-orb"><Network size={21} /></div><div><div className="section-kicker">WORLD MODEL · SCHEMA 1.0</div><h2>Synthetic dependency graph</h2><p>Node identities and relationships are scoped to the selected workspace.</p></div></div>
                <div className="world-stats"><div><strong>{entities.length.toString().padStart(2, "0")}</strong><span>Entities</span></div><div><strong>{relationships.length.toString().padStart(2, "0")}</strong><span>Relationships</span></div><div><strong>SHA-256</strong><span>Baseline digest</span></div></div>
                <button className="button button-primary" onClick={() => setShowEntityModal(true)}><Plus size={15} /> Add entity</button>
              </div>
              <div className="world-grid">
                <section className="panel graph-panel">
                  <div className="panel-heading"><div><div className="section-kicker">INTERACTIVE CANVAS</div><h2>Digital world</h2><p>Drag nodes · zoom · pan · select an entity to inspect</p></div><div className="graph-actions"><button className="icon-button" aria-label="Zoom instructions" onClick={() => notify("Use the graph zoom controls at the lower-left of the canvas.")}>＋</button><button className="icon-button" aria-label="Graph options" onClick={() => notify("Only synthetic, workspace-scoped entities are shown.")}><MoreHorizontal size={17} /></button></div></div>
                  <div className="graph-legend"><span><i className="legend-node identity" /> Identity</span><span><i className="legend-node service" /> Service</span><span><i className="legend-node data" /> Data asset</span><span><i className="legend-edge" /> Typed relationship</span></div>
                  <div className="graph-canvas">
                    {graphNodes.length === 0 ? <div className="graph-empty"><Network size={26} /><strong>No entities yet</strong><span>Create a synthetic entity to start the graph.</span><button className="button button-secondary button-small" onClick={() => setShowEntityModal(true)}><Plus size={14} /> Add first entity</button></div> : <ReactFlow nodes={graphNodes} edges={graphEdges} fitView minZoom={0.25} maxZoom={1.8} onNodeClick={(_, node) => setSelectedEntity(node.data.entity as WorldEntity)} nodesDraggable nodesConnectable={false} elementsSelectable>
                      <Background color={theme === "obsidian" ? "#36343a" : "#e1e5ec"} gap={22} size={1} />
                      <Controls showInteractive={false} />
                      <MiniMap pannable zoomable nodeColor={theme === "obsidian" ? "#b3943f" : "#ff5a24"} maskColor={theme === "obsidian" ? "rgba(10,12,17,.72)" : "rgba(238,241,245,.65)"} />
                    </ReactFlow>}
                  </div>
                  <div className="graph-footer"><span><span className="live-dot" /> Synthetic environment</span><span>Workspace-scoped graph</span><span>Pan & zoom enabled</span></div>
                </section>
                <aside className="panel inspector-panel">
                  <div className="panel-heading"><div><div className="section-kicker">ENTITY INSPECTOR</div><h2>Selected asset</h2><p>Typed attributes and provenance context</p></div><button className="icon-button tiny" aria-label="Clear selected asset" onClick={() => setSelectedEntity(null)}><X size={14} /></button></div>
                  {selectedEntity ? <>
                    <div className="entity-identity"><div className="entity-large-icon"><Server size={20} /></div><div><strong>{selectedEntity.name}</strong><small>{selectedEntity.entity_type.toUpperCase()} · SYNTHETIC</small></div></div>
                    <div className="inspector-field"><span>Entity ID</span><code>{selectedEntity.id}</code></div>
                    <div className="inspector-field"><span>Environment</span><strong>{selectedEntity.environment_id}</strong></div>
                    <div className="inspector-field"><span>Source class</span><StatusTag value={selectedEntity.source_class} /></div>
                    <div className="section-kicker attributes-heading">ATTRIBUTES</div>
                    <div className="attributes-list">{Object.entries(selectedEntity.attributes || {}).map(([key, value]) => <div key={key}><span>{key.replace(/_/g, " ")}</span><strong>{String(value ?? "—")}</strong></div>)}{Object.keys(selectedEntity.attributes || {}).length === 0 && <div className="attributes-empty">No attributes recorded.</div>}</div>
                    <div className="inspector-note"><ShieldCheck size={15} /><span>Entity is marked synthetic. It does not establish the presence of a real host, user, or service.</span></div>
                  </> : <div className="empty-state"><CircleHelp size={22} /><strong>No entity selected</strong><span>Select a node from the graph.</span></div>}
                  <div className="related-entities"><div className="section-kicker">RELATED RELATIONSHIPS</div>{selectedEntity ? relationships.filter((relationship) => relationship.from_entity_id === selectedEntity.id || relationship.to_entity_id === selectedEntity.id).map((relationship) => {
                    const otherId = relationship.from_entity_id === selectedEntity.id ? relationship.to_entity_id : relationship.from_entity_id;
                    const other = entities.find((entity) => entity.id === otherId);
                    return <div className="related-row" key={relationship.id}><GitBranch size={13} /><span>{relationship.relationship_type.replace(/_/g, " ")}</span><strong>{other?.name || "Unknown entity"}</strong></div>;
                  }) : <span className="muted-copy">Select a node to list its relationships.</span>}</div>
                </aside>
              </div>
            </section>
          )}

          {screen === "simulation" && (
            <section className="screen-stack">
              <div className="simulation-banner"><div className="simulation-banner-icon"><FlaskConical size={22} /></div><div><div className="section-kicker">CONTROLLED EXECUTION</div><h2>Deterministic simulation lab</h2><p>Only registered fixtures execute. No target discovery, shell commands, real credentials, or live-system mutation are exposed.</p></div><span className="env-lock"><LockKeyhole size={13} /> ISOLATED</span></div>
              <div className="simulation-grid">
                <section className="panel scenario-panel">
                  <div className="panel-heading"><div><div className="section-kicker">SCENARIO CATALOG</div><h2>Available fixtures</h2><p>Select a registered scenario</p></div><span className="count-badge">{registeredScenarios.length} active</span></div>
                  <div className="scenario-list">{SCENARIOS.map((scenario) => {
                    const Icon = scenario.icon;
                    return <button key={scenario.id} className={"scenario-card " + (selectedScenarioId === scenario.id ? "scenario-selected" : "") + (!scenario.enabled ? " scenario-disabled" : "")} onClick={() => setSelectedScenarioId(scenario.id)}>
                      <div className="scenario-icon"><Icon size={17} /></div><div className="scenario-copy"><strong>{scenario.name}</strong><p>{scenario.description}</p><div className="scenario-meta"><span className="type-pill">{scenario.category}</span><StatusTag value={scenario.enabled ? "Registered" : "Planned"} /></div></div><ChevronRight size={15} className="scenario-chevron" />
                    </button>;
                  })}</div>
                  <div className="scenario-foot"><Shield size={15} /><span>Unregistered scenarios are displayed as roadmap placeholders only.</span></div>
                </section>
                <section className="panel scenario-detail-panel">
                  <div className="panel-heading"><div><div className="section-kicker">SCENARIO DETAILS</div><h2>{SCENARIOS.find((item) => item.id === selectedScenarioId)?.name}</h2><p>{selectedScenarioId}</p></div><StatusTag value={selectedScenario?.enabled ? "Registered" : "Planned"} /></div>
                  <div className="scenario-detail-copy">{selectedScenario?.description}</div>
                  <div className="detail-callout"><div className="callout-icon"><LockKeyhole size={16} /></div><div><strong>Execution boundary</strong><p>Fixture data is inert. The simulator does not connect to the named identities or external systems, and its teaching thresholds are not calibrated for operational detection.</p></div></div>
                  <div className="section-kicker prerequisites-heading">PREREQUISITES</div>
                  <div className="check-list">
                    <div className="check-row"><CheckCircle2 size={16} /><span>Authenticated workspace or sample session</span><StatusTag value={demoMode ? "Sample" : user ? "Verified" : "Required"} /></div>
                    <div className="check-row"><CheckCircle2 size={16} /><span>Mission with synthetic-only scope</span><StatusTag value={selectedMission ? "Ready" : "Required"} /></div>
                    <div className="check-row"><CheckCircle2 size={16} /><span>Explicit simulate_synthetic tier</span><StatusTag value={selectedMission?.autonomy_tier === "simulate_synthetic" ? "Ready" : "Review Required"} /></div>
                    <div className="check-row"><Clock3 size={16} /><span>Versioned world baseline</span><StatusTag value="Captured on run" /></div>
                  </div>
                  <div className="selected-mission-box"><div className="section-kicker">MISSION CONTEXT</div>{selectedMission ? <><strong>{selectedMission.objective}</strong><small>{selectedMission.id} · <span className="mono">{selectedMission.autonomy_tier}</span></small></> : <span className="muted-copy">No mission selected.</span>}<button className="text-button" onClick={() => setScreen("missions")}>Choose mission <ChevronRight size={14} /></button></div>
                  <div className="run-actions"><button className="button button-primary button-wide" disabled={busy || !selectedScenario?.enabled || !selectedMission} onClick={runScenario}>{busy ? <RefreshCw className="spin" size={16} /> : <FlaskConical size={16} />}{busy ? "Executing fixture…" : "Run synthetic simulation"}<ArrowUpRight size={15} /></button><span><LockKeyhole size={12} /> Mission state and scope are enforced by the API.</span></div>
                </section>
              </div>
              <section className="panel recent-runs-panel"><div className="panel-heading compact"><div><div className="section-kicker">EXECUTION HISTORY</div><h2>Recent runs</h2></div><button className="text-button" onClick={() => setScreen("reports")}>Open reports <ChevronRight size={14} /></button></div>
                <div className="table-wrap"><table className="data-table"><thead><tr><th>RUN ID</th><th>SCENARIO</th><th>OUTCOME</th><th>VERIFICATION</th><th>COMPLETED</th><th /></tr></thead><tbody>{runs.slice(0, 5).map((run) => <tr key={run.id}><td className="mono">{run.id.slice(0, 18)}</td><td>{SCENARIOS.find((item) => item.id === run.scenario_id)?.name || run.scenario_id}</td><td><StatusTag value={run.outcome} /></td><td><StatusTag value={String((run.result.verification as { status?: string } | undefined)?.status || "Inconclusive")} /></td><td>{formatDate(run.completed_at)}</td><td><button className="icon-button tiny" aria-label="Inspect run evidence" onClick={() => setScreen("evidence")}><ChevronRight size={15} /></button></td></tr>)}{runs.length === 0 && <tr><td colSpan={6}><div className="empty-state small-empty">No runs recorded in this workspace.</div></td></tr>}</tbody></table></div>
              </section>
            </section>
          )}

          {screen === "evidence" && (
            <section className="screen-stack">
              <div className="evidence-banner"><div className="evidence-banner-icon"><Fingerprint size={22} /></div><div><div className="section-kicker">PROVENANCE FIRST</div><h2>Evidence & bounded verification</h2><p>Inspect content digests, fixture sources, linked runs, and deterministic consistency checks.</p></div><div className="verification-summary"><span>{verifiedRuns.toString().padStart(2, "0")}</span><small>Verified fixture runs</small></div></div>
              <div className="evidence-metrics"><div className="mini-stat"><FileCheck2 size={16} /><span>Evidence records</span><strong>{allEvidence.length}</strong></div><div className="mini-stat"><Fingerprint size={16} /><span>Digest attached</span><strong>{allEvidence.filter((item) => item.content_digest).length}</strong></div><div className="mini-stat"><ShieldCheck size={16} /><span>Source class</span><strong>synthetic</strong></div><div className="mini-stat"><AlertTriangle size={16} /><span>Integrity caveats</span><strong>Visible</strong></div></div>
              <section className="panel evidence-table-panel">
                <div className="panel-heading"><div><div className="section-kicker">EVIDENCE REGISTER</div><h2>Collected artifacts</h2><p>Records returned with registered synthetic simulation runs</p></div><div className="table-actions"><label className="select-field"><Filter size={14} /><select value={evidenceFilter} onChange={(event) => setEvidenceFilter(event.target.value)}><option value="all">All types</option><option value="auth">Authentication</option><option value="synthetic">Synthetic</option><option value="log">Log</option></select></label><button className="button button-secondary button-small" onClick={() => setScreen("reports")}><Download size={14} /> Export</button></div></div>
                <div className="table-wrap"><table className="data-table evidence-table"><thead><tr><th>TYPE</th><th>SOURCE REFERENCE</th><th>CONTENT DIGEST</th><th>PROVENANCE</th><th>RECORD TIME</th><th /></tr></thead><tbody>{visibleEvidence.map((item) => <tr key={item.id}><td><div className="type-with-icon"><span className="table-type-icon"><FileText size={14} /></span><span><strong>{item.evidence_type.replace(/_/g, " ")}</strong><small>{item.id.slice(0, 14)}</small></span></div></td><td className="mono">{item.source_ref}</td><td><code className="digest-text">{item.content_digest.slice(0, 18)}…</code><small className="digest-label">SHA-256</small></td><td><StatusTag value={item.source_class} /><small className="producer-label">{item.producer || "synthetic fixture"}</small></td><td>{formatDate(item.created_at)}</td><td><button className="icon-button tiny" aria-label="Inspect evidence" onClick={() => notify("Evidence record " + item.id + " is linked to run " + item.run_id + ".") }><ChevronRight size={15} /></button></td></tr>)}{visibleEvidence.length === 0 && <tr><td colSpan={6}><div className="empty-state"><FileCheck2 size={23} /><strong>No evidence records</strong><span>Run a registered synthetic fixture to create a provenance record.</span><button className="button button-secondary button-small" onClick={() => setScreen("simulation")}>Open Simulation Lab</button></div></td></tr>}</tbody></table></div>
                <div className="panel-foot"><span>Evidence rows are supplied by run records or explicitly marked sample fixtures.</span><span className="foot-right">{visibleEvidence.length} records</span></div>
              </section>
              <div className="content-grid evidence-detail-grid">
                <section className="panel">
                  <div className="panel-heading"><div><div className="section-kicker">VERIFICATION TRACE</div><h2>Bounded fixture checks</h2><p>Illustrative structure from the registered verifier</p></div><span className="panel-icon"><BadgeCheck size={18} /></span></div>
                  {(missionRuns[0]?.result.verification as { checks?: Array<{ check: string; passed: boolean }>; status?: string; limitations?: string[] } | undefined)?.checks?.map((check) => <div className="check-row trace-row" key={check.check}><span className={check.passed ? "trace-check passed" : "trace-check failed"}>{check.passed ? <Check size={12} /> : <X size={12} />}</span><span>{check.check.replace(/_/g, " ")}</span><StatusTag value={check.passed ? "Passed" : "Failed"} /></div>) || <div className="empty-state small-empty">Select a mission with a run to inspect checks.</div>}
                </section>
                <section className="panel limitations-panel"><div className="panel-heading"><div><div className="section-kicker">INTERPRETATION BOUNDARY</div><h2>What this verifies</h2></div><span className="panel-icon warning-icon"><AlertTriangle size={18} /></span></div><p className="body-copy">The current API compares a registered fixture with a deterministic result and checks that referenced evidence IDs resolve. It does not independently validate a live system or external telemetry.</p><div className="limitation-list"><div><CheckCircle2 size={15} /><span>Registered fixture and schema expectations</span></div><div><CheckCircle2 size={15} /><span>Event-count and evidence-reference consistency</span></div><div><AlertTriangle size={15} /><span>Not full independent Origo verification</span></div><div><AlertTriangle size={15} /><span>No claims about real-world compromise</span></div></div></section>
              </div>
            </section>
          )}

          {screen === "reports" && (
            <section className="screen-stack">
              <div className="reports-hero"><div><div className="section-kicker">RESEARCH OUTPUTS</div><h2>Reports & reproducibility</h2><p>Summaries are derived from recorded simulation runs and their attached evidence.</p></div><div className="reports-hero-mark"><FileText size={25} /></div></div>
              <div className="report-card-grid">
                <div className="report-type-card"><div className="report-type-top"><span className="report-file-icon blue"><FileText size={18} /></span><StatusTag value="Available" /></div><h3>Mission Summary</h3><p>Objectives, mission state, scope, and execution outcome.</p><div className="report-type-foot"><span>{missions.length} mission records</span><button className="text-button" onClick={() => setScreen("missions")}>Review <ChevronRight size={13} /></button></div></div>
                <div className="report-type-card"><div className="report-type-top"><span className="report-file-icon amber"><ShieldAlert size={18} /></span><StatusTag value="Bounded" /></div><h3>Security Findings</h3><p>Registered fixture outcome and the applicable limitations.</p><div className="report-type-foot"><span>{runs.length} run records</span><button className="text-button" onClick={() => setScreen("simulation")}>Review <ChevronRight size={13} /></button></div></div>
                <div className="report-type-card"><div className="report-type-top"><span className="report-file-icon green"><BadgeCheck size={18} /></span><StatusTag value="Evidence-linked" /></div><h3>Verification Trace</h3><p>Fixture-check statuses and linked evidence digests.</p><div className="report-type-foot"><span>{allEvidence.length} evidence records</span><button className="text-button" onClick={() => setScreen("evidence")}>Review <ChevronRight size={13} /></button></div></div>
              </div>
              <section className="panel reports-table-panel"><div className="panel-heading"><div><div className="section-kicker">RECENT REPORTABLE RUNS</div><h2>Run register</h2><p>Export each run record in Markdown or JSON</p></div><span className="count-badge">{runs.length} runs</span></div>
                <div className="table-wrap"><table className="data-table"><thead><tr><th>MISSION / RUN</th><th>SCENARIO</th><th>OUTCOME</th><th>VERIFICATION</th><th>GENERATED</th><th>EXPORT</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id}><td><div className="report-name-cell"><span className="report-file-icon blue"><FileText size={15} /></span><span><strong>{missions.find((mission) => mission.id === run.mission_id)?.objective || run.mission_id}</strong><small className="mono">{run.id}</small></span></div></td><td>{SCENARIOS.find((item) => item.id === run.scenario_id)?.name || run.scenario_id}</td><td><StatusTag value={run.outcome} /></td><td><StatusTag value={String((run.result.verification as { status?: string } | undefined)?.status || "Inconclusive")} /></td><td>{formatDate(run.completed_at)}</td><td><div className="export-actions"><button className="icon-button tiny" title="Export Markdown" aria-label="Export Markdown" onClick={() => exportReport(run, "md")}><FileText size={15} /></button><button className="icon-button tiny" title="Export JSON" aria-label="Export JSON" onClick={() => exportReport(run, "json")}><FileJson size={15} /></button></div></td></tr>)}{runs.length === 0 && <tr><td colSpan={6}><div className="empty-state"><FileText size={23} /><strong>No reports generated</strong><span>Complete a registered fixture run to create an exportable report.</span><button className="button button-secondary button-small" onClick={() => setScreen("simulation")}>Go to Simulation Lab</button></div></td></tr>}</tbody></table></div>
                <div className="panel-foot"><span>Exports are generated in the browser from the selected run record.</span><span className="foot-right"><Download size={13} /> Markdown · JSON</span></div>
              </section>
              <div className="report-disclaimer"><Shield size={15} /><span>Reports preserve synthetic provenance and disclose limitations. A passed fixture check is not a certification of a real environment.</span></div>
            </section>
          )}

          {screen === "settings" && (
            <section className="screen-stack settings-stack">
              <section className="panel settings-profile"><div className="panel-heading"><div><div className="section-kicker">WORKSPACE PROFILE</div><h2>Session and workspace</h2><p>Identity and data-context information currently in use</p></div><span className="panel-icon"><Users size={18} /></span></div>
                <div className="settings-profile-row"><div className="user-avatar large-avatar">{user?.email?.slice(0, 1).toUpperCase() || "S"}</div><div className="settings-profile-info"><strong>{user?.email || "Sample Analyst"}</strong><span>{demoMode ? "Sample browser session" : "Authenticated API user"}</span></div><StatusTag value={demoMode ? "Sample" : user ? "Authenticated" : "Offline"} /></div>
                <div className="settings-info-grid"><div><span>Workspace</span><strong>{demoMode ? "Research Sandbox" : workspaces.find((workspace) => workspace.id === workspaceId)?.name || "No workspace selected"}</strong></div><div><span>Workspace role</span><strong>{demoMode ? "Sample analyst" : workspaces.find((workspace) => workspace.id === workspaceId)?.role || "—"}</strong></div><div><span>Environment</span><strong>synthetic-lab</strong></div><div><span>Execution tier</span><strong>Registered fixtures only</strong></div></div>
              </section>
              <section className="panel settings-theme-panel"><div className="panel-heading"><div><div className="section-kicker">APPEARANCE SYSTEM</div><h2>Theme architecture</h2><p>Same information architecture with coordinated visual treatments</p></div></div>
                <div className="theme-choice-grid"><button className={"theme-choice obsidian-choice " + (theme === "obsidian" ? "theme-choice-active" : "")} onClick={() => setTheme("obsidian")}><span className="theme-preview dark-preview"><i /><i /><i /><b /></span><span><strong>Obsidian Gold</strong><small>Editorial · premium · governance</small></span>{theme === "obsidian" && <CheckCircle2 size={18} />}</button><button className={"theme-choice polar-choice " + (theme === "polar" ? "theme-choice-active" : "")} onClick={() => setTheme("polar")}><span className="theme-preview light-preview"><i /><i /><i /><b /></span><span><strong>Polar Minimalist</strong><small>Technical · analytical · high clarity</small></span>{theme === "polar" && <CheckCircle2 size={18} />}</button></div>
              </section>
              <section className="panel connection-panel"><div className="panel-heading"><div><div className="section-kicker">SERVICE CONNECTIVITY</div><h2>API connection</h2><p>The frontend uses the Vite proxy for local development by default.</p></div><span className="panel-icon"><Globe2 size={18} /></span></div>
                <div className="connection-row"><div className={"connection-symbol " + (apiStatus === "online" ? "is-online" : "")}><Activity size={18} /></div><div className="connection-copy"><strong>{apiStatus === "online" ? "API reachable" : apiStatus === "sample" ? "Sample environment active" : "API unavailable or not authenticated"}</strong><small>{apiStatus === "online" ? "Authenticated session and workspace endpoints responded." : "Local default: /api → http://localhost:8000. Set VITE_API_BASE_URL for a deployed frontend."}</small></div><button className="button button-secondary button-small" onClick={() => user && workspaceId ? refreshWorkspace(workspaceId) : notify("Sign in to test the authenticated workspace connection.")}><RefreshCw size={14} /> Test connection</button></div>
                <div className="connection-notice"><AlertTriangle size={15} /><span>Cross-origin deployments must allow the frontend origin in the API's CORS policy and preserve cookie/CSRF protections. Do not place secrets in VITE_ variables.</span></div>
              </section>
              <section className="panel safety-settings"><div className="panel-heading"><div><div className="section-kicker">GUARDRAILS</div><h2>Security context</h2></div><span className="panel-icon"><ShieldCheck size={18} /></span></div><div className="safety-setting-row"><div><strong>Environment banner</strong><small>Persistent synthetic / isolated context across every workspace screen.</small></div><StatusTag value="Enforced" /></div><div className="safety-setting-row"><div><strong>External execution</strong><small>Network scanning, shell commands, real credentials, and live mutation are not exposed by this interface.</small></div><StatusTag value="Unavailable" /></div><div className="safety-setting-row"><div><strong>Evidence interpretation</strong><small>Fixture checks remain separate from claims about real-world behavior.</small></div><StatusTag value="Bounded" /></div></section>
            </section>
          )}

          <footer className="app-footer"><div><span className="footer-brand"><LogoMark /> NEXORION</span><span>Synthetic Cyber Research Platform</span></div><div><span>Research</span><span>·</span><span>Intelligence</span><span>·</span><span>A safer digital future</span></div><span className="footer-version">UI BUILD 0.1 · SYNTHETIC SCOPE</span></footer>
        </main>
      </div>

      <nav className="mobile-bottom-nav" aria-label="Mobile navigation">{NAV.slice(0, 5).map((item) => { const Icon = item.icon; return <button key={item.id} className={screen === item.id ? "active" : ""} onClick={() => changeScreen(item.id)}><Icon size={18} /><span>{item.id === "missions" ? "Missions" : item.id === "world" ? "World" : item.id === "simulation" ? "Simulate" : item.id === "evidence" ? "Evidence" : "Reports"}</span></button>; })}</nav>

      {showMissionModal && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowMissionModal(false); }}><form className="modal-card" onSubmit={createMission}>
        <div className="modal-heading"><div><div className="section-kicker">MISSION SETUP</div><h2>Create synthetic mission</h2><p>Define the objective and allowed registered fixture.</p></div><button type="button" className="icon-button" aria-label="Close modal" onClick={() => setShowMissionModal(false)}><X size={18} /></button></div>
        <label className="field-label">Mission objective<textarea value={missionObjective} onChange={(event) => setMissionObjective(event.target.value)} minLength={10} maxLength={500} rows={3} required /></label>
        <label className="field-label">Registered scenario<select value={missionScenario} onChange={(event) => setMissionScenario(event.target.value)}>{registeredScenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}</select></label>
        <div className="modal-security-note"><ShieldCheck size={16} /><span>Scope is fixed to synthetic-only. External targets are excluded. The mission API enforces the execution tier and registered scenario.</span></div>
        <div className="modal-actions"><button type="button" className="button button-secondary" onClick={() => setShowMissionModal(false)}>Cancel</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving…" : "Create mission"}<ChevronRight size={15} /></button></div>
      </form></div>}

      {showEntityModal && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowEntityModal(false); }}><form className="modal-card" onSubmit={createEntity}>
        <div className="modal-heading"><div><div className="section-kicker">DIGITAL WORLD</div><h2>Add synthetic entity</h2><p>Add a typed node to the current workspace graph.</p></div><button type="button" className="icon-button" aria-label="Close modal" onClick={() => setShowEntityModal(false)}><X size={18} /></button></div>
        <label className="field-label">Entity name<input value={entityName} onChange={(event) => setEntityName(event.target.value)} maxLength={120} required /></label>
        <label className="field-label">Entity type<select value={entityType} onChange={(event) => setEntityType(event.target.value)}><option value="identity">Identity</option><option value="host">Host / application</option><option value="service">Service</option><option value="log_source">Log source</option><option value="dataset">Dataset</option><option value="control">Control</option><option value="other">Other</option></select></label>
        <div className="modal-security-note"><Database size={16} /><span>Only typed synthetic metadata is stored. Do not enter passwords, tokens, secrets, real credentials, or sensitive personal data.</span></div>
        <div className="modal-actions"><button type="button" className="button button-secondary" onClick={() => setShowEntityModal(false)}>Cancel</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving…" : "Add entity"}<Plus size={15} /></button></div>
      </form></div>}

      {toast && <div className="toast" role="status"><span className="toast-mark"><CheckCircle2 size={16} /></span>{toast}<button className="toast-close" aria-label="Dismiss message" onClick={() => setToast("")}><X size={14} /></button></div>}
    </div>
  );
}

export default App;