# Autónoma Dev — Implementación verificable, 23/10/2026

## Enlaces productivos
- Página comercial ARS (ES): https://autonoma-dev-agencia-v2.onrender.com/
- Página internacional USD/EUR (EN): https://autonoma-dev-agencia-v2.onrender.com/en/
- Bandeja de leads privada: https://autonoma-dev-agencia-v2.onrender.com/admin/
- Política de privacidad ES/EN: /privacidad/ y /en/privacy/
- API pública Neon: `agencialeads` en proyecto `cold-forest-36462352`.
- API privada Neon: `agenciaadmin` — verificación EdDSA JWT + admin_users allowlist (vacía hasta alta autorizada).
- Código: rama `agencia-autonoma-infra` dentro del repositorio temporal `adedramaa/freellmapi`. **Migrar a repositorio exclusivo privado** antes de producir software de clientes.

## Resultados probados
- Nuevo HTML/CSS/JS publicado en Render, sitios ES y EN, sitemap y privacidad accesibles.
- Formulario público a Neon: prueba HTTP 201 con USD/US y separación de importes; CORS 204, error 400 datos inválidos, 403 origen inválido y 429 duplicado.
- PostgreSQL: `agencia.leads`, `events`, `quote_drafts`, `client_communications`, `payments`, `payment_intents`, `admin_users`; triggers comerciales.
- Prueba sintética en `integration_test`: crea presupuesto USD como borrador sin monto aprobado, respuesta EN sin enviar, eventos. Marcada descartada.
- API privada: desplegada con token obligatorio. GET sin Origin autorizado devuelve 403, no entrega datos. **No existe ningún admin activo**, pendiente crear usuario y aprobar UUID.
- Flujo de cobro: no se registró ningún pago real, no se activó ninguna pasarela externa.
- Archivo `.github/workflows/agencia-autonoma-qa.yml`: verificaciones de seguridad y esquema de skills limitadas a rama agencia. **No existe prueba de que GitHub Actions lo haya ejecutado**; revisar que Actions esté habilitado.
- Códigos fuente API y scripts de navegador pasaron comprobaciones estáticas de sintaxis. No equivale a QA completo de producción ni a una prueba de inicio de sesión desde Android.

## Qué existe y qué NO
| Componente | Estado real |
|---|---|
| Sitio comercial ES/EN | Publicado y accesible |
| Formulario + persistencia + clasificación | E2E HTTP verificado |
| Borrador de presupuesto por consulta | Trigger probado |
| Borrador de respuesta ES/EN | Trigger probado; no enviado |
| Autenticación Neon y panel HTML | Provisionados y publicados; falta usuario aprobado y prueba de sesión real |
| Edición/revisión del presupuesto desde panel | Código publicado, pendiente prueba con usuario real autorizado |
| Seguimiento de pagos internacionales | Tabla y restricciones; cero conciliaciones habilitadas |
| Cobros ARQ/Binance/MP | NO conectados. No se inventaron APIs/webhooks |
| Factura E y régimen fiscal exportaciones | Validación fiscal con contador/banco del titular pendiente |
| Alertas autónomas de leads | NO activas; ChatGPT tiene cinco tareas existentes y rechazó agregar otra |
| Claude Code con 9 skills | Archivos instalados en repo; runner autónomo de proyectos pagados NO validado |
| Entrega al cliente y soporte | NO validados |
| Servicio $0 garantizado ilimitado | NO; proveedor sujeto a cuotas y gastos variables |

## Para habilitar dueño y dejar la bandeja accesible
1. Abrir `/admin/` desde Android. Crear cuenta personal usando contraseña **que no debe enviarse a ChatGPT**, y después ingresar.
2. Compartir **solo el ID de usuario** que muestra la interfaz. Una cuenta recién registrada no puede leer datos; por diseño la lista `agencia.admin_users` está vacía.
3. Autorizar en Neon **únicamente el ID confirmado por el titular del proyecto**; activar la fila `active=true`, `approved_at=now()`, `approved_by='owner' ` tras verificación adicional de identidad.
4. Completar configuración de Neon Auth de producción: validación de correo, SMTP propio, restricción de altas, deshabilitar localhost, dominios de confianza; después hacer pruebas de sesión, logout, JWT expirado, permisos y acceso desde Android.
5. Solo después comenzar a operar leads personales desde el panel.

## Cobros internacionales
- Potencial vía ARQ Finance: ACH doméstico US y SEPA EU según titular y tipo Personal/Business. ARQ Personal para actividad freelance permitida bajo términos; negocios legalmente registrados evalúan ARQ Business.
- Binance Pay: alternativa si el cliente acepta cripto; merchant/API sujeto a elegibilidad. No marcar pagado a partir de captura o QR.
- Mercado Pago AR: ruta principal local en ARS; crossborder requiere cuenta específica. `agencia.payment_intents` conserva moneda, provider, monto minor, referencia y requisitos para un estado verificado.
- Ningún tipo de cuenta, identificación fiscal o método de extracción ha sido verificado del usuario real. **No poner botón de pago ni iniciar automáticamente un proyecto**.
- Condiciones ARCA/BCRA/factura E y retiro al banco argentino deben validarse previamente, sin eludir obligaciones.

## Orden de ejecución recomendado
**1. Propietario y mensajería:** validar login y permisos; tener notificación al captar lead y copia de seguridad.
**2. Cotización profesional:** plantillas ES/EN, precio por moneda y proyecto, alcance, anticipo, contrato; todo editable y aprobado.
**3. Cobro real:** verificar titular ARQ o Merchant Binance, fiscal y conciliación. Pago verificado ≠ captura de pantalla.
**4. Ejecutar Claude Code:** repositorio privado dedicado por cliente, skills efectivas (no --bare), CI/QA independiente, tope de costos y PR aprobable.
**5. Entrega:** backups, deployment preview, aceptación, soporte, contrato, factura E cuando corresponda.
**6. Ventas:** SEO, portafolio real, adquisición ética, métricas de conversión y beneficio neto.

## Compilación y despliegue
- Neon Functions: los paquetes ZIP contienen `index.mjs`, runtime `nodejs24`; `DATABASE_URL` y `NEON_AUTH_*` son secretos/variables gestionados por Neon. Nunca poner conexión ni JWT en la web.
- Render estático: `srv-dbdn43m7bikc73e70420`, rama `agencia-autonoma-infra`, publish `agencia-autonoma/site`, autodeploy desactivado. Hacer despliegue manual solo después de QA.
- La versión antigua `autonoma-dev-agencia.onrender.com` redirige al sitio nuevo mediante HTML/JS; falta HTTP 301 de servidor y dejar de descargar el HTML legacy de Floot en el build.
- Cuentas y suscripciones nuevas NO autorizadas; no activar cargos sin autorización.

## Criterio de «100 %»
1. Cuenta propietaria puede entrar y recuperar una consulta real.
2. Respuesta y cotización revisada, enviada, contrato aceptado.
3. Pago real conciliado y factura válida.
4. Claude Code desarrolla en entorno separado con skills, revisión, QA y aprobación de deploy.
5. Cliente acepta entrega y se abre soporte; reconcilian ingreso, costo y beneficio.
6. Repetir el circuito sin fallos críticos y con datos de control completos.

La meta está en curso, **no terminada 100 %**. Esta bitácora impide que publicación de sitio, schema o skill se confundan con operación monetizable completa.
