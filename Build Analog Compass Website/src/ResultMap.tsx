import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

type Pin = {
  code: string;
  coords: string;
  score: number;
  place?: string;
  lat?: number | null;
  lon?: number | null;
};

// Parse "20.6421° N · 17.5214° E" -> [lon, lat]
function parseCoords(c: string): [number, number] | null {
  const m = c.match(/([\d.]+)°\s*([NS]).*?([\d.]+)°\s*([EW])/);
  if (!m) return null;
  let lat = parseFloat(m[1]);
  if (m[2] === "S") lat = -lat;
  let lon = parseFloat(m[3]);
  if (m[4] === "W") lon = -lon;
  return [lon, lat];
}

// A realistic satellite map (Esri World Imagery, no API key) of the candidate sites.
export default function ResultMap({
  candidates,
  focus,
}: {
  candidates: Pin[];
  focus?: Pin | null;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
      if (cancelled || !ref.current || mapRef.current) return;
      const map = new maplibregl.Map({
        container: ref.current,
        style: {
          version: 8,
          sources: {
            sat: {
              type: "raster",
              tiles: [
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
              ],
              tileSize: 256,
              attribution: "Imagery © Esri, Maxar, Earthstar Geographics",
            },
            labels: {
              type: "raster",
              tiles: [
                "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
              ],
              tileSize: 256,
            },
          },
          layers: [
            { id: "sat", type: "raster", source: "sat" },
            { id: "labels", type: "raster", source: "labels", paint: { "raster-opacity": 0.6 } },
          ],
        },
        center: [10, 25],
        zoom: 1.3,
      });
      mapRef.current = map;

      const pts: [number, number][] = [];
      for (const c of candidates) {
        const ll =
          c.lat != null && c.lon != null ? ([c.lon, c.lat] as [number, number]) : parseCoords(c.coords);
        if (!ll) continue;
        pts.push(ll);
        const el = document.createElement("div");
        el.className = "map-pin";
        el.textContent = c.code;
        const popup = new maplibregl.Popup({ offset: 16, closeButton: false }).setHTML(
          `<b>Candidate ${c.code}</b><br/>${c.score}% match<br/>${c.coords}` +
            (c.place ? `<br/><span style="opacity:.7">${c.place}</span>` : ""),
        );
        new maplibregl.Marker({ element: el }).setLngLat(ll).setPopup(popup).addTo(map);
      }
      if (pts.length) {
        const bounds = pts.reduce(
          (b, p) => b.extend(p),
          new maplibregl.LngLatBounds(pts[0], pts[0]),
        );
        map.fitBounds(bounds, { padding: 90, maxZoom: 5, duration: 0 });
      }
    })();
    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [candidates]);

  // Fly to a focused candidate (e.g. "Inspect on satellite map").
  useEffect(() => {
    if (!focus) return;
    const ll =
      focus.lat != null && focus.lon != null
        ? ([focus.lon, focus.lat] as [number, number])
        : parseCoords(focus.coords);
    const map = mapRef.current;
    if (!map || !ll) return;
    const go = () => map.flyTo({ center: ll, zoom: 7, duration: 1200 });
    if (map.loaded()) go();
    else map.once("load", go);
  }, [focus]);

  return <div ref={ref} className="result-map" aria-label="Map of candidate analog sites" />;
}
