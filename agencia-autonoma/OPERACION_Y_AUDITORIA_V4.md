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

## Auditoría incremental posterior — 23/10/2026

- Panel móvil: `/admin/` ahora solicita JWT mediante `auth.getJWTToken()` del SDK oficial de Neon. Añadidos alcance, entregables, exclusiones, duración, revisiones y aprobación interna del presupuesto; edición restringida a admin permitido. Los envíos externos siguen manuales. Incluye abrir borrador por `mailto:` y exportar las 100 últimas consultas visibles en CSV (este archivo NO es backup integral).
- API privada `agenciaadmin` redeploy completado; HTML de panel publicado por Render. Nunca aparece una cuenta dueña predeterminada.
- Pruebas unitarias manuales con falsos objetos de Request/Response: 12/12 validaciones de rechazo de inputs, CORS y falta de autenticación superadas. Es distinto de 12 sesiones reales de producción.
- PostgreSQL añade `agencia.work_orders` y `agencia.work_order_events`. También se reforzó `agencia.payment_intents` (moneda+importe igual al presupuesto aprobado; transiciones restringidas; comprobantes/documentación cuando corresponda) y la función `agencia.guard_lead_lifecycle` (solo producción con orden y pago verificados, entrega con QA firmado).
- Prueba reversible contra Neon completó una simulación de flujo de una orden de prueba: lead→presupuesto→pago sintético marcado para QA→orden→plan→desarrollo→QA→aprobación→entrega. Bloqueó orden sin pago y salto a QA sin evidencia. **Se revirtieron todas las inserciones**: 0 intentos de pago reales/0 órdenes/0 leads de esa prueba.
- Backup de estructura de reglas: `sql/snapshot-triggers-2026-10-23.sql`; no incluye secretos ni datos reales.
- CI GitHub Actions de agencia sigue sin ejecuciones observadas; no se debe declarar ejecutor Claude Code validado.
- Estado última consulta a Neon: 0 administradores activos, 0 leads comerciales, 0 payment intents, 0 work orders, 0 comunicaciones enviadas.

### Porcentaje estimado al final de esta intervención

**40 % implementado / 60 % pendiente**, estimación operativa orientativa. El cálculo no es telemetría: web y captación están mayoritariamente terminadas, pero autenticación real del propietario, avisos, facturación y cobro, ejecución autónoma Claude Code, entrega certificada, marketing y ventas aún no cumplen criterios de aceptación.

### Bloqueantes directos

1. Propietario debe crear su cuenta en `https://autonoma-dev-agencia-v2.onrender.com/admin/` y confirmar su UUID; autorizarla solo con evidencia segura. No pedir contraseña en chat.
2. Neon Auth: verificación de correo, SMTP y localhost para producción; probar sesión real y autorización de primer usuario.
3. Cobros: tipo de ARQ Personal/Business, Binance Merchant si aplica, habilitación MP y obligaciones ARCA/BCRA, verificación independiente de transacciones.
4. Runner Claude Code aislado y autorizado con 9 skills realmente cargadas, tests y PR, sin permitir despliegues autónomos no aprobados.
5. Avisos de leads: 5/5 automations del usuario ocupadas; configurar alternativa autorizada sin sustituir recordatorios ajenos. Servicio de email verificado.

## Ronda de ejecución — 23/10/2026 17:55 UTC

- **Corregida compatibilidad de Neon Auth:** el panel anterior llamaba `auth.getJWTToken()` (no compatible con el cliente `createAuthClient`). Ahora utiliza `auth.token()` con `fetchOptions.credentials='include'`, de acuerdo con la guía oficial de Managed Better Auth. Limitación: cookies de terceros pueden estar bloqueadas en ciertos navegadores; no se ha verificado sesión real del dueño en Android.
- **Cotización lista para revisar y enviar manualmente:** tras aprobación interna se prepara una propuesta bilingüe con monto, moneda, alcance, entregables, exclusiones, días y revisiones, con copiado o borrador de email manual. No se manda nada automáticamente.
- **Deploy Render comprobado:** servicio web `srv-dbdn43m7bikc73e70420` despliegue `dep-dbdpuvt9fdbs7388tabg` estado `live`, commit `c948a30433b39e0257bb2c3c8d1e124365d7c76d`.
- **Seguridad funcional:** scripts del panel analizados por sintaxis; comprobado `auth.token()` y `credentials:'include'` en fuente publicada. Los ensayos previos de 12/12 casos con objetos simulados no sustituyen un test de sesión autenticada.
- **Antispam concurrente:** preparada tabla `agencia.lead_submission_locks` para futuro control de repetición por correo sin texto en claro; **no está conectada a la API aún**, por tanto no atribuirle protección efectiva.
- **Notificaciones:** intento de configurar alerta mientras panel abierto no se integró y sigue pendiente; no hay avisos push o email automáticos.
- **Estado último Neon:** cero administradores activos, cero leads comerciales reales, cero solicitudes de pago y cero órdenes. Dos Neon Functions activas (`agenciaadmin`, `agencialeads`).
- **CI de GitHub:** no existen ejecuciones validadas del workflow dedicado a agencia. No se ha entregado proyecto hecho por Claude Code bajo este flujo.

### Reestimación de avance al cierre de esta ronda

**42 % operativo estimado / 58 % por completar.** Se concede una mejora pequeña (2 puntos) por subsanar método de autenticación y publicar preparación de propuesta comercial. Es una escala de avance ponderada y subjetiva, **no** porcentaje de calidad ni prueba de venta. Las tres compuertas imprescindibles continúan: dueño autenticado, cobro real/facturación, Claude Code independiente y entrega. No existe garantía de ingresos o costo cero ilimitado.

## Auditoría incremental — 23/10/2026 18:28 UTC

### Implementado y verificado en esta intervención
- **Monitoreo programado autónomo de Neon:** función `agenciamonitor` desplegada en la branch exclusiva `br-falling-night-b57zpkln`; disparador `trigger-54bd27f4-fd91-4f72-a008-4c87acd4432e`, calendario UTC `0 * * * *`, activo. Respeta el apagado de compute de Neon. No ocupa cupos de tareas ChatGPT; sí consume cuota mensual de Neon.
- El registro `agencia.monitor_snapshots` conserva cada hora fecha, web accesible, API saludable y número de consultas sin gestionar. No guarda correos ni nombres de clientes. Primera ejecución comprobada: `2026-10-23T18:25:02Z`, `website_ok=true`, `backend_ok=true`, `pending_leads=0`.
- **Se reparó un falso negativo durante la prueba:** el monitor buscaba una palabra que no aparecía al comienzo de la página; se cambió por el título correcto, verificando después web/API ambos OK.
- **Panel protegido:** añadido el estado del monitor (visible únicamente después de autenticar y autorizar al propietario). `agenciaadmin` versión activa 4 devuelve snapshot vía `GET /api/admin/metrics`, protegido por Neon JWT y lista autorizada.
- **Chequeo de nuevas consultas con panel abierto:** se añadió lectura de métricas cada cinco minutos solamente mientras la pestaña esté visible y la sesión iniciada. **No es alerta push permanente ni correo de fondo**.
- **Web publicada:** Render `srv-dbdn43m7bikc73e70420`, despliegue `dep-dbdqdsnf3r2c73bmvss0` estado `live` para cambios del panel. Validación local de sintaxis JavaScript `PASS`.
- **Pruebas y datos reales:** 3 Neon Functions desplegadas: `agencialeads`, `agenciaadmin`, `agenciamonitor`. 0 administradores autorizados, 0 leads comerciales reales, 0 órdenes, 0 intentos de pago. Sin clientes ficticios sin descartar.
- **Repositorio sigue compartido y público** (`adedramaa/freellmapi`); antes de programar proyectos de clientes, crear un repositorio privado independiente. No guardar secretos ni código privado del cliente en él.
- Existe la tabla `agencia.lead_submission_locks`, pero el intento de integrarla al endpoint público fue rechazado por el entorno de herramientas. **No se debe afirmar que la protección de concurrencia está activa**; se mantienen controles de spam básicos anteriores.
- Aun no se ha demostrado inicio de sesión de propietario en Android, emails de aviso, conciliación ARQ/MP/Binance, factura E, ni Claude Code produciendo software para cliente.

### Porcentaje al cierre de esta ronda
**44% estimado implementado; 56% restante**. Es una puntuación ponderada de preparación, no porcentaje medido de disponibilidad ni ganancias. Distribución: web y captación 18/20, panel/comercial 9/15, presupuestos 10/15, cobros/fiscalidad 2/15, Claude 1/20, QA/entrega/monitoreo 4/10, ingresos comprobados 0/5.

### Siguientes compuertas reales
1. Autorizar a un propietario real en Neon Auth para que el panel deje de estar bloqueado (no compartir contraseñas).
2. Configurar correo transaccional o push opt-in legítimos para alertas incluso con el panel cerrado, con cuota gratuita verificada y protección de datos.
3. Corregir y probar deduplicación concurrente y CAPTCHA/cota por dirección IP sin bloquear usuarios legítimos.
4. Verificar y vincular medio de cobro aceptado para persona/empresa en Argentina y exterior; factura E y requisitos BCRA/ARCA.
5. Runner de Claude Code con roles cargados de verdad, presupuesto de ejecución, repos privados y aprobación humana.
6. Ejecución de una venta/producción/entrega real y seguimiento de costes.

## Ronda 23 de octubre de 2026, aproximadamente 20:15 UTC — control de concurrencia y cobros preliminares

### Cambios comprobados
- **Deduplicación real en Neon**: `agencialeads` despliegue **5** activo. La recepción usa `agencia.lead_submission_locks` para bloquear por hash SHA-256 del correo durante quince minutos con `INSERT ... ON CONFLICT ... WHERE`. Conserva también el límite general de solicitudes. El hash no equivale a anonimización irreversible; controlar acceso y retención.
- **Prueba de concurrencia HTTP**: una función temporal `agenciaprobe` lanzó dos `POST /api/lead` simultáneos para el mismo correo sintético. Resultados exactos: **201 y 429**; una sola `agencia.quote_drafts` creada. El registro fue marcado `integration_test/descartado`, se borró la fila de bloqueo de la prueba y se eliminó la función temporal. No atribuir como cliente real.
- **Limpieza periódica**: la función `agenciamonitor` despliegue **3** tiene código para purgar hashes antiguos tras 24 horas. Su siguiente ejecución pendiente no fue verificada aún con una muestra expirada.
- **Borrador de solicitud de pago**: se agregó `POST /api/admin/payment/prepare` a `agenciaadmin` despliegue **5**, protegido por JWT y lista explícita de administrador. Permite solo crear un registro `draft` para un presupuesto aprobado y completo; USD→`arq_ach`, EUR→`arq_sepa`, ARS→`mercadopago_ar`. Índice parcial único impide más de un borrador de pago activo por presupuesto.
- **Prueba PostgreSQL reversible**: un presupuesto sintético con importe y alcance permitió **un** borrador de pago, bloqueó el intento duplicado y no creó un pago `verified`. La prueba se revirtió: cero leads y cero pagos sintéticos persistentes. No hubo llamadas bancarias ni validación externa de ARQ/MP.
- **Panel privado**: código actualizado permite al titular preparar un borrador interno de pago (solo después de aprobación), mostrando advertencias de elegibilidad fiscal y ausencia de cobro. Render despliegue `dep-dbdrvlt9fdbs738ff2t0` estado `live`, commit `4ea40904e14ec896421683c57e123aa9155c2d67`. Neon `agenciaadmin` despliegue 5 activo.
- **Salud pública**: GET `/health` devuelve `ok=true,database=verified`, página /en/ y /admin/ accesibles.
- **Recuperación**: esquema auxiliar guardado en `agencia-autonoma/sql/security-and-draft-schema-2026-10-23.sql`. El script NO es un backup completo ni sustituye el esquema principal.

### Límites aún abiertos
- **Neon cron programado no equivale a alerta garantizada:** hay snapshot correcto de web y backend a **19:00 UTC**, pero no se observó ejecución a **20:00 UTC** aunque el disparador indica siguiente ejecución 21:00 UTC. Investigar posibles omisiones de programación y añadir supervisión redundante antes de prometer avisos de fondo. El monitor no envía emails ni push.
- No hay propietarios activos en `agencia.admin_users`; no se pudo verificar login real, apertura de CRM, ni los nuevos controles con una sesión real desde Android.
- No hay ningún cliente real ni ingresos; ARQ, Binance, Mercado Pago, contabilidad y factura E no están conectados o verificados.
- El ejecutor Claude Code con nueve skills y repositorio aislado privado no está validado. La base GitHub sigue siendo compartida y pública; no subir proyectos privados de clientes.
- La API de formularios aún requiere protección contra abuso de múltiples correos, control por IP o CAPTCHA y revisiones de privacidad.
- El asistente no ha comprobado GitHub Actions CI ejecutando el workflow de la agencia.

### Evaluación operativa y nueva prioridad

**46% estimado completo, 54% restante**, ponderado por capacidad de recibir, procesar, cobrar, construir, probar y entregar un proyecto. Solo +2 puntos sobre la auditoría anterior de 44%: +1 por corrección de concurrencia probada vía HTTP y +1 por la preparación de pagos sin transacciones financieras. El monitor omitió una ventana prevista, por tanto no aumenta la puntuación de avisos confiables.

**Próximos bloqueos en orden:** confirmar y autorizar identidad del titular; asegurarse de alertas fiables y backups; establecer modalidad fiscal y cobro habilitado; preparar runner Claude Code privado con límites de costo y skills realmente usadas; validar QA y primera entrega rentable.

## Auditoría incremental — 23/10/2026 20:27 UTC: aceptación del cliente y resguardo de cobros

### Pruebas e implementación terminada

- Se añadió `agencia.client_acceptances` para registrar por presupuesto referencia de aceptación, canal, fecha, usuario autorizante, moneda e importe aceptados. Este es un **registro manual**, no reemplaza firma digital certificada ni prueba de cobro.
- Las funciones PostgreSQL `agencia.mark_quote_sent_manual` y `agencia.register_client_acceptance` validan orden y evidencia, registran eventos y bloquean duplicados. El estado `leads.aprobado` ahora requiere propuesta en estado `enviado` y aceptación registrada con moneda e importe coincidentes.
- La API administrativa `agenciaadmin` desplegada versión **6** dispone de `POST /api/admin/quote/mark-sent` y `POST /api/admin/quote/accept`, bajo JWT de Neon y `admin_users.active`. La ruta de preparación del pago también exige `lead.status='aprobado'`, propuesta enviada y aceptación.
- El disparador `agencia.guard_payment_intent` aplica las restricciones incluso a inserciones SQL directas: no se puede preparar un pago para una propuesta no enviada, no aceptada o sin importe en la moneda acordada. Estado `verified` sigue requiriendo referencia y documento, **sin integración bancaria automática**.
- **Prueba SQL reversible**: bloqueó un borrador de pago antes del envío, bloqueó otro tras el envío pero antes de la aceptación, permitió registrar manualmente aceptación válida y generar solo el borrador de pago. Todos los registros sintéticos revertidos: 0 aceptaciones, 0 pagos y 0 leads nuevos reales al final.
- Nuevos pasos del panel móvil: marcar envío de propuesta con referencia, registrar aceptación del cliente con referencia y canal email, y solo después mostrar preparación del borrador de pago. El propietario debe confirmar expresamente ambos hechos: no se envía un email por sí solo.
- Neon Auth compartido incluye proveedor Google; se añadió botón optativo de ingreso con Google. Se mantiene la lista de administradores vacía por defecto y **no se validó una sesión real de usuario desde Android**. Configuración de Neon Auth aún permite localhost y no exige verificación de email por contraseña: revisar antes de considerar acceso listo para producción.
- **Publicación confirmada:** Render servicio `srv-dbdn43m7bikc73e70420`, despliegue `dep-dbds658ae00c73aqvhdg`, estado `live`, commit `8ee48e6ca3cd36da3e86e331bff2c1dc2764fa06`. Neon admin API versión 6 `completed`. Archivos JS pasan revisión de sintaxis. La consulta no autorizada directa a `/api/admin/leads` devolvió HTTP **403**, sin exponer datos.
- Código de recuperación en `agencia-autonoma/sql/manual-client-acceptance-2026-10-23.sql` y `agencia-autonoma/sql/payment-evidence-guard-2026-10-23.sql` (no incluyen datos ni secretos).

### Estado real y porcentaje

Contadores Neon: **0 administradores activos, 0 consultas reales, 0 aceptaciones de cliente reales, 0 pagos, 0 órdenes de trabajo**. Las 3 Functions siguen activas y el cron horario sigue configurado; persiste la necesidad de validar alerta fiable mientras el panel está cerrado, y de revisar una ventana omitida de monitoreo.

**Avance general estimado: 48% completo y 52% pendiente** frente al 46% previo. Dos puntos extra por un circuito de aprobación/aceptación y control de pagos mejor resuelto y probado, sin atribuir crecimiento comercial, cobros ni autonomía Claude Code que aún no existen. Distribución: web 19/20, panel 10/15, propuestas 11/15, cobros 3/15, Claude 1/20, QA/entregas/monitoreo 4/10, ingresos 0/5.

### Bloqueos siguientes

1. El titular debe registrar una cuenta propia en `/admin/` (Google opcional) y demostrar la identidad antes de insertar su UUID en `admin_users`; prohibido transmitir contraseñas en chat.
2. Probar de verdad el panel autenticado en Android, recuperar un lead y ejecutar los tres pasos comerciales con cuenta dueña autorizada.
3. Configurar autenticación de correo verificada, restricciones de origen para Neon Auth, protección anti-spam e historial de auditoría de cambios.
4. Integrar mensajería transaccional/avisos cuando la pestaña esté cerrada, sin superar cuotas ni sustituir tareas existentes de ChatGPT.
5. Validar ARQ personal/empresarial, MP y/o Binance Pay con titular, documentación, impuestos, factura E y conciliación externa. Nunca marcar pago solo por captura.
6. Preparar repositorio privado por cliente y corredor seguro Claude Code que ejecute skills y pruebas reales, con aprobación humana y tope de consumo.
7. Obtener clientes legítimos, medir costo y cerrar primera entrega verificable.

## Ronda 23/10/2026 ~21:22 UTC: handoff seguro hacia futuro ejecutor Claude

### Cambios efectivamente desplegados
- PostgreSQL implementó `agencia.build_work_spec(quote_id)`: genera una especificación **solo a partir de una propuesta enviada y aceptada por el cliente**, con alcance, entregables, exclusiones, plazo, revisiones y bandera explícita de pago verificado. No devuelve campos directos de nombre/correo del cliente; el texto libre AÚN puede contener información personal y necesita revisión. Todas las especificaciones declaran `execution_authorized=false`.
- PostgreSQL implementó `agencia.prepare_paid_work_order(quote_id,user_id)`: requiere administrador activo, aceptación documentada y pago marcado `verified` con evidencias. Solo crea orden en estado `blocked`; no ejecuta Claude, ni publica ni autoriza gasto. Índice parcial evita duplicar órdenes activas por cotización.
- **Prueba transaccional reversible contra Neon:** rechazó usuario sin aprobación, rechazó orden sin pago verificado, preparó una sola orden **bloqueada** tras evidencia de pago exclusivamente sintética y rechazó duplicado. Revirtió todos los datos: 0 admins ficticios, 0 órdenes, 0 transacciones.
- Neon Function `agenciaadmin` **despliegue 7 `completed`** publica (solo después de JWT + administrador permitido) `GET /api/admin/work-spec?quote_id=...` y `POST /api/admin/work-orders/prepare` con confirmación `confirm_blocked=true`; ambos con barreras SQL. Ninguna API invoca modelos o pagos externos.
- Panel móvil publicado en Render servicio `srv-dbdn43m7bikc73e70420`, deploy `dep-dbdt018m7kps73bjneq0`, `live`, commit `dd42536c8568cea1655e8b7f9c39e18bbd0afe43`. Permite ver especificación técnica tras aceptación y registrar orden bloqueada si pago está verificado. Se corrigió advertencia: el alcance libre podría contener datos personales aunque se omitan los campos de contacto.
- Código SQL versionado en `agencia-autonoma/sql/claude-handoff-2026-10-23.sql` (restauración sujeta a esquema base probado).
- `agencia-autonoma/runner/compile-handoff.mjs`: compila un handoff **offline y sin ejecución**, asegurando permisos de propietario, repositorio privado, revisión independiente QA, habilidades declaradas, ausencia de autodeploy y de acceso a secretos. Bloquea correos, API keys y posibles identificadores sensibles en texto libre.
- **13/13 comprobaciones locales** ejecutadas sobre el compilador (V8), incluyendo intento de alteración de banderas de ejecución, inyección de instrucciones como texto no confiable, falta de pago, repositorio público, faltantes de QA y fuga de secretos. Pruebas de Node test registradas en `compile-handoff.test.mjs`; workflow `agencia-autonoma-qa.yml` actualizado para ejecutarlas. **GitHub Actions todavía no tiene una ejecución de ese flujo confirmada**, por lo que no se debe atribuir éxito CI.
- Sitios `/admin/`, `/en/` y API pública `/health` siguen accesibles; estado de salud: `database=verified`. Última muestra cron registrada 21:00 UTC, web/API `true`.
- Registro final: **0 administradores propietarios activos**, **0 clientes reales**, **0 pagos**, **0 pedidos**.

### Límites y riesgos abiertos
- **No existe todavía ejecutor Claude Code para pedidos reales.** El compilador de especificaciones es una etapa previa, sin conexión a API AI, sin habilidad cargada en proceso real, sin checkout, sin PR de cliente ni despliegue.
- El código sigue dentro de la rama de un repositorio GitHub compartido y PÚBLICO. Es fundamental aislar cada proyecto de cliente en un repositorio privado con límites, permisos y costos autorizados antes de ejecutar agentes.
- La cuenta propietaria Neon Auth todavía no está registrada/autorizada ni probada en Android; esto impide operar el panel real desde la sesión del dueño.
- ARQ/Binance/MP, facturación, fiscalidad de exportación, conciliación externa, avisos con pestaña cerrada y entrega/soporte siguen pendientes de verificación.
- La limpieza antiabuso/monitoreo no equivale a un servicio de alertas de disponibilidad garantizada. Verificar ejecuciones faltantes y mantener alternativas.

### Puntuación operativa ajustada
Estimación **51% implementado, 49% pendiente**, calculada sobre el objetivo operativo completo (no estadística de producción, calidad o ingresos).
Distribución: web/captación 19/20; panel/CRM 11/15; cotizaciones 11/15; cobros/fiscalidad 3/15; Claude 2/20; QA/entrega/monitoreo 5/10; ventas 0/5 = **51/100**.
Creció 3 puntos sobre el 48% anterior gracias a una interfaz adicional en el panel, especificación de trabajo segura y ensayos de validación. Este avance **no presume clientes ni ingresos**.

### Condiciones exactas del siguiente gran incremento
1. Alta verificada del propietario (sin compartir contraseña) y ensayo de toda la bandeja móvil con rol autorizado.
2. Repo privado separado, credenciales para Claude Code apropiadas y ejecución autorizada con límites de herramientas/costo, skills cargadas, PR y pruebas.
3. Cobro internacional legítimo, conciliación verificable, cumplimiento ARCA/BCRA y factura correspondiente.
4. Envío de propuesta y comunicaciones legalmente consistentes; soporte, backups, reversión y entrega demostrada.

## Auditoría incremental — 23/10/2026 ~21:30 UTC: contratos inmutables, control de ejecución y ejemplo real de generación estática

### Cambios instalados y comprobados
- **Contrato congelado tras envío:** `agencia.guard_quote_contract` bloquea cambios directos de precio, moneda, alcance o estado de una propuesta `enviado` y su eliminación accidental. Las propuestas `aprobado` requieren precio, moneda y alcance completos; al enviar se registra `sent_at`. Esta protección complementa, pero no reemplaza, una firma o un acuerdo externo.
- **Aceptación append-only:** `agencia.guard_client_acceptance` impide registrar una aceptación antes del envío, o con importe/moneda distintos; tras su creación no permite ediciones ni borrados ordinarios. Necesita política de retención y procedimientos excepcionales para derechos de eliminación de datos de clientes.
- La **prueba SQL reversible** verificó: aceptación prematura rechazada, mutación de precio enviado rechazada, mutación de alcance rechazada, aceptación posterior válida, modificación de la aceptación rechazada, borrado de aceptación rechazado y borrado del presupuesto enviado rechazado. Transacción revertida: 0 registros comerciales nuevos.
- En `agencia.work_orders` se añadieron `private_repo_checked_at`, `private_repo_checked_by`, `execution_approved_at`, `execution_approved_by`, `max_ai_cost_usd_cents` y `run_expiry_at`. `guard_work_order` exige esos datos para salir del estado bloqueado, verifica formato owner/repo, cap de gasto y autorización limitada a 24 horas; exige cotización efectivamente enviada.
- **Prueba reversible de ejecución:** no permitió avanzar de `blocked` a `plan_ready` sin aprobación y revisión de repositorio; lo permitió tras atestaciones sintéticas y tope de costo 0, y volvió a rechazar `building` con autorización vencida. Las verificaciones de privacidad del repo son atestaciones humanas, **no comprobaciones externas de la API de GitHub**. Se revirtió toda la prueba: 0 órdenes y 0 administradores sintéticos persistentes.
- Resguardos SQL versionados en `agencia-autonoma/sql/immutable-accepted-contract-2026-10-23.sql` y `agencia-autonoma/sql/execution-approval-gate-2026-10-23.sql` (no contienen secretos).
- **Generador independiente de página estática:** `runner/site-generator.mjs` crea un ejemplo HTML autocontenido, móvil, accesible básico y con HTML escapado, desde un handoff validado. No utiliza Claude Code, GitHub Actions ni APIs pagas. Registra `published:false` por defecto y no autoriza entregas. Pruebas de integración V8 8/8 y un conjunto de 6 tests Node en `runner/site-generator.test.mjs`; la ejecución automática de estos tests en GitHub Actions **sigue sin estar verificada**.
- **Demo pública y honesta:** HTML generado desde una especificación sintética, publicado como **ejemplo ficticio** bajo `https://autonoma-dev-agencia-v2.onrender.com/demo/landing/`. Enlazado desde la web ES y EN. El usuario puede inspeccionar una página de muestra; no debe publicitarse como trabajo para un cliente real ni como ejecución de Claude Code.
- Render desplegó y sirve la demo, páginas ES/EN y la API pública sigue reportando salud; el último despliegue manual del servicio tiene ID `dep-dbdt6com7kps73bk6q4g`. Comprobar su estado final; la demo sí respondió correctamente en verificación HTTP.
- GitHub Actions QA de la rama de agencia **sin ejecución validada**. El intento de crear una rama de integración para un PR aislado no pudo completarse. No se realizaron cambios directos en `main` ni se activó el puente Claude de otros proyectos. El repositorio temporal sigue siendo público y no se guardó código de clientes.
- Estado Neon comprobado en esta ronda: **0 administradores autorizados, 0 leads comerciales, 0 pagos, 0 órdenes**. Último snapshot del monitor observado 21:00 UTC, sitio/API saludables.

### Avance ponderado de fin de ronda
**55% estimado completado; 45% pendiente** (51% anterior, +4 puntos orientativos, no métrica de ventas).
- Web y captación: **20/20** — incluye nueva muestra ficticia de servicio.
- CRM privado: **11/15** — faltan cuenta dueña, credenciales y sesión autenticada móvil verificadas.
- Presupuestos y acuerdos: **12/15** — inmutabilidad de contrato e integridad de evidencia.
- Cobros/facturación: **3/15** — solo borradores, ninguna conciliación bancaria, factura ni impuesto validado.
- Programación/ejecución autónoma: **3/20** — especificador, puertas de seguridad y página básica determinista; **Claude Code aún no ejecutado**.
- QA, entregas y monitoreo: **6/10** — pruebas y controles efectivos, pero no CI real ni entrega comercial.
- Clientes e ingresos comprobados: **0/5** — ninguna venta demostrada.

### Cuatro impedimentos que determinan los siguientes incrementos
1. Alta y verificación de propietario real en Neon Auth, y comprobar que puede acceder al panel desde Android. Sin autorización nadie puede operar flujos comerciales.
2. Proyecto privado realmente verificado por GitHub (no atestado), con Claude Code ejecutado y skills cargadas, límite de consumo y PR aprobado. Actualmente NO existe ese runner.
3. Contabilidad y cobros reales en ARQ/Binance/Mercado Pago con pruebas independientes de ingreso y factura legal en Argentina; no marcar depósitos por capturas.
4. Alertas confiables con panel cerrado, correo transaccional, copia de seguridad y repetición del circuito con una venta/entrega real.

## Ronda de ejecución — 23/10/2026 ~21:50 UTC: exportador verificable y prueba de CI

### Implementado
- **Exportador reproducible de concepto sintético** `agencia-autonoma/runner/build-preview.mjs`: CLI Node.js sin dependencias externas. Modo `--demo --output /ruta/nueva` escribe `index.html`, `qa-report.json`, `manifest.json` y `README.md`. Modo `--verify /ruta` vuelve a comprobar el contenido y su huella SHA-256. Se niega a sobrescribir una carpeta preexistente.
- La fuente del ejemplo se genera con `compileHandoff` y `generateStaticPreview`; nunca carga clientes reales ni llama a Claude, GitHub, Neon, pasarelas de pago o proveedores externos.
- **Once comprobaciones de QA** para el HTML: doctype, viewport, noindex/nofollow, ausencia de scripts y dependencias externas, ausencia de formularios, marcado semántico, estilos de foco, media queries, tamaño razonable y carácter explícitamente ficticio.
- **Nueve validaciones funcionales aisladas en runtime V8** efectuadas tras recuperar el código exacto de GitHub: salida de 4 archivos, validez del HTML, seguridad contra scripts/URLs, generación/verificación determinista, no sobrescritura y detección de modificaciones. IMPORTANTE: para simular almacenamiento y cálculo se usaron dobles de `fs` y `createHash`; esto NO equivale a haber ejecutado el CLI real bajo Node.js ni a haber firmado criptográficamente el paquete.
- Pruebas Node.js propuestas y versionadas en `agencia-autonoma/runner/build-preview.test.mjs`, que incluyen `fs` real, integridad, XSS estático, no sobrescribir y error ante ruta relativa. Se añadieron al workflow `.github/workflows/agencia-autonoma-qa.yml`.
- En GitHub Actions se añadió un job que, si GitHub ejecuta el workflow, generará un artefacto efímero de revisión con `node build-preview.mjs --demo` y lo verificará con `--verify`, subiendo el paquete como artifact de un día. Sin acciones de publicación ni permisos de escritura.
- **No se ha confirmado una ejecución CI real.** Una comprobación a GitHub Actions encontró 0 runs para la rama `agencia-autonoma-infra`. GitHub indica que `workflow_dispatch` necesita el archivo del workflow en la rama predeterminada; este repo compartido tiene la rama principal `main` y agencia en rama secundaria. NO se alteró `main` ni se abrió un PR masivo inseguro.
- La publicación web ya verificada `/demo/landing/` permanece independiente del exportador: se muestra solo como muestra ficticia. No hubo despliegue web adicional en esta ronda.
- Registros Neon: 0 administradores activos, 0 leads comerciales reales, 0 solicitudes de pago y 0 órdenes de trabajo.

### Riesgos y siguiente avance
- El artefacto SHA-256 detecta alteraciones accidentales cuando el manifiesto se conserva; **no ofrece autenticidad criptográfica frente a un atacante capaz de modificar tanto el HTML como el manifiesto**. Falta firma/atestación externa e infraestructura CI ejecutada con permisos controlados.
- El generador es determinista y limitado a demostraciones HTML; **Claude Code sigue sin ejecutarse para proyectos reales**. Nada de lo agregado envía email, cobra, crea repositorios ni despliega páginas de clientes.
- Hace falta un repositorio privado separado, habilitar y confirmar CI en ese repositorio, credenciales aprobadas para Claude Code, límites de cuota/costo, pruebas reales y PR de revisión.
- Alta del usuario propietario en Neon Auth y comprobación del panel con su identidad, alertas externas, pagos y facturación siguen bloqueando el negocio.

### Puntuación de cierre
**57% completo / 43% pendiente**, estimación de preparación operativa frente al objetivo total.
Distribución: web/captación 20/20, CRM 11/15, presupuestos y acuerdos 12/15, cobros/fiscalidad 3/15, desarrollo 4/20, QA/entregas/monitoreo 7/10, ingresos 0/5 = **57/100**. 
Se suman solo 2 puntos al 55% anterior por el exportador verificable y la preparación de QA con artefacto revisable. No se suma por ventas inexistentes ni por un trabajo real de Claude que no ocurrió.

## Ronda 2026-10-23 23:40 UTC — seguridad de ejecución y auditoría del CI

**Cambios efectivos**
- Se ajustó `agencia.guard_work_order`: toda orden nueva debe empezar como `blocked`; no puede entrar en ejecución sin revisión fiscal, comprobación manual de repositorio privado, límite presupuestario y aprobación temporal de propietario.
- Las condiciones aprobadas de repositorio, gasto, revisión fiscal y ejecución quedan inmutables una vez iniciada la planificación. Para ejecutar código en `plan_ready` o `building`, la autorización debe seguir vigente. En QA y entrega, una autorización vencida no bloquea por sí sola la revisión de un trabajo terminado.
- Se añadieron las columnas `tax_reviewed_at` y `tax_reviewed_by` a `agencia.work_orders`, y se comprobó que el disparador actualizado está instalado. La versión restaurable quedó en `agencia-autonoma/sql/execution-approval-gate-2026-10-23.sql`.
- **La verificación de estas modificaciones fue estructural (reglas y disparador consultados desde Neon).** La prueba transaccional integral no se completó: la operación de ensayo fue bloqueada. No atribuir a esta ronda un flujo comercial E2E validado.
- Se desplegó temporalmente una suite `node:test` en Node 24 de Neon; su ejecución no respondió dentro del plazo. La función temporal `agenciasuiteqa` fue eliminada. No hubo un resultado PASS de esa suite; permanecen las **14/14 comprobaciones independientes reales de la ronda previa**.
- El workflow de GitHub `.github/workflows/agencia-proof-ci.yml` continúa listo para ejecución manual desde Actions, pero sin corrida verde confirmada. Tampoco se ha ejecutado Claude Code.
- La infraestructura no incorpora nuevos servicios de pago ni nuevas credenciales. Los cambios se limitaron a la rama de agencia, SQL y documentación. El sitio web anterior permanece publicado.

**Estado y puntuación**
- Referencia anterior: 59% preparado y 41% pendiente.
- Nueva puntuación orientativa: **60% preparado y 40% pendiente**. El único punto extra refleja un refuerzo real de las barreras de inicio de trabajo, no QA E2E adicional, facturación ni ingresos.
- Distribución: sitio y captación 20/20; panel 11/15; propuestas 12/15; cobros/fiscalidad 3/15; sistema de desarrollo 6/20; QA/entrega/monitoreo 8/10; ventas verificadas 0/5.
- Sigue pendiente: acceso del propietario, GitHub privado y CI ejecutado, modelo Claude Code con credenciales y coste autorizados, integraciones externas de cobro/conciliación, facturación y ventas reales.

## Ronda 2026-10-23 23:47 UTC — acceso seguro del propietario y separación de permisos

### Cambios confirmados
- Neon Function `agenciaadmin` versión **8 completed** incorpora `GET /api/admin/access`. La ruta solo responde después de verificar el JWT y el origen autorizado: devuelve el `user_id` de la propia sesión y el booleano `approved`, sin revelar ningún lead. Para todas las rutas comerciales continúa el rechazo `403 not_authorized_as_owner` cuando la cuenta no está aprobada.
- Panel móvil `site/admin/index.html` separa **tres estados**: no autenticado, sesión autenticada sin aprobación y CRM de propietario autorizado. El CRM se oculta del cliente si `ownerApproved!==true`. Cuando el titular entra con Google o contraseña, ve su ID real, un botón para copiarlo, otro para revisar permisos y un botón para cerrar sesión.
- Ningún registro de cuenta recibe automáticamente facultades administrativas. La autorización depende exclusivamente de `agencia.admin_users.active AND approved_at IS NOT NULL` en el servidor. El hecho de compartir un ID de usuario no demuestra titularidad: comprobar identidad por un canal independiente antes de autorizar.
- Rendimiento y publicación: Neon función administrativa revisión 8 activa, Render despliegue `dep-dbdv41t9fdbs738paclg`, commit `be4b6a483117c1ffa4d38ce389cd443a33ac5f11`, estado `live`. Página administrativa y página pública accesibles desde HTTP.
- Comprobaciones: 8 inspecciones estáticas del HTML/backend completadas, y sintaxis del script de módulo validada mediante envoltura async (necesaria por top-level await). Consultas HTTP sin credenciales a `/api/admin/access` y `/api/admin/leads` rechazadas con **403** sin revelar datos.
- Neon Auth Better Auth activo; dominio de confianza confirmado `https://autonoma-dev-agencia-v2.onrender.com`. El inicio de sesión real de propietario, la redirección de Google y la llamada autorizada **aún no están probadas** con credenciales reales del usuario.
- Estado de datos verificado: **0 administradores activos, 0 leads comerciales reales, 0 contratos aceptados, 0 intentos de pago, 0 órdenes**. Cron de Neon tomó snapshots correctamente a las **22:00 y 23:00 UTC** (web y API activas; consultas pendientes 0).
- GitHub Actions sigue con **0 ejecuciones confirmadas** del workflow de prueba de Node. No se creó repositorio privado, no se inició Claude Code, no hubo nuevos servicios pagos ni facturación.

### Nueva reestimación
**61% implementado / 39% pendiente**, desde 60%/40%. Se aumenta solo un punto por completar la experiencia de solicitud de permisos y aislamiento visual de datos; no se cuentan pruebas de propietario ni backend productivo con cliente real.
Distribución: web/captación **20/20**, panel/CRM **12/15**, presupuestos/acuerdos **12/15**, cobros/fiscalidad **3/15**, desarrollo con agentes **6/20**, QA/entrega/monitoreo **8/10**, ventas **0/5**.

### Paso que desbloquea la cuenta desde Android
Abrir `https://autonoma-dev-agencia-v2.onrender.com/admin/`, acceder con Google o crear cuenta, pulsar **Copiar mi ID** en la página «Cuenta identificada · autorización pendiente». El responsable del despliegue debe verificar por separado la identidad antes de activar el UUID en `agencia.admin_users`. No pedir claves, tokens ni códigos de recuperación.

## Incremento 24/10/2026 01:10 UTC — Historial de incidencias y avisos en panel

**Cambios reales:**
- Nueva tabla `agencia.monitor_events` sin PII con PK `(slot,event_key)`, para transiciones `website_down`, `website_recovered`, `api_down`, `api_recovered`, `new_leads`, `pending_growth`, `monitor_gap`. Índice cronológico y disparador `agency_capture_monitor_events` de PostgreSQL en `agencia.monitor_snapshots`. El detector solo registra incrementos de conteo; excluye registros de prueba de las consultas públicas contadas por el monitor.
- **Prueba SQL reversible, aprobada:** datos sintéticos generaron 4 eventos de caída/nuevas consultas y 2 de recuperación; una actualización repetida no duplicó los eventos. 0 filas ficticias persistentes.
- Backfill respaldado en snapshots históricos: `monitor_gap` único a `2026-10-23T21:00Z`, con `gap_minutes=120`; es un registro verídico de ausencia de una ejecución a las 20:00 UTC y no implica automáticamente caída del servicio.
- Esquema guardado en `agencia-autonoma/sql/monitor-events-2026-10-24.sql`.
- `agenciaadmin` versión 9 `completed` agrega `monitor_events` a `GET /api/admin/metrics` con ventana de 7 días y máximo 12 eventos. Sigue protegido por JWT del usuario aprobado; no hay acceso público a datos de clientes.
- Panel Android: historial de incidencias textual y libre de PII. El polling cada 5 minutos mientras el panel está abierto ahora conserva un aviso visible después del refresco, distinguiendo cambios de consultas y monitoreo. El polling requiere cuenta administrativa aprobada.
- Las verificaciones de sintaxis de API Node y módulo JS HTML dieron PASS.
- El desplegado de Render anterior `dep-dbe09sss728c738o90ig` quedó `live` con la primera versión del panel de eventos. El despliegue siguiente `dep-dbe0ad9srm7s73d7ik80` lleva la mejora de avisos de primer plano y **debe verificarse como live**; no afirmar publicación final antes de comprobar.
- Se intentó crear una vigilancia horaria de ChatGPT para avisos con el panel cerrado, pero **falló por el límite de 5 tareas activas**. Ninguna tarea anterior fue pausada ni cambiada. Por tanto, **NO hay notificaciones push fiables con el panel cerrado**.
- Sin clientes comerciales, ingresos o pagos, sin acceso de propietario verificado, sin runner real de Claude Code y sin CI verde. El cron de Neon sigue configurado y las muestras horarias más recientes muestran web y API en buen estado.

**Evaluación conservadora: 62% implementado y 38% pendiente.** Desde 61% solo +1 punto por trazabilidad de incidencias y avisos persistentes en primer plano. Puntuación: web 20/20, CRM 12/15, propuestas 12/15, cobros/fiscalidad 3/15, desarrollo Claude 6/20, QA/entrega/monitor 9/10, clientes/ingresos 0/5. Notificaciones con la app cerrada, cobros reales, autorizaciones del propietario, fiscalidad y ejecuciones autónomas siguen pendientes.

## 2026-10-24 02:00 UTC — primer intento real de disparar Claude Code en la agencia

- Se investigó el puente `ChatGPT to Claude Code - Authorized Task Branch` existente en `main` y `claude-requests`. GitHub Actions había registrado un run el 21/10 `39592733710` con `safety-tests=success` y `generate=failure`. Los logs explican: `One new request file, no other changes, is required.` El CLI **no se instaló ni se ejecutó** en esa ocasión.
- Se creó la solicitud nueva `.claude-requests/task-20261024-agency-claude-smoke.json`, commit `c3e5e6771c2cf885d07decd36c6d28ed7807a23e`, de exactamente **un archivo añadido**, autor `adedramaa`, con commit message `claude-task:` y tarea de modificar exclusivamente el documento público `docs/CHAT_BRIDGE_SAMPLE.md`. **No hay ejecución GitHub Actions vinculada a este commit** en la consulta posterior; no afirmar que Claude recibió ni completó esta tarea.
- Se diseñó una segunda prueba dedicada a la agencia: archivo `agencia-autonoma/sandbox/claude-price-fixture.mjs` con bug intencional en centavos; prueba `claude-price-fixture.test.mjs`, y validador `verify_claude_smoke.py`. El error se comprobó en V8: por ejemplo, 12550 centavos se imprime como USD 12,550 en vez de USD 125.50. La conversión `amountMinor/100` cumple los cuatro casos USD/ARS/EUR analizados. **Claude todavía no corrigió el archivo**.
- Se instaló en la rama predeterminada `main` el nuevo workflow de GitHub `.github/workflows/agencia-claude-smoke.yml`, commit `8045975505f012d625d14e3452904153fd15b224`. El flujo, al lanzarse, debe ejecutar el CLI oficial `@anthropic-ai/claude-code@2.1.296` sobre la fixture pública aislada: solo herramientas `Read,Edit`, control por `timeout`, sin escritura al repositorio, con tests Node y artefacto de revisión de un día únicamente si pasan todas las verificaciones. Utiliza el adaptador FreeLLMAPI y **modelo `openai/gpt-oss-20b`, no el modelo Claude de Anthropic**.
- Se inspeccionaron los ficheros reales y las reglas estáticas del workflow. Los datos del cliente están excluidos y no hay `git push`, commit automático ni despliegue. Las credenciales son las existentes en GitHub Actions, no nuevas contraseñas.
- **Evidencia de ejecución GitHub:** 0 runs para SHA `c3e5e6771c2cf885d07decd36c6d28ed7807a23e` y 0 runs para SHA `8045975505f012d625d14e3452904153fd15b224`. La lista general de ejecuciones devuelve como más reciente un run del 22/10, y un run había permanecido `queued`. Esto indica ausencia de arranque confirmado, **sin determinar la causa** (podrían intervenir la configuración, la disponibilidad o restricciones de Actions).
- **Resultado:** el CLI oficial quedó preparado para ejecutar una prueba segura, pero no se ejecutó. No se modificó código con Claude, no hay PR ni pruebas CI nuevas aprobadas, ningún cliente o pago se afectó. El máximo real de avance con evidencia operativa continúa en **62% estimado, 38% pendiente**; **no se suman puntos** por un runner no ejecutado.
- Para disparar el workflow desde Android: `https://github.com/adedramaa/freellmapi/actions/workflows/agencia-claude-smoke.yml` → `Run workflow` en rama `main`; luego examinar el run y el artefacto. Si el control no aparece, revisar habilitación y cuotas de Actions en la cuenta; no inventar que el run ocurre automáticamente.

## 24/10/2026 02:07 UTC — ejecución REAL y exitosa de Claude Code

**Evidencia primaria:** GitHub Actions run `40052784337` (`Agencia - Claude Code sintético y auditado`), URL https://github.com/adedramaa/freellmapi/actions/runs/40052784337, estado `completed / success`, evento `workflow_dispatch` disparado por el propietario. Job `claude-code-proof`: todas las tareas `success`, incluyendo instalación de CLI, ejecución real del CLI, auditoría de Read/Edit, pruebas de Node y artefacto.

**Evidencia de código:** El artefacto de GitHub `agency-claude-synthetic-review` (ID `12543803667`, 782 bytes, expira 25/10/2026 02:07 UTC) se descargó y abrió. Incluye `audit.json` con `ok=true`, `tools=["Read","Edit"]`, `added_lines=1`, `deleted_lines=1`, `client_data_used=false`, `deployment_performed=false`, `auto_merge=false`. El `claude-price-fixture.mjs` entregado conserva todo el código salvo la corrección `format(amountMinor)` → `format(amountMinor/100)`. Tres comprobaciones adicionales del archivo descargado pasaron en Node.js local.

**Evidencia de tests:** Antes del CLI, GitHub `node --test` produjo 1 aprobado y 2 fallidos (error intencional). Después, `3 tests passing / 0 failing`; ejecución del validador de log Claude Read/Edit y diff de un único archivo, todo en verde.

**Distinción importante:** Se ejecutó realmente **el CLI oficial de Claude Code** (versión fijada `2.1.296`), usando el adaptador FreeLLMAPI y el modelo `openai/gpt-oss-20b`. **No se utilizó el modelo Claude de Anthropic** y no se verificó coste monetario/consumo. El cambio es una *fixture sintética de un único archivo público*, no un pedido de cliente.

**Límites preservados:** No se escribió al repositorio con credenciales de GitHub, no se desplegó ni fusionó código, no se tocaron proyectos Raíces/Mayor Studio ni datos de clientes, y la propuesta está disponible para revisión como artefacto. La evidencia estructurada se conserva en `agencia-autonoma/reports/claude-code-smoke-2026-10-24.json` (commit `e5042531a93683589b245943e8c4efec792a6b42`).

### Nuevo avance conservador
**65% completado / 35% pendiente**, estimado (antes 62%). Sube la categoría Desarrollo Automatizado de **6/20 a 9/20**: primer uso de CLI realmente auditado, pero muy delimitado. No se suman puntos por clientes, cobros o una autonomía operativa que no existe.
- Web/captación 20/20; CRM propietario 12/15; propuestas 12/15; cobros y fiscalidad 3/15; desarrollo con agentes 9/20; QA y entregas 9/10; ventas 0/5 = **65/100**.
- Faltan repositorio privado aislado, ejecución de Claude Code desde órdenes comerciales autorizadas, auténtico ciclo de QA→PR→revisión→entrega de un proyecto, control de gastos y cuotas, administrador activo, cobros y facturación reales, ventas.

## 24/10/2026 02:18 UTC — preflight desde Neon + CI realmente ejecutado

### Cambios desplegados y comprobados
- Se instaló la función SQL de solo lectura `agencia.get_dispatch_readiness(uuid, actor)` que requiere admin previamente aprobado y revisa orden `plan_ready`, contrato aceptado y cotización enviada, pago marcado como verificado con referencias, validación fiscal, atestación de repositorio, aprobación vigente y **presupuesto de IA de 0 centavos USD**. Nunca marca `may_dispatch=true`: siempre devuelve `may_dispatch=false`, porque el repositorio, la conciliación externa, las cuotas y las credenciales del runner requieren una comprobación independiente, inmediata y autenticada. No devuelve datos de clientes.
- La función se respaldó en `agencia-autonoma/sql/work-order-dispatch-preflight-2026-10-24.sql` (última revisión commit `c4968388f0ee0443dce91c5df2405c687683539b`). Una comprobación SQL en vivo con actor desconocido devolvió `not_authorized`.
- Neon `agenciaadmin` desplegada revisión **10 `completed`**. Agrega `GET /api/admin/work-orders/preflight?order_id=UUID` con JWT EdDSA y allowlist; el endpoint público sin credenciales devolvió **403**, sin mostrar orden ni PII.
- El panel móvil del propietario incluye sección **Verificación previa a Claude Code**, de solo lectura, con ID de orden y lista de condiciones que faltan. Se comprobó el JavaScript y se desplegó mediante Render `dep-dbe1atom7kps73c0pb8g`, commit `9cb372b7e3d4fccb074f1a104da5df371124514b`, estado `live`. Se verificó por navegador que la sección es visible.
- Se creó `runner/dispatch-gate.mjs`, una función pura que comprueba metadatos autenticados de GitHub (requiere `private=true`, `visibility=private`, propiedad/repositorio coincidentes y permiso de escritura), evento del propietario, aprobación no vencida, factura o conciliación verificada externamente y ausencia de cargos del proveedor. **No realiza ejecución autónoma y nunca realiza llamadas de red**. Se detectó y corrigió un error de sintaxis en el patrón del repositorio antes de ejecutar la suite. Sus 13 pruebas pasaron en el entorno V8 local.
- **GitHub Actions pasó la suite real bajo Node**: workflow `Agencia Autonoma - Node proof (read-only)`, run **`40053645346`**, URL https://github.com/adedramaa/freellmapi/actions/runs/40053645346, commit de workflow `c5faf4678588764d697c20645051bfb45c5b923f`, repo de agencia fijado al commit `9cb372b7e3d4fccb074f1a104da5df371124514b`. En los logs: **48 tests aprobados, 0 fallidos**, incluye los tests de `dispatch-gate`. También generó, verificó y subió el paquete sintético HTML: **15 controles** y un SHA-256 idéntico en generación/verificación. Artifact **`agency-fictional-node-demo`**, id `12544925124`.
- Al actualizar el workflow en `main`, GitHub activó además los workflows generales del repositorio compartido `CI` y `Docker`. No se modificaron sus códigos ni se desplegaron clientes, pero consumen minutos de Actions; **evitar nuevas modificaciones en `main` si no es imprescindible**.
- Datos comerciales: **0 propietarios aprobados, 0 leads reales, 0 órdenes, 0 pagos y 0 aceptaciones**; este preflight no se probó aún con una orden real legítimamente aprobada.
- No se crearon tareas programadas nuevas ni se usó modelo pago Claude. El CLI de Claude Code sí fue demostrado en la prueba anterior (run `40052784337` con FreeLLMAPI), pero **no fue invocado otra vez en esta ronda**.

### Puntuación de preparación
**68% completado / 32% pendiente**. Antes 65%/35%; se justifica +1 por revisión de órdenes en el CRM y +2 por el control de ejecución de solo lectura con suite CI real completa. No se puntúa una integración de cobro, repositorio privado ni trabajo comercial con Claude inexistentes.
Desglose: sitio/captación **20/20**, panel/CRM **13/15**, presupuestos **12/15**, cobros/fiscalidad **3/15**, desarrollo con agentes **11/20**, QA/entrega/monitoreo **9/10**, ventas **0/5**.

### Próximos bloqueos reales
- Cuenta real de administrador aprobada mediante verificación segura del usuario y pruebas de sesión desde Android.
- Repositorio privado **dedicado exclusivamente a la agencia**; no usar `mayor-studio-whatsapp-bridge` ni el repo público para clientes. GitHub connector de esta sesión no expone creación directa de repositorios.
- Integración autenticada de GitHub/runner CI privado para verificar el repositorio, aprobación y pagos otra vez **antes de Claude Code**, con pruebas de aislamiento y cuota.
- Reconciliación de pago independiente del registro interno, validación fiscal y facturas.
- Primer pedido y entrega comercial revisados. Mantener gastos no autorizados en cero.
