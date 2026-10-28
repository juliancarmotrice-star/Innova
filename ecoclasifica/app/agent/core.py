"""
ECOCLASIFICA — Bucle del agente (Claude + tool use).
"""

import json

import anthropic

from app.agent.handlers import dispatch
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOLS
from app.config import settings


def get_client():
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada. Agrégala en .env.")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def run_agent(messages: list, es_admin: bool = False, max_turns: int = 6) -> dict:
    """Retorna {"response": str, "tools_used": [...], "messages": [...]}."""
    client = get_client()
    tools_used = []

    for _ in range(max_turns):
        resp = client.messages.create(
            model=settings.modelo,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"response": text, "tools_used": tools_used, "messages": messages}

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            try:
                out = dispatch(block.name, block.input, es_admin=es_admin)
            except Exception as e:
                out = {"error": str(e)}
            tools_used.append({"tool": block.name, "input": block.input, "output": out})
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(out, default=str, ensure_ascii=False),
            })
        messages.append({"role": "user", "content": results})

    return {
        "response": "No pude resolverlo. Pregunta de nuevo con más detalle o consulta al equipo de sostenibilidad.",
        "tools_used": tools_used,
        "messages": messages,
    }
