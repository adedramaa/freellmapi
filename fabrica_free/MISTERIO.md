# La Fábrica — NOVELAS DE MISTERIO 3D (costo adicional 0)

**Estatus:** piloto en pruebas en la rama `fabrica-gratis-prototipo`. No se publica nada en redes automáticamente.

## Qué hace cada herramienta
- **Claude Code oficial** con el puente FreeLLMAPI/Groq existente: guionista, editores, jurado y lectores simulados (son *simulaciones de evaluación editorial*, no espectadores reales).
- **Kokoro 82M local**: sintetiza las frases en español sin ElevenLabs ni cuenta paga. La naturalidad debe ser evaluada por oído.
- **Blender Cycles + Rhubarb + Remotion + FFmpeg**: escena 3D, labios, fondos, montaje, subtítulos y MP4.
- **GitHub Actions**: ejecuta todo fuera de Android con el cupo gratuito disponible. No se contrató GPU externa.
- **El original de @tarritoai** se descarga en el runner para uso personal, con su licencia restrictiva. No revender/redistribuir el software original; sí usar los videos producidos según licencia.

## Control móvil
1. En GitHub, abre [mystery_request.json](./mystery_request.json).
2. Cambia **topic** para definir el conflicto y **voice** entre `em_alex` (masculina), `em_santa` o `ef_dora` (femeninas).
3. Usa **agents: "1"** para pruebas económicas y rápidas de historia; **"16"** para revisión editorial exhaustiva, sujeta a cuotas.
4. Usa **quality: "humo"** para primer prototipo o **"draft"** para revisión visual más cuidada (mucho más CPU).
5. Guarda en la rama `fabrica-gratis-prototipo`, sin tocar `main`.
6. En **Actions → La Fabrica - Novelas de misterio 3D GRATIS**, abre la última ejecución y descarga `misterio-piloto-...` de **Artifacts**.
7. Antes de publicar verifica continuidad, voz, guion, subtítulos, contenido original y licencias.

## Temporada editorial
[Plan de seis capítulos](./season_plan.json): El archivo de las 03:17. El guion de prueba inicial utiliza exclusivamente el capítulo 1. La automatización del resto de capítulos y la persistencia de la continuidad están en desarrollo, no están aprobados como producción final.

## Límites operativos
- Que un workflow tenga estado **success** no prueba que los 16 agentes hayan respondido: el fichero `mystery_report.json` informa éxitos, errores y uso de guion de respaldo.
- El MP4 **solo** se declara verificado cuando pasa inspección de pistas H.264 1080×1920 + audio AAC y revisión visual.
- Las voces pueden sonar menos naturales que servicios pagos. No hay garantía de viralidad.
- GitHub Actions y FreeLLMAPI tienen cuotas, aunque no se contrate un plan de pago.
