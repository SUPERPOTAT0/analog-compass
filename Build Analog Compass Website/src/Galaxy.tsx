import { useEffect, useRef } from "react";

// Procedural Hubble-style spiral galaxy on a twinkling starfield (canvas 2D).
// Palette: gold core, nebula-blue arms, dust-rose star-forming regions on Void.
export default function Galaxy() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouse = useRef({ x: 0, y: 0, tx: 0, ty: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const isTouch = window.matchMedia("(pointer: coarse)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const mobile = window.innerWidth < 768;
    const N = mobile ? 2600 : 6000;
    const ARMS = 2;
    const B = 0.42;

    let w = 0, h = 0, cx = 0, cy = 0;
    type P = { r: number; theta: number; omega: number; size: number; col: number[]; glow: boolean; dust: boolean; a: number };
    const parts: P[] = new Array(N);
    const maxR = () => Math.min(w, h) * (mobile ? 0.44 : 0.4);

    function build() {
      const R = maxR();
      for (let i = 0; i < N; i++) {
        const rr = Math.pow(Math.random(), 0.6);
        const r = rr * R;
        const base = (i % ARMS) * ((Math.PI * 2) / ARMS);
        const theta = base + B * Math.log(r + 20) + (Math.random() - 0.5) * (0.5 - 0.35 * rr);
        const t = rr;
        const pink = Math.random() < 0.035 && t > 0.35;
        const dust = Math.random() < 0.14 && t > 0.2 && t < 0.85;
        let col: number[];
        if (pink) col = [232, 120, 158];
        else if (t < 0.18) col = [255, 244, 194];
        else if (t < 0.45) col = [242, 181, 68];
        else if (t < 0.7) col = [150, 160, 190];
        else col = [110, 134, 184];
        if (dust) col = [20, 16, 26];
        parts[i] = {
          r, theta,
          omega: (mobile ? 0.00016 : 0.00013) * (1 / (0.4 + rr)),
          size: t < 0.2 ? 1.6 : Math.random() < 0.1 ? 1.5 : 0.8,
          col, glow: t < 0.22 || pink, dust, a: dust ? 0.5 : 0.55 + 0.45 * (1 - t),
        };
      }
    }

    type S = { x: number; y: number; layer: number; r: number; tw: number; tws: number; c: number[] };
    let stars: S[] = [];
    let hero: { x: number; y: number; ph: number }[] = [];
    function buildStars() {
      const count = mobile ? 170 : 320;
      stars = new Array(count).fill(0).map(() => ({
        x: Math.random() * w, y: Math.random() * h, layer: Math.floor(Math.random() * 3),
        r: Math.random() * 1.3 + 0.3, tw: Math.random() * Math.PI * 2, tws: 0.5 + Math.random() * 2,
        c: Math.random() < 0.6 ? [255, 244, 194] : Math.random() < 0.5 ? [255, 233, 168] : [255, 255, 255],
      }));
      hero = new Array(mobile ? 3 : 5).fill(0).map(() => ({
        x: Math.random() * w, y: Math.random() * h * 0.7, ph: Math.random() * Math.PI * 2,
      }));
    }

    let shooting: { x: number; y: number; vx: number; vy: number; life: number }[] = [];
    let lastShoot = 0;

    function resize() {
      w = canvas!.clientWidth; h = canvas!.clientHeight;
      canvas!.width = w * dpr; canvas!.height = h * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = w / 2; cy = h * 0.48;
      build(); buildStars();
    }

    let raf = 0, t0 = performance.now();
    const squash = 0.46;

    function frame(now: number) {
      const dt = now - t0; t0 = now;
      mouse.current.tx += (mouse.current.x - mouse.current.tx) * 0.05;
      mouse.current.ty += (mouse.current.y - mouse.current.ty) * 0.05;
      const parX = isTouch ? 0 : mouse.current.tx * 22;
      const parY = isTouch ? 0 : mouse.current.ty * 14;
      const tiltX = isTouch ? 0 : mouse.current.tx * 0.12;

      ctx!.clearRect(0, 0, w, h);
      ctx!.globalAlpha = 1;

      for (const s of stars) {
        const tw = reduced ? 0.8 : 0.55 + 0.45 * Math.sin(now * 0.001 * s.tws + s.tw);
        ctx!.globalAlpha = tw * 0.9;
        ctx!.fillStyle = `rgb(${s.c[0]},${s.c[1]},${s.c[2]})`;
        ctx!.beginPath();
        ctx!.arc(s.x + parX * (0.2 + s.layer * 0.25), s.y + parY * (0.2 + s.layer * 0.25), s.r * (1 + s.layer * 0.4), 0, 7);
        ctx!.fill();
      }

      ctx!.globalCompositeOperation = "lighter";
      for (const hs of hero) {
        const p = reduced ? 0.7 : 0.5 + 0.5 * Math.sin(now * 0.0012 + hs.ph);
        const x = hs.x + parX * 0.5, y = hs.y + parY * 0.5;
        const g = ctx!.createRadialGradient(x, y, 0, x, y, 26);
        g.addColorStop(0, `rgba(255,244,194,${0.9 * p})`);
        g.addColorStop(1, "rgba(255,244,194,0)");
        ctx!.fillStyle = g;
        ctx!.fillRect(x - 26, y - 26, 52, 52);
        ctx!.strokeStyle = `rgba(255,255,255,${0.5 * p})`;
        ctx!.lineWidth = 1;
        ctx!.beginPath();
        ctx!.moveTo(x - 16 * p, y); ctx!.lineTo(x + 16 * p, y);
        ctx!.moveTo(x, y - 16 * p); ctx!.lineTo(x, y + 16 * p);
        ctx!.stroke();
      }

      const haze = ctx!.createRadialGradient(cx + parX, cy + parY, 0, cx + parX, cy + parY, maxR() * 1.3);
      haze.addColorStop(0, "rgba(110,134,184,0.12)");
      haze.addColorStop(1, "rgba(110,134,184,0)");
      ctx!.fillStyle = haze;
      ctx!.fillRect(0, 0, w, h);

      for (const p of parts) {
        if (!reduced) p.theta += p.omega * dt;
        const x0 = Math.cos(p.theta) * p.r;
        const y0 = Math.sin(p.theta) * p.r * squash;
        const x = cx + x0 + parX + y0 * tiltX * 0.01;
        const y = cy + y0 + parY;
        ctx!.globalCompositeOperation = p.dust ? "source-over" : "lighter";
        ctx!.globalAlpha = p.a * (p.dust ? 0.7 : 1);
        if (p.glow) {
          const gr = ctx!.createRadialGradient(x, y, 0, x, y, p.size * 3.2);
          gr.addColorStop(0, `rgba(${p.col[0]},${p.col[1]},${p.col[2]},${p.a})`);
          gr.addColorStop(1, "rgba(0,0,0,0)");
          ctx!.fillStyle = gr;
          ctx!.fillRect(x - p.size * 3.2, y - p.size * 3.2, p.size * 6.4, p.size * 6.4);
        } else {
          ctx!.fillStyle = `rgb(${p.col[0]},${p.col[1]},${p.col[2]})`;
          ctx!.fillRect(x, y, p.size, p.size);
        }
      }

      ctx!.globalCompositeOperation = "lighter";
      const core = ctx!.createRadialGradient(cx + parX, cy + parY, 0, cx + parX, cy + parY, maxR() * 0.33);
      core.addColorStop(0, "rgba(255,248,214,0.55)");
      core.addColorStop(0.4, "rgba(242,181,68,0.22)");
      core.addColorStop(1, "rgba(242,181,68,0)");
      ctx!.fillStyle = core;
      ctx!.fillRect(0, 0, w, h);

      if (!reduced) {
        if (now - lastShoot > 2600 + Math.random() * 2600) {
          lastShoot = now;
          shooting.push({ x: Math.random() * w, y: Math.random() * h * 0.4, vx: (Math.random() - 0.3) * 9, vy: 3 + Math.random() * 4, life: 1 });
        }
        shooting = shooting.filter((s) => s.life > 0);
        for (const s of shooting) {
          s.x += s.vx; s.y += s.vy; s.life -= 0.018;
          ctx!.globalAlpha = Math.max(0, s.life);
          const grad = ctx!.createLinearGradient(s.x, s.y, s.x - s.vx * 6, s.y - s.vy * 6);
          grad.addColorStop(0, "rgba(255,244,194,0.9)");
          grad.addColorStop(1, "rgba(255,244,194,0)");
          ctx!.strokeStyle = grad;
          ctx!.lineWidth = 1.6;
          ctx!.beginPath();
          ctx!.moveTo(s.x, s.y); ctx!.lineTo(s.x - s.vx * 6, s.y - s.vy * 6);
          ctx!.stroke();
        }
      }

      ctx!.globalCompositeOperation = "source-over";
      ctx!.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener("resize", resize);
    const onMove = (e: MouseEvent) => {
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    if (!isTouch) window.addEventListener("mousemove", onMove);
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return <canvas ref={canvasRef} className="galaxy-canvas" aria-hidden="true" />;
}
