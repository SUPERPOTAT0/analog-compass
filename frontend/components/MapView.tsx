"use client";

import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import { SiteResult, Verdict } from "@/lib/api";

const COLOR: Record<Verdict, string> = {
  pass: "#34d399",
  borderline: "#fbbf24",
  excluded: "#fb7185",
  blocked: "#94a3b8",
};

export function MapView({ sites }: { sites: SiteResult[] }) {
  const ref = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
      if (cancelled || !ref.current || mapRef.current) return;
      mapRef.current = new maplibregl.Map({
        container: ref.current,
        style: "https://demotiles.maplibre.org/style.json",
        center: [10, 25],
        zoom: 1.3,
      });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
      const map = mapRef.current;
      if (!map || cancelled) return;
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      for (const s of sites) {
        if (s.lat == null || s.lon == null) continue;
        const el = document.createElement("div");
        el.style.width = s.candidate_kind === "new" ? "14px" : "12px";
        el.style.height = el.style.width;
        el.style.borderRadius = "50%";
        el.style.background = COLOR[s.verdict];
        el.style.border = s.candidate_kind === "new" ? "2px dashed #fff" : "2px solid #0b1020";
        el.style.cursor = "pointer";
        const popup = new maplibregl.Popup({ offset: 12 }).setHTML(
          `<b>${s.label}</b><br/>${s.verdict.toUpperCase()} · score ${s.score.toFixed(
            2
          )} · gate ${(s.p_gate * 100).toFixed(0)}%<br/>${
            s.candidate_kind === "new" ? "🔎 discovered candidate<br/>" : ""
          }${s.honest_limits.map((h) => "• " + h).join("<br/>")}`
        );
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([s.lon, s.lat])
          .setPopup(popup)
          .addTo(map);
        markersRef.current.push(marker);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sites]);

  return <div ref={ref} className="h-full w-full rounded-lg overflow-hidden" />;
}
