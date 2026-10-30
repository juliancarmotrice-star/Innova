import io
import json
import logging
import sys
import time
from pathlib import Path
from typing import Union, Optional
from PIL import Image, ImageOps

# UTF-8 para consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google import genai
from google.genai import types

import config
from schemas import WasteClassificationResponse, CanecaTipo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AUTONOMOUS_SYSTEM_PROMPT = """
Eres EcoGuide-IA, un agente experto en visión artificial por computadora y gestión ambiental.
Tu objetivo es analizar e inspeccionar VISUALMENTE y de forma 100% AUTÓNOMA la imagen del residuo o basura que te envía el usuario.
El usuario ÚNICAMENTE enviará la fotografía, SIN escribir texto ni dar explicaciones. 

REGLAS DE IDENTIFICACIÓN Y CLASIFICACIÓN TÉCNICA:
1. IDENTIFICACIÓN VISUAL:
   - Reconoce la silueta, textura, marca, transparencia y material del objeto.
   - Aplica tanto a residuos comunes de cocina como a objetos domésticos diversos:
     • Botellas, latas, plásticos, vidrios, papeles, cartones.
     • Artículos deportivos o juguetes (ej: pelotas de tenis, balones de goma/cuero, juguetes plásticos).
     • Ropa, telas, zapatos o accesorios en desuso.

2. CÓDIGO DE COLORES ESTANDARIZADO:
   🟢 CANECA VERDE (Orgánicos aprovechables):
      - Cáscaras de fruta, verduras, restos de comida, borra de café, poda, hojas secas.

   ⚪ CANECA BLANCA (Aprovechables / Reciclables):
      - Plásticos limpios (botellas PET, recipientes), vidrio, latas de aluminio/metal, cartón y papel secos.
      - Si tiene líquido o suciedad leve: clasificar en BLANCO e instruir vaciar y enjuagar.

   ⚫ CANECA NEGRA (No aprovechables / Basura ordinaria):
      - Servilletas usadas, papel higiénico, cartón o papel con MANCHAS DE GRASA o comida.
      - Empaques metalizados (papitas, snacks).
      - Pelotas deportivas desgastadas (ej: pelotas de tenis compuestas de caucho + fieltro, balones inservibles de hule/cuero mixto que no se pueden reciclar en caneca blanca).
      - Plásticos sucios no lavables, cerámicas, colillas de cigarrillo.

   🔴 PUNTO ESPECIAL (Residuos Peligrosos / RAEES):
      - Pilas, baterías, bombillos, medicamentos vencidos, jeringas.

REGLAS DE BREVEDAD PARA ALTA VELOCIDAD:
- 'instruccion_accion': Sé directo, máximo 12 palabras.
- 'explicacion': Explica en máximo 20 palabras por qué va en esa caneca.
- 'recomendaciones_adicionales': Entre 1 y 2 consejos breves (ej: si es una pelota de tenis o juguete, sugerir donación o reutilización si aún sirve).
"""


class WasteClassifierAgent:
    """Agente de clasificación visual optimizado para baja latencia y alta confiabilidad."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model_name or config.GEMINI_MODEL
        self.fallback_model = config.GEMINI_FALLBACK_MODEL
        self.demo_mode = not bool(self.api_key and self.api_key != "tu_api_key_aqui")

        if self.demo_mode:
            logger.warning(
                "⚠️ Operando en MODO DEMO GRATUITO. Agrega tu GEMINI_API_KEY en .env para IA real."
            )
            self.client = None
        else:
            # Cliente GenAI con pooling optimizado
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Agente optimizado listo. Modelo principal: {self.model_name} | Fallback: {self.fallback_model}")

    def _optimize_and_prepare_image(self, image_input: Union[bytes, str, Path, Image.Image]) -> types.Part:
        """
        Optimización crítica de rendimiento:
        1. Carga la imagen desde bytes, archivo o PIL.
        2. Corrige orientación EXIF (típica en fotos de celular).
        3. Reduce la resolución a máximo 800px (suficiente para IA pero 98% más ligera).
        4. Comprime a JPEG calidad 80 con optimización.
        Esto reduce una foto de 8MB a ~50KB, reduciendo la latencia de 25s a menos de 4s.
        """
        try:
            if isinstance(image_input, (str, Path)):
                img = Image.open(image_input)
            elif isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                raise TypeError(f"Tipo de imagen no compatible: {type(image_input)}")

            # 1. Corregir rotación automática de celular
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # 2. Redimensionar preservando aspecto (máximo 800x800)
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)

            # 3. Guardar comprimida en memoria
            buffer = io.BytesIO()
            img.convert("RGB").save(buffer, format="JPEG", quality=80, optimize=True)
            compressed_bytes = buffer.getvalue()

            logger.info(f"Imagen optimizada con éxito: {len(compressed_bytes) / 1024:.1f} KB enviados a la IA.")
            return types.Part.from_bytes(data=compressed_bytes, mime_type="image/jpeg")

        except Exception as e:
            logger.error(f"Error optimizando imagen: {e}")
            raise

    def _demo_classify(self) -> WasteClassificationResponse:
        """Respuesta demostrativa cuando no hay API Key configurada."""
        return WasteClassificationResponse(
            residuo_identificado="Objeto de muestra",
            material_principal="Material reciclable",
            estado_detectado="Limpio",
            caneca_destino=CanecaTipo.BLANCO,
            nombre_caneca="Caneca Blanca (Aprovechables)",
            color_hex="#FFFFFF",
            emoji_caneca="⚪",
            confianza="ALTA",
            instruccion_accion="Vaciar y depositar en la caneca blanca.",
            explicacion="[Modo Demo] Configura tu GEMINI_API_KEY para análisis en vivo con IA.",
            recomendaciones_adicionales=["Configura el archivo .env para visión real."]
        )

    def classify(
        self,
        image_input: Union[bytes, str, Path, Image.Image],
        user_comment: Optional[str] = None
    ) -> WasteClassificationResponse:
        """
        Inspecciona visualmente la foto de forma autónoma con reintentos automáticos
        y failover inmediato para evitar desconexiones.
        """
        if self.demo_mode:
            return self._demo_classify()

        # Optimizar imagen para velocidad relámpago
        t0 = time.time()
        image_part = self._optimize_and_prepare_image(image_input)

        prompt_text = (
            "Analiza visualmente este residuo u objeto de forma 100% autónoma. "
            "Identifícalo con precisión (sea comida, botella, pelota/juguete, empaque, tela o residuo), "
            "evalúa su material y determina en qué caneca debe depositarse según las reglas."
        )

        config_options = types.GenerateContentConfig(
            system_instruction=AUTONOMOUS_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=WasteClassificationResponse,
            temperature=0.1,
        )

        # Probar primero con el modelo de baja latencia
        models_to_try = [self.model_name, self.fallback_model]
        last_error = None

        for model in models_to_try:
            try:
                logger.info(f"Enviando solicitud a {model}...")
                response = self.client.models.generate_content(
                    model=model,
                    contents=[image_part, prompt_text],
                    config=config_options
                )
                raw_text = response.text
                data_dict = json.loads(raw_text)
                result = WasteClassificationResponse(**data_dict)
                logger.info(f"Clasificado en {time.time() - t0:.2f}s: '{result.residuo_identificado}' -> {result.caneca_destino}")
                return result
            except Exception as err:
                logger.warning(f"Fallo temporal con {model}: {err}. Intentando alternativa...")
                last_error = err
                time.sleep(0.5)

        # Si ambos fallaron, lanzar el último error registrado
        raise RuntimeError(f"No fue posible completar la clasificación tras reintentar: {last_error}")
