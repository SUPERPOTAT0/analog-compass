// Live backend wiring for the Analog Compass product. Every call degrades gracefully:
// if the engine API is unreachable, the UI falls back to the built-in sample data, so the
// product always renders. Set VITE_API_URL to point at the Python API.

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

// Real, high-resolution terrain photos keyed by environment so each card shows imagery
// matching the discovered analog's dominant characteristics (desert, volcanic, polar…).
const u = (id: string) => `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=1100&q=80`;
const BIOME: Record<string, string> = {
  volcanic: u("1620824175623-930d7a980da8"), // dark basaltic terrain
  lava_tube: u("1504280317859-3eef6e3c3f5a"), // cave interior
  polar: u("1517783999520-f068d7431a60"), // snow / ice field
  permafrost: u("1517783999520-f068d7431a60"),
  arid: u("1666668152560-e6807f6ffabe"), // cracked arid ground
  desert: u("1684275750619-8ae782588f78"), // dune desert
  rocky: u("1648498015611-4e51d7d3f74a"), // rugged rock ridges
  salt: u("1684275751032-9108ff470c6a"),
};

function pickBiomeImage(profById: Record<string, any>): string {
  const num = (id: string) => {
    const v = profById[id]?.value_display;
    return v != null && !isNaN(parseFloat(v)) ? parseFloat(v) : null;
  };
  const cave = profById["cave_evidence"]?.value_display;
  const permafrost = num("permafrost_index");
  const basalt = num("basaltic_volcanic_fraction");
  const veg = num("vegetation_cover");
  if (cave === "candidate" || cave === "confirmed") return BIOME.lava_tube;
  if (permafrost != null && permafrost > 0.5) return BIOME.polar;
  if (basalt != null && basalt > 0.5) return BIOME.volcanic;
  if (veg != null && veg < 2) return BIOME.arid;
  if (veg != null && veg < 8) return BIOME.desert;
  return BIOME.rocky;
}

// --- Scientist filters -> strict engine constraints --------------------------
export type Filters = {
  slopeMax: number;        // degrees (40 = off)
  tempMax: number;         // °C ceiling (40 = off)
  sunlitMin: number;       // % (0 = off)
  basalticMin: number;     // % (0 = off)
  remotenessMin: number;   // engine units/min (0 = off)
  windMax: number;         // m/s (40 = off)
  requirePermafrost: boolean;
  lowVegetation: boolean;
  highDust: boolean;
  requireCaves: boolean;
};

export const DEFAULT_FILTERS: Filters = {
  slopeMax: 40, tempMax: 40, sunlitMin: 0, basalticMin: 0, remotenessMin: 0, windMax: 40,
  requirePermafrost: false, lowVegetation: false, highDust: false, requireCaves: false,
};

type Constraint = { characteristic: string; op: "min" | "max"; value: number; required: boolean };

export function buildConstraints(f: Filters): Constraint[] {
  const c: Constraint[] = [];
  if (f.slopeMax < 40) c.push({ characteristic: "slope", op: "max", value: f.slopeMax, required: true });
  if (f.tempMax < 40) c.push({ characteristic: "temperature", op: "max", value: f.tempMax, required: true });
  if (f.sunlitMin > 0) c.push({ characteristic: "sunlit_fraction", op: "min", value: f.sunlitMin / 100, required: true });
  if (f.basalticMin > 0) c.push({ characteristic: "basaltic_volcanic_fraction", op: "min", value: f.basalticMin / 100, required: true });
  if (f.remotenessMin > 0) c.push({ characteristic: "remoteness_time", op: "min", value: f.remotenessMin, required: true });
  if (f.windMax < 40) c.push({ characteristic: "wind_speed_mean", op: "max", value: f.windMax, required: true });
  if (f.requirePermafrost) c.push({ characteristic: "permafrost_index", op: "min", value: 0.5, required: true });
  if (f.lowVegetation) c.push({ characteristic: "vegetation_cover", op: "max", value: 5, required: true });
  if (f.highDust) c.push({ characteristic: "dust_aerosol_load", op: "min", value: 0.3, required: true });
  if (f.requireCaves) c.push({ characteristic: "cave_evidence", op: "min", value: 2, required: true });
  return c;
}

// Count of active (non-"off") filters — for UI chips.
export function activeFilterCount(f: Filters): number {
  return buildConstraints(f).length;
}

// Map the SearchFlow choices to engine ids.
export const MISSION_TO_TEST: Record<string, string> = {
  "Habitat setup": "eva_procedure_rehearsal",
  "Rover traverse": "rover_traverse_autonomy",
  "Drilling for water ice": "cryo_drill_trial",
  "Life detection": "life_detection_assay",
  "Resource extraction": "isru_regolith_processing",
};
export const PLANET_TO_TARGET: Record<string, string> = {
  Moon: "moon_polar",
  Mars: "mars_mid_latitude",
};

// compareRows order in App.tsx -> engine characteristic ids.
const ROW_CHARS = [
  "slope", "sunlit_fraction", "temperature", "basaltic_volcanic_fraction",
  "basaltic_volcanic_fraction", "cave_evidence", "remoteness_time",
  "dust_aerosol_load", "wind_speed_mean", "permafrost_index",
];

async function j<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...opts,
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function isOnline(): Promise<boolean> {
  const h = await j<any>("/health");
  return !!h;
}

export async function getLayers(): Promise<any | null> {
  return j<any>("/layers");
}

export async function getSites(): Promise<any[] | null> {
  return j<any[]>("/sites");
}

export async function submitContribution(payload: any): Promise<any | null> {
  return j<any>("/data/contributions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function fmtCoords(lat: number, lon: number): string {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(4)}° ${ns} · ${Math.abs(lon).toFixed(4)}° ${ew}`;
}
function regionLabel(lat: number, lon: number): string {
  const band =
    lat > 66 ? "High Arctic" : lat < -60 ? "Antarctic" :
    Math.abs(lat) < 23.5 ? "Tropics" : Math.abs(lat) < 45 ? "Subtropics" : "High latitudes";
  return band;
}
function fitFromMatch(m: number | null | undefined): string {
  if (m == null) return "partial";
  return m > 0.66 ? "close" : m > 0.33 ? "partial" : "far";
}
function fmtValue(unit: string | null, v: string | null): string {
  if (v == null) return "—";
  const num = parseFloat(v);
  switch (unit) {
    case "fraction": return isNaN(num) ? v : `${Math.round(num * 100)}%`;
    case "degree": return `${v}°`;
    case "percent": return `${v}%`;
    case "celsius": return `${v}°C`;
    case "minute": return `${v} min`;
    case "meter_per_second": return `${v} m/s`;
    default: return v;
  }
}

export interface LiveCandidate {
  code: string; slug: string; place: string; country: string; coords: string;
  score: number; image: string; keys: string[]; why: string; limit: string;
  tradeoff: string; values: string[][]; lat: number; lon: number;
  gridId?: string; targetId?: string;
}

// Run the real discovery + profiles and transform into the UI's Candidate shape.
// Returns null when the API is unreachable (UI falls back to sample data), or [] when the
// engine ran but no window matched the scientist's filters (strict, no random results).
export async function discoverCandidates(
  planet: string, mission: string, filters?: Filters, k = 3,
): Promise<LiveCandidate[] | null> {
  const target = PLANET_TO_TARGET[planet] || "mars_mid_latitude";
  const test = MISSION_TO_TEST[mission] || "rover_traverse_autonomy";
  const constraints = filters ? buildConstraints(filters) : [];
  const [disc, layers] = await Promise.all([
    j<any>("/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_id: target, test_id: test, k, n_draws: 160, constraints }),
    }),
    getLayers(),
  ]);
  if (!disc) return null;
  const newOnes = (disc.sites || []).filter((s: any) => s.candidate_kind === "new").slice(0, k);
  if (newOnes.length === 0) return [];

  const unitOf: Record<string, string | null> = {};
  const srcOf: Record<string, string> = {};
  (layers?.layers || []).forEach((l: any) => {
    unitOf[l.id] = l.unit;
    srcOf[l.id] = (l.source?.name || "").split(" ")[0] || l.source?.id || "";
  });

  const out: LiveCandidate[] = [];
  for (let i = 0; i < newOnes.length; i++) {
    const s = newOnes[i];
    const gid = s.provenance?.window?.grid_id;
    const prof = gid ? await j<any>(`/site_profile?grid_id=${encodeURIComponent(gid)}`) : null;
    const profById: Record<string, any> = {};
    (prof?.characteristics || []).forEach((c: any) => (profById[c.characteristic] = c));
    const matchById: Record<string, number> = {};
    (s.characteristics || []).forEach((c: any) => (matchById[c.characteristic] = c.match));

    const values = ROW_CHARS.map((cid, idx) => {
      const p = profById[cid];
      let disp = fmtValue(unitOf[cid], p?.value_display ?? null);
      // row 3 is "Lithology" (categorical), row 4 "Basaltic fraction" (percent)
      if (idx === 3) disp = p?.value_display != null && parseFloat(p.value_display) >= 0.5 ? "Basaltic" : "Mixed";
      return [disp, fitFromMatch(matchById[cid]), srcOf[cid] || p?.source_name || "—"];
    });

    const code = `N-${String(i + 1).padStart(3, "0")}`;
    out.push({
      code,
      slug: code.toLowerCase().replace("-", ""),
      place: regionLabel(s.lat, s.lon),
      country: "Discovered",
      coords: fmtCoords(s.lat, s.lon),
      score: Math.round(s.score * 100),
      image: pickBiomeImage(profById),
      gridId: gid,
      targetId: target,
      keys: [
        profById["slope"] ? `${fmtValue("degree", profById["slope"].value_display)} slope` : `${s.verdict}`,
        profById["basaltic_volcanic_fraction"] ? `${fmtValue("fraction", profById["basaltic_volcanic_fraction"].value_display)} basaltic` : "basaltic n/a",
        profById["temperature"] ? `${fmtValue("celsius", profById["temperature"].value_display)} median` : "temp n/a",
      ],
      why: `Nominated by the Offline Candidate Screen; engine verdict ${s.verdict} at ${Math.round(s.p_gate * 100)}% gate confidence for this target and operation.`,
      limit: (s.honest_limits && s.honest_limits.join(" ")) || "Proxy evidence and coverage limits apply; field verification required.",
      tradeoff: s.verdict === "borderline"
        ? "A real match on the measured characteristics, but a proxy or borderline gate caps confidence."
        : "Meets the required characteristics in most simulations.",
      values,
      lat: s.lat,
      lon: s.lon,
    });
  }
  return out;
}

// Tests & Base Operations for a discovered window (or curated site).
export interface Operation {
  test_id: string; label: string; verdict: string; supported: boolean;
  actionable: string; base_relevance: string; limiting_characteristic: string | null;
}
export async function fetchOperations(
  gridId: string | undefined, targetId: string | undefined, siteId?: string,
): Promise<Operation[] | null> {
  const params = new URLSearchParams();
  if (siteId) params.set("site_id", siteId);
  else if (gridId) params.set("grid_id", gridId);
  else return null;
  if (targetId) params.set("target_id", targetId);
  const res = await j<any>(`/site_operations?${params.toString()}`);
  return res?.operations ?? null;
}

// Stream the grounded AI agent. Returns false if unavailable (caller falls back to mock).
export async function streamAssistant(
  messages: { role: string; content: string }[],
  onText: (t: string) => void,
  onTool: (name: string) => void,
): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/agent/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    if (res.status === 503 || !res.ok || !res.body) return false;
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const part of parts) {
        const ev = /event:\s*(.*)/.exec(part)?.[1]?.trim();
        const data = /data:\s*([\s\S]*)/.exec(part)?.[1] ?? "";
        if (ev === "text") onText(data);
        else if (ev === "tool") {
          try { onTool(JSON.parse(data).name); } catch {}
        }
      }
    }
    return true;
  } catch {
    return false;
  }
}

export { API_URL };
