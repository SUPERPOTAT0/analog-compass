"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";

interface Msg { role: "user" | "assistant"; content: string }

export function ChatView() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [tools, setTools] = useState<string[]>([]);

  async function send() {
    if (!input.trim() || streaming) return;
    const next: Msg[] = [...messages, { role: "user", content: input }];
    setMessages(next);
    setInput("");
    setStreaming(true);
    setTools([]);
    let assistant = "";
    try {
      const res = await fetch(`${API_URL}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      if (res.status === 503) {
        setMessages([...next, { role: "assistant", content: "⚠️ The agent isn't configured on the server (ANTHROPIC_API_KEY missing). Compare, Discover and Suitability still work." }]);
        setStreaming(false);
        return;
      }
      if (!res.body) throw new Error("no stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      setMessages([...next, { role: "assistant", content: "" }]);
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";
        for (const chunk of chunks) {
          const ev = /event:\s*(.*)/.exec(chunk)?.[1]?.trim();
          const dataLine = /data:\s*([\s\S]*)/.exec(chunk)?.[1] ?? "";
          if (ev === "text") {
            assistant += dataLine;
            setMessages([...next, { role: "assistant", content: assistant }]);
          } else if (ev === "tool") {
            try { setTools((t) => [...t, JSON.parse(dataLine).name]); } catch {}
          }
        }
      }
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${String(e)}` }]);
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-auto pr-1">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            Ask the Geologist-Analysis agent, e.g. <em>&ldquo;Where could I trial a cryo-drill for a
            Mars mid-latitude mission, and why?&rdquo;</em> Every answer is grounded in the engine.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div className={`inline-block max-w-[90%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-indigo-500/30" : "bg-slate-700/40"}`}>
              {m.content || (streaming ? "…" : "")}
            </div>
          </div>
        ))}
        {tools.length > 0 && (
          <div className="text-xs text-slate-500">ran: {tools.join(", ")}</div>
        )}
      </div>
      <div className="mt-2 flex gap-2">
        <input
          className="flex-1 rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about analogues, tests, or sites…"
        />
        <button
          onClick={send}
          disabled={streaming}
          className="rounded bg-indigo-500 px-4 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {streaming ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
