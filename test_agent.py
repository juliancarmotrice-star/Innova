import sys
import os
from pathlib import Path

# Configurar stdout con codificación UTF-8 para soporte de emojis en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont

import config
from schemas import WasteClassificationResponse, CanecaTipo


def create_sample_test_image(text: str, filename: str) -> Path:
    """Crea una imagen sintética simple para pruebas si no tienes una foto a mano."""
    img = Image.new("RGB", (400, 300), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    # Dibujar un recuadro ilustrativo
    d.rectangle([(20, 20), (380, 280)], outline=(100, 100, 100), width=3)
    d.text((40, 130), f"[RESIDUO DE PRUEBA]\n{text}", fill=(20, 20, 20))
    
    test_dir = Path("tests/test_images")
    test_dir.mkdir(parents=True, exist_ok=True)
    file_path = test_dir / filename
    img.save(file_path)
    return file_path


def main():
    print("=" * 60)
    print("🌱 ECOGUIDE-IA - PROBANDO AGENTE DE CLASIFICACIÓN DE RESIDUOS")
    print("=" * 60)

    # 1. Verificar si hay API KEY
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "tu_api_key_aqui":
        print("\n⚠️ AVISO: No se detectó GEMINI_API_KEY configurada en el archivo .env.")
        print("Para probar la llamada real a la IA:")
        print("1. Copia '.env.example' a '.env'")
        print("2. Pega tu API Key de https://aistudio.google.com/ en GEMINI_API_KEY")
        print("\nProbando estructura de schemas y formateador de Telegram...")
        
        # Prueba de schema simulado
        mock = WasteClassificationResponse(
            residuo_identificado="Cáscara de banano",
            material_principal="Materia orgánica vegetal",
            estado_detectado="Fresco, sin contaminantes externos",
            caneca_destino=CanecaTipo.VERDE,
            nombre_caneca="Caneca Verde (Orgánicos)",
            color_hex="#2E7D32",
            emoji_caneca="🟢",
            confianza="ALTA",
            instruccion_accion="Depositar directamente sin bolsa ni etiquetas plásticas.",
            explicacion="Las cáscaras de frutas son materia orgánica degradable ideal para compostaje.",
            recomendaciones_adicionales=[
                "Retirar stickers o pegatinas de la fruta.",
                "Ideal para abono o lombricultura."
            ]
        )
        print("\n--- Vista previa del mensaje listo para Telegram ---")
        print(mock.to_telegram_markdown())
        print("=" * 60)
        return

    # 2. Si hay API KEY, proceder a clasificar
    from waste_agent import WasteClassifierAgent

    agent = WasteClassifierAgent()

    # Si se pasó una imagen por argumento CLI:
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
    else:
        # Crear imagen de muestra rápida para probar
        print("\nCreando imagen sintética de prueba...")
        image_path = create_sample_test_image("Botella de plastico aplastada limpia", "muestra_botella.jpg")
        print(f"Imagen generada en: {image_path}")

    print(f"\n📸 Analizando imagen: {image_path}...")
    try:
        resultado = agent.classify(image_path)
        print("\n✅ CLASIFICACIÓN COMPLETADA:")
        print("=" * 60)
        print(resultado.to_telegram_markdown())
        print("=" * 60)
        print(f"JSON Crudo:\n{resultado.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"❌ Error al clasificar: {e}")


if __name__ == "__main__":
    main()
