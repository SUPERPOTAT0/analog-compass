# Analog Compass — unified product (this is the canonical website)

This Figma Make app is the **main product**: the editorial landing + storytelling **and**
the functional explorer, wired to the real Analog Compass engine. Everything degrades
gracefully — if the backend is offline, the UI falls back to built-in sample data, so it
always renders.

## What's wired to the live engine (`src/api.ts`)

| UI surface | Backend | Behaviour |
|---|---|---|
| Landing **"Find an analog"** CTA | — | Launches the explorer (SearchFlow). |
| **SearchFlow → Result** | `POST /discover` + `GET /site_profile` | Real **discovered** candidates with real per-window measurements in the compare table. Shows "Live engine". |
| Result **Map** view | — | Realistic **satellite basemap** (Esri World Imagery, no key) in `src/ResultMap.tsx`, with a rust pin per candidate at its real coordinates. "Inspect on satellite map" in the detail drawer flies the map to that candidate. |
| **Precision filtering** (step 4) | `POST /discover` `constraints[]` | Controlled sliders/toggles (`src/api.ts` `Filters` → `buildConstraints`) become **strict required gates**: slope/temperature/sunlit/basaltic/remoteness/wind + permafrost/low-veg/dust/caves. The engine returns only windows that satisfy every required parameter; if none qualify the UI shows a "no windows match" state (no random lists). |
| **Tests & Base Operations** | `GET /site_operations` | Per-candidate section in the detail drawer: the tests this environment supports (`actionable`) plus a professional **"why it matters for a Moon/Mars base"** explanation (`base_relevance` in `config/tests.yaml`), ranked by engine verdict. |
| **Card imagery** | `GET /site_profile` | Each result card shows a real, high-res **environment-matched** terrain photo chosen from the window's dominant characteristics (`pickBiomeImage` in `src/api.ts`): volcanic / polar / arid / desert / lava-tube / rocky. |
| **Compare** table | `/site_profile` | Real values (slope, temperature, basaltic fraction…) + source + fit. |
| **Data** page | `GET /layers` | Live source ledger + data-layer catalog ("live catalog"). |
| **Add new data** | `POST /data/contributions` | Real intake validation → review ticket (`DS-…`). |
| **AI Assistant** | `POST /agent/chat` (SSE) | Streams the grounded Claude agent; falls back to built-in answers if `ANTHROPIC_API_KEY` is unset. |

Mission → engine test and planet → target mapping lives in `src/api.ts`
(`MISSION_TO_TEST`, `PLANET_TO_TARGET`).

## Visual direction

The **Figma layout, structure and input fields are preserved**; the skin is the
**deep-space palette** (Void `#04050C` · Core Gold `#F2B544` · Nebula Blue `#6E86B8` ·
Dust Rose `#E8789E` · warm white `#F4EEDD`) applied by remapping the design tokens in
`src/index.css` (`:root`) plus a "SPACE THEME" override layer at the end of that file.

3D / motion elements (reconstructed from the earlier concept):
- `src/Galaxy.tsx` — procedural spiral galaxy on the Landing hero (lazy-loaded).
- `src/fx.tsx` — `CursorGlow` (gold cursor halo) + `useCardTilt()` (global 3D tilt +
  gold glow on candidate/analog/type cards). Honors `prefers-reduced-motion` / touch.
- The **map is lazy-loaded** (`lazy(() => import("./ResultMap"))`), so MapLibre (~786 kB)
  only downloads when the Map view is opened; initial JS stays ~83 kB gzip.

## Run

```bash
# 1. backend (from the repo root)
make serve                      # http://localhost:8000

# 2. this website
npm install
npm run dev                     # http://localhost:5173  (or `npm run preview` on 4173)
```

Point the site at the API with `VITE_API_URL` (default `http://localhost:8000`). The API
allows any localhost port via CORS, so dev "just works". For the AI assistant, set
`ANTHROPIC_API_KEY` on the backend.

## Note on the other frontend

- `../frontend/` — a Next.js engineer-facing dashboard (map + raw compare/suitability).
  Useful for debugging the engine; not the public product. (The earlier standalone cinematic
  galaxy site was removed — this unified product supersedes it.)
