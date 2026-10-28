"""
ECOCLASIFICA — Pipeline foto → residuos → contenedor sugerido.
"""

from app.config import settings
from app.db import store
from app.services.residuos import decidir, formatear_item
from app.services.vision import identificar_residuos


def clasificar_foto(image_bytes: bytes, chat_id="anon", ubicacion: str = "") -> dict:
    """
    Retorna:
      {
        "repetir_foto": bool,       # confianza baja o nada identificable
        "items": [{nombre, material, estado, cantidad, contenedor, pasos}],
        "confianza": float,
        "observaciones": str,
        "foto_id": int | None,
        "mensaje": str              # HTML listo para Telegram
      }
    """
    vis = identificar_residuos(image_bytes)
    items = []
    for it in vis["items"]:
        d = decidir(it.get("material"), it.get("estado"))
        items.append({
            "nombre": it.get("nombre", "residuo"),
            "material": it.get("material", "desconocido"),
            "estado": it.get("estado", "limpio"),
            "cantidad": it.get("cantidad", 1),
            "contenedor": d["contenedor"],
            "pasos": d["pasos"],
        })

    resultado = {
        "items": items,
        "confianza": vis["confianza"],
        "observaciones": vis["observaciones"],
        "foto_id": None,
    }

    if not items:
        resultado.update(
            repetir_foto=True,
            mensaje="🤔 No veo ningún residuo en la foto. Acércate y toma otra con el objeto bien visible.",
        )
        return resultado

    if vis["confianza"] < settings.umbral_confianza or all(i["contenedor"] is None for i in items):
        resultado.update(
            repetir_foto=True,
            mensaje="🔍 No estoy seguro de lo que veo. ¿Puedes tomar otra foto más cerca y con buena luz?"
                    + (f"\n<i>{vis['observaciones']}</i>" if vis["observaciones"] else ""),
        )
        return resultado

    resultado["foto_id"] = store.guardar_foto(chat_id, ubicacion, vis["confianza"], items)
    lineas = [formatear_item(i["nombre"], i["material"], i["estado"], i["cantidad"]) for i in items]
    msg = "♻️ <b>¿Dónde lo boto?</b>\n\n" + "\n".join(lineas)
    if vis["observaciones"]:
        msg += f"\n\n<i>{vis['observaciones']}</i>"
    resultado.update(repetir_foto=False, mensaje=msg)
    return resultado
