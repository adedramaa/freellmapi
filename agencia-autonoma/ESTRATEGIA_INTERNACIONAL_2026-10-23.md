# Autónoma Dev — Estrategia internacional de ventas y cobros v3.0

**23 de octubre de 2026 · Investigación con fuentes oficiales · Estado: captación internacional técnica habilitándose, pagos NO habilitados todavía**

## Meta y restricciones del plan original

Agencia remota de sitios web, automatización comercial y paneles sencillos, desde Argentina, administrable en Android, sin nuevos cargos fijos voluntarios ni confundir software funcional con ingresos garantizados. Separada de Mayor Studio/Raíces/Aura y de proyectos privados de clientes. Presupuestos, contratos, pagos, impuestos y despliegues protegidos por revisión humana, límites y auditoría. Internacional se suma al embudo local, no lo reemplaza.

## Decisión por tipo de cliente (condicionada a habilitación real)

| Mercado y perfil | Canal potencial | Estado previo imprescindible |
|---|---|---|
| Empresa de EE. UU. con banco ACH | ARQ (datos USD de EE. UU., ACH/Wire domésticos) | Verificar tipo de cuenta ARQ, legitimidad de recepción comercial, documentación, BCRA/ARCA y retiro local |
| Empresa de la zona SEPA | ARQ (EUR por IBAN/SEPA) | Igual; verificación de datos IBAN y contraparte; no SWIFT |
| Cliente internacional que pide tarjeta | Evaluar Payoneer Request a Payment solo si tarifas aceptadas; alternativa pasarela compatible | Alta y aprobación, tasas y posible costo anual; no declarar activa antes de probar |
| Cliente técnicamente familiarizado con cripto | Binance Pay manual con link/QR, sólo cuando elegible | Legalidad, impuestos, KYC, titularidad, red y activo; no automatizar en base a captura |
| Clientes de Argentina | Mercado Pago ARS | Verificar cuenta comercial titular y conciliación API/webhook para automatizar |
| Empresa sin ACH/SEPA, no acepta cripto | Transferencia bancaria internacional conforme a su banco, o proveedor autorizado alternativo | Costos de SWIFT y documentación fiscal/cambiaria, antes de prometer precio neto |

### ARQ — hechos comprobados y limitaciones

- ARQ Personal permite **ingresos de freelance a título personal**, pero sus términos diferencian uso empresarial (pagos de una empresa) que corresponde a **ARQ Business**. No recibir ingresos de entidad empresarial en cuenta personal si viola las condiciones.
- ARQ Business admite solicitudes de negocios registrados en Argentina; una persona sin empresa registrada no tiene acceso garantizado. No asumir que inscribirse como monotributista por sí solo da derecho a Business sin confirmación de ARQ.
- ACH o wire **doméstica en EE. UU.**: tarifa publicada Standard USDc 3 por entrada. ACH usualmente tarda 3–6 días hábiles. No hay recepción por SWIFT en esa ruta.
- SEPA europeo: tarifa publicada EURc 3 por transferencia.
- El saldo se convierte en **dólares/euros digitales (USDc/EURc)**. No confundirlo con depósito bancario en divisas en Argentina. Los retiros en USD a cuenta bancaria propia Argentina se despliegan gradualmente y pueden implicar tasa de conversión. Verificar en la cuenta real y con contador/banco.
- ARQ Business no tiene cuota mensual declarada; aún así comprobar comisiones, spread y elegibilidad concretos.

### Binance Pay

- Puede solicitar pagos por link o código QR (también con moneda y monto específico); el enlace puede caducar a los 30 días; disponibilidad sujeta a cuenta/país.
- **No confundir QR entre personas con Binance Pay Merchant/API de e-commerce.** Aprobación comercial y términos separados.
- No es primera opción para compradores empresariales tradicionales; usar solo si cliente ya acepta cripto y normativa del país de ambas partes lo permite.
- Si se usa cripto: acordar moneda, red, valor de referencia fiat, fecha, factura, tx ID, confirmación, procedimientos ante errores y recepción efectivamente conciliada.

### Mercado Pago

- Mantener como opción nacional (ARS). El producto Cross Border de Mercado Pago requiere **cuenta especial creada por el equipo comercial**; no suponer que un link estándar argentina cobra eficazmente en USD a compradores de cualquier país.
- No integrar ni colocar enlace de cobro crossborder sin aprobación de su proveedor y pruebas de tarjetas/localización.

### Alternativas sin cuenta hoy

- Payoneer puede enviar link de pago por tarjeta y métodos bancarios y admite clientes internacionales. Tarjeta hasta 3,99% (puede tener fijo adicional). Aviso: publica tarifa anual de USD 29,95 si se recibe menos de USD 6.000 en 12 meses, según condiciones. No abrir si viola presupuesto fijo cero.
- PayPal Argentina es opción adicional de tarjeta, pero comisión comercial internacional publicada 5,4% + fijo para Argentina y conversión adicional en ciertos escenarios; revisar retiro local y disputas antes de adoptarlo.
- Stripe Argentina no debe ser supuesto como ruta directa habilitada; no crear LLC ni contratar terceros sólo para conseguir procesador sin análisis.

## Fiscalidad argentina — compuerta obligatoria

- Los servicios de desarrollo entregados desde Argentina para uso económico exterior suelen corresponder a exportación de servicios, según caso concreto.
- Para monotributistas ARCA exige **factura E**, punto de venta habilitado y límites de categoría. Es distinto de una factura C local o de un comprobante simple de la app.
- BCRA Comunicación **A 8330 (septiembre 2025)** quitó límite anual USD 36.000 para la excepción de liquidación de personas humanas y exigió mantener los requisitos de ingreso/acreditación; **A 8417 (abril 2026)** extendió la excepción a todos los conceptos de servicios. Las excepciones **no equivalen a permiso general para dejar fondos cobrados en una wallet exterior indefinidamente**. Verificar la operatoria con banco y contador.
- Ingreso en dólares/euros digitales en fintech no necesariamente cumple la acreditación local de divisas exigida para ciertas operaciones. Documentar movimiento desde cliente hasta banco local, moneda, tasas, comisiones, factura, titulares y fechas. No recomendar Binance P2P como evasión cambiaria o tributaria.
- Si el usuario aún no está registrado fiscalmente para la actividad, se deben validar los requisitos **antes de aceptar un trabajo oneroso y emitir factura**. No es necesario asumir una empresa societaria sólo para empezar como profesional independiente.

## Cambios técnicos requeridos (con compuertas)

**A — Captación multinacional**
- Web /en/ en inglés, contacto internacional sin checkout, formulario país y moneda USD/EUR; ES local continúa en ARS.
- Neon campos de país, idioma, moneda y rango de presupuesto extranjero; evitar reinterpretar estimación ARS como monto USD.
- Documentos de privacidad internacional, consentimiento y anti-spam. Probar 201 E2E, 429, 400, 403 y funcionamiento en móvil antes de considerar producción validada.

**B — Preparación comercial**
- Un mismo CRM central: origen, país, idioma, moneda, presupuesto, zona horaria y estado del lead. Dedupe, alertas reales y bandeja autenticada.
- Plantillas de propuestas ES/EN con alcance, entregables, exclusiones, hitos y anticipo (p.ej. 50% bajo acuerdo específico; no obligación universal). Datos legales del prestador correctos.
- Modelo de precios y márgenes separados por moneda; no mezclar monedas ni fijar cotización ARS↔USD sin tipo y fecha.
- Tarifas EXPERIMENTALES para descubrimiento (USD): landing 250–500; automatización acotada 350–900; herramienta interna pequeña 700–1.600; mantenimiento 75–250/mes. Sin garantía de demanda ni oferta pública automática; decidir según complejidad, competencia, costos e impuestos.

**C — Cobros seguros**
- Modelos: `payment_methods`, `payment_intents`, `payment_confirmations`, `fx_quotes`, `refund_reviews`; uno por presupuesto aceptado.
- Estados `quote_approved → invoicing_ready → awaiting_payment → provider_pending → paid_verified → work_authorized`.
- ARQ/Binance: empezar con confirmación manual de titular y evidencia documental; NO inventar webhook/API o consultar saldos con un conector inexistente.
- Mercado Pago: webhook firma validada + consulta API + importe/moneda/orden.
- No pasar a desarrollo si es pago de tercero no autorizado, importe insuficiente, titular distinto, crypto/red equivocada, documentación incompleta o controversia.

**D — Producción y entrega**
- Aprobaciones, repositorio privado aislado, skills realmente detectadas por Claude Code, CI y pruebas.
- Cliente revisa preview, se entrega bajo condiciones acordadas y soporte definido.
- Factura E/confirmación documental ligada al pedido para exportaciones; conciliación y archivo seguro.

**E — Ventas internacionales**
- Aceptar briefs en inglés desde web (sin simular oficina en USA).
- Posicionar propuestas especializadas para pequeñas agencias, comercios, consultores y administradores de ecommerce.
- Comenzar con servicios definidos y métricas sobre 10–20 consultas comerciales; no atribuir ganancias superiores solo por moneda.
- Evitar mensajes masivos, scraping no permitido, testimonios falsos y perfiles comerciales engañosos.
- SEO bilingüe con canonical/hreflang, sitemap y demos reales. Search Console cuando el propietario la conecte.

## Condición exacta para activar pagos públicos

1. Titular/cuenta comercial individual o empresarial autorizada para el método y el país.
2. Inscripción fiscal/circuito factura E, moneda y forma de ingreso de los fondos confirmadas por contador/banco.
3. Prueba de un pago de bajo riesgo y confirmación independiente (no screenshot) + guardas de importe/moneda/ID.
4. Política de cancelación/reembolso y acuerdo ES/EN revisados.
5. Ruta segura de soporte, incidencias, disputas, protección de datos y tope de gastos.

Hasta entonces: **solicitudes de presupuesto internacionales sí; checkout automatizado de cobros no**.

## Fuentes oficiales consultadas

- ARQ personal vs business: https://www.arqfinance.com/es-MX/help/articles/can-i-use-my-arq-personal-account-for-my-business
- ARQ Business elegibilidad: https://www.arqfinance.com/es-MX/help/articles/who-can-open-an-arq-business-account
- ARQ USD cobros ACH: https://www.arqfinance.com/es-AR/help/articles/how-to-receive-your-first-usd-transfer-from-someone-else-in-arq
- ARQ Argentina tarifas: https://www.arqfinance.com/es-AR/help/articles/arq-costs-and-fees-argentina
- ARQ retiro USD AR: https://www.arqfinance.com/es-MX/help/articles/send-us-dollars-usd-to-my-argentine-bank-account
- Binance Pay: https://www.binance.com/es/support/faq/detail/c92c2a2daf5a457cb1adc08c4ad8315c
- Mercado Pago CrossBorder: https://www.mercadopago.com.ar/developers/es/docs/resources/localization/crossborder-integration
- Payoneer tarifas: https://www.payoneer.com/es/about/pricing/
- ARCA exportación: https://www.arca.gob.ar/monotributo/exportacion-servicios/
- BCRA A8330: https://www.boletinoficial.gob.ar/detalleAviso/primera/331822/20250923
- BCRA A8417: https://nuevaweb.boletinoficial.gob.ar/detalleAviso/primera/340665/20260413
