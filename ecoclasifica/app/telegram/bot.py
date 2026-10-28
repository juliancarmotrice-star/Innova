"""
ECOCLASIFICA — Bot de Telegram.

Flujo principal: el estudiante manda una foto de un residuo (opcional: en el
pie de foto, el lugar, p. ej. "Biblioteca piso 2") y el bot responde en qué
contenedor botarlo, con botones para confirmar si acertó.

Texto libre → agente (preguntas tipo "¿dónde boto una caja de pizza?").
Roles: cualquiera clasifica; solo los IDs en ADMIN_TELEGRAM_IDS ven /stats.
"""

import logging
import time

import httpx

from app.config import settings
from app.db import store

logger = logging.getLogger("ecoclasifica.bot")

AYUDA = (
    "♻️ <b>ECOCLASIFICA</b>\n\n"
    "📸 Mándame una <b>foto</b> del residuo y te digo en qué caneca botarlo.\n"
    "Si quieres, escribe en el pie de foto dónde estás (ej: <i>Biblioteca piso 2</i>).\n\n"
    "💬 También puedes preguntarme: <i>¿dónde boto una lata de atún?</i>\n\n"
    "⚪ Blanco: aprovechables limpios y secos\n"
    "🟢 Verde: orgánicos\n"
    "⚫ Negro: no aprovechables\n"
    "🔴 Pilas, electrónicos y bombillos: punto especial"
)


class TelegramBot:
    def __init__(self, token: str | None = None):
        self.token = token or settings.telegram_bot_token
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.token and len(self.token) > 10)

    def es_admin(self, chat_id) -> bool:
        ids = [a.strip() for a in settings.admin_telegram_ids.split(",") if a.strip()]
        return str(chat_id) in ids

    # ─── Telegram API ───
    def _post(self, method: str, payload: dict) -> bool:
        if not self.is_configured:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado.")
            return False
        try:
            with httpx.Client(timeout=10.0) as c:
                c.post(f"{self.api_url}/{method}", json=payload).raise_for_status()
            return True
        except Exception as e:
            logger.error("Telegram %s falló: %s", method, e)
            return False

    def send_message(self, chat_id, text: str, botones: list | None = None) -> bool:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if botones:
            payload["reply_markup"] = {"inline_keyboard": [botones]}
        return self._post("sendMessage", payload)

    def _descargar_foto(self, file_id: str) -> bytes | None:
        try:
            with httpx.Client(timeout=15.0) as c:
                r = c.get(f"{self.api_url}/getFile", params={"file_id": file_id})
                r.raise_for_status()
                path = r.json()["result"]["file_path"]
                img = c.get(f"https://api.telegram.org/file/bot{self.token}/{path}")
                img.raise_for_status()
                return img.content
        except Exception as e:
            logger.error("No se pudo descargar la foto: %s", e)
            return None

    # ─── Entrada ───
    def process_update(self, update: dict) -> dict:
        if update.get("callback_query"):
            return self._handle_feedback(update["callback_query"])

        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ignored"}

        chat_id = message["chat"]["id"]
        text = (message.get("text") or "").strip()

        if message.get("photo"):
            return self._handle_photo(chat_id, message)
        if text.startswith("/"):
            return self._handle_command(chat_id, text)
        if text:
            return self._handle_text(chat_id, text)
        self.send_message(chat_id, "📸 Mándame una foto del residuo o escríbeme tu pregunta.")
        return {"status": "ok", "action": "empty"}

    # ─── Handlers ───
    def _handle_photo(self, chat_id, message: dict) -> dict:
        from app.services.clasificador import clasificar_foto

        self.send_message(chat_id, "🔎 <i>Mirando tu residuo...</i>")
        img = self._descargar_foto(message["photo"][-1]["file_id"])
        if not img:
            self.send_message(chat_id, "⚠️ No pude descargar la foto. Intenta de nuevo.")
            return {"status": "error", "error": "download"}

        try:
            res = clasificar_foto(img, chat_id=chat_id, ubicacion=(message.get("caption") or "").strip())
        except ValueError as e:  # falta API key
            logger.error(e)
            self.send_message(chat_id, "⚠️ El servicio de análisis no está configurado todavía.")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception("Error clasificando")
            self.send_message(chat_id, "⚠️ Tuve un problema analizando la foto. Intenta de nuevo en un momento.")
            return {"status": "error", "error": str(e)}

        botones = None
        if res["foto_id"]:
            botones = [
                {"text": "✅ Correcto", "callback_data": f"ok:{res['foto_id']}"},
                {"text": "❌ No es así", "callback_data": f"mal:{res['foto_id']}"},
            ]
        self.send_message(chat_id, res["mensaje"], botones)
        return {"status": "ok", "action": "foto", "resultado": res}

    def _handle_feedback(self, cb: dict) -> dict:
        data = cb.get("data", "")
        chat_id = cb["message"]["chat"]["id"]
        try:
            valor, foto_id = data.split(":")
            if valor not in ("ok", "mal"):
                raise ValueError
            store.guardar_feedback(int(foto_id), valor)
        except ValueError:
            return {"status": "ignored"}
        self._post("answerCallbackQuery", {"callback_query_id": cb["id"]})
        self.send_message(
            chat_id,
            "¡Gracias! 🌱" if valor == "ok"
            else "Gracias por avisar, así aprendemos. 🙏 Si quieres, pregúntame por escrito qué era.",
        )
        return {"status": "ok", "action": "feedback", "valor": valor}

    def _handle_command(self, chat_id, text: str) -> dict:
        cmd = text.split()[0].lower().split("@")[0]
        if cmd in ("/start", "/help", "/ayuda"):
            self.send_message(chat_id, AYUDA)
            return {"status": "ok", "action": "help"}
        if cmd == "/stats":
            if not self.es_admin(chat_id):
                self.send_message(chat_id, "🔒 Este comando es solo para el equipo de sostenibilidad.")
                return {"status": "forbidden"}
            s = store.estadisticas(30)
            cont = "\n".join(f"  • {k}: {v}" for k, v in s["por_contenedor"].items()) or "  (sin datos)"
            prec = f"{s['precision_percibida']*100:.0f}%" if s["precision_percibida"] is not None else "n/d"
            self.send_message(
                chat_id,
                f"📊 <b>Últimos {s['dias']} días</b>\n"
                f"• Fotos: <b>{s['fotos']}</b> · Usuarios: <b>{s['usuarios_unicos']}</b>\n"
                f"• Precisión percibida: <b>{prec}</b>\n"
                f"• Por contenedor:\n{cont}",
            )
            return {"status": "ok", "action": "stats"}
        self.send_message(chat_id, "❓ Comando desconocido. Usa /ayuda.")
        return {"status": "unknown_command"}

    def _handle_text(self, chat_id, text: str) -> dict:
        if not settings.anthropic_api_key:
            self.send_message(chat_id, AYUDA)
            return {"status": "ok", "action": "help_no_ai"}
        try:
            from app.agent.core import run_agent

            r = run_agent([{"role": "user", "content": text}], es_admin=self.es_admin(chat_id))
            self.send_message(chat_id, r["response"])
            return {"status": "ok", "action": "agent", "tools_used": r["tools_used"]}
        except Exception as e:
            logger.exception("Error del agente")
            self.send_message(chat_id, "⚠️ No pude responder ahora. Prueba enviando una foto del residuo.")
            return {"status": "error", "error": str(e)}

    # ─── Polling local ───
    def poll_forever(self, interval: float = 2.0):
        if not self.is_configured:
            print("❌ TELEGRAM_BOT_TOKEN no configurado en .env")
            return
        print("🤖 ECOCLASIFICA activo (polling)...")
        offset = 0
        try:
            with httpx.Client(timeout=10.0) as c:
                c.post(f"{self.api_url}/deleteWebhook")
        except Exception:
            pass
        while True:
            try:
                with httpx.Client(timeout=30.0) as c:
                    r = c.get(f"{self.api_url}/getUpdates", params={"offset": offset + 1, "timeout": 20})
                    for u in r.json().get("result", []):
                        offset = max(offset, u.get("update_id", 0))
                        try:
                            self.process_update(u)
                        except Exception:
                            logger.exception("Error procesando update")
            except Exception as e:
                logger.error("Polling: %s", e)
                time.sleep(interval)


telegram_bot = TelegramBot()
