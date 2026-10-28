"""
ECOCLASIFICA — Implementación de las herramientas del agente.
"""

from app.db import store
from app.services.residuos import CONTENEDORES, decidir


def consultar_contenedor(material: str, estado: str = "limpio") -> dict:
    d = decidir(material, estado)
    if d["contenedor"]:
        d["contenedor_info"] = CONTENEDORES[d["contenedor"]]
    return d


def estadisticas_campus(dias: int = 30) -> dict:
    return store.estadisticas(dias)


_HANDLERS = {
    "consultar_contenedor": consultar_contenedor,
    "estadisticas_campus": estadisticas_campus,
}


def dispatch(name: str, args: dict, es_admin: bool = False) -> dict:
    if name not in _HANDLERS:
        return {"error": f"Herramienta desconocida: {name}"}
    if name == "estadisticas_campus" and not es_admin:
        return {"error": "No autorizado: solo personal de sostenibilidad."}
    return _HANDLERS[name](**args)
