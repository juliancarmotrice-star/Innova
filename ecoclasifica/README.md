# ECOCLASIFICA

Bot de Telegram con IA que le dice a estudiantes y personal **en qué caneca botar cada residuo** a partir de una foto. Pensado para mejorar la separación en la fuente en la universidad (latas, plásticos, papel, orgánicos, etc.).

Basado en la estructura de [REDIN-RECOLECTA / RETORNA](https://github.com/juliancarmotrice-star/REDIN-RECOLECTA): bot + visión con Claude + agente con herramientas + reglas de negocio en código + API FastAPI.

## Cómo funciona

```
Foto (Telegram) ──► vision.py ──► residuos.py ──► respuesta + botones ✅/❌
                    Claude         reglas en       guardado en SQLite
                    describe       código decide   (estadísticas)
                    material y     el contenedor
                    estado
```

**Idea clave:** la IA solo *describe* (lata, metal, con líquido); el *contenedor* lo decide `app/services/residuos.py`, que es código testeable y se ajusta a las canecas reales del campus sin tocar prompts.

Contenedores por defecto (Res. 2184/2019, Colombia): ⚪ blanco aprovechables · 🟢 verde orgánicos · ⚫ negro no aprovechables · 🔴 punto especial (pilas, electrónicos).

## Estructura

```
app/
├── main.py                 FastAPI (/api/clasificar, /api/telegram/webhook, /api/stats)
├── config.py
├── services/
│   ├── vision.py           foto → ítems (tool use forzado, JSON siempre válido)
│   ├── residuos.py         material+estado → contenedor (REGLAS, editar aquí)
│   └── clasificador.py     pipeline completo
├── agent/                  preguntas de texto ("¿dónde boto X?"), 2 herramientas
├── db/store.py             SQLite: fotos, ítems, feedback, estadísticas
└── telegram/bot.py
scripts/  run_telegram.py (polling local) · simular_foto.py (sin Telegram)
tests/    test_residuos.py
docs/MEJORAS.md             cambios sugeridos al proyecto de referencia y próximos pasos
```

## Correrlo

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # completa ANTHROPIC_API_KEY y TELEGRAM_BOT_TOKEN
pytest                          # reglas de clasificación
python scripts/simular_foto.py foto.jpg "Biblioteca piso 2"   # prueba sin Telegram
python scripts/run_telegram.py  # bot en polling
uvicorn app.main:app --reload   # API (webhook en producción)
```

Token del bot: habla con [@BotFather](https://t.me/BotFather) en Telegram. Tu ID para `ADMIN_TELEGRAM_IDS`: [@userinfobot](https://t.me/userinfobot).

## Comandos

| Comando | Quién | Qué hace |
|---|---|---|
| foto (+ pie de foto con el lugar) | todos | sugiere la caneca |
| texto libre | todos | el agente responde dudas |
| `/ayuda` | todos | guía de colores |
| `/stats` | admins | uso de los últimos 30 días |

## Seguridad y privacidad

- Sin claves por defecto: los admins se definen por ID de Telegram en `.env`.
- El webhook valida `X-Telegram-Bot-Api-Secret-Token`.
- Los usuarios se guardan como hash; las fotos **no** se almacenan, solo el resultado.
