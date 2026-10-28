"""
ECOCLASIFICA — API principal (FastAPI).

- GET  /ping
- POST /api/clasificar        foto → residuos + contenedor (útil para web/kiosko)
- POST /api/agent/chat        pregunta de texto al agente
- GET  /api/stats             estadísticas (requiere header X-Admin-Token)
- POST /api/telegram/webhook  webhook de Telegram (valida el secret token)
"""

import hmac
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import store

app = FastAPI(
    title="ECOCLASIFICA",
    description="Agente que dice en qué contenedor botar cada residuo en el campus",
    version="0.1.0",
)


@app.get("/ping")
def ping():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/clasificar")
async def api_clasificar(file: UploadFile = File(...), ubicacion: str = Form("")):
    from app.services.clasificador import clasificar_foto

    try:
        return clasificar_foto(await file.read(), chat_id="api", ubicacion=ubicacion)
    except ValueError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"No se pudo analizar la foto: {e}"})


@app.post("/api/agent/chat")
async def api_agent_chat(request: Request):
    body = await request.json()
    msg = body.get("message", "").strip()
    if not msg:
        return JSONResponse(status_code=400, content={"error": "Mensaje vacío"})
    try:
        from app.agent.core import run_agent

        r = run_agent([{"role": "user", "content": msg}])  # sin es_admin: no expone estadísticas
        return {"response": r["response"], "tools_used": [t["tool"] for t in r["tools_used"]]}
    except ValueError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})


@app.get("/api/stats")
def api_stats(dias: int = 30, x_admin_token: str = Header("")):
    # Reutiliza el secret del webhook como token admin simple para el piloto.
    esperado = settings.telegram_webhook_secret
    if not esperado or not hmac.compare_digest(x_admin_token, esperado):
        raise HTTPException(status_code=401, detail="No autorizado")
    return store.estadisticas(dias)


@app.post("/api/telegram/webhook")
async def api_telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(""),
):
    from app.telegram.bot import telegram_bot

    if settings.telegram_webhook_secret and not hmac.compare_digest(
        x_telegram_bot_api_secret_token, settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=403, detail="Secret inválido")
    return telegram_bot.process_update(await request.json())
