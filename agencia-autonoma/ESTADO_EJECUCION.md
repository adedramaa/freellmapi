# Autónoma Dev — control de implementación (2026-10-23)

## Operativo y conservado
- Sitio comercial anterior: https://autonoma-dev-agencia.onrender.com (Render Free), con formulario publicado hacia Floot; NO sustituir, redirigir ni dar de baja hasta prueba de POST y copia de leads.
- Skills de agencia: 9 archivos en `.claude/skills/agencia-*/SKILL.md` del repositorio compartido de herramientas. Separadas de las skills para Mayor Studio y Raíces.
- Infraestructura nueva: proyecto Neon **Autonoma Dev Agencia**, ID `cold-forest-36462352`, rama `br-falling-night-b57zpkln`, plan Free del usuario.
- Esquema Postgres aislado `agencia`: leads, events, quote_drafts, payments, abuse_events, índices y restricciones comerciales.
- Disparador Postgres `agencia_quote_draft_after_insert` que crea un borrador **interno, sin precio final ni aprobación**, cada vez que se inserta un lead.
- Función HTTP Neon `agencialeads` desplegada (Node.js 24); GET /health devuelve servicio activo. Código: `agencia-autonoma/neon/index.mjs` en esta rama.

## Comprobado
- Creación de Neon y SELECT de tablas/cuentas cero exitosos.
- Registro de trigger confirmado en pg_trigger.
- Despliegue Neon Functions #1 `completed`.
- GET HTTPS `/health` real respondió: `{"ok":true,"service":"autonoma-dev-intake","database":"configured"}`.
- Código del backend recibido por herramienta GitHub, empaquetado sin dependencias externas y desplegado mediante API Neon.
- GET HTTPS `/health` ahora ejecuta `SELECT count(*) FROM agencia.leads` antes de responder. Prueba real verificada: `{"ok":true,"service":"autonoma-dev-intake","database":"verified"}`.
- Segundo trigger de Postgres `agencia_lead_lifecycle_before_update`: transiciones de estados permitidas, exige presupuesto aprobado y pago verificado antes de producción. Confirmado por instalación, pendiente prueba de transición funcional.
- **Todavía NO se ha probado POST real a Neon**; no confundir consulta de health con registro de un lead ni conectar frontend hasta probar el circuito.

## Pendientes prioritarios con dependencias
1. Integración frontal: probar POST /api/lead desde origen permitido, validar registro+evento+borrador en Neon y cotejar con resultados; habilitar Turnstile antiabuso y política de retención.
2. Publicar frontend desde repositorio independiente de la agencia, quitar la dependencia de descargar HTML de Floot; reemplazar formulario del sitio principal sólo tras pruebas y plan de rollback.
3. Revisión interna: autenticación fuerte, pipeline de presupuestos y aprobaciones, datos mínimos, acuerdos y conservación.
4. Correo propio: dominio+DNS+proveedor de email, notificaciones automáticas disparadas por evento con opt-in y controles.
5. Mercado Pago/ARCA: cuenta comercial autorizada, webhook con firma y consulta de pagos con API, facturación según la situación fiscal. Nunca marcar pago aprobado basándose sólo en notificación.
6. Claude Code: ejecución real de nueve skills bajo un flujo **diferente** al de otros proyectos. El puente general `chat-claude-bridge.yml` usa `--bare`/`--disable-slash-commands`, por lo que no conviene asegurar uso de skills allí. Crear runner propio en repo de agencia con sandbox, tests, límites de turnos, permisos mínimos, PR y revisión.
7. Entregas/soporte: releases QA/CI, acta, respaldos comprobados, políticas de garantía, incidencias, reportes.
8. Captación comercial ética y medición de tasa de respuesta y conversiones. No hay ventas ni ingresos verificados todavía.

## Protección de costos y negocios
- Gratis **según las cuotas** de Neon Free/Render Free/GitHub Free; comprobar uso y no cambiar a facturación paga sin autorización.
- No tocar las aplicaciones/tiendas de Raíces, Mayor Studio, Aura ni FreeLLMAPI.
- Esta rama es temporal y de solo código de la agencia; una vez disponible, migrarla a repositorio privado independiente.
- No incorporar credenciales, correos privados, datos de clientes, tokens ni logs sensibles al repositorio.
