# DesignCraft directo desde ChatGPT usando Floot VM (28/10/2026)

## Resultado REAL: probado, sin Railway ni Render

La ruta funcional es **ChatGPT → conector Floot `run_code_in_vm` → Node.js/`child_process` → DesignCraft CLI v0.14.0 → MCP stdio → PDF/PNG/.designcraft → almacenamiento Floot**.

Pruebas efectuadas con la versión ARM64 oficial del release v0.14.0:
1. Descarga `designcraft-0.14.0-linux-aarch64.tar.gz` (118401111 bytes) en VM Linux ARM64 de Floot.
2. Extracción no privilegiada usando `tar --no-same-owner --no-same-permissions`.
3. Ejecución de `bin/designcraft-cli --help`, `--version`.
4. Ejecución de `designcraft-cli run --sample --export sample.pdf --page 0 --export sample.png`; PDF y PNG reales, cabeceras verificadas.
5. Inicio MCP stdio mediante `spawn(bin, ['mcp','--automation-read-root', workdir,'--automation-write-root', workdir])`.
6. MCP `initialize` con protocolo `2025-06-18`; herramientas confirmadas (`new_document`, `execute`, `open_document`, `save_document`, `export_png`, `inspect_document`, etc.).
7. Creación A4 mediante `new_document`, cinco `frame.create`, guardado `save_document` (11145 bytes), exportación PDF (8849 bytes) y PNG (96580 bytes).
8. Almacenamiento de los tres resultados con `_floot.storageUpload({filename,contentType,sizeBytes})` + PUT firmado.
9. En una segunda ejecución aislada, descarga del archivo nativo anterior, `open_document`, creación de un nuevo frame, `inspect_document`, guardado de versión 2 (12929 bytes) y exportación PDF v2 (8987 bytes). Resultados nuevamente alojados.

Rutas de demostración (públicas, **solo contienen texto de prueba, no datos privados**):
- `/_cdn/static/Prueba_DesignCraft_Autonomo.pdf`
- `/_cdn/static/Prueba_DesignCraft_Autonomo.png`
- `/_cdn/static/Prueba_DesignCraft_Autonomo.designcraft`
- `/_cdn/static/Prueba_DesignCraft_Autonomo_v2.pdf`
- `/_cdn/static/Prueba_DesignCraft_Autonomo_v2.designcraft`

En el ensayo, el almacenamiento se limitó a archivos demo sin datos de clientes, mediante un proyecto Floot existente; NO se modificó el código del proyecto ni ningún sitio publicado. El enlace CDN se obtiene al anteponer a la ruta `https://<project-id>.sandbox.floot.app`.

## LIMITACIONES (no ocultarlas)

- Floot Free tiene límite de 5 proyectos, ya alcanzado, y 100 MB de almacenamiento por cuenta. No se creó un proyecto nuevo ni se contrató plan.
- `run_code_in_vm` ejecuta una instancia **efímera** y admite un máximo de 120 s por invocación. El motor debe descargarse o recuperarse cada vez y el estado necesita guardarse fuera de la VM.
- Solo se ha demostrado una página de texto, no un catálogo final de 20 páginas con imágenes de Raíces, tipografías especiales, colores y preflight de imprenta.
- No se ha instalado un plugin MCP personalizado en ChatGPT: el control es a través del **conector Floot ya conectado**, que ejecuta el cliente MCP internamente.
- Evitar almacenar datos reales de clientes en espacios públicos de proyectos no relacionados. Utilizar almacenamiento privado o exportación protegida cuando se resuelva su transporte.
- La disponibilidad futura del método depende de los permisos, cuotas y uptime de Floot.

## Plantilla de ejecución

Dentro de `mcp__Floot__run_code_in_vm`:
- Usar `child_process.execFileSync('curl', ...)` para descargar release ARM64.
- `tar --no-same-owner --no-same-permissions -xzf ...`.
- `spawn(bin,['mcp','--automation-read-root',dir,'--automation-write-root',dir])`.
- Leer stdout por líneas JSON-RPC con `readline`, emparejar por ID; enviar `initialize` y luego herramientas `tools/call`.
- `new_document({preset:'A4',margins:40})`; `execute({command:'frame.create',params:{rect:[...],content:'text',text:'...'}})`.
- `save_document({path:'...designcraft'})`, `export_png({page:0,path:'...png'})`, `execute({command:'file.exportPdf',params:{path:'...pdf'}})`.
- Enviar archivos vía `_floot.storageUpload` y PUT.
- Para editar después: descargar el nativo a la VM, `open_document({path})`, editar, exportar y subir nueva versión.

La versión anterior de puente HTTP para Render/Railway se conserva solo como alternativa no desplegada. **No describirla como servidor funcionando.**
