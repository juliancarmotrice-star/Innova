from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CanecaTipo(str, Enum):
    BLANCO = "BLANCO"          # Aprovechables limpios (plástico, vidrio, metal, papel, cartón)
    VERDE = "VERDE"            # Orgánicos aprovechables (restos de comida, cáscaras, poda)
    NEGRO = "NEGRO"            # No aprovechables (servilletas, papel higiénico, cartón sucio/grasoso, empaques metalizados)
    ESPECIAL = "ESPECIAL"      # Peligrosos/RAEE (pilas, medicamentos, bombillos, jeringas)


class WasteClassificationResponse(BaseModel):
    residuo_identificado: str = Field(
        ...,
        description="Nombre claro del residuo u objeto principal identificado en la foto (ej: 'Botella de plástico', 'Cáscara de plátano', 'Caja de pizza engrasada')."
    )
    material_principal: str = Field(
        ...,
        description="Material predominante detectado (ej: Plástico PET, Cartón, Orgánico, Vidrio, Metal, Papel aluminizado)."
    )
    estado_detectado: str = Field(
        ...,
        description="Estado físico o de limpieza del residuo (ej: 'Limpio y seco', 'Con restos de grasa/aceite', 'Húmedo con restos de comida', 'Roto/Fragmentado')."
    )
    caneca_destino: CanecaTipo = Field(
        ...,
        description="Caneca correspondiente según el código estandarizado: BLANCO, VERDE, NEGRO o ESPECIAL."
    )
    nombre_caneca: str = Field(
        ...,
        description="Nombre descriptivo de la caneca (ej: 'Caneca Blanca (Aprovechables)', 'Caneca Verde (Orgánicos)', 'Caneca Negra (No aprovechables)', 'Punto de recolección especial')."
    )
    color_hex: str = Field(
        ...,
        description="Color hexadecimal para la interfaz (#FFFFFF para blanco, #2E7D32 para verde, #212121 para negro, #D32F2F para especial)."
    )
    emoji_caneca: str = Field(
        ...,
        description="Emoji representativo de la caneca: ⚪ (Blanca), 🟢 (Verde), ⚫ (Negra), 🔴 (Especial)."
    )
    confianza: str = Field(
        ...,
        description="Nivel de certidumbre de la clasificación: ALTA, MEDIA o BAJA."
    )
    instruccion_accion: str = Field(
        ...,
        description="Acción inmediata y concisa que el usuario debe realizar (máx 15 palabras, ej: 'Vaciar líquidos, enjuagar y aplastar antes de depositar')."
    )
    explicacion: str = Field(
        ...,
        description="Explicación clara y didáctica de por qué corresponde a esa caneca específica."
    )
    recomendaciones_adicionales: List[str] = Field(
        default_factory=list,
        description="Consejos adicionales de separación, reducción o reciclaje (1 a 3 puntos breves)."
    )

    def to_telegram_markdown(self) -> str:
        """Genera un mensaje formateado con formato MarkdownV2 o estándar para Telegram."""
        recs = "\n".join([f"  • {r}" for r in self.recomendaciones_adicionales]) if self.recomendaciones_adicionales else "  • Ninguna adicional."
        
        return (
            f"{self.emoji_caneca} *CANECAS SUGERIDA:* *{self.nombre_caneca.upper()}*\n\n"
            f"🔍 *Residuo:* {self.residuo_identificado}\n"
            f"🧱 *Material:* {self.material_principal}\n"
            f"💧 *Estado:* {self.estado_detectado}\n"
            f"🎯 *Certeza:* {self.confianza}\n\n"
            f"⚡ *Paso a seguir:* \n*{self.instruccion_accion}*\n\n"
            f"ℹ️ *¿Por qué va en esta caneca?*\n{self.explicacion}\n\n"
            f"💡 *Recomendaciones:*\n{recs}"
        )

