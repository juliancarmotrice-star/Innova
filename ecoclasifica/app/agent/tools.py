"""
ECOCLASIFICA — Herramientas del agente (pocas y bien definidas).
"""

from app.services.residuos import ESTADOS, MATERIALES

TOOLS = [
    {
        "name": "consultar_contenedor",
        "description": (
            "Dice en qué contenedor va un residuo según su material y estado, "
            "con los pasos previos (vaciar, enjuagar). Úsala SIEMPRE antes de responder dónde botar algo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "material": {"type": "string", "enum": MATERIALES},
                "estado": {"type": "string", "enum": ESTADOS},
            },
            "required": ["material"],
        },
    },
    {
        "name": "estadisticas_campus",
        "description": (
            "Estadísticas de uso: fotos clasificadas, residuos por contenedor, "
            "los más frecuentes y precisión percibida. Solo para personal autorizado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"dias": {"type": "integer", "description": "Ventana en días (por defecto 30)."}},
        },
    },
]
