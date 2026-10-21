---
name: catalogo-editorial-raices
description: Diseña, rehace, audita y exporta catálogos comerciales profesionales en PDF para Raíces Regalos y proyectos similares. Usar OBLIGATORIAMENTE si el usuario pide catálogo, lista de productos ilustrada, catálogo mayorista, dossier comercial, actualización de precios en catálogo o mejorar la calidad visual de un PDF de productos. Comprueba fuentes reales de fotos, SKUs y precios; crea maquetación editorial premium; renderiza, inspecciona y audita cada página antes de entregar. Nunca inventa artículos ni precios.
---

# Catálogo Editorial Raíces — protocolo profesional

## Objetivo

Producir un catálogo **comercialmente útil, atractivo y verificable**, no simplemente un PDF funcional. Destinado a compradores mayoristas de mates, accesorios para asado y regalos personalizables. Priorizar la legibilidad en Android y la impresión en A4, con una identidad visual propia, sin estética de arte generado por IA (brillos, degradados, saturaciones arbitrarias, falsas fotos de productos).

Esta skill complementa otras herramientas y skills visuales (`frontend-design`, `canvas-design`, `pdf`) si están disponibles; **no sustituye los controles de fidelidad de producto**. Para catálogos multipágina se prefieren HTML/CSS paginado y exportación mediante Playwright/Chromium, o Paged.js si hacen falta funciones de edición impresa más sofisticadas. Si el entorno no permite instalar dependencias, producir el HTML/CSS listo y declarar exactamente la limitación: NO fingir un PDF terminado.

## Condiciones innegociables

1. **Solo contenido verificado.** Cada producto requiere SKU/código, nombre, categoría, foto oficial/local verificable, precio oficial vigente y fuente del precio. Nunca inventes imágenes, variantes, packs, descuentos, stock, promociones, medidas, grabados o especificaciones.
2. **No sustituir la fotografía original.** Si no existe foto autorizada, marcar el producto como pendiente de foto. NO reemplazar por una imagen generada, foto parecida, mockup falso o de otra variante. Para bocetos, usar una casilla claramente etiquetada `FOTO ORIGINAL PENDIENTE` y no entregar como catálogo final.
3. **Precios trazables.** Identificar fecha y fuente de los datos. No cambiar ni deducir importes, márgenes, promociones o moneda. Si un precio no se puede verificar, bloquear la publicación de ese producto en la salida final; solicitar/recuperar la fuente antes. Todo cambio debe figurar en un log.
4. **No publicar ni enviar sin aprobación.** Producir primero vista previa y PDF candidato con reporte de calidad; pedir la aprobación antes de reemplazar un PDF publicado, enviar por WhatsApp/email o sincronizar precios con una tienda.
5. **No perder datos.** Conciliar recuento y SKU de entrada contra salida; explicar explícitamente si hay elementos excluidos y por qué. No deduplicar por nombres parecidos; solo por SKU confirmado.
6. **Gasto adicional cero.** Priorizar recursos ya disponibles y herramientas gratuitas/open source. No pedir PC al usuario; ejecutar en servidor/agente autorizado si dispone de él.
7. **No afirmar tests inexistentes.** Diferenciar claramente `verificado automáticamente`, `revisado visualmente` y `pendiente`. Una skill por sí sola no certifica el resultado.

## Flujo obligatorio, sin atajos

### Fase A — Inventario de fuentes

- Detectar dónde está la fuente autorizada: CSV/JSON, base de datos, catálogo anterior, web de Raíces, fotos locales o almacenamiento conectado. Comprobar acceso real. NO dar por hecho que hay acceso a una tienda/ERP si la integración no está activa.
- Guardar instantánea/versionado para que el catálogo sea reproducible. Comparar precio/productos con la versión anterior si la hay.
- Construir un `catalogo.json` con `empresa`, `titulo`, `moneda`, `fecha_corte`, `fuentes`, `productos` y opcionalmente `contacto`, `destacado_sku`.
- Para cada producto incluir `sku`, `nombre`, `categoria`, `precio`, `fuente_precio`, `imagen`, `fuente_imagen`, `verificado`. Consultar esquema en `references/CONTRATO_DATOS.md`.
- No extraer precios de imágenes de baja calidad u OCR incierto sin verificarlos con fuente adicional.

### Fase B — Dirección visual

Leer `references/DISENO_EDITORIAL.md`. Definir retícula, tipografías, escala de tamaños, paleta y categorías. Si hay manual de marca, conservarlo; no inventar el logo.

Concepto predeterminado: diseño editorial mayorista contemporáneo. Fondos claros, tinta oscura, color acento terroso o corporativo **solo si aprobado o derivado de identidad verificable**; fotos reales grandes, fichas comparables, suficiente espacio en blanco. Sin falsas texturas de madera, confeti, marcos pretenciosos, sombras exageradas, degradados o efectos de IA.

Maquetación sugerida: portada tipográfica cuidada + páginas con encabezados consistentes por familia + cuatro productos/página cuando hay fotos y textos breves; variar densidad para productos destacados sin perder sistema. Imagen siempre `contain` si recortarla pudiera alterar la identificación comercial. No generar fotos de portada que puedan parecer productos reales; usar imagen original autorizada o portada tipográfica.

### Fase C — Primera prueba editorial

Crear al menos una portada y dos páginas de producto con datos/fotos REALES (si están disponibles). Inspeccionar el resultado renderizado como imágenes, no solo el HTML o texto. Ajustar jerarquía, márgenes, legibilidad, recortes y coherencia. Si el usuario ya definió el estilo y autorizó continuar, no frenar innecesariamente para pedir detalles que ya constan.

### Fase D — Construcción y exportación

Plantilla reproducible incluida en esta skill:

```bash
python scripts/validar_catalogo.py /ruta/a/catalogo.json
python scripts/construir_catalogo.py /ruta/a/catalogo.json --out /ruta/a/salida/catalogo.html
node scripts/exportar_pdf.cjs /ruta/a/salida/catalogo.html /ruta/a/salida/catalogo.pdf
```

Los scripts están en la carpeta `scripts/` de esta skill; resolver rutas con `${CLAUDE_SKILL_DIR}` donde sea compatible, sin copiar comandos si la ruta activa difiere. El exportador usa `playwright` ya presente en el entorno, o debe configurarse en el servidor autorizado antes. Los scripts proporcionan un punto de partida limpio, no sustituyen un trabajo visual más elaborado según las fuentes y la identidad reales.

El catálogo final debe tener fondo/color impreso, gráficos vectoriales cuando sea posible, texto seleccionable y fotos suficientes para la finalidad de uso. No prometer que una foto raster tiene 300 ppp efectivos sin comprobar sus dimensiones respecto al tamaño impreso.

### Fase E — Control de calidad obligatorio

Leer y cumplir `references/CONTROL_CALIDAD.md`. **Renderizar cada página a imagen**, comprobar portada y páginas interiores, detectar fotos faltantes/estiradas, solapamientos, textos cortados, páginas vacías, artículos duplicados, SKU desparejados y diferencias de precio. Comparar salida vs entrada con conteos. Si se usa `pdftoppm` o PyMuPDF, verificar su instalación y recorrer TODAS las páginas; para catálogos largos es válido generar además una hoja de contacto.

Si hay PyMuPDF, ejecutar `python scripts/auditar_pdf.py /ruta/catalogo.pdf --catalogo /ruta/catalogo.json --out /ruta/vistas` y examinar el directorio de páginas renderizadas. No declarar `APROBADO` si hay bloqueantes. Entregar:

- PDF candidato y, si se solicita, HTML editable.
- Cuadro de auditoría: total de productos, total de páginas, categorías, precios/fotos no validados (ideal: 0), cambios vs versión anterior, defectos encontrados/corregidos.
- Vista previa de las páginas representativas.
- Registro de las fuentes y fecha de corte para reproducibilidad.

## Decisiones ante incertidumbre

- Sin datos completos: generar un **prototipo no publicable** con tarjetas identificadas como faltantes y un reporte; nunca inventar para completar la retícula.
- Si un SKU tiene precio distinto en dos fuentes: parar el tratamiento de ESE SKU, reportar conflicto, mantener los demás verificables en borrador.
- Si las fotos de dos productos son muy parecidas: cotejar nombre de archivo, SKU y fuente; no asignar imagen por similitud visual.
- Si el usuario dice que la última edición fue mala: extraer y auditar la versión anterior si está accesible; identificar errores concretos y no repetir su diseño.
- Si faltan bibliotecas o permisos: explicar el requisito y elegir alternativa gratuita ejecutable en el entorno existente; nunca simular exportación.

## Activación y resultado esperado

Invocar `/catalogo-editorial-raices` en Claude Code, o pedir directamente "rehace el catálogo de Raíces". El proceso prioriza **integridad de datos + dirección de arte + verificación visual real**. Un PDF generado sin inspección visual y trazabilidad se considera incompleto.
