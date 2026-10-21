---
name: catalogo-editorial-raices
description: Produce y revisa catálogos profesionales A4 para Raíces Regalos, exclusivamente con fotografías auténticas asociadas a SKU verificados.
---
# Dirección editorial Raíces — edición 2026

## Fuente autoritativa
- Nunca inventar productos, packs, grabados, SKUs, variantes, fotografías, precios ni disponibilidad.
- Conservar exactamente el vínculo SKU a página de producto a fotografía original verificado.
- Para esta edición: catálogo sin precios, un máximo de 25 páginas, blanco puro, aire editorial, tipografía grande, fotografía protagonista.
- Empezar por artículos negros/marrones, terminar con los de color. Sin cajas, tarjetas, recuadros, sombras, brillos, degradados ni sustituciones generadas por IA.
- No recortar fotografías hasta cambiar el producto: usar encaje proporcional (contain).
- Máximo cuatro productos por página para mantener fotografías legibles en móvil.
- No convertir el archivo en una cotización ni publicarlo/enviarlo sin la revisión del usuario.

## Ejecución
1. Leer también las skills oficiales canvas-design, frontend-design y pdf disponibles en Claude Code.
2. Analizar el script original catalogo/raices/build.py y el nuevo build_v2.py de la rama aislada.
3. Editar de forma acotada catalogo/raices/editorial.py solo si mejora el mensaje editorial; conservar nombres de variables y sintaxis.
4. Generar con python3 build_v2.py dentro de catalogo/raices.
5. Validar todas las páginas, conteo de SKUs, imágenes embebidas, ausencia de precios y vínculos a páginas originales.
6. Entregar PDF, preview, trazabilidad y auditoría sin publicar en producción.
