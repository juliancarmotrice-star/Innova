"""
ECOCLASIFICA — Reglas de clasificación de residuos (código determinista, sin IA).

La visión identifica QUÉ es el residuo (material y estado). Esta capa decide
A QUÉ CONTENEDOR va. Así las reglas son testeables y fáciles de ajustar a los
contenedores reales de la universidad sin tocar el prompt.

Código de colores por defecto: Resolución 2184 de 2019 (Colombia).
Si la universidad usa otro esquema, edita CONTENEDORES y decidir().
"""

CONTENEDORES = {
    "blanco": {
        "emoji": "⚪",
        "nombre": "Blanco · Aprovechables",
        "acepta": "plástico, vidrio, metal, papel y cartón limpios y secos",
    },
    "verde": {
        "emoji": "🟢",
        "nombre": "Verde · Orgánicos",
        "acepta": "restos de comida, cáscaras, residuos de jardín",
    },
    "negro": {
        "emoji": "⚫",
        "nombre": "Negro · No aprovechables",
        "acepta": "papel sucio o grasoso, servilletas, icopor, envolturas metalizadas, colillas",
    },
    "especial": {
        "emoji": "🔴",
        "nombre": "Punto especial (NO va en canecas)",
        "acepta": "pilas, bombillos, electrónicos, medicamentos, tóner",
    },
}

MATERIALES = [
    "plastico", "vidrio", "metal", "papel", "carton", "tetrapak",
    "organico", "ordinario", "peligroso", "desconocido",
]
ESTADOS = ["limpio", "sucio", "con_liquido"]

_RECIPIENTES = {"plastico", "vidrio", "metal", "tetrapak"}
_PAPELES = {"papel", "carton"}


def decidir(material: str, estado: str = "limpio") -> dict:
    """
    Devuelve {"contenedor": clave|None, "pasos": [str], "motivo": str}.
    `pasos` son las acciones previas (vaciar, enjuagar, aplastar...).
    """
    material = (material or "desconocido").lower()
    estado = (estado or "limpio").lower()

    if material not in MATERIALES or material == "desconocido":
        return {"contenedor": None, "pasos": [], "motivo": "No pude identificar el material."}

    if material == "peligroso":
        return {
            "contenedor": "especial",
            "pasos": ["No lo tires en una caneca: llévalo al punto de recolección especial."],
            "motivo": "Residuo peligroso o electrónico.",
        }

    if material == "organico":
        return {"contenedor": "verde", "pasos": [], "motivo": "Residuo orgánico."}

    if material == "ordinario":
        return {"contenedor": "negro", "pasos": [], "motivo": "No es aprovechable."}

    if material in _PAPELES:
        if estado == "limpio":
            return {"contenedor": "blanco", "pasos": [], "motivo": "Papel/cartón limpio y seco."}
        return {
            "contenedor": "negro",
            "pasos": [],
            "motivo": "Papel/cartón sucio o mojado ya no se recicla.",
        }

    if material in _RECIPIENTES:
        pasos = []
        if estado == "con_liquido":
            pasos.append("Vacíalo por completo (en un lavamanos, no en la caneca).")
        elif estado == "sucio":
            pasos.append("Enjuágalo rápido para quitarle los restos.")
        if material == "metal" or material == "plastico":
            pasos.append("Aplástalo si puedes para ahorrar espacio.")
        motivo = "Material aprovechable."
        if estado != "limpio":
            motivo += " Si no puedes limpiarlo, va al negro."
        return {"contenedor": "blanco", "pasos": pasos, "motivo": motivo}

    return {"contenedor": None, "pasos": [], "motivo": "No pude identificar el material."}


def formatear_item(nombre: str, material: str, estado: str, cantidad: int = 1) -> str:
    """Texto corto para una línea de respuesta (HTML de Telegram)."""
    d = decidir(material, estado)
    cant = f"{cantidad}× " if cantidad and cantidad > 1 else ""
    if not d["contenedor"]:
        return f"❓ {cant}<b>{nombre}</b> — no estoy seguro, ¿puedes mandar otra foto más cerca?"
    c = CONTENEDORES[d["contenedor"]]
    linea = f"{c['emoji']} {cant}<b>{nombre}</b> → <b>{c['nombre']}</b>"
    for p in d["pasos"]:
        linea += f"\n    • {p}"
    return linea
