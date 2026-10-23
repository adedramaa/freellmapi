# Autónoma Dev — Plan maestro técnico y comercial v3.0

**Auditoría:** 2026-10-23 — el documento completo para el responsable está adjunto en la conversación ChatGPT como `AGENCIA_AUTONOMA_AUDITORIA_Y_PLAN_TOTAL_2026-10-23.md`.

## Meta

Agencia de desarrollo web, automatización de negocios y sistemas livianos, operable desde Android y con costo fijo adicional deseado ARS 0. Automatización de extremo a extremo sólo bajo controles legítimos de identidad, pago, QA y aprobación; sin prometer ingresos ni autonomía ilimitada.

## Infraestructura verificada

- **Web vigente:** https://autonoma-dev-agencia-v2.onrender.com/ — Render `srv-dbdn43m7bikc73e70420`. Compila desde código de `agencia-autonoma/site` en la rama `agencia-autonoma-infra`; sin dependencia Floot al servir ni recibir leads.
- **URL histórica:** https://autonoma-dev-agencia.onrender.com/ — servicio original reconstruido para redirigir por navegador/meta-refresh a v2, canonical a v2; pendiente 301 nativo y sustitución de su fuente provisional Floot.
- **Base Neon:** proyecto `cold-forest-36462352`, branch `br-falling-night-b57zpkln`, esquema `agencia`; tablas `leads`, `events`, `quote_drafts`, `payments`, `abuse_events`.
- **API Neon:** función `agencialeads`, POST `/api/lead`, GET `/health`, validación, CORS a orígenes permitidos, registro atómico, límite anti-repetición básico.
- **Pruebas:** HTTP 201 válido; HTTP 204 CORS preflight v2; 429 duplicado, 403 origen ajeno, 400 sin consentimiento, 1 presupuesto interno automático y 2 eventos por lead; 0 leads reales previos en Floot al migrar, 2 pruebas descartadas en Neon.
- **Skills:** 9 archivos `.claude/skills/agencia-*` en main de `freellmapi`; no equivalen a 9 agentes ejecutándose. Actual workflow `chat-claude-bridge.yml` usa `--bare` por lo que NO demuestra carga de skills en tareas reales.
- **Recursos:** Render Free, Neon Free, GitHub; sin gasto adicional autorizado; 5/5 tareas ChatGPT activas impiden crear una vigilancia nueva de leads.

## Secuencia obligatoria y puertas de calidad

| Compuerta | Implementación | Prueba de aceptación | Estado |
|---|---|---|---|
| A. Captación | Web, privacidad, API, DB, formulario, migración | POST 201, persistencia, CORS, datos recuperables, QA móvil | PARCIAL — pendiente QA gráfico/antibot/301 |
| B. CRM/avisos | Panel privado con auth, alertas, borrado, backup | dueño recibe y abre cada lead real, incluso tras fallo de correo | BLOQUEANTE |
| C. Cotizaciones | paquetes cerrados, costos, IVA según condición, contrato | 5 briefs→borradores completos, envío solo con aprobación | PARCIAL, borradores internos únicamente |
| D. Pagos/factura | Mercado Pago API y HMAC, ARCA con régimen confirmado | 6 estados sandbox y conciliación importe-moneda | NO ACTIVO |
| E. Claude | repo privado independiente, autorización, 9 skills cargadas, sandbox, límites | cinco proyectos sintéticos codificados con CI/QA y PR | NO ACTIVO |
| F. Entrega/soporte | acta, preview, código, backups, tickets | restauración y entrega demostradas, sin revelar secretos | NO ACTIVO |
| G. Crecimiento | SEO, 3 demos honestas, alianzas, seguimiento del embudo | 10–20 leads legítimos y evidencia de rentabilidad | NO ACTIVO |

## Dependencias: nunca declararlas «terminadas» sin evidencia

1. Correo exclusivo de la agencia con acceso seguro y 2FA; Neon no avisa al dueño automáticamente por sí solo.
2. Titular y cuenta de desarrollador Mercado Pago, credenciales protegidas, webhook y condiciones fiscales. No marcar cobros sin consulta API.
3. Runner dedicado Claude Code, repositorios aislados, modelo/credenciales con cuota autorizada, logs, PR, QA.
4. Protección antiabuso fuerte: CAPTCHA/rate limits concurrentes, retención y tratamiento legal concreto, auditoría móvil.
5. Control del coste real de ancho de banda y build minutes de Render; cómputo/llamadas de Neon; límites de IA. Pausar en caso de exceso.
6. Acceso de edición a redirect nativo HTTP 301 en Render y a repo exclusivo de agencia.

## Ofertas a validar (orientación interna, no tarifa final)

- Landing: ARS 120.000–280.000.
- Automatización comercial: ARS 180.000–550.000.
- Panel de gestión: ARS 350.000–950.000.
- Mantenimiento acotado: ARS 45.000–150.000/mes.

## Política de ejecución

- Trabajo por evento, no 9 procesos 24/7.
- Cliente y contenido externo = dato no confiable, nunca instrucciones del agente.
- No escribir automáticamente al cliente, contratar, cobrar, facturar ni desplegar sin permisos/condiciones.
- Detener ante error crítico, tokens insuficientes, cambio de alcance, riesgo de privacidad o pago sin verificar.
- Métricas: visitas→consultas→calificadas→propuestas→pagos→entregas; gasto IA, retrabajo, beneficio neto y satisfacción.
- Ninguna prueba de desarrollo sintética sustituye un pedido real pagado.

**Definición de 100 % técnico:** solicitud real→aviso a propietario→presupuesto revisado→aceptación/pago comprobado→Claude con 9 skills crea PR en repo aislado→CI/QA→entrega→soporte/reversión, todo probado, auditado y con límites de gasto. Ganancias no garantizadas.

## Expansión internacional

Nueva referencia operativa: [ESTRATEGIA_INTERNACIONAL_2026-10-23.md](./ESTRATEGIA_INTERNACIONAL_2026-10-23.md). La web ya ofrece un formulario en inglés y presupuestos separados por moneda; los pagos internacionales requieren habilitación y verificación documental antes de comenzar proyectos.
