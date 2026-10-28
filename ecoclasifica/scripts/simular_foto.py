"""
Prueba el pipeline sin Telegram: python scripts/simular_foto.py ruta/foto.jpg ["Biblioteca piso 2"]
Requiere ANTHROPIC_API_KEY en .env.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.clasificador import clasificar_foto  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python scripts/simular_foto.py foto.jpg [ubicacion]")
    img = Path(sys.argv[1]).read_bytes()
    res = clasificar_foto(img, chat_id="simulador", ubicacion=sys.argv[2] if len(sys.argv) > 2 else "")
    print(res["mensaje"])
    print(json.dumps({k: v for k, v in res.items() if k != "mensaje"}, indent=2, ensure_ascii=False))
