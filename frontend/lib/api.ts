export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Verdict = "pass" | "borderline" | "excluded" | "blocked";

export interface Target {
  target_id: string;
  body: string;
  label: string;
  characteristics: string[];
}

export interface TestTemplate {
  test_id: string;
  label: string;
  rationale: string;
  domains: string[];
}

export interface SiteMeta {
  site_id: string;
  label: string;
  lat: number;
  lon: number;
  known_analog: boolean;
}

export interface CharResult {
  characteristic: string;
  role: string;
  status: string;
  match: number | null;
  tier: string;
  source_id: string;
  contribution: number | null;
  gate_pass_rate: number | null;
}

export interface SiteResult {
  site_id: string;
  label: string;
  lat: number | null;
  lon: number | null;
  candidate_kind: "curated" | "new";
  verdict: Verdict;
  p_gate: number;
  score: number;
  coverage: number;
  characteristics: CharResult[];
  honest_limits: string[];
  provenance?: Record<string, unknown> | null;
}

export interface CompareResult {
  run_id: string;
  seed: number;
  data_version: string;
  data_mode: string;
  target_id: string;
  test_id: string;
  sites: SiteResult[];
}

export interface SuitabilityEntry {
  test_id: string;
  label: string;
  verdict: Verdict;
  driving_characteristic: string | null;
  limiting_characteristic: string | null;
  reasons: string[];
}

export interface SuitabilityResult {
  site_id: string;
  target_id: string;
  tests: SuitabilityEntry[];
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  targets: () => get<Target[]>("/targets"),
  tests: () => get<TestTemplate[]>("/tests"),
  sites: () => get<SiteMeta[]>("/sites"),
  compare: (target_id: string, test_id: string) =>
    post<CompareResult>("/compare", { target_id, test_id }),
  discover: (target_id: string, test_id: string, k = 10) =>
    post<CompareResult>("/discover", { target_id, test_id, k }),
  suitability: (site_id: string, target_id?: string) =>
    post<SuitabilityResult>("/suitability", { site_id, target_id }),
};
