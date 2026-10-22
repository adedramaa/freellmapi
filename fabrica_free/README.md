# La Fábrica gratis desde Android — prueba aislada

Esta rama `fabrica-gratis-prototipo` no modifica el servicio FreeLLMAPI ni el puente de Claude Code existente.

**Qué hace:** Claude Code oficial, conectado al FreeLLMAPI/Groq existente, propone dos frases en español. Kokoro 82M las sintetiza gratis y localmente (voz `em_alex`, sin ElevenLabs). El programa original de La Fábrica de @tarritoai genera sincronización de labios (Rhubarb), escenas 3D (Blender), montaje (Remotion) y archivo MP4 (FFmpeg). Si Claude falla, lo reporta y ejecuta un guion de demostración para seguir probando.

**Licencia:** el código de [La Fábrica](https://github.com/tarritoai/fabrica) se descarga en tiempo de ejecución para uso personal; no se redistribuye el software original, que tiene una licencia restrictiva. Los videos creados se pueden monetizar de acuerdo con esa licencia.

**Dónde aparece:** en GitHub → Actions → «La Fabrica gratis - Claude Code, Kokoro y Blender» → Artifacts → `fabrica-3d-kokoro-...` (MP4 de prueba). No hay publicación automática en redes. GitHub Actions tiene cuotas y límites; no se garantiza ejecución ilimitada ni un resultado vocal idéntico a ElevenLabs.

**Prueba pendiente:** un flujo escrito no es una producción verificada. Comprobar el estado del run, el MP4 resultante, la naturalidad de la voz y el tiempo real de render antes de ampliar a 16 agentes y videos largos. No hacer cambios en `main` hasta aprobar la prueba.