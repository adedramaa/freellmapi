# DesignCraft autónomo — puente MCP protegido (prototipo)

**Estado:** código de integración y pruebas unitarias; instalación y funcionamiento del binario DesignCraft en nube **sin validar** hasta realizar un despliegue real.

Este gateway toma el MCP `stdio` oficial de DesignCraft y lo expone como MCP HTTP (`POST /mcp`) con autenticación Bearer. Cada servicio contiene **una sesión DesignCraft** y solo puede usar `/workspace/inputs` y `/workspace/output`.

## Componentes

- Dockerfile: Ubuntu 24.04, instala DesignCraft CLI **v0.14.0** del release oficial y ejecuta el puente.
- server.py: traduce JSON-RPC HTTP a `designcraft-cli mcp` stdio, devuelve JSON al cliente, serializa operaciones, aplica autenticación y límites de tamaño.
- Herramientas MCP extra: `gateway_save_asset`, `gateway_list_outputs`, `gateway_get_download_link`.
- `/healthz`: comprueba el proceso HTTP y presencia del CLI.
- `/download/{filename}?expires=...&signature=...`: entrega temporal de exportaciones con firma HMAC (20 minutos).

## Configuración

Generar un secreto aleatorio largo (no guardarlo en el repo): `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`.

Variables en la plataforma de alojamiento:

```text
MCP_BEARER_TOKEN=<secreto generado en la plataforma>
WORKSPACE_DIR=/workspace
DESIGNCRAFT_CLI=/usr/bin/designcraft-cli
MCP_TOOL_TIMEOUT=180
PUBLIC_BASE_URL=https://TU-SERVICIO.onrender.com
```

No establezcas `MCP_BEARER_TOKEN` como valor público en GitHub o en enlaces. Conéctalo únicamente a un cliente MCP remoto que pueda transmitir una credencial segura. Si el cliente no admite Bearer, configura OAuth con un proveedor confiable antes de abrirlo al público. **No elimines la autenticación.**

## Seguridad y operación

- No se permite ejecutar código arbitrario del sistema; los métodos JSON-RPC públicos están restringidos a los métodos MCP necesarios.
- DesignCraft inicia con banderas `--automation-read-root` y `--automation-write-root`, y solo tiene acceso explícito a los directorios de trabajo.
- Un solo cliente/usuario; no ejecutar múltiples réplicas. La sesión vive en memoria y **se pierde al reiniciar**.
- Render Free puede suspender el contenedor. Debe transferirse el archivo editable y los PDF tras cada trabajo, o agregarse almacenamiento persistente compatible.
- Los enlaces temporales de descarga son bearer links: cualquier persona que los obtenga antes de su expiración puede descargar el archivo. No compartirlos públicamente.
- Este prototipo no tiene OAuth ni almacenamiento duradero. No es una integración de producción lista para conectar sin pruebas.

## Pruebas

```bash
MCP_BEARER_TOKEN=$(python -c 'import secrets;print(secrets.token_urlsafe(48))') pytest -q
```

Las pruebas usan un servidor MCP simulado; **no prueban el ejecutable real**.

## Prueba real requerida

1. Construir el contenedor `docker build -t designcraft-autonomo .`.
2. Ejecutarlo con un `MCP_BEARER_TOKEN` secreto y un volumen de trabajo.
3. Invocar por HTTP `initialize`, `notifications/initialized`, `tools/list`, `tools/call`.
4. En DesignCraft, crear un cuadro de texto, guardar `.designcraft`, exportar `.pdf` y PNG.
5. Revisar la salida y confirmar los archivos descargables.
6. Configurar un plugin MCP personalizado en ChatGPT **solo si** tu plan permite acciones de escritura mediante MCP y admite la autenticación del gateway.

**Limitación de infraestructura:** Railway conectado no puede crear nuevos recursos actualmente: su prueba gratuita expiró. No convertirlo a un plan de pago sin autorización.