"""
ECOCLASIFICA — Visión: identifica los residuos de una foto con Claude.

El modelo SOLO describe (nombre, material, estado). No decide el contenedor:
eso lo hace app/services/residuos.py. Se fuerza una llamada a herramienta para
obtener JSON siempre válido. Si no hay API key se falla de forma explícita; no
se inventan resultados.
"""

import base64
import logging
from io import BytesIO

from PIL import Image

from app.config import settings
from app.services.residuos import ESTADOS, MATERIALES

logger = logging.getLogger("ecoclasifica.vision")

_TOOL = {
    "name": "reportar_residuos",
    "description": "Reporta los residuos visibles en la foto.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "Un elemento por cada tipo de residuo distinto en la foto.",
                "items": {
                    "type": "object",
                    "properties": {
                        "nombre": {"type": "string", "description": "Ej: lata de gaseosa, vaso de icopor."},
                        "material": {"type": "string", "enum": MATERIALES},
                        "estado": {
                            "type": "string",
                            "enum": ESTADOS,
                            "description": "limpio/seco, sucio (restos de comida o grasa) o con_liquido.",
                        },
                        "cantidad": {"type": "integer", "minimum": 1},
                    },
                    "required": ["nombre", "material", "estado"],
                },
            },
            "confianza": {"type": "number", "minimum": 0, "maximum": 1},
            "observaciones": {"type": "string", "description": "Máx. una frase: dudas, objetos ocultos, foto borrosa."},
        },
        "required": ["items", "confianza"],
    },
}

_PROMPT = (
    "Eres un experto en separación de residuos en un campus universitario. "
    "Identifica cada residuo visible en la foto: qué objeto es, de qué material está hecho "
    "y si está limpio, sucio (restos de comida/grasa) o con líquido. "
    "Si hay varios objetos, lista cada tipo por separado. "
    "Usa material 'desconocido' si no puedes distinguirlo, y baja la confianza si la foto está "
    "borrosa, muy lejos o hay objetos ocultos. Si la foto no contiene residuos, devuelve items vacío."
)


def optimizar_imagen(image_bytes: bytes, max_size: int = 1200) -> tuple[bytes, str]:
    """Reduce el tamaño de la foto para acelerar el análisis y ahorrar tokens."""
    img = Image.open(BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > max_size:
        r = max_size / max(img.size)
        img = img.resize((int(img.width * r), int(img.height * r)), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue(), "image/jpeg"


def identificar_residuos(image_bytes: bytes) -> dict:
    """
    Retorna {"items": [...], "confianza": float, "observaciones": str}.
    Lanza ValueError si falta la API key y RuntimeError si el modelo no responde con la herramienta.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada. Agrégala en .env.")

    import anthropic

    data, mime = optimizar_imagen(image_bytes)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.modelo,
        max_tokens=800,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "reportar_residuos"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": mime,
                    "data": base64.b64encode(data).decode(),
                }},
                {"type": "text", "text": _PROMPT},
            ],
        }],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "reportar_residuos":
            out = dict(block.input)
            out.setdefault("items", [])
            out.setdefault("observaciones", "")
            out["confianza"] = float(out.get("confianza", 0))
            return out
    logger.error("El modelo no devolvió reportar_residuos: %s", resp.content)
    raise RuntimeError("Respuesta de visión inválida.")
