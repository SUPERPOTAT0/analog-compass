import { useEffect, useRef, useState } from "react";

// A gold glow that follows the cursor (desktop only).
export function CursorGlow() {
  const [pos, setPos] = useState({ x: -500, y: -500 });
  const [touch, setTouch] = useState(false);
  useEffect(() => {
    setTouch(window.matchMedia("(pointer: coarse)").matches);
    const on = (e: MouseEvent) => setPos({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", on);
    return () => window.removeEventListener("mousemove", on);
  }, []);
  if (touch) return null;
  return (
    <div
      className="cursor-glow"
      style={{
        left: pos.x,
        top: pos.y,
        background: "radial-gradient(circle, rgba(242,181,68,0.10) 0%, rgba(242,181,68,0) 60%)",
      }}
    />
  );
}

// Global 3D tilt: delegated so new cards (results, analogs) get it automatically.
const TILT_SELECTOR = ".candidate-card, .analog-card, .select-card.image-card, .planet, .source-row";

export function useCardTilt() {
  const current = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (window.matchMedia("(pointer: coarse)").matches) return;
    const reset = (el: HTMLElement) => {
      el.style.setProperty("--rx", "0deg");
      el.style.setProperty("--ry", "0deg");
      el.style.setProperty("--gx", "50%");
      el.style.setProperty("--gy", "50%");
      el.style.setProperty("--tz", "0px");
    };
    const onMove = (e: MouseEvent) => {
      const el = (e.target as HTMLElement)?.closest?.(TILT_SELECTOR) as HTMLElement | null;
      if (el !== current.current && current.current) reset(current.current);
      current.current = el;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width;
      const py = (e.clientY - r.top) / r.height;
      el.style.setProperty("--ry", `${(px - 0.5) * 9}deg`);
      el.style.setProperty("--rx", `${(py - 0.5) * -8}deg`);
      el.style.setProperty("--gx", `${px * 100}%`);
      el.style.setProperty("--gy", `${py * 100}%`);
      el.style.setProperty("--tz", "6px");
    };
    const onLeave = () => {
      if (current.current) reset(current.current);
      current.current = null;
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseleave", onLeave);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
    };
  }, []);
}
