"use client";

import { useEffect, useMemo, useState } from "react";
import {
  api,
  CompareResult,
  SiteMeta,
  SiteResult,
  SuitabilityResult,
  Target,
  TestTemplate,
} from "@/lib/api";
import { MapView } from "@/components/MapView";
import { VerdictBadge } from "@/components/VerdictBadge";
import { ChatView } from "@/components/ChatView";

type Tab = "compare" | "discover" | "suitability" | "ask";

export default function Page() {
  const [tab, setTab] = useState<Tab>("compare");
  const [targets, setTargets] = useState<Target[]>([]);
  const [tests, setTests] = useState<TestTemplate[]>([]);
  const [sites, setSites] = useState<SiteMeta[]>([]);
  const [targetId, setTargetId] = useState("");
  const [testId, setTestId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [suit, setSuit] = useState<SuitabilityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [t, te, s] = await Promise.all([api.targets(), api.tests(), api.sites()]);
        setTargets(t); setTests(te); setSites(s);
        setTargetId(t[0]?.target_id ?? "");
        setTestId(te[0]?.test_id ?? "");
        setSiteId(s[0]?.site_id ?? "");
      } catch (e) {
        setError(`Cannot reach the API at ${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}. Is it running?`);
      }
    })();
  }, []);

  async function run() {
    setLoading(true); setError(null); setResult(null); setSuit(null);
    try {
      if (tab === "compare") setResult(await api.compare(targetId, testId));
      else if (tab === "discover") setResult(await api.discover(targetId, testId, 12));
      else if (tab === "suitability") setSuit(await api.suitability(siteId, targetId));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const mapSites: SiteResult[] = useMemo(() => result?.sites ?? [], [result]);

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-4 p-4">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analog Compass 🧭🪐</h1>
          <p className="text-sm text-slate-400">
            Test-led Earth-analogue finder for Moon/Mars field campaigns — evidence-based, with honest limits.
          </p>
        </div>
        {result && (
          <div className="text-right text-xs text-slate-500">
            run <code>{result.run_id.slice(0, 10)}</code> · {result.data_mode} · {result.data_version}
          </div>
        )}
      </header>

      <nav className="flex gap-2">
        {(["compare", "discover", "suitability", "ask"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1.5 text-sm font-medium capitalize ${tab === t ? "bg-indigo-500" : "bg-slate-700/50"}`}
          >
            {t}
          </button>
        ))}
      </nav>

      {error && <div className="rounded bg-rose-500/20 px-3 py-2 text-sm text-rose-200">{error}</div>}

      {tab === "ask" ? (
        <section className="h-[70vh] rounded-lg bg-[var(--panel)] p-4">
          <ChatView />
        </section>
      ) : (
        <section className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[380px_1fr]">
          <div className="space-y-3 rounded-lg bg-[var(--panel)] p-4">
            <Controls
              tab={tab} targets={targets} tests={tests} sites={sites}
              targetId={targetId} testId={testId} siteId={siteId}
              setTargetId={setTargetId} setTestId={setTestId} setSiteId={setSiteId}
              onRun={run} loading={loading}
            />
            <div className="max-h-[55vh] space-y-2 overflow-auto">
              {tab === "suitability" && suit && <SuitabilityList suit={suit} />}
              {tab !== "suitability" && mapSites.map((s) => <SiteCard key={s.site_id} s={s} />)}
            </div>
          </div>
          <div className="min-h-[60vh] rounded-lg bg-[var(--panel)] p-2">
            <MapView sites={mapSites} />
          </div>
        </section>
      )}
    </main>
  );
}

function Controls(props: {
  tab: Tab; targets: Target[]; tests: TestTemplate[]; sites: SiteMeta[];
  targetId: string; testId: string; siteId: string;
  setTargetId: (v: string) => void; setTestId: (v: string) => void; setSiteId: (v: string) => void;
  onRun: () => void; loading: boolean;
}) {
  const { tab } = props;
  return (
    <div className="space-y-3">
      {(tab === "compare" || tab === "discover" || tab === "suitability") && (
        <label className="block text-sm">
          <span className="text-slate-400">Target</span>
          <select className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm"
            value={props.targetId} onChange={(e) => props.setTargetId(e.target.value)}>
            {props.targets.map((t) => <option key={t.target_id} value={t.target_id}>{t.label}</option>)}
          </select>
        </label>
      )}
      {(tab === "compare" || tab === "discover") && (
        <label className="block text-sm">
          <span className="text-slate-400">Test / operation</span>
          <select className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm"
            value={props.testId} onChange={(e) => props.setTestId(e.target.value)}>
            {props.tests.map((t) => <option key={t.test_id} value={t.test_id}>{t.label}</option>)}
          </select>
        </label>
      )}
      {tab === "suitability" && (
        <label className="block text-sm">
          <span className="text-slate-400">Site</span>
          <select className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm"
            value={props.siteId} onChange={(e) => props.setSiteId(e.target.value)}>
            {props.sites.map((s) => <option key={s.site_id} value={s.site_id}>{s.label}</option>)}
          </select>
        </label>
      )}
      <button onClick={props.onRun} disabled={props.loading}
        className="w-full rounded bg-indigo-500 px-4 py-2 text-sm font-semibold disabled:opacity-50">
        {props.loading ? "Running…" : tab === "discover" ? "Discover new sites" : tab === "suitability" ? "Show suitability" : "Compare sites"}
      </button>
      <p className="text-xs text-slate-500">
        {tab === "discover" ? "Searches global windows for new candidates, excludes known sites, and attaches provenance."
          : tab === "suitability" ? "Shows which tests this site can support, and the limiting characteristic for each."
          : "Ranks sites with per-draw gating; proxy evidence stays provisional."}
      </p>
    </div>
  );
}

function SiteCard({ s }: { s: SiteResult }) {
  return (
    <div className="rounded border border-slate-700 bg-slate-900/50 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">{s.label}</span>
        <VerdictBadge verdict={s.verdict} />
      </div>
      <div className="mt-1 text-xs text-slate-400">
        score {s.score.toFixed(2)} · gate {(s.p_gate * 100).toFixed(0)}% · coverage {(s.coverage * 100).toFixed(0)}%
        {s.candidate_kind === "new" && <span className="ml-1 text-indigo-300">· 🔎 new candidate</span>}
      </div>
      {s.honest_limits.length > 0 && (
        <ul className="mt-1 list-inside list-disc text-xs text-amber-300/80">
          {s.honest_limits.map((h, i) => <li key={i}>{h}</li>)}
        </ul>
      )}
    </div>
  );
}

function SuitabilityList({ suit }: { suit: SuitabilityResult }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-400">vs target <code>{suit.target_id}</code></p>
      {suit.tests.map((e) => (
        <div key={e.test_id} className="rounded border border-slate-700 bg-slate-900/50 p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-semibold">{e.label}</span>
            <VerdictBadge verdict={e.verdict} />
          </div>
          {e.limiting_characteristic && (
            <div className="mt-1 text-xs text-slate-400">limited by: {e.limiting_characteristic}</div>
          )}
          {e.reasons.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-xs text-amber-300/80">
              {e.reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}
