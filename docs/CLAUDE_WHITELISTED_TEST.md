# Claude Code - ejecutar pruebas con un comando estrictamente permitido

## Propósito

Comprobar que Claude Code **real** (CLI oficial 2.1.296), mediante FreeLLMAPI/Groq, puede usar su herramienta Bash para ejecutar UN test en una carpeta temporal, sin permisos de escritura sobre GitHub, sin acceso a proyectos reales y sin recurrir a proveedores pagos.

Workflow: **Claude Code - Whitelisted Test Command** en GitHub Actions.

## Protocolo

1. CI de Pull Request verifica el código de auditoría, instala el CLI y ejecuta pruebas offline sin secretos.
2. En main, el primer intento de verificación se dispara automáticamente solo mediante un commit con prefijo de prueba autorizado. Después puede repetirse con workflow_dispatch.
3. Se crea un archivo temporal test_demo.py con una sola prueba básica de Python.
4. A Claude Code se le ofrece únicamente Bash; la regla --allowedTools autoriza SOLO el comando exacto python3 -m unittest test_demo.py, sin variantes ni concatenaciones. permission-mode dontAsk rechaza comandos fuera de la lista.
5. El verificador examina stream-json y exige UNA llamada Bash cuyo comando coincida exactamente, el tool_result correspondiente y fin de la sesión sin errores.
6. GitHub comprueba que no se añadieron archivos en la carpeta de prueba y que el repositorio continúa limpio. No se guardan logs del modelo ni claves como artefactos.

**Precaución:** la selección de herramientas del CLI no equivale a un sandbox de sistema operativo. Esta es una demostración controlada en un runner efímero, no una autorización para ejecutar Bash arbitrario en tus proyectos.

## Pendiente para llegar a la experiencia del video

- Un flujo de cambios con Claude Code sobre archivos reales, con PR en borrador y aprobación.
- Un puente autorizado desde ChatGPT hasta el runner para que las tareas iniciadas aquí no exijan iniciar GitHub Actions en Android.
- Tests de edición multiarchivo y manejo de fallos de cuota gratuita sin cambiar silenciosamente de proveedor.
- No desplegar cambios en Render hasta aprobación separada.
