# Puente directo: ChatGPT → Claude Code oficial → Pull Request

## Objetivo comprobable

Enviar una instrucción en el chat, convertirla **desde la conexión GitHub autorizada de ChatGPT** en un issue del repositorio público y ejecutar Claude Code real en un runner efímero de GitHub Actions mediante FreeLLMAPI/Groq. El resultado permitido es **exclusivamente un PR en borrador**. No se fusiona ni se despliega automáticamente.

Este es el primer puente de control desde ChatGPT; NO es todavía automatización general sobre cualquier proyecto.

## Cómo se utiliza

1. En este chat, solicitar una modificación específica de FreeLLMAPI a partir de un archivo público permitido. Ejemplo: "Mejora una oración de docs/CHAT_BRIDGE_SAMPLE.md con Claude Code, sin cambiar nada más".
2. ChatGPT verifica el alcance y crea, con el GitHub conectado, un issue titulado EXACTAMENTE: [claude-task] ChatGPT code proposal.
3. El cuerpo del issue es un JSON pequeño con SOLO estas propiedades:
   {"file":"docs/CHAT_BRIDGE_SAMPLE.md","task":"Improve a single explanatory sentence without changing the heading."}
4. El evento issues.opened activa el workflow ChatGPT to Claude Code - Owner Issue Bridge. Se aceptan únicamente issues NUEVOS del propietario adedramaa en adedramaa/freellmapi. Otras solicitudes se rechazan sin llamar a Groq.
5. Claude Code oficial 2.1.296 lee y edita una ruta pública autorizada usando Read y Edit, nunca Bash, y sin credenciales de escritura a GitHub.
6. Un validador distinto comprueba evidencia real de herramientas, solo el archivo solicitado, máximo 35 líneas cambiadas y ninguna ruta adicional.
7. Otro job separado, que no tiene acceso a la clave FreeLLMAPI, crea un PR en borrador y agrega un comentario al issue enlazándolo. El usuario aprueba por separado la fusión y otro despliegue si llegase a ser necesario.

## Restricciones y seguridad

- **Repositorio público:** el título, la instrucción y el cuerpo del issue son visibles en internet. Nunca poner allí contraseñas, claves, información privada de clientes, archivos confidenciales ni datos personales.
- Solo código TS/TSX/CSS EXISTENTE bajo client/src o Markdown EXISTENTE bajo docs; el nombre no puede contener referencias a credenciales, auth, token, env, private o secret.
- Archivo de hasta 4500 bytes; tarea de entre 12 y 350 caracteres, sin saltos de línea.
- Propuestas de hasta 6000 bytes, crecimiento limitado y máximo 35 líneas modificadas. La revisión de código sigue siendo obligatoria: estos límites NO prueban que el contenido sea semánticamente seguro.
- Sin permiso de escribir para el job que llama al modelo. El job publicador no invoca modelos, usa artefactos delimitados y verifica otra vez su contenido.
- Sin terminal Bash ni acceso a otros proyectos. El workflow no ejecuta scripts sugeridos por el modelo ni instala dependencias del proyecto.
- Render Auto-Deploy permanece desactivado, no se usan credenciales Anthropic ni proveedores pagos.
- El plan gratuito de Groq y los runners públicos tienen cuotas: si se agotan o falla el modelo, el PR no se crea y el run marca error.
- GitHub puede pedir revisión manual antes de ejecutar CI de PR creados por GitHub Actions.

## Prueba de extremo a extremo

Para probarlo se utiliza docs/CHAT_BRIDGE_SAMPLE.md, un archivo público específico para este puente. El issue creado desde ChatGPT debe provocar un run de GitHub Actions y un **PR en borrador**, que se inspeccionará sin fusionarlo.

Si la creación del issue falla (por ejemplo, issues desactivados) o no inicia el workflow, no se declarará el puente operativo. Se debe diagnosticar y corregir la causa.

## Pendiente después del piloto

- Generalizar a 2–3 archivos según la cuota de Groq.
- Controles por repositorio/proyecto antes de usarlo en Mayor Studio u otros.
- Envío de tareas largas y privadas por un canal autorizado no público, manteniendo costo cero cuando sea posible.
- Confirmación explícita antes de fusionar código y antes de publicar cambios.
