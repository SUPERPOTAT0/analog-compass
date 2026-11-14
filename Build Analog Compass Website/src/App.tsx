import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  DEFAULT_FILTERS,
  discoverCandidates,
  fetchOperations,
  getLayers,
  PLANET_TO_TARGET,
  streamAssistant,
  submitContribution,
  type Filters,
  type LiveCandidate,
  type Operation,
} from "./api";
// Lazy-loaded so MapLibre (heavy) only downloads when the Map view is opened.
const ResultMap = lazy(() => import("./ResultMap"));
const Galaxy = lazy(() => import("./Galaxy"));
import { CursorGlow, useCardTilt } from "./fx";

type Page = "landing" | "find" | "result" | "analogs" | "data" | "add" | "assistant" | "system";

const photos = [
  "https://images.unsplash.com/photo-1648498015611-4e51d7d3f74a?auto=format&fit=crop&w=1200&q=85",
  "https://images.unsplash.com/photo-1666668152560-e6807f6ffabe?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1620824175623-930d7a980da8?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1684275750619-8ae782588f78?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1684275751032-9108ff470c6a?auto=format&fit=crop&w=900&q=80",
];

type Candidate = {
  code: string;
  slug: string;
  place: string;
  country: string;
  coords: string;
  score: number;
  image: string;
  keys: string[];
  why: string;
  limit: string;
  tradeoff: string;
  values: string[][];
};

const compareRows = [
  ["Slope", "Traverse effort", "4—12°"],
  ["Sunlit fraction", "Direct light during field season", "≥ 60%"],
  ["Temperature range", "Surface working range", "−25—25°C"],
  ["Lithology", "Mapped surface material", "Basaltic"],
  ["Basaltic fraction", "Share of mapped surface", "≥ 70%"],
  ["Caves / lava tubes", "Mapped subsurface access", "Preferred"],
  ["Remoteness", "Distance from maintained road", "≥ 80 km"],
  ["Dust", "Exposed fine surface material", "High"],
  ["Wind", "Median field-season wind", "≤ 30 km/h"],
  ["Permafrost", "Persistently frozen ground", "Preferred"],
];

const candidates: Candidate[] = [
  {
    code: "N-017",
    slug: "n017",
    place: "Tibesti Mountains",
    country: "Chad",
    coords: "20.6421° N · 17.5214° E",
    score: 84,
    image: photos[3],
    keys: ["7.2° mean slope", "Basaltic lithology", "−19—23°C"],
    why: "The exposed volcanic terrain, thermal range and workable slopes closely match the requested desert field setting.",
    limit: "No mapped permafrost; access and seasonal wind observations are incomplete.",
    tradeoff: "Best thermal and lithology match. Remote access makes a field campaign harder.",
    values: [
      ["7.2°", "close", "LOLA / SRTM"],
      ["67%", "close", "LRO"],
      ["−19—23°C", "close", "Diviner"],
      ["Basaltic", "close", "ASTER"],
      ["82%", "close", "Sentinel-2"],
      ["Possible", "partial", "PDS"],
      ["142 km", "close", "Earthdata"],
      ["High", "close", "Worldview"],
      ["27 km/h", "close", "MERRA-2"],
      ["None mapped", "far", "ESA OSC"],
    ],
  },
  {
    code: "N-042",
    slug: "n042",
    place: "Dry Valleys",
    country: "Antarctica",
    coords: "77.4682° S · 162.5178° E",
    score: 78,
    image: photos[4],
    keys: ["0.4% vegetation", "126 km remote", "Permafrost"],
    why: "Extreme dryness, remoteness and frozen ground make this a useful operational analog for a lunar polar habitat.",
    limit: "Low winter illumination and protected-area logistics are not represented by the score.",
    tradeoff: "Strongest for dryness and permafrost. Illumination is the weakest of the three.",
    values: [
      ["9.8°", "close", "LOLA / REMA"],
      ["41%", "far", "LRO"],
      ["−31—8°C", "partial", "Diviner"],
      ["Dolerite", "partial", "USGS"],
      ["64%", "partial", "Sentinel-2"],
      ["None mapped", "far", "PDS"],
      ["126 km", "close", "Earthdata"],
      ["Low", "partial", "Worldview"],
      ["34 km/h", "partial", "MERRA-2"],
      ["Continuous", "close", "ESA OSC"],
    ],
  },
  {
    code: "N-063",
    slug: "n063",
    place: "Puna de Atacama",
    country: "Argentina",
    coords: "23.4618° S · 66.9412° W",
    score: 71,
    image: photos[1],
    keys: ["6.1° mean slope", "48 km from road", "Dry volcanic plain"],
    why: "The plateau offers a practical, dry traverse setting with close slope behavior and broad exposed terrain.",
    limit: "Basaltic coverage is below the request and no subsurface ice claim can be made.",
    tradeoff: "Easiest to reach and strongest slope match. Basaltic coverage is below the request.",
    values: [
      ["6.1°", "close", "LOLA / SRTM"],
      ["72%", "close", "LRO"],
      ["−8—19°C", "partial", "Diviner"],
      ["Andesite", "partial", "ASTER"],
      ["53%", "far", "Sentinel-2"],
      ["Possible", "partial", "PDS"],
      ["48 km", "far", "Earthdata"],
      ["High", "close", "Worldview"],
      ["22 km/h", "close", "MERRA-2"],
      ["Patchy", "partial", "ESA OSC"],
    ],
  },
];

type Analog = {
  name: string;
  place: string;
  type: string;
  temp: string;
  rain: string;
  image: string;
  new?: boolean;
};

const analogs: Analog[] = [
  {
    name: "Atacama Desert",
    place: "Antofagasta, Chile",
    type: "Desert",
    temp: "−2—32°C",
    rain: "< 2 mm/yr",
    image: photos[1],
  },
  {
    name: "Haughton Crater",
    place: "Devon Island, Canada",
    type: "Impact crater",
    temp: "−40—10°C",
    rain: "Permafrost",
    image: photos[0],
  },
  {
    name: "Death Valley",
    place: "California, USA",
    type: "Desert",
    temp: "5—47°C",
    rain: "60 mm/yr",
    image: photos[2],
  },
  {
    name: "Surtshellir lava tube",
    place: "Western Iceland",
    type: "Lava tube",
    temp: "1—5°C",
    rain: "Basaltic",
    image: photos[3],
  },
  {
    name: "McMurdo Dry Valleys",
    place: "Victoria Land, Antarctica",
    type: "Polar / ice",
    temp: "−30—0°C",
    rain: "< 100 mm/yr",
    image: photos[4],
  },
  {
    name: "Askja volcanic field",
    place: "Icelandic Highlands",
    type: "Volcanic",
    temp: "−15—12°C",
    rain: "Basaltic",
    image: photos[0],
  },
  ...candidates.map((candidate) => ({
    name: `Candidate ${candidate.code}`,
    place: `${candidate.place}, ${candidate.country}`,
    type: "New candidate",
    temp: candidate.values[2][0],
    rain: `${candidate.score}% match`,
    image: candidate.image,
    new: true,
  })),
];

const characteristics = [
  ["Mean slope", "7.4", "degrees", "Inside 4—12°", "LOLA / SRTM"],
  ["Sunlit fraction", "63", "%", "3% above minimum", "LRO illumination"],
  ["Surface temperature", "−18—21", "°C", "Inside requested range", "Diviner / MODIS"],
  ["Lithology", "Basaltic andesite", "—", "Close match", "PDS / ASTER"],
  ["Volcanic fraction", "81", "%", "11% above minimum", "Earthdata"],
  ["Remoteness", "118", "km to road", "Meets request", "OpenStreetMap"],
  ["Vegetation cover", "0.7", "%", "Meets < 2%", "Worldview"],
  ["Wind, median", "22", "km/h", "Within tolerance", "MERRA-2"],
];

function Mark({ small = false }: { small?: boolean }) {
  return (
    <button
      className={`mark ${small ? "small" : ""}`}
      onClick={() => location.reload()}
      aria-label="Analog Compass home"
    >
      <span>AC</span> Analog Compass
    </button>
  );
}

function Icon({
  name,
}: {
  name: "arrow" | "menu" | "close" | "chat" | "plus" | "search" | "upload";
}) {
  const paths = {
    arrow: (
      <>
        <path d="M5 12h14M14 7l5 5-5 5" />
      </>
    ),
    menu: (
      <>
        <path d="M4 7h16M4 12h16M4 17h16" />
      </>
    ),
    close: (
      <>
        <path d="m6 6 12 12M18 6 6 18" />
      </>
    ),
    chat: (
      <>
        <path d="M5 5h14v11H9l-4 3V5Z" />
      </>
    ),
    plus: (
      <>
        <path d="M12 5v14M5 12h14" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 4 4" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4m-4 4 4-4 4 4M5 14v5h14v-5" />
      </>
    ),
  };
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

function Button({
  children,
  kind = "primary",
  onClick,
  disabled = false,
  type = "button",
}: {
  children: React.ReactNode;
  kind?: "primary" | "secondary" | "text";
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={`btn ${kind}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

function Nav({ page, go }: { page: Page; go: (p: Page) => void }) {
  const [menu, setMenu] = useState(false);
  const links: [string, Page][] = [
    ["Find an analog", "find"],
    ["All analogs", "analogs"],
    ["Data", "data"],
    ["Add new data", "add"],
    ["AI assistant", "assistant"],
  ];
  return (
    <header className="nav">
      <button className="menu-btn" onClick={() => setMenu(!menu)} aria-label="Open menu">
        <Icon name={menu ? "close" : "menu"} />
      </button>
      <nav className={menu ? "open" : ""}>
        {links.map(([label, p]) => (
          <button
            className={page === p ? "active" : ""}
            key={p}
            onClick={() => {
              go(p);
              setMenu(false);
            }}
          >
            {label}
          </button>
        ))}
      </nav>
    </header>
  );
}

function Assistant({ full = false, onClose }: { full?: boolean; onClose?: () => void }) {
  const [messages, setMessages] = useState<{ who: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const mockAnswer = (q: string) => {
    const unknown = q.toLowerCase().includes("permit") || q.toLowerCase().includes("today");
    const comparing = q.toLowerCase().includes("which of these");
    return comparing
      ? "From the displayed measurements, I would start with the top-ranked candidate — its score comes from the closest temperature, slope and basaltic-lithology fit. I cannot decide operational suitability from these data because permits, current access and field costs are not included."
      : unknown
        ? "I do not know that from the records available here. The dataset has no current access, permit or live weather information, so a local field team would need to check it."
        : q.toLowerCase().includes("limit")
          ? "The strongest limit is the atmosphere: Earth pressure, weather and biology cannot reproduce Mars — nor can Earth reproduce reduced gravity, vacuum or space radiation. The terrain and thermal range are the useful parts of this comparison."
          : "I would compare the terrain first — mean slope and mapped basaltic material are the closest displayed values for the current search.";
  };
  const ask = async (q: string) => {
    if (!q.trim() || busy) return;
    const history = [...messages, { who: "you", text: q }];
    setMessages([...history, { who: "field", text: "" }]);
    setInput("");
    setBusy(true);
    const convo = history.map((m) => ({
      role: m.who === "you" ? "user" : "assistant",
      content: m.text,
    }));
    let acc = "";
    const ok = await streamAssistant(
      convo,
      (t) => {
        acc += t;
        setMessages([...history, { who: "field", text: acc }]);
      },
      () => {},
    );
    if (ok) setLive(true);
    else setMessages([...history, { who: "field", text: mockAnswer(q) }]);
    setBusy(false);
  };
  return (
    <aside className={full ? "assistant full" : "assistant"}>
      <div className="assistant-head">
        <div>
          <span className="eyebrow">Field notes / sample</span>
          <h2>AI Assistant</h2>
        </div>
        {onClose && (
          <button className="icon-btn" onClick={onClose} aria-label="Close assistant">
            <Icon name="close" />
          </button>
        )}
      </div>
      <p className="muted">
        A plain-spoken guide to the records. The AI Assistant cites the sample data it uses and says
        when it cannot tell.
      </p>
      <div className="suggestions">
        {[
          "Which of these should I pick, and why?",
          "What are their limits?",
          "Which source covers temperature?",
        ].map((q) => (
          <button onClick={() => ask(q)} key={q}>
            {q}
          </button>
        ))}
      </div>
      <div className="messages">
        {messages.length === 0 && (
          <div className="note-empty">
            <div className="tiny-contours" />
            <strong>No notes yet.</strong>
            <span>Ask about an analog, measurement or source.</span>
          </div>
        )}
        {messages.map((m, i) => (
          <div className={`message ${m.who}`} key={i}>
            <small>{m.who === "you" ? "You" : "AI Assistant"}</small>
            <p>{m.text || (busy ? "…" : "")}</p>
            {m.who === "field" && m.text && (
              <span className="source">
                {live ? "Grounded in engine tools" : "Sources: sample LOLA · ASTER"}
              </span>
            )}
          </div>
        ))}
      </div>
      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
      >
        <label htmlFor={full ? "full-chat" : "side-chat"}>Your question</label>
        <div>
          <input
            id={full ? "full-chat" : "side-chat"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a specific question…"
          />
          <button aria-label="Send question">
            <Icon name="arrow" />
          </button>
        </div>
      </form>
    </aside>
  );
}

function Landing({ start }: { start: () => void }) {
  return (
    <main className="landing">
      <Suspense fallback={null}>
        <Galaxy />
      </Suspense>
      <div
        className="landing-photo"
        role="img"
        aria-label="Rocky desert ridges like a planetary field site"
      />
      <div className="topo topo-one" />
      <div className="topo topo-two" />
      <div className="hero">
        <span className="kicker">Earth sites for off-world questions</span>
        <h1>
          All analogs
          <br />
          in one place.
        </h1>
        <div className="hero-bottom">
          <ol>
            <li>
              <b>01</b>
              <span>Finds new places using data that is already available.</span>
            </li>
            <li>
              <b>02</b>
              <span>Brings the data together, instead of leaving it across scattered portals.</span>
            </li>
            <li>
              <b>03</b>
              <span>Keeps growing as data is added and new analogs are discovered.</span>
            </li>
          </ol>
          <Button onClick={start}>
            Find an analog <Icon name="arrow" />
          </Button>
        </div>
      </div>
    </main>
  );
}

const types = [
  ["Desert", "Dry, exposed terrain with little vegetation.", photos[1]],
  ["Polar / ice", "Cold ground, permafrost and persistent ice.", photos[4]],
  ["Volcanic", "Young basalt, ash and rugged lava fields.", photos[2]],
  ["Cave / lava tube", "Sheltered subsurface volcanic terrain.", photos[3]],
  ["Impact crater", "Shocked rock and cratered topography.", photos[0]],
  ["Similar overall", "Let the measurements lead the search.", photos[4]],
];
const missions = [
  ["Habitat setup", "Stable terrain and long-term surface access."],
  ["Rover traverse", "A route that tests mobility and navigation."],
  ["Drilling for water ice", "Cold material and subsurface access."],
  ["Life detection", "Low biomass and preserved signatures."],
  ["Resource extraction", "Mapped geology and workable slopes."],
];

function StepHeader({ step }: { step: number }) {
  return (
    <div className="steps" aria-label={`Step ${step} of 4`}>
      <span>Search plan</span>
      <div>
        {[1, 2, 3, 4].map((n) => (
          <i className={n <= step ? "done" : ""} key={n}>
            <b>{n}</b>
          </i>
        ))}
      </div>
      <em>{step} / 4</em>
    </div>
  );
}

function SearchFlow({
  finish,
  initialStep = 1,
  initialChoices,
}: {
  finish: (choices: Record<number, string>, filters: Filters) => void;
  initialStep?: number;
  initialChoices?: Record<number, string>;
}) {
  const [step, setStep] = useState(initialStep);
  const [selected, setSelected] = useState<Record<number, string>>(
    initialChoices ?? {
      1: "Volcanic",
      2: "Mars",
      3: "Rover traverse",
    },
  );
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const setF = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    setFilters((f) => ({ ...f, [key]: value }));
  const [loading, setLoading] = useState(false);
  const [loadStep, setLoadStep] = useState(0);
  const finishedRef = useRef(false);
  useEffect(() => {
    if (!loading) return;
    const id = window.setInterval(
      () =>
        setLoadStep((s) => {
          if (s >= 2) {
            window.clearInterval(id);
            if (!finishedRef.current) {
              finishedRef.current = true;
              setTimeout(() => finish(selected, filters), 650);
            }
            return s;
          }
          return s + 1;
        }),
      900,
    );
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);
  if (loading) {
    const lines = [
      "Reading Diviner temperature data…",
      "Checking terrain and illumination…",
      "Comparing the records with your choices…",
    ];
    return (
      <section className="loading">
        <div className="orbit">
          <span />
        </div>
        <span className="eyebrow">Search in progress</span>
        <h1>Looking carefully.</h1>
        <div className="loading-list">
          {lines.map((l, i) => (
            <p className={i <= loadStep ? "current" : ""} key={l}>
              <i>{i < loadStep ? "✓" : "—"}</i>
              {l}
            </p>
          ))}
        </div>
        <div className="result-skeleton" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
        <small>This prototype is using sample records.</small>
      </section>
    );
  }
  return (
    <main className="page flow-page">
      <StepHeader step={step} />
      {step === 1 && (
        <section className="step-content">
          <div className="step-title">
            <span className="eyebrow">Step one · terrain family</span>
            <h1>
              What kind of place
              <br />
              are you looking for?
            </h1>
            <p>Choose the broad terrain family. You can make it precise later.</p>
          </div>
          <div className="type-grid">
            {types.map(([name, desc, image]) => (
              <button
                className={`select-card image-card ${selected[1] === name ? "selected" : ""}`}
                onClick={() => setSelected({ ...selected, 1: name })}
                key={name}
              >
                <img src={image} alt="" />
                <span>
                  <strong>{name}</strong>
                  <small>{desc}</small>
                </span>
                <i />
              </button>
            ))}
          </div>
        </section>
      )}
      {step === 2 && (
        <section className="step-content">
          <div className="step-title">
            <span className="eyebrow">Step two · destination</span>
            <h1>Where will the mission be built?</h1>
            <p>Pick the off-world setting the Earth site should help you understand.</p>
          </div>
          <div className="planet-grid">
            {[
              ["Moon", "Moon"],
              ["Mars", "Mars"],
            ].map(([name, planet]) => (
              <button
                className={`planet ${selected[2] === name ? "selected" : ""}`}
                onClick={() => setSelected({ ...selected, 2: name })}
                key={name}
              >
                <div className={planet.toLowerCase()}>
                  <span />
                  <i />
                </div>
                <h3>{name}</h3>
              </button>
            ))}
          </div>
        </section>
      )}
      {step === 3 && (
        <section className="step-content">
          <div className="step-title">
            <span className="eyebrow">Step three · field objective</span>
            <h1>What does the mission need to do?</h1>
            <p>The same landscape can be useful for one test and poor for another.</p>
          </div>
          <div className="mission-list">
            {missions.map(([name, desc], i) => (
              <button
                className={selected[3] === name ? "selected" : ""}
                onClick={() => setSelected({ ...selected, 3: name })}
                key={name}
              >
                <b>0{i + 1}</b>
                <span>
                  <strong>{name}</strong>
                  <small>{desc}</small>
                </span>
                <i />
              </button>
            ))}
          </div>
        </section>
      )}
      {step === 4 && (
        <section className="step-content">
          <div className="step-title">
            <span className="eyebrow">Step four · precise parameters</span>
            <h1>What must the place be like?</h1>
            <p>
              Set the environmental, terrain and soil parameters that matter. The engine returns
              only windows that strictly satisfy them — no generic or random lists.
            </p>
          </div>
          <div className="controls">
            <CtrlRange label="Max mean slope" helper="Cap traverse slope. 40° = no limit."
              min={2} max={40} value={filters.slopeMax} unit="°"
              display={filters.slopeMax >= 40 ? "Any" : `≤ ${filters.slopeMax}°`}
              onChange={(v) => setF("slopeMax", v)} />
            <CtrlRange label="Max surface temperature" helper="Thermal ceiling (median). 40°C = no limit."
              min={-40} max={40} value={filters.tempMax} unit="°C"
              display={filters.tempMax >= 40 ? "Any" : `≤ ${filters.tempMax}°C`}
              onChange={(v) => setF("tempMax", v)} />
            <CtrlRange label="Min sunlit fraction" helper="Share of the period with direct light."
              min={0} max={100} value={filters.sunlitMin} unit="%"
              display={filters.sunlitMin <= 0 ? "Any" : `≥ ${filters.sunlitMin}%`}
              onChange={(v) => setF("sunlitMin", v)} />
            <CtrlRange label="Min basaltic regolith" helper="Share of mapped surface that is basaltic."
              min={0} max={100} value={filters.basalticMin} unit="%"
              display={filters.basalticMin <= 0 ? "Any" : `≥ ${filters.basalticMin}%`}
              onChange={(v) => setF("basalticMin", v)} />
            <CtrlRange label="Min remoteness (isolation)" helper="Travel time from infrastructure. 0 = off."
              min={0} max={2000} step={50} value={filters.remotenessMin} unit=""
              display={filters.remotenessMin <= 0 ? "Any" : `≥ ${filters.remotenessMin}`}
              onChange={(v) => setF("remotenessMin", v)} />
            <CtrlRange label="Max median wind" helper="Near-surface wind. 40 m/s = no limit."
              min={1} max={40} value={filters.windMax} unit=" m/s"
              display={filters.windMax >= 40 ? "Any" : `≤ ${filters.windMax} m/s`}
              onChange={(v) => setF("windMax", v)} />
            {([
              ["requireCaves", "Caves or lava tubes", "Require mapped subsurface access."],
              ["requirePermafrost", "Permafrost / ground ice", "Require persistently frozen ground."],
              ["lowVegetation", "Hyper-arid / low vegetation", "Require a life-limited surface."],
              ["highDust", "High dust exposure", "Require strong aeolian / dust signal."],
            ] as [keyof Filters, string, string][]).map(([key, title, help]) => (
              <label className="toggle-row" key={key}>
                <span>
                  <strong>{title}</strong>
                  <small>{help}</small>
                </span>
                <input type="checkbox" checked={!!filters[key]}
                  onChange={(e) => setF(key, e.target.checked as Filters[typeof key])} />
                <i />
              </label>
            ))}
          </div>
        </section>
      )}
      <div className="flow-actions">
        <Button
          kind="secondary"
          onClick={() => (step === 1 ? location.reload() : setStep(step - 1))}
        >
          Back
        </Button>
        <span className="mono">
          {selected[1]} / {selected[2]}
        </span>
        <Button onClick={() => (step < 4 ? setStep(step + 1) : setLoading(true))}>
          {step < 4 ? "Next" : "Find"} <Icon name="arrow" />
        </Button>
      </div>
    </main>
  );
}

function Range({
  label,
  value,
  helper,
  min,
  max,
}: {
  label: string;
  value: string;
  helper: string;
  min: number;
  max?: number;
}) {
  return (
    <label className="range-row">
      <span>
        <strong>{label}</strong>
        <small>{helper}</small>
      </span>
      <div>
        <output>{value}</output>
        <input type="range" defaultValue={min} />
        <div
          className="range-mark"
          style={{ left: `${min}%`, width: max ? `${max - min}%` : "30%" }}
        />
      </div>
    </label>
  );
}

function CtrlRange({
  label, helper, min, max, step = 1, value, display, onChange,
}: {
  label: string;
  helper: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  unit?: string;
  display: string;
  onChange: (v: number) => void;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <label className="range-row">
      <span>
        <strong>{label}</strong>
        <small>{helper}</small>
      </span>
      <div>
        <output>{display}</output>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <div className="range-mark" style={{ left: `${pct}%`, width: "2px" }} />
      </div>
    </label>
  );
}

function Table() {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Characteristic</th>
            <th>Value</th>
            <th>Compared with request</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {characteristics.map(([name, value, unit, match, source]) => (
            <tr key={name}>
              <th>{name}</th>
              <td>
                <b>{value}</b> <small>{unit}</small>
              </td>
              <td>
                <span className="match">Within range</span>
                {match}
              </td>
              <td>
                <span className="source">{source}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OperationsSection({ gridId, targetId }: { gridId?: string; targetId?: string }) {
  const [ops, setOps] = useState<Operation[] | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const r = await fetchOperations(gridId, targetId);
      if (!cancelled) {
        setOps(r);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [gridId, targetId]);

  if (loading)
    return (
      <div className="ops-section">
        <span className="eyebrow">Tests &amp; base operations</span>
        <p className="muted">Assessing which tests this environment can support…</p>
      </div>
    );
  if (!ops || ops.length === 0) return null;
  const supported = ops.filter((o) => o.supported);
  const rest = ops.filter((o) => !o.supported);
  return (
    <div className="ops-section">
      <span className="eyebrow">Tests &amp; base operations</span>
      <h3>What you can test here — and why it matters for a base</h3>
      {supported.length === 0 && (
        <p className="muted">No standard test clears the bar at this site; see limits below.</p>
      )}
      {supported.map((o) => (
        <article className={`op-card op-${o.verdict}`} key={o.test_id}>
          <div className="op-head">
            <strong>{o.label}</strong>
            <span className={`op-verdict ${o.verdict}`}>{o.verdict}</span>
          </div>
          <p className="op-actionable">{o.actionable}</p>
          <p className="op-why">
            <b>Why it matters for a Moon/Mars base:</b> {o.base_relevance}
          </p>
        </article>
      ))}
      {rest.length > 0 && (
        <p className="op-rest muted">Not suitable here: {rest.map((o) => o.label).join(", ")}.</p>
      )}
    </div>
  );
}

function Result({
  restart,
  change,
  ask,
  choices,
  liveCandidates,
}: {
  restart: () => void;
  change: () => void;
  ask: () => void;
  choices: Record<number, string>;
  liveCandidates?: Candidate[] | null;
}) {
  const online = liveCandidates !== null && liveCandidates !== undefined;
  const list: Candidate[] = online ? (liveCandidates as Candidate[]) : candidates;
  const live = online && list.length > 0;
  const targetId = PLANET_TO_TARGET[choices[2]] || "mars_mid_latitude";
  const [view, setView] = useState<"cards" | "compare" | "map">("cards");
  const [focus, setFocus] = useState<Candidate | null>(null);
  const [selected, setSelected] = useState(() => list.slice(0, 2).map((c) => c.code));
  const [detail, setDetail] = useState<Candidate | null>(null);
  const [mobileCandidate, setMobileCandidate] = useState(list[0]?.slug ?? "n017");
  const state = new URLSearchParams(window.location.search).get("result");
  const toggleCandidate = (code: string) =>
    setSelected((current) =>
      current.includes(code) ? current.filter((item) => item !== code) : [...current, code],
    );
  const viewOnMap = (c: Candidate) => {
    setFocus(c);
    setDetail(null);
    setView("map");
  };
  const compared = list.filter((candidate) => selected.includes(candidate.code));

  // Strict filtering produced no matching windows (engine ran, nothing qualified).
  if (online && list.length === 0)
    return (
      <main className="page result-state">
        <div className="state-illustration">
          <span />
          <i />
        </div>
        <span className="eyebrow">No windows match your parameters</span>
        <h1>Nothing on Earth fits all of those at once.</h1>
        <p>
          The engine strictly matched every required parameter and found no qualifying window.
          Loosen a slider or clear a required toggle to widen the search.
        </p>
        <Button onClick={change}>Adjust parameters</Button>
      </main>
    );

  if (state === "empty" || state === "error")
    return (
      <main className="page result-state">
        <div className="state-illustration">
          <span />
          <i />
        </div>
        <span className="eyebrow">
          {state === "error" ? "The source check stopped" : "No candidates found"}
        </span>
        <h1>{state === "error" ? "One archive did not answer." : "The notebook is empty here."}</h1>
        <p>
          {state === "error"
            ? "Your choices are safe. Try the search again, or return later when the source is available."
            : "Try loosening the temperature, basaltic fraction or remoteness filters to give the search more room."}
        </p>
        <Button onClick={change}>{state === "error" ? "Try again" : "Loosen filters"}</Button>
      </main>
    );

  return (
    <main className="page result-page">
      <section className="result-summary">
        <div>
          <span className="eyebrow">
            Search complete · {live ? "Live engine" : "Sample data"}
          </span>
          <h1>
            We found {list.length} new place{list.length === 1 ? "" : "s"} that fit a{" "}
            {choices[1].toLowerCase()} analog for a {choices[2]} {choices[3].toLowerCase()}.
          </h1>
          <div className="choice-tags">
            <span>{choices[1]}</span>
            <span>{choices[2]}</span>
            <span>{choices[3]}</span>
          </div>
        </div>
        <button onClick={change}>Change my choices</button>
      </section>

      <div className="result-toolbar">
        <span className="eyebrow">Ranked strongest to weakest</span>
        <div className="view-toggle" aria-label="Result view">
          <button className={view === "cards" ? "active" : ""} onClick={() => setView("cards")}>
            Cards
          </button>
          <button className={view === "map" ? "active" : ""} onClick={() => setView("map")}>
            Map
          </button>
          <button
            className={view === "compare" ? "active" : ""}
            onClick={() => {
              setMobileCandidate(compared[0]?.slug ?? "n017");
              setView("compare");
            }}
          >
            Compare {selected.length}
          </button>
        </div>
      </div>

      {view === "cards" && (
        <section className="candidate-grid">
          {list.map((candidate, index) => (
            <article className={`candidate-card rank-${index + 1}`} key={candidate.code}>
              <div className="candidate-photo">
                <img src={candidate.image} alt={`${candidate.place} terrain`} loading="lazy" />
                <span className="candidate-footprint">{index + 1}</span>
                <em>{candidate.place}</em>
              </div>
              <div className="candidate-copy">
                <div className="candidate-labels">
                  <span className="new-label">New candidate</span>
                  {index === 0 && <span className="best-label">Best match</span>}
                </div>
                <span className="eyebrow">
                  {candidate.place} · {candidate.country}
                </span>
                <h2>Candidate {candidate.code}</h2>
                <p className="coords">{candidate.coords}</p>
                <div className="score">
                  <div>
                    <i style={{ width: `${candidate.score}%` }} />
                  </div>
                  <b>{candidate.score}% match</b>
                </div>
                <ul>
                  {candidate.keys.map((key) => (
                    <li key={key}>{key}</li>
                  ))}
                </ul>
                <div className="candidate-actions">
                  <Button kind="secondary" onClick={() => setDetail(candidate)}>
                    Open details
                  </Button>
                  <label>
                    <input
                      type="checkbox"
                      checked={selected.includes(candidate.code)}
                      onChange={() => toggleCandidate(candidate.code)}
                    />
                    <span>Add to compare</span>
                  </label>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}
      {view === "map" && (
        <section className="map-view">
          <Suspense fallback={<div className="result-map map-loading">Loading map…</div>}>
            <ResultMap candidates={list} focus={focus} />
          </Suspense>
        </section>
      )}
      {view === "compare" && (
        <section className="compare-view">
          <div className="mobile-candidate-tabs">
            {compared.map((candidate) => (
              <button
                className={mobileCandidate === candidate.slug ? "active" : ""}
                onClick={() => setMobileCandidate(candidate.slug)}
                key={candidate.code}
              >
                {candidate.code}
              </button>
            ))}
            <span>Compare {selected.length}</span>
          </div>
          {compared.length < 2 ? (
            <div className="compare-empty">
              <h2>Choose at least two places.</h2>
              <p>Return to Cards and add another candidate to compare.</p>
              <Button kind="secondary" onClick={() => setView("cards")}>
                Back to cards
              </Button>
            </div>
          ) : (
            <>
              <div className={`compare-table-wrap focus-${mobileCandidate}`}>
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th>Characteristic / request</th>
                      {compared.map((candidate, index) => (
                        <th data-candidate={candidate.slug} key={candidate.code}>
                          <small>
                            0{index + 1} · {candidate.score}%
                          </small>
                          Candidate {candidate.code}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {compareRows.map(([name, helper, asked], rowIndex) => {
                      const bestScore = Math.min(
                        ...compared.map((candidate) => {
                          const fit = candidate.values[rowIndex][1];
                          return fit === "close" ? 0 : fit === "partial" ? 1 : 2;
                        }),
                      );
                      return (
                        <tr key={name}>
                          <th>
                            <strong>{name}</strong>
                            <small>{helper}</small>
                            <code>Asked: {asked}</code>
                          </th>
                          {compared.map((candidate) => {
                            const [value, fit, source] = candidate.values[rowIndex];
                            const fitScore = fit === "close" ? 0 : fit === "partial" ? 1 : 2;
                            return (
                              <td
                                className={fitScore === bestScore ? "best-value" : ""}
                                data-candidate={candidate.slug}
                                key={candidate.code}
                              >
                                <span className={`fit ${fit}`} />
                                <b>{value}</b>
                                <span className="source">{source}</span>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                    <tr className="overall-row">
                      <th>Overall match</th>
                      {compared.map((candidate) => (
                        <td data-candidate={candidate.slug} key={candidate.code}>
                          <b>{candidate.score}%</b>
                        </td>
                      ))}
                    </tr>
                    <tr className="limits-row">
                      <th>
                        <strong>Limits</strong>
                        <small>Where the analogy stops</small>
                      </th>
                      {compared.map((candidate) => (
                        <td data-candidate={candidate.slug} key={candidate.code}>
                          {candidate.limit}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="difference-note">
                <span className="eyebrow">How they differ</span>
                <p>
                  N-017 is the best match for temperature and lithology, but its remoteness makes
                  access harder than N-063. N-042 adds permafrost and extreme dryness, with much
                  less useful illumination.
                </p>
              </div>
              <div className="comparison-map">
                <div className="map-lines" />
                {compared.map((candidate, index) => (
                  <button
                    className={`marker marker-${index + 1}`}
                    onClick={() => setDetail(candidate)}
                    key={candidate.code}
                  >
                    <b>{index + 1}</b>
                    <span>{candidate.code}</span>
                  </button>
                ))}
                <em>Selected candidate footprints · diagrammatic map</em>
              </div>
              <div className="tradeoff-grid">
                {compared.map((candidate) => (
                  <article key={candidate.code}>
                    <span className="source">Candidate {candidate.code}</span>
                    <h3>{candidate.place}</h3>
                    <p>{candidate.tradeoff}</p>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      )}

      {detail && (
        <div className="drawer-backdrop" onClick={() => setDetail(null)}>
          <aside className="drawer candidate-drawer" onClick={(event) => event.stopPropagation()}>
            <button className="icon-btn close" onClick={() => setDetail(null)}>
              <Icon name="close" />
            </button>
            <span className="new-label">New candidate · Sample data</span>
            <span className="eyebrow">
              {detail.place} · {detail.country}
            </span>
            <h1>Candidate {detail.code}</h1>
            <p className="coords">{detail.coords}</p>
            <div className="candidate-photo drawer-photo">
              <img src={detail.image} alt={`${detail.place} terrain`} loading="lazy" />
              <em>{detail.place}</em>
            </div>
            <p className="drawer-why">{detail.why}</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Characteristic</th>
                    <th>Value</th>
                    <th>Compared</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {compareRows.map(([name, , asked], index) => (
                    <tr key={name}>
                      <th>{name}</th>
                      <td>
                        <b>{detail.values[index][0]}</b>
                      </td>
                      <td>
                        <span className={`fit ${detail.values[index][1]}`} />
                        {asked}
                      </td>
                      <td>
                        <span className="source">{detail.values[index][2]}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <OperationsSection
              gridId={(detail as LiveCandidate).gridId}
              targetId={(detail as LiveCandidate).targetId || targetId}
            />
            <div className="drawer-limit">
              <h3>Limits</h3>
              <p>{detail.limit}</p>
            </div>
            <div className="end-actions">
              <Button kind="secondary" onClick={() => viewOnMap(detail)}>
                Inspect on satellite map
              </Button>
              <Button
                onClick={() => {
                  setDetail(null);
                  ask();
                }}
              >
                Ask the AI Assistant <Icon name="arrow" />
              </Button>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}

function AllAnalogs() {
  const [filter, setFilter] = useState("All");
  const [characteristic, setCharacteristic] = useState("Any characteristic");
  const [open, setOpen] = useState<(typeof analogs)[0] | null>(null);
  const [compare, setCompare] = useState<string[]>([]);
  let visible = filter === "All" ? analogs : analogs.filter((a) => a.type.includes(filter));
  if (characteristic === "Cold terrain") visible = visible.filter((a) => a.temp.includes("−"));
  if (characteristic === "Basaltic")
    visible = visible.filter((a) => a.rain === "Basaltic" || a.new);
  if (characteristic === "New candidate") visible = visible.filter((a) => a.new);
  const openCandidate = open
    ? candidates.find((candidate) => open.name.includes(candidate.code))
    : null;
  return (
    <main className="page collection-page">
      <div className="page-title">
        <div>
          <span className="eyebrow">Shared field index · sample records</span>
          <h1>All analogs</h1>
        </div>
        <p>Known sites and newly found candidates, read through the same set of characteristics.</p>
      </div>
      <div className="filter-bar">
        <div>
          <Icon name="search" />
          <input placeholder="Search by site or location" />
        </div>
        <div className="filter-chips">
          {["All", "Desert", "Volcanic", "Polar", "Impact", "New"].map((f) => (
            <button className={filter === f ? "active" : ""} onClick={() => setFilter(f)} key={f}>
              {f}
            </button>
          ))}
        </div>
        <label className="character-filter">
          <span>Characteristic</span>
          <select value={characteristic} onChange={(e) => setCharacteristic(e.target.value)}>
            <option>Any characteristic</option>
            <option>Cold terrain</option>
            <option>Basaltic</option>
            <option>New candidate</option>
          </select>
        </label>
      </div>
      <div className="analog-grid">
        {visible.length === 0 && (
          <div className="analog-empty">
            <div className="tiny-contours" />
            <span className="eyebrow">No overlapping records</span>
            <h2>Nothing in this part of the notebook yet.</h2>
            <p>Try a broader terrain type or remove the characteristic filter.</p>
            <Button
              kind="secondary"
              onClick={() => {
                setFilter("All");
                setCharacteristic("Any characteristic");
              }}
            >
              Clear filters
            </Button>
          </div>
        )}
        {visible.map((a, i) => (
          <article className="analog-card" key={a.name}>
            <button className="analog-open" onClick={() => setOpen(a)}>
              <div className="analog-image">
                <img src={a.image} alt={`${a.name} field landscape`} />
                {a.new && <span className="new-label">New</span>}
                <b>0{i + 1}</b>
              </div>
              <span className="source">{a.type}</span>
              <h2>{a.name}</h2>
              <p>{a.place}</p>
              <dl>
                <div>
                  <dt>Temperature</dt>
                  <dd>{a.temp}</dd>
                </div>
                <div>
                  <dt>Field note</dt>
                  <dd>{a.rain}</dd>
                </div>
              </dl>
              <span className="card-link">
                Open field record <Icon name="arrow" />
              </span>
            </button>
            <label className="analog-compare">
              <input
                type="checkbox"
                checked={compare.includes(a.name)}
                disabled={compare.length >= 4 && !compare.includes(a.name)}
                onChange={() =>
                  setCompare((current) =>
                    current.includes(a.name)
                      ? current.filter((name) => name !== a.name)
                      : [...current, a.name],
                  )
                }
              />
              <span>Add to compare</span>
              <b>{compare.length}/4</b>
            </label>
          </article>
        ))}
      </div>
      {open && (
        <div className="drawer-backdrop" onClick={() => setOpen(null)}>
          <aside className="drawer" onClick={(e) => e.stopPropagation()}>
            <button className="icon-btn close" onClick={() => setOpen(null)}>
              <Icon name="close" />
            </button>
            <img src={open.image} alt="" />
            <span className="source">{open.type} · sample record</span>
            <h1>{open.name}</h1>
            <p>{open.place}</p>
            {openCandidate ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Characteristic</th>
                      <th>Value</th>
                      <th>Compared</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareRows.map(([name, , asked], index) => (
                      <tr key={name}>
                        <th>{name}</th>
                        <td>
                          <b>{openCandidate.values[index][0]}</b>
                        </td>
                        <td>
                          <span className={`fit ${openCandidate.values[index][1]}`} />
                          {asked}
                        </td>
                        <td>
                          <span className="source">{openCandidate.values[index][2]}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Table />
            )}
            <div className="drawer-limit">
              <h3>Limits</h3>
              <p>
                {openCandidate
                  ? openCandidate.limit
                  : "This record describes terrain and climate only. Operational access, permits and local conditions require field verification."}
              </p>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}

const sources = [
  [
    "Earth",
    "NASA Earthdata Search",
    "Finds Earth-observation collections across NASA archives.",
    ["Temperature", "Vegetation", "Dust", "Lithology"],
  ],
  [
    "Earth",
    "NASA Worldview",
    "Browses and compares daily satellite imagery.",
    ["Vegetation", "Ice", "Dust"],
  ],
  [
    "Moon & Mars",
    "NASA Planetary Data System (PDS)",
    "Archives planetary mission science products.",
    ["Lithology", "Terrain", "Temperature"],
  ],
  [
    "Moon & Mars",
    "LRO · LROC, LOLA, Diviner, LEND, Mini-RF",
    "Maps imagery, elevation, temperature, neutrons and radar.",
    ["Slope", "Illumination", "Ice", "Temperature"],
  ],
  [
    "Moon & Mars",
    "LRO Diviner polar data",
    "Measures lunar surface thermal behavior.",
    ["Temperature", "Polar cold traps"],
  ],
  [
    "Agency partner",
    "CSA RADARSAT Constellation & RADARSAT-1",
    "SAR observations through cloud and darkness.",
    ["Ice", "Roughness", "Moisture"],
  ],
  [
    "Agency partner",
    "ESA Copernicus Data Space & Open Science Catalog",
    "Earth imagery and open research products.",
    ["Vegetation", "Lithology", "Permafrost"],
  ],
  [
    "Agency partner",
    "JAXA G-Portal",
    "Earth-observation data from Japanese missions.",
    ["Temperature", "Vegetation", "Rainfall"],
  ],
];

type LedgerRow = { group: string; name: string; description: string; tags: string[] };

function DataPage() {
  const fallback: LedgerRow[] = sources.map((s) => ({
    group: s[0] as string,
    name: s[1] as string,
    description: s[2] as string,
    tags: s[3] as string[],
  }));
  const [rows, setRows] = useState<LedgerRow[]>(fallback);
  const [layers, setLayers] = useState<any[]>([]);
  const [live, setLive] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const cat = await getLayers();
      if (cancelled || !cat?.sources) return;
      setRows(
        cat.sources.map((s: any) => ({
          group: s.group,
          name: s.name,
          description: s.description,
          tags: s.feeds,
        })),
      );
      setLayers(cat.layers || []);
      setLive(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="page data-page">
      <div className="page-title">
        <div>
          <span className="eyebrow">
            Source ledger · open agency data {live && "· live catalog"}
          </span>
          <h1>Where the measures come from</h1>
        </div>
        <p>Each source has a job. We keep that chain visible so a match can be checked.</p>
      </div>
      <div className="ledger-head">
        <span>Archive / source</span>
        <span>What it provides</span>
        <span>Characteristics fed</span>
      </div>
      {rows.map((r, i) => (
        <article className="source-row" key={r.name + i}>
          <b>{String(i + 1).padStart(2, "0")}</b>
          <div>
            <span className="source">{r.group}</span>
            <h2>{r.name}</h2>
          </div>
          <p>{r.description}</p>
          <div className="tags">
            {r.tags.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </article>
      ))}
      {live && layers.length > 0 && (
        <div className="data-note">
          <strong>Live data layers ({layers.length})</strong>
          <p>
            {layers
              .map(
                (l) =>
                  `${l.id} (${l.tier}${l.proxy_for ? ", proxy" : ""})`,
              )
              .join(" · ")}
          </p>
        </div>
      )}
      <div className="data-note">
        <strong>A note on provenance</strong>
        <p>
          {live
            ? "This catalog is served live from the engine's source registry. Every characteristic links to a source with a licence and an evidence tier; proxy layers can never grant a hard pass."
            : "The source catalog is real; connections and values shown in the interactive search are sample representations until the engine API is connected."}
        </p>
      </div>
    </main>
  );
}

function AddData() {
  const [result, setResult] = useState<any | null>(null);
  if (result)
    return (
      <main className="page success-page">
        <div className="success-mark">{result.status === "received" ? "✓" : "!"}</div>
        <span className="eyebrow">
          Dataset {result.status} {result.ticket_id ? `· ${result.ticket_id}` : ""}
        </span>
        <h1>
          {result.status === "received"
            ? "It’s in the review notebook."
            : "A few fields need attention."}
        </h1>
        <p>{result.message}</p>
        {result.checks && (
          <ul className="margin-note" style={{ listStyle: "none", padding: 0 }}>
            {result.checks.map((c: any) => (
              <li key={c.name}>
                {c.ok ? "✓" : "✗"} {c.note}
              </li>
            ))}
          </ul>
        )}
        <Button onClick={() => setResult(null)}>Add another dataset</Button>
      </main>
    );
  return (
    <main className="page add-page">
      <div className="add-copy">
        <span className="eyebrow">Keep the index growing</span>
        <h1>A useful atlas is never finished.</h1>
        <p>
          When NASA or another space agency publishes or updates a dataset, it should have a place
          here. Once checked, it is treated like every other source: it joins the search, fills
          characteristic gaps and may point to analogs no one has named yet.
        </p>
        <p>
          Send us the record as you found it. A person reviews its coverage, units and provenance
          before it is added.
        </p>
        <div className="margin-note">
          <b>What helps</b>
          <span>
            A stable source link, a clear unit of measure, and a note about geographic coverage.
          </span>
        </div>
      </div>
      <form
        className="dataset-form"
        onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          const payload = {
            name: String(fd.get("name") || ""),
            source_link: String(fd.get("source_link") || ""),
            measures: String(fd.get("measures") || ""),
            characteristics: fd.getAll("characteristics").map(String),
          };
          const res = await submitContribution(payload);
          setResult(
            res ?? {
              status:
                payload.name && payload.source_link.startsWith("http") && payload.measures.length >= 10
                  ? "received"
                  : "rejected",
              ticket_id: "DS-LOCAL",
              message:
                "Recorded locally (engine API offline). A reviewer would check source, units, coverage and licence.",
              checks: [],
            },
          );
        }}
      >
        <div className="form-head">
          <span>Dataset intake</span>
          <b>All fields required</b>
        </div>
        <label>
          Name
          <input name="name" required placeholder="e.g. Global Permafrost Zonation Index" />
        </label>
        <label>
          Source link
          <input name="source_link" required type="url" placeholder="https://…" />
        </label>
        <label>
          What does it measure?
          <textarea
            name="measures"
            required
            placeholder="Describe the measurement and its coverage in a few plain sentences."
          />
        </label>
        <fieldset>
          <legend>Characteristics it feeds</legend>
          <div className="check-grid">
            {[
              "Slope",
              "Temperature",
              "Lithology",
              "Ice / permafrost",
              "Vegetation",
              "Dust",
              "Wind",
              "Other",
            ].map((x) => (
              <label key={x}>
                <input type="checkbox" name="characteristics" value={x} /> <span>{x}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <label className="upload">
          <Icon name="upload" />
          <strong>Attach a sample or documentation</strong>
          <small>CSV, GeoTIFF or PDF · up to 50 MB</small>
          <input type="file" />
        </label>
        <Button type="submit">
          Send for review <Icon name="arrow" />
        </Button>
        <small className="form-note">The record is validated by the engine; files are not stored.</small>
      </form>
    </main>
  );
}

function DesignSystem() {
  return (
    <main className="page system-page">
      <div className="page-title">
        <div>
          <span className="eyebrow">Living reference</span>
          <h1>Design system</h1>
        </div>
        <p>
          A field notebook language: warm paper, direct labels, measured color and sharp
          information.
        </p>
      </div>
      <section>
        <h2>Color</h2>
        <div className="swatches">
          {[
            ["Basalt night", "#14181F"],
            ["Regolith sand", "#D9C9B0"],
            ["Paper", "#F2ECE0"],
            ["Mars rust", "#B5532F"],
            ["Glacier", "#7FB7C9"],
            ["Lichen", "#6B7A4B"],
          ].map(([n, c]) => (
            <div style={{ "--swatch": c } as React.CSSProperties} key={n}>
              <i />
              <b>{n}</b>
              <code>{c}</code>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Typography</h2>
        <div className="type-spec">
          <h1>Terrain tells a story.</h1>
          <p>Humane text supports long field notes and careful decisions.</p>
          <code>23.4618° S / AC–27 / 4,230 M</code>
        </div>
      </section>
      <section>
        <h2>Controls & states</h2>
        <div className="component-row">
          <Button>Primary action</Button>
          <Button kind="secondary">Secondary</Button>
          <Button disabled>Disabled</Button>
          <span className="source">Source label</span>
          <span className="new-label">New</span>
        </div>
        <div className="state-grid">
          {[
            "Default",
            "Hover",
            "Active",
            "Focus",
            "Disabled",
            "Loading",
            "Empty",
            "Error",
            "Success",
          ].map((x, i) => (
            <div className={`state s${i}`} key={x}>
              <i />
              {x}
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Spacing & radius</h2>
        <p className="muted">
          4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 &nbsp; / &nbsp; Radius: 4—6 px
        </p>
      </section>
    </main>
  );
}

function App() {
  useCardTilt();
  const [page, setPage] = useState<Page>("landing");
  const [panelOpen, setPanelOpen] = useState(true);
  const [searchVersion, setSearchVersion] = useState(0);
  const [searchStartStep, setSearchStartStep] = useState(1);
  const [resultChoices, setResultChoices] = useState<Record<number, string>>({
    1: "Volcanic",
    2: "Mars",
    3: "Rover traverse",
  });
  const [liveCandidates, setLiveCandidates] = useState<LiveCandidate[] | null>(null);
  const go = (p: Page) => {
    if (p === "find") {
      setSearchStartStep(1);
      setSearchVersion((version) => version + 1);
      setLiveCandidates(null);
    }
    setPage(p);
    window.scrollTo(0, 0);
  };
  const body = useMemo(() => {
    if (page === "landing")
      return (
        <Landing
          start={() => {
            setPanelOpen(window.innerWidth >= 700);
            go("find");
          }}
        />
      );
    if (page === "find")
      return (
        <SearchFlow
          key={searchVersion}
          initialStep={searchStartStep}
          initialChoices={resultChoices}
          finish={async (choices, filters) => {
            setResultChoices(choices);
            const live = await discoverCandidates(choices[2], choices[3], filters);
            setLiveCandidates(live);
            go("result");
          }}
        />
      );
    if (page === "result")
      return (
        <Result
          restart={() => go("find")}
          choices={resultChoices}
          liveCandidates={liveCandidates}
          change={() => {
            setSearchStartStep(4);
            setSearchVersion((version) => version + 1);
            setPage("find");
            window.scrollTo(0, 0);
          }}
          ask={() => {
            setPanelOpen(true);
            if (innerWidth < 700) go("assistant");
          }}
        />
      );
    if (page === "analogs") return <AllAnalogs />;
    if (page === "data") return <DataPage />;
    if (page === "add") return <AddData />;
    if (page === "assistant")
      return (
        <main className="page assistant-page">
          <Assistant full />
        </main>
      );
    return <DesignSystem />;
  }, [page, searchVersion, searchStartStep, resultChoices, liveCandidates]);
  if (page === "landing")
    return (
      <>
        <CursorGlow />
        {body}
      </>
    );
  return (
    <div className={`app-shell ${panelOpen && page !== "assistant" ? "with-panel" : ""}`}>
      <CursorGlow />
      <Nav page={page} go={go} />
      <div className="content">{body}</div>
      {page !== "assistant" && panelOpen && (
        <div className="side-assistant">
          <Assistant onClose={() => setPanelOpen(false)} />
        </div>
      )}
      {page !== "assistant" && (
        <button className="mobile-assistant" onClick={() => setPanelOpen(!panelOpen)}>
          <Icon name="chat" />
          <span>AI Assistant</span>
        </button>
      )}
    </div>
  );
}

export default App;
