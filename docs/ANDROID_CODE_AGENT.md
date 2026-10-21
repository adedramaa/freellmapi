# Agente Android con FreeLLMAPI (beta controlada)

Este agente se ejecuta en GitHub Actions desde un navegador Android: no requiere computadora personal, servidor adicional, ni una suscripción de IA. Está limitado al repositorio público **adedramaa/freellmapi**.

## Qué hace

Un trabajo iniciado MANUALMENTE puede:

1. Validar una instrucción y un archivo del repositorio SIN consumir tokens.
2. En modo **propose**, enviar una sola solicitud a FreeLLMAPI con el contenido de ese archivo.
3. Guardar la propuesta en una rama nueva, y crear un **pull request en borrador** para revisión humana.

No fusiona cambios, no ejecuta comandos proporcionados por el modelo y no modifica otros repositorios. Los runners estándar de GitHub son gratuitos en repositorios públicos, pero Groq y Render tienen límites gratuitos de uso.

## Configuración inicial (una sola vez)

1. Entrar en FreeLLMAPI > **Keys** y copiar su **clave API unificada** (no la de Groq, ni la de Hugging Face).
2. Abrir GitHub: Settings > Secrets and variables > Actions > **New repository secret**.
3. Nombre exacto: **FREELLMAPI_API_KEY**. Valor: la clave unificada. Guardar. **Nunca pegarla en una tarea, un issue, un archivo de código o este chat.**
4. En Settings > Actions > General > Workflow permissions, permitir **Allow GitHub Actions to create and approve pull requests** si aparece la opción. Esto permite crear el PR en borrador; el workflow no lo aprueba ni lo fusiona.
5. Conservar Render Auto-Deploy **Off**.

## Primera prueba sin claves ni llamadas a la IA

En GitHub, ir a **Actions > Android Code Agent (FreeLLMAPI) > Run workflow**, con rama **main**:

- operation: **validate**
- file: **client/src/components/getting-started.tsx**
- task: **Improve the readability of the first-steps card on a phone without changing its behavior.**
- model: **openai/gpt-oss-20b**

El trabajo debe mostrar "Validation passed". No genera código ni pull request.

## Primera propuesta

Repetir el procedimiento seleccionando **propose**. El agente consultará a FreeLLMAPI y, si hay una modificación válida, creará un PR en borrador.

Abrir el PR, leer el diff, esperar los checks de GitHub y SOLO DESPUÉS decidir si quieres fusionarlo. Render no se actualiza automáticamente.

## Límites de seguridad

- Solo permite modificar un archivo existente y pequeño (12 KB máximo) bajo **client/src** (.ts/.tsx/.css) o **docs** (.md).
- Bloquea nombres relacionados con credenciales, tokens, autenticación, privacidad y archivos ocultos.
- Rechaza respuestas vacías, demasiado grandes o reescrituras masivas.
- No admite tareas que requieran múltiples archivos, instalar dependencias, usar terminal o desplegar cambios.
- Cada llamada puede fallar si Render está dormido o se alcanzó el límite gratuito de Groq.
- Las instrucciones aparecen en el historial de GitHub Actions, así que no contienen datos privados.
- Una propuesta de IA puede contener errores o código inseguro: la revisión humana y las pruebas siguen siendo imprescindibles.

**Esto es un primer agente de edición restringida, no una sesión completa de Claude Code.** La ampliación a múltiples archivos y herramientas se hará después de comprobar este flujo seguro.
