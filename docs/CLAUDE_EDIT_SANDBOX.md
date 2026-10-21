# Claude Code real: etapa Edit controlada (solo carpeta temporal)

Este flujo prueba que Claude Code oficial 2.1.296 puede **usar Read + Edit** con FreeLLMAPI/Groq y **NO** solamente producir texto. No permite escribir directamente en los proyectos del usuario.

## Qué se prueba

Workflow: **Actions → Claude Code - Isolated Edit Verification**

- En Pull Requests ejecuta únicamente pruebas offline del auditor y comprueba la instalación del CLI, sin API key ni solicitudes a Groq.
- En main permite una única ejecución de verificación mediante commit autorizado (prefijo test(claude-edit):) y ejecuciones manuales.
- Instala el CLI oficial, y crea una carpeta **temporal** con task.txt: status: before + una línea de prueba.
- Solo expone herramientas Read y Edit; no Bash, Write, Web, MCP ni herramientas de desarrollo adicionales.
- Claude Code debe abrir task.txt con Read y reemplazar únicamente status: before → status: after mediante Edit.
- Un verificador independiente examina stream-json y exige que haya Read, Edit, y resultados de ambas herramientas, sobre el mismo archivo.
- GitHub compara el contenido final exacto, comprueba que no haya archivos adicionales en la carpeta temporal y verifica que el checkout original se mantenga intacto.
- La ejecución no tiene credenciales git para hacer push, no crea PR ni despliega Render.
- Capturamos las respuestas brutas solo en el runner temporal; NO publicamos transcripciones, claves ni contenidos de archivos.

## Restricciones y siguiente etapa

- El entorno GitHub Actions es efímero y de costo base gratuito para este repositorio público; Groq conserva límites de uso y Render Free puede dormir.
- **No** es una garantía de sandbox a nivel de kernel: el CLI usa las herramientas disponibles, por eso el scope debe continuar siendo solamente material no sensible en un runner efímero.
- Aunque esta prueba pase, NO habilitamos aún edición de proyectos reales ni Bash por libre.
- Para probar comandos, después habrá que autorizar explícitamente una lista de comandos de test seguros y auditar el tool_use real, sin credenciales de despliegue.
- Para llegar al video: conectar solicitudes desde ChatGPT al runner de Claude Code, con repositorio definido, aprobaciones antes de cambios productivos, resultados y PR de revisión.
