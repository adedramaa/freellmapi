# NORMA MAESTRA: solo animación tridimensional real en Blender

**Obligatoria desde 22 de octubre de 2026.** Todo video NUEVO de novelas de misterio debe usar Blender como **motor de movimiento**, no Blender solo para exportar doce fotogramas estáticos.

## Reglas de aceptación innegociables

1. Voz en off natural, **narrador invisible**. El narrador original del capítulo 1 está archivado en `fabrica_free/audio/narrador_original_ep01.opus`. No cambiar esa voz.
2. Acciones en el mundo físico de la historia: Vera actúa, los objetos cambian posición/rotación, hay iluminación en movimiento y cambios de cámaras animadas.
3. No se permiten animatics de fotografías, simples JPEG con pan/zoom, slideshows, talking-heads, ni la taza/personaje presentador.
4. Los subtítulos siguen el audio original. El montaje final conserva la voz sin alterar diálogos ni ritmo.
5. GitHub Actions debe comprobar `scene.blend`, procedencia Blender Cycles, transformaciones 3D en distintos fotogramas, múltiples cámaras y pista de audio real. Si no existen, **fallar en lugar de exportar un falso video**.
6. Para capítulos 2–6, escribir y probar acciones tridimensionales adecuadas al guion de cada capítulo. **No reciclar sin cambios** la animación de 03:17 del capítulo 1.
7. Los 16 agentes de Claude Code son asesores editoriales, NO generadores de animación. Si fallan, registrar `N/16` y no declarar que completaron. La última auditoría editorial válida de la entrega anterior fue 15/16.
8. Nunca publicar en YouTube/TikTok/Instagram ni reemplazar la edición aprobada sin autorización del usuario.
9. Mantener la infraestructura gratuita sin suscripciones nuevas, consciente de los límites de GitHub Actions y Groq.

## Flujo vigente

- `fabrica_free/blender_noir_3d.py`: episodio piloto, 12 cámaras 3D, actriz, cajón, fotografía, puertas y animación a lo largo de 32,8 segundos.
- `fabrica_free/subtitles_narrator3d.py`: subtítulos temporizados según la grabación aprobada.
- `.github/workflows/misterio-blender3d-obligatorio.yml`: primera prueba y render 3D obligatorio, entrega MP4, archivo Blender editable y metadatos de procedencia.
- `fabrica_free/season_plan.json`: historia y continuidad de 6 capítulos; **solo el capítulo 1 está implementado en este motor nuevo**.
- Los flujos antiguos `fabrica-misterio.yml` y `fabrica-misterio-animatic.yml` están retirados.

**Puerta de publicación:** el resultado no será etiquetado como completo hasta que el MP4 se haya inspeccionado por técnica, sincronía, narrativa y calidad audiovisual. El pase del workflow sin revisión estética no equivale a aprobación.
