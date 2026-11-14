# 08 — The Geologist-Analysis AI Agent

> The agent is an **integrated component**, not the whole product. Its job: let a user ask natural-language questions about analogues and get **meaningful, data-driven** answers — recommend tests for a site, explain why a site suits an operation, compare sites with evidence. It must never invent science.

## 1. Design stance: grounded, not generative

The agent does **not** answer from the model's own knowledge. It answers by **calling the deterministic engine, discovery, suitability and KB as tools** and composing a reply strictly from what those tools return. This makes the agent's claims:

- **Reproducible** — the same question over the same data gives the same numbers (the engine is deterministic).
- **Cited** — every characteristic value carries a `source_id` and evidence tier; the agent surfaces them.
- **Honest** — the agent inherits the engine's honest-limit notes and the KB's grades, and the banned-words list.

This directly satisfies the project's first rule — *never invent data/science* — by *architecture*, not by asking the model nicely.

## 2. Model & SDK

- **Anthropic Claude** via the official SDK, using **tool use** (function calling) in an agentic loop. Default model: a current Claude model (configurable via `ANALOG_AGENT_MODEL`); see the `claude-api` reference for current model ids and parameters — do **not** hard-code a stale id.
- Streaming responses to the UI over SSE.
- Prompt caching on the (large, static) system prompt + KB summary to cut latency/cost.
- Key from `ANTHROPIC_API_KEY` (env only). On Vercel, the AI Gateway may front the provider for observability/fallback (see [[11_DEPLOYMENT]]).

## 3. Tools (read-only, engine-backed)

| Tool | Input | Returns | Backed by |
|------|-------|---------|-----------|
| `list_targets` | — | targets + labels + bodies | `kb/targets` |
| `list_tests` | — | tests + rationale + domains | `kb/tests` |
| `compare_sites` | `target_id, test_id, site_ids?` | per-site verdicts, evidence, honest limits, `run_id` | `engine` |
| `site_suitability` | `site_id` | supported/borderline/unsupported tests + reasons | `suitability` |
| `discover` | `target_id, test_id, region?, k?` | new candidates + provenance + verdicts | `discovery` |
| `explain_verdict` | `run_id, site_id` | per-characteristic contributions, gate pass rates, limiting characteristic | `engine` |
| `target_facts` | `target_id` | cited facts with grades | `kb/targets` |
| `characteristic_info` | `characteristic_id` | kind, unit, source, tier, what it proxies | `kb` |

All tools are **read-only**. The agent cannot write, deploy, or call the network outside these tools. Tool outputs are the only external facts allowed into the answer.

## 4. The agent loop (`agent/runtime.py`)

```
system = system_prompt + kb_summary (cached)
messages = [user_turn]
loop:
    resp = claude.messages(model, system, tools, messages, stream=True)
    stream text deltas to client
    if resp.stop_reason == "tool_use":
        for each tool_use:
            result = dispatch(tool_name, tool_input)   # calls engine/discovery/kb
            append tool_result to messages
        continue
    else: done
```

A hard cap on tool-iterations and a token budget prevent runaway loops. Every tool call + `run_id` is logged for traceability.

## 5. System prompt (shape)

- **Role:** "You are a field-geology analysis assistant for planetary analogue site selection."
- **Grounding rule:** "Only state facts returned by your tools or present in the knowledge base with a grade. If a tool has not given you a number, say you need to run it. Never estimate a characteristic value yourself."
- **Honesty rule:** surface evidence tiers and honest-limit notes; distinguish `pass` from `borderline`; flag proxy-based passes as provisional.
- **Banned words:** inherit the engine list ([[03_ENGINE_SPEC]] §10) — no *perfect*, *identical to Mars*, *guaranteed*, etc.
- **Style:** concise, scientific, cite `source_id` and `run_id`; offer the next useful tool action.

## 6. Example interactions

- *"Where on Earth could I trial a cryo-drill for a Mars mid-latitude mission?"* → agent calls `discover(mars_mid_latitude, cryo_drill_trial)`, returns new candidates with permafrost-proxy caveats and provenance, and a map link.
- *"Why is Site C only borderline?"* → `explain_verdict(run_id, C)` → "Its slope gate is met in 55% of draws — the uncertainty interval straddles the 15° gate; permafrost is proxy-only, so the pass is provisional."
- *"Compare Rio Tinto and Atacama for a life-detection assay."* → `compare_sites(mars_mid_latitude, life_detection_assay, [rio_tinto, atacama])` → evidence-based ranking + where each breaks down.
- *"What tests can I run at this newly found site?"* → `site_suitability(site_id)` → supported/borderline/unsupported with the limiting characteristic for each.

## 7. Guardrails & evaluation

- **No ungrounded numbers:** a post-generation check scans the answer for numeric characteristic claims not present in any tool result for the session and flags/removes them.
- **Banned-words filter** on output.
- **Citations required:** any site/target claim must carry a `source_id`/`run_id` from a tool result.
- **Eval set:** a fixed battery of questions with expected tool-call sequences and expected honest-limit mentions, run in CI against recorded tool stubs (deterministic engine makes this stable).
- **Refusal behaviour:** for out-of-scope domains (subsurface, Earth processes — see [[13_CHALLENGE_ALIGNMENT]]) the agent states the limit rather than guessing.

## 8. Competitive edge

Most "AI + map" entries bolt a chatbot onto a dataset and let it hallucinate. Here the agent is **physically unable** to fabricate a characteristic value — it must go through the deterministic engine, and it reports provenance and honest limits by default. That is a trustworthy scientific assistant, which is exactly what a mission planner needs.

See next: [[09_WORK_PLAN]].
