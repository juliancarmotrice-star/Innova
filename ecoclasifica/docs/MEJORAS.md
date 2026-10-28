# Cambios sugeridos

## A. Qué mejoramos respecto al proyecto de referencia (RETORNA)

| Hallazgo en RETORNA | Qué hicimos aquí |
|---|---|
| El conteo por foto cae a un "detector piloto" que **inventa un número** si falla la IA o falta la API key | Sin datos inventados: si falla, se avisa; si la confianza es baja, se pide otra foto |
| El modelo devuelve JSON en texto y se limpia con regex | Tool use forzado: salida estructurada siempre válida |
| Nombres de modelo fijos y distintos en cada archivo (algunos ya retirados) | Un solo `MODELO` en `.env` |
| Clave de gerencia por defecto en el código (`gerencia2026`) y roles en un JSON dentro del repo | Admins por ID de Telegram en `.env`; sin claves compartidas |
| Webhook sin validar el secret | Se valida `X-Telegram-Bot-Api-Secret-Token` |
| Detección de "entrega/recogida" por listas de palabras | El agente entiende texto libre; las reglas críticas siguen en código |
| Herramientas duplicadas como alias (proveedor/transportador) y fotos pendientes solo en memoria | 2 herramientas claras; sin estado en memoria |
| Dependencias sin usar (pandas, scikit-learn, sqlalchemy, reportlab…) | Solo lo necesario |

## B. Cambios sugeridos para el proyecto (campus)

**Alto impacto, poco esfuerzo**
1. **Códigos QR en cada punto ecológico** que abran el bot con el lugar ya cargado (`t.me/bot?start=biblioteca_p2`). Así sabemos *dónde* se confunde más la gente sin que escriban nada.
2. **Mensaje corto con el "por qué"** (ej. "la lata con líquido contamina el papel del mismo contenedor"). Cambia hábitos mejor que solo decir el color.
3. **Señalización uniforme**: la misma imagen de la respuesta del bot pegada en las canecas. Si el bot dice "blanco" y la caneca real es gris, el sistema falla.
4. **Ajustar `residuos.py` a las canecas reales** de cada edificio (algunas sedes tienen 2 o 5 colores) y a lo que el gestor de residuos realmente recibe.

**Para medir si funciona (clave para el proyecto)**
5. **Línea base**: auditoría de 1 semana de la bolsa de una caneca blanca (% de contaminación) antes de lanzar, y repetirla a las 4 y 8 semanas.
6. **Usar el feedback ✅/❌**: ya se guarda. Revisar semanalmente los ❌ para corregir reglas o el prompt.
7. **Meta sugerida**: precisión percibida > 85 %, contaminación de la caneca blanca −30 % en 8 semanas.

**Fase 2**
8. **Panel web** (Streamlit) con mapa de calor de confusiones por edificio y ranking por facultad.
9. **Gamificación suave**: puntos/insignias por escaneos, retos entre facultades (cuidando no premiar el spam de fotos).
10. **Modo "una lata, un clic"** en cámaras de las canecas inteligentes si hay presupuesto (misma API: `POST /api/clasificar`).
11. **WhatsApp** además de Telegram, si los estudiantes lo prefieren (la lógica ya está separada del canal).
12. **Entrenar un modelo propio** (YOLO) solo cuando haya cientos de fotos reales etiquetadas con el feedback acumulado; mientras tanto, la visión de Claude basta.

## C. Riesgos a vigilar
- Fotos con rostros o personas: no se almacenan, pero conviene avisarlo en `/ayuda`.
- Objetos mezclados (vaso con tapa y pitillo): el bot lista cada parte; validar que sea claro en pruebas con estudiantes.
- Costo por foto: se reduce la imagen a 1200 px; fijar un límite diario por usuario si se masifica.
