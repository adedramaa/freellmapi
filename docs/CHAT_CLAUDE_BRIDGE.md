# Puente directo: ChatGPT → Claude Code oficial → Pull Request

## Funcionamiento

Desde este chat, una instrucción pública crea un archivo de solicitud nuevo en la rama `claude-requests` del repositorio conectado `adedramaa/freellmapi`. Un `push` a esa rama inicia GitHub Actions. Claude Code REAL se ejecuta en un runner efímero, utiliza FreeLLMAPI/Groq, modifica únicamente el archivo permitido y devuelve un **Pull Request en borrador**, que requiere revisión humana.

**No es un sistema que pueda editar cualquier proyecto o procesar datos privados.** Es el piloto de comunicación con Claude Code real, sin PC.

## Enviar tarea desde ChatGPT

1. Pídele a ChatGPT que utilice Claude Code para modificar un archivo público conocido de FreeLLMAPI (por ejemplo, `docs/CHAT_BRIDGE_SAMPLE.md`).
2. ChatGPT crea directamente mediante su conexión GitHub un archivo único en la rama `claude-requests`, bajo la ruta `.claude-requests/task-YYYYMMDD-IDENTIFICADOR.json`.
3. La confirmación del commit debe comenzar exactamente con `claude-task: `, seguido de JSON con SOLO `file` y `task`. Ejemplo de mensaje de commit:

    claude-task: {"file":"docs/CHAT_BRIDGE_SAMPLE.md","task":"Improve one explanatory sentence, preserving the heading and other text."}

4. GitHub limita la automatización a un solo nuevo archivo de solicitud por commit, creado desde la cuenta propietaria, sin cambios extra. Las tareas ajenas se rechazan antes de enviar nada a Groq.
5. El workflow `ChatGPT to Claude Code - Authorized Task Branch` lee el commit, valida la instrucción, instala Claude Code oficial, permite solo `Read` y `Edit`, comprueba los eventos reales y el archivo modificado.
6. Un segundo job, **sin la clave de FreeLLMAPI**, verifica de nuevo el artefacto y crea un Pull Request **en borrador** contra `main`.
7. ChatGPT revisa el PR y las pruebas; solo con aprobación separada se fusiona, y Render nunca se despliega automáticamente.

## Restricciones verificadas

- Las instrucciones y archivos de solicitud son PÚBLICOS. No compartir contraseñas, datos privados, nombres de clientes o información confidencial.
- Solo una ruta de archivo existente menor de 4500 bytes, dentro de `client/src` (.ts/.tsx/.css) o `docs` (.md), con exclusiones de credenciales y autenticación.
- Tarea de 12–350 caracteres; máximo 35 líneas modificadas; respuesta de menos de 6000 bytes; cero archivos no solicitados.
- Los permisos de escritura de GitHub pertenecen únicamente al job de publicación. Claude Code se ejecuta en otro runner, con checkout sin credenciales persistentes y permiso de solo lectura.
- El único resultado permitido es un PR en borrador. Sin Bash para el agente, sin instalaciones de paquetes desde sus instrucciones, sin auto-merge ni Auto-Deploy de Render.
- Fallos de red, límites de Groq o errores del modelo detienen la ejecución; no se cambia a una API paga.
- GitHub Actions puede exigir autorización manual de CI para PR creados por bots.

## Piloto de extremo a extremo

El archivo `docs/CHAT_BRIDGE_SAMPLE.md` está creado únicamente para verificar esta cadena. El criterio de éxito es: **mensaje en ChatGPT → commit de tarea vía conexión GitHub → GitHub Actions → Claude Code Read/Edit reales → PR nuevo en borrador**.

La rama `claude-requests` mantiene registros públicos de las solicitudes. Por ahora el puente acepta solo una petición pequeña por ejecución; más adelante ampliaremos varios archivos y repositorios, y estudiaremos un canal privado sin costo.
