"""Ejecuta el bot en modo polling (desarrollo local, sin webhook ni ngrok)."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.telegram.bot import telegram_bot  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    telegram_bot.poll_forever()
