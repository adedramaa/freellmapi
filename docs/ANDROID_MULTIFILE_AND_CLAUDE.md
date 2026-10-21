# Etapa 2: varios archivos y Claude Code oficial

Se utiliza desde Android, sin PC. El objetivo final es enviar instrucciones desde ChatGPT a Claude Code AUTÉNTICO en la nube con FreeLLMAPI/Groq, pero esa compatibilidad todavía no está demostrada.

## Agente multiar­chivo intermedio (NO es Claude Code)

Abrir Actions > Android Multi-file Agent (FreeLLMAPI).

1. Run workflow, rama main y operación validate primero (no utiliza IA ni secretos).
2. Introducir exactamente 2 o 3 archivos existentes separados por comas, por ejemplo:
   client/src/components/getting-started.tsx,client/src/lib/composer-geometry.ts
3. Introducir una tarea pública, breve y específica, que afecte únicamente esos archivos.
4. Tras superar validate, seleccionar propose para pedir una propuesta a FreeLLMAPI con el modelo openai/gpt-oss-20b.
5. Revisar el Pull Request generado en borrador, autorizar CI si GitHub lo solicita, y decidir separadamente si fusionarlo. Render tiene Auto-Deploy desactivado.

### Controles

- De 2 a 3 archivos, máximo 9 KB cada uno y 20 KB en conjunto.
- Solo código TS/TSX/CSS dentro de client/src o Markdown dentro de docs.
- No permite editar servidor, directorio .github, credenciales, archivos ocultos ni scripts de despliegue.
- Parches JSON con sustituciones exactas, hasta cuatro por archivo y cambios acotados a 35 líneas por archivo / 70 en total.
- Rechaza archivos no solicitados, JSON inválido, sustituciones ambiguas, resultados parciales, rutas fuera de alcance y archivos no rastreados.
- Primero valida TODOS los cambios y solo después escribe. No ejecuta comandos del modelo ni fusiona, despliega o publica.
- Las instrucciones en GitHub Actions son públicas: no incluir secretos ni datos privados.
- El código de un modelo no es fiable por defecto. Inspeccionar siempre el diff y los resultados CI.

## Claude Code oficial: prueba independiente

Abrir Actions > Claude Code - Official CLI Compatibility.

- Opción install_only (predeterminada): instala el paquete oficial @anthropic-ai/claude-code versión 2.1.296 y ejecuta claude --version. No utiliza un modelo ni autentica ni modifica código.
- Opción gateway_probe (SOLO si se elige): intenta una respuesta breve mediante el formato Anthropic Messages de FreeLLMAPI, con la clave unificada ya guardada como secreto. No utiliza credenciales de proveedores pagos.
- Los modelos gratuitos de Groq pueden ser incompatibles con las expectativas de Claude Code para herramientas, streaming, metadatos o nombres de modelo. Hasta validar respuestas reales y herramientas, no considerar el puente terminado.
- Render Free duerme por inactividad y Groq impone límites de cuota. Cero facturación no significa disponibilidad garantizada.

## Criterios reales de finalización

1. Instalar y ejecutar Claude Code REAL en la nube.
2. Probar su conexión con FreeLLMAPI/Groq sin pagar.
3. Probar que Claude Code lea/edite archivos y ejecute pruebas de verdad, de manera aislada.
4. Conectar órdenes enviadas desde ESTE chat al runner, con permisos, auditoría y revisiones de PR.
5. Reutilizarlo en proyectos aprobados sin PC, sin modificar otros proyectos sin autorización.

El agente multiar­chivo de esta etapa es un recurso transitorio de seguridad y automatización; NO debe presentarse como Claude Code.

## Incidencia real del primer gateway_probe (21/10/2026)

La instalación del CLI oficial funcionó. La petición llegó a FreeLLMAPI por la ruta Anthropic Messages, pero Render informó que Groq tenía un límite de 8000 tokens/minuto y que Claude Code solicitaba aproximadamente 16117. El mensaje del CLI sobre "Request too large (max 32MB)" era engañoso para este caso: la pasarela NO probó un error real de tamaño de 32 MB ni llegó a ejecutar el modelo upstream.

El primer script usaba --allowedTools "", que cambia los permisos de uso, pero no elimina los esquemas de herramientas del contexto. El diagnóstico corregido usa --tools "" para desactivar las herramientas, --bare y un system prompt mínimo. Así se ensaya SOLAMENTE la respuesta textual de Claude Code auténtico a través de FreeLLMAPI, dentro del límite gratuito si el prompt cabe.

Para evitar un paso de móvil adicional, este cambio incluye una única ejecución en push a main, estrictamente acotada al mensaje de commit previsto, y luego se conserva la activación manual habitual. No se añade una clave de Anthropic ni un servicio pago. Aunque responda OK, las herramientas reales de lectura, escritura y tests seguirán pendientes de verificación.
