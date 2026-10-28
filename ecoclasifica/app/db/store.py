"""
ECOCLASIFICA — Persistencia (SQLite para el piloto; migrable a Postgres/Supabase).

Se guarda cada foto y sus ítems, más el feedback del estudiante (¿fue correcto?).
El identificador de usuario se guarda como hash: no necesitamos saber quién es,
solo distinguir usuarios para medir participación.
"""

import hashlib
import sqlite3
from contextlib import contextmanager

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creado_en TEXT DEFAULT (datetime('now')),
    usuario TEXT,
    ubicacion TEXT,
    confianza REAL,
    feedback TEXT            -- 'ok' | 'mal' | NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    foto_id INTEGER REFERENCES fotos(id),
    nombre TEXT, material TEXT, estado TEXT, cantidad INTEGER DEFAULT 1,
    contenedor TEXT
);
"""


@contextmanager
def _conn():
    c = sqlite3.connect(settings.db_path)
    c.row_factory = sqlite3.Row
    c.executescript(_SCHEMA)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def hash_usuario(chat_id) -> str:
    return hashlib.sha256(str(chat_id).encode()).hexdigest()[:12]


def guardar_foto(chat_id, ubicacion: str, confianza: float, items: list[dict]) -> int:
    """items: [{nombre, material, estado, cantidad, contenedor}]"""
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO fotos (usuario, ubicacion, confianza) VALUES (?, ?, ?)",
            (hash_usuario(chat_id), ubicacion or None, confianza),
        )
        foto_id = cur.lastrowid
        c.executemany(
            "INSERT INTO items (foto_id, nombre, material, estado, cantidad, contenedor) VALUES (?,?,?,?,?,?)",
            [(foto_id, i["nombre"], i["material"], i["estado"], i.get("cantidad", 1), i.get("contenedor"))
             for i in items],
        )
        return foto_id


def guardar_feedback(foto_id: int, feedback: str) -> None:
    with _conn() as c:
        c.execute("UPDATE fotos SET feedback = ? WHERE id = ?", (feedback, foto_id))


def estadisticas(dias: int = 30) -> dict:
    """Resumen para gerencia/sostenibilidad."""
    filtro = f"-{int(dias)} days"
    with _conn() as c:
        fotos = c.execute(
            "SELECT COUNT(*) n, COUNT(DISTINCT usuario) u, "
            "SUM(feedback='ok') ok, SUM(feedback='mal') mal "
            "FROM fotos WHERE creado_en >= datetime('now', ?)", (filtro,)).fetchone()
        por_cont = c.execute(
            "SELECT i.contenedor, SUM(i.cantidad) n FROM items i JOIN fotos f ON f.id=i.foto_id "
            "WHERE f.creado_en >= datetime('now', ?) GROUP BY i.contenedor ORDER BY n DESC", (filtro,)).fetchall()
        por_mat = c.execute(
            "SELECT i.material, i.estado, SUM(i.cantidad) n FROM items i JOIN fotos f ON f.id=i.foto_id "
            "WHERE f.creado_en >= datetime('now', ?) GROUP BY i.material, i.estado ORDER BY n DESC LIMIT 10",
            (filtro,)).fetchall()
        por_lugar = c.execute(
            "SELECT ubicacion, COUNT(*) n FROM fotos WHERE ubicacion IS NOT NULL "
            "AND creado_en >= datetime('now', ?) GROUP BY ubicacion ORDER BY n DESC LIMIT 5", (filtro,)).fetchall()
    valoradas = (fotos["ok"] or 0) + (fotos["mal"] or 0)
    return {
        "dias": dias,
        "fotos": fotos["n"],
        "usuarios_unicos": fotos["u"],
        "precision_percibida": round((fotos["ok"] or 0) / valoradas, 2) if valoradas else None,
        "por_contenedor": {r["contenedor"] or "sin_clasificar": r["n"] for r in por_cont},
        "residuos_mas_frecuentes": [dict(r) for r in por_mat],
        "ubicaciones_top": [dict(r) for r in por_lugar],
    }
