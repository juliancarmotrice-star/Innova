# 🌱 EcoGuide-IA: Agente de Clasificación de Residuos

Agente de Inteligencia Artificial Multimodal (Visión + Razonamiento) diseñado para identificar residuos a partir de fotografías y determinar la caneca adecuada de separación (Aprovechables, Orgánicos o No aprovechables) según el código de colores estandarizado.

---

### 📲 Prueba el Bot en Telegram

Escanea el código QR desde tu celular o accede directamente al enlace para interactuar con el bot:

<p align="center">
  <a href="https://t.me/Eco_21bot">
    <img src="assets/qr_telegram_bot.png" width="220" alt="Código QR EcoGuide Telegram Bot" /><br/>
    <b>👉 @Eco_21bot (t.me/Eco_21bot)</b>
  </a>
</p>

---

## 🎨 Código de Colores Soportado

| Caneca | Tipo de Residuo | Materiales Típicos | Condición Clave |
| :---: | :--- | :--- | :--- |
| 🟢 | **Orgánicos aprovechables** | Cáscaras de frutas/verduras, restos de comida, café, poda. | Sin bolsas ni empaques plásticos. |
| ⚪ | **Aprovechables / Reciclables** | Plástico, cartón, papel, vidrio, metales. | **Completamente limpios y secos**. |
| ⚫ | **No aprovechables** | Servilletas usadas, papel higiénico, cartón/papel con grasa (cajas de pizza sucias), empaques metalizados (mecatos). | Contaminados o no reciclables. |
| 🔴 | **Peligrosos / RAEES** | Pilas, bombillos, medicamentos, jeringas. | Punto de recolección especial posconsumo. |

---

## 📁 Estructura del Proyecto

```text
INNOVA/
├── assets/
│   └── qr_telegram_bot.png  # Código QR de acceso directo al bot de Telegram
├── config.py                # Gestión centralizada de configuración y variables de entorno
├── schemas.py               # Modelos de datos Pydantic y formateador de mensajes
├── waste_agent.py           # Motor del Agente Multimodal con Google Gemini Vision
├── telegram_bot.py          # Bot de Telegram conectado al Agente de IA (+ micro-servidor web)
├── Procfile                 # Configuración de despliegue en la nube (Render)
├── test_agent.py            # Script de pruebas CLI para validar el agente con imágenes
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Plantilla para variables de entorno (API Keys)
└── README.md                # Documentación técnica
```

---

## 🚀 Puesta en Marcha Rápida

### 1. Requisitos Previos
Tener Python 3.10 o superior instalado. Las dependencias ya han sido preparadas:
```bash
pip install -r requirements.txt
```

### 2. Configurar Claves de API
Copia el archivo `.env.example` y renómbralo a `.env`:
```bash
copy .env.example .env
```

Edita `.env` con tus credenciales:
```env
# Obtén tu clave gratuita en: https://aistudio.google.com/
GEMINI_API_KEY=tu_api_key_de_gemini

# Modelo recomendado por velocidad y precisión multimodal:
GEMINI_MODEL=gemini-3.5-flash-lite

# Obtén tu token de bot en Telegram con @BotFather:
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
```

---

## 🧪 Pruebas del Agente (Sin Telegram)

Puedes probar el agente directamente desde tu terminal pasando una foto real:

```bash
python test_agent.py ruta/a/tu/foto.jpg
```

Si no especificas una foto, el script generará automáticamente una muestra sintética para validar el flujo.

---

## 📲 Ejecutar el Bot de Telegram Localmente

Una vez configurado `TELEGRAM_BOT_TOKEN`:

```bash
python telegram_bot.py
```

1. Abre tu bot en Telegram: [@Eco_21bot](https://t.me/Eco_21bot).
2. Envía `/start`.
3. Toma una foto con la cámara de tu celular a cualquier residuo (por ejemplo, una cáscara de fruta, un vaso sucio, una botella plástica o una pila).
4. El agente responderá en segundos con:
   - Nombre del residuo y material detectado.
   - Estado de limpieza/contaminación.
   - Caneca correspondiente con emoji y color.
   - Paso a seguir inmediato (ej: *"Vaciar líquidos y enjuagar antes de depositar"*).
   - Explicación didáctica y recomendaciones de aprovechamiento.
