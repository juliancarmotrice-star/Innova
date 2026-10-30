import io
import json
import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# UTF-8 para consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from waste_agent import WasteClassifierAgent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instancia global del agente clasificador
agent: WasteClassifierAgent = None


# -----------------------------------------------------------------------------
# Micro-servidor HTTP para Render Web Service (Plan GRATUITO $0)
# -----------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Responde 200 OK a los pings de Render para validar que el servicio está vivo."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        body = json.dumps({
            "status": "online",
            "bot": "EcoGuide-IA",
            "mode": "Telegram Polling 24/7",
            "provider": "Render Free Web Service"
        })
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        # Silenciar logs recurrentes de healthcheck
        return


def start_health_server():
    """Inicia el servidor HTTP en un hilo demonio para el puerto asignado por Render."""
    port = int(os.environ.get("PORT", "10000"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"✅ Micro-servidor web activo en el puerto {port} (compatible con Render Free Web Service)")
    except Exception as e:
        logger.warning(f"No se pudo iniciar el micro-servidor web (no crítico en local): {e}")


# -----------------------------------------------------------------------------
# Handlers del Bot de Telegram
# -----------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida y explicación del bot."""
    welcome_text = (
        "👋 *¡Hola! Soy EcoGuide-IA*\n\n"
        "🌱 Tu clasificador de residuos inteligente.\n\n"
        "📸 *¿Cómo usarme?*\n"
        "👉 *Solo tómale una foto al residuo y envíala.*\n"
        "No necesitas escribir nada; la inteligencia artificial examinará la imagen y determinará la caneca correcta por sí sola:\n\n"
        "⚪ *Caneca Blanca:* Aprovechables limpios (plástico, vidrio, latas, cartón)\n"
        "🟢 *Caneca Verde:* Orgánicos (restos de comida, cáscaras, borra de café)\n"
        "⚫ *Caneca Negra:* No aprovechables (servilletas usadas, cajas de pizza engrasadas, mecatos, pelotas inservibles)\n"
        "🔴 *Punto Especial:* Pilas, medicamentos o bombillos\n\n"
        "¡Envía tu foto ahora!"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instrucciones de ayuda."""
    help_text = (
        "ℹ️ *Instrucciones simples:*\n\n"
        "1. Toma una foto clara del residuo o basura.\n"
        "2. Envíala a este chat.\n"
        "3. No necesitas escribir nada. La IA detectará:\n"
        "   • Qué residuo u objeto es.\n"
        "   • Si está limpio o contaminado con grasa/comida.\n"
        "   • En qué caneca depositarlo y cómo prepararlo (ej: enjuagar)."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la foto del residuo, la analiza de forma 100% autónoma y responde."""
    if not update.message or not update.message.photo:
        return

    chat_id = update.effective_chat.id

    # Notificar al usuario que estamos analizando
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text("🔎 *Analizando visualmente la imagen...*", parse_mode=ParseMode.MARKDOWN)

    try:
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Descargar la imagen en memoria (bytes)
        image_bytes = await photo_file.download_as_bytearray()

        # Análisis visual 100% autónomo (sin requerir texto)
        resultado = agent.classify(bytes(image_bytes))

        # Generar texto enriquecido formateado
        response_text = resultado.to_telegram_markdown()

        # Eliminar mensaje temporal y enviar resultado final
        await status_msg.delete()
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error procesando la foto: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Lo siento, ocurrió un error analizando la imagen: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde cuando el usuario envía texto en lugar de una foto."""
    await update.message.reply_text(
        "📷 *Solo envíame una foto del residuo*.\n"
        "No hace falta que me escribas texto, yo analizaré la imagen por mi cuenta.",
        parse_mode=ParseMode.MARKDOWN
    )


def main():
    global agent

    # 1. Iniciar micro-servidor de healthcheck para Render Free Web Service
    start_health_server()

    # 2. Validar variables requeridas
    if not config.TELEGRAM_BOT_TOKEN:
        print("\n" + "=" * 60)
        print("❌ FALTA CONFIGURAR EL TOKEN DE TELEGRAM")
        print("=" * 60)
        print("1. Abre tu archivo .env")
        print("2. Pega tu token en la variable: TELEGRAM_BOT_TOKEN=tu_token_aqui")
        print("(Si aún no tienes uno, créalo gratis en Telegram hablando con @BotFather)")
        print("=" * 60 + "\n")
        return

    print("🤖 Iniciando Agente EcoGuide para Telegram...")
    agent = WasteClassifierAgent()

    # 3. Configurar la aplicación de Telegram
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))

    print("🚀 Bot en línea y listo para recibir fotos. Presiona Ctrl+C para detenerlo.")
    app.run_polling()


if __name__ == "__main__":
    main()
