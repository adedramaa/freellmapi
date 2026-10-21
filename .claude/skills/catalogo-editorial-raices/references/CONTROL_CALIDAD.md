# Auditoría de catálogo — criterio de salida

## BLOQUEANTES (no publicar)
- [ ] Producto no existe en fuente, nombre/código alterado o variantes/sets inventados.
- [ ] Precio diferente del precio validado, moneda o vigencia ambigua.
- [ ] Fotografía no oficial, de otra variante, inventada o sin procedencia verificable.
- [ ] Artículo en PDF no presente en el inventario o SKU esperado omitido sin justificación.
- [ ] Texto cortado, valores ocultos, fotografías ausentes, página en blanco o elementos solapados que afecten compra.
- [ ] Catálogo enviado/publicado sin autorización.

## AUDITORÍA AUTOMÁTICA
1. Validar JSON (campos obligatorios, tipos, SKU únicos, precios positivos, fuentes no vacías).
2. Verificar que cada imagen exista localmente o haya sido descargada desde una fuente autorizada, registrar hash cuando sea posible.
3. Comparar conteos por categoría con los datos de entrada y listado de SKU reproducido en HTML/PDF.
4. Exportar PDF y confirmar que existe, que tiene páginas y que puede abrirse; extraer texto de las páginas para cotejar códigos/precios cuando las herramientas están disponibles.
5. Renderizar **todas** las páginas y generar hoja de contacto; inspeccionarla y ampliar páginas problemáticas. Verificar que la fuente no sea diminuta, la retícula no desborde y las fotos no queden recortadas.
6. Repetir render y revisión tras cada corrección que altere el PDF.

## RESULTADO DE AUDITORÍA (ejemplo de campos, no de aprobación)
- Estado: APROBADO PARA REVISIÓN / BLOQUEADO
- Fecha de corte de precios:
- Productos de fuente / productos publicados:
- Fotos verificadas / faltantes:
- Precios verificados / conflictos:
- Páginas PDF:
- Páginas inspeccionadas como imagen:
- Errores encontrados y corregidos:
- Pendientes que impiden publicar:
- Rutas de PDF / vista previa / fuente:

No rellenar un campo con una cifra asumida; usar `NO VERIFICADO` cuando falte evidencia.
