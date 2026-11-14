"""Agent runtime: a streaming, manual tool-use loop (docs/08_AI_AGENT.md §4).

Streams Server-Sent Events: `text` deltas, `tool` activity, and a final `done`. Uses
the official Anthropic SDK with claude-opus-4-8 + adaptive thinking. Read-only tools.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from analog_compass.agent import tools
from analog_compass.agent.prompts import build_system_prompt
from analog_compass.engine.text import contains_banned
from analog_compass.settings import get_settings

DEFAULT_MODEL = "claude-opus-4-8"


async def stream_chat(messages: list[dict[str, Any]]) -> AsyncIterator[dict[str, str]]:
    settings = get_settings()
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = settings.analog_agent_model or DEFAULT_MODEL
    system = [{"type": "text", "text": build_system_prompt(),
               "cache_control": {"type": "ephemeral"}}]

    convo: list[dict[str, Any]] = list(messages)
    max_iters = settings.analog_agent_max_tool_iters

    try:
        for _ in range(max_iters):
            assembled_text: list[str] = []
            async with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system,
                tools=tools.TOOL_SPECS,
                thinking={"type": "adaptive"},
                messages=convo,
            ) as stream:
                async for text in stream.text_stream:
                    assembled_text.append(text)
                    yield {"event": "text", "data": text}
                final = await stream.get_final_message()

            # Guardrail: flag banned phrasing (does not alter streamed text, but logs).
            banned = contains_banned("".join(assembled_text))
            if banned:
                yield {"event": "warn", "data": json.dumps({"banned": banned})}

            convo.append({"role": "assistant", "content": final.content})
            tool_uses = [b for b in final.content if getattr(b, "type", None) == "tool_use"]
            if not tool_uses:
                yield {"event": "done", "data": "{}"}
                return

            results = []
            for tu in tool_uses:
                yield {"event": "tool", "data": json.dumps({"name": tu.name, "input": tu.input})}
                try:
                    out = tools.dispatch(tu.name, tu.input)  # type: ignore[arg-type]
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out})
                except Exception as exc:  # surface tool errors to the model, do not crash
                    results.append({"type": "tool_result", "tool_use_id": tu.id,
                                    "content": f"Error: {exc}", "is_error": True})
            convo.append({"role": "user", "content": results})

        yield {"event": "done", "data": json.dumps({"stopped": "max_tool_iterations"})}
    except Exception as exc:  # pragma: no cover - network/runtime guard
        yield {"event": "error", "data": json.dumps({"message": str(exc)})}
