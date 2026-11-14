import { Verdict } from "@/lib/api";

const STYLE: Record<Verdict, string> = {
  pass: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  borderline: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  excluded: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  blocked: "bg-slate-500/20 text-slate-300 border-slate-500/40",
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${STYLE[verdict]}`}>
      {verdict}
    </span>
  );
}
