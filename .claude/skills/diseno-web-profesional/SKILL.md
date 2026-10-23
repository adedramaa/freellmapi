---
name: diseno-web-profesional
description: Protocolo obligatorio cuando se diseña, implementa, rediseña, mejora o audita la interfaz web o móvil de un proyecto. Orquesta Taste Skill, UI UX Pro Max, referencias visuales, Impeccable y subagentes de dirección visual, implementación y auditoría cuando estén disponibles.
---

# Protocolo de diseño web profesional para Claude Code

Aplicar a sitios web, apps, tiendas y dashboards. **No sustituye** el protocolo para catálogos PDF Raíces: `catalogo-editorial-raices` conserva prioridad total en ese ámbito.

## Herramientas del video
1. **Taste Skill** (`taste-skill@taste-skill`): criterio de dirección artística para evitar plantillas genéricas. Requiere Node 22+ y navegador Chrome/Chromium para validación completa.
2. **UI UX Pro Max** (`ui-ux-pro-max@ui-ux-pro-max-skill`): investigar paletas, pares tipográficos, layout y recomendaciones por tipo de negocio. Requiere Python 3 para búsquedas locales.
3. **Referencias**: leer `.claude/design-references.md`, registrar de 2 a 4 sitios pertinentes y sus principios aprovechables sin copiar el diseño original.
4. **Impeccable** (`impeccable@impeccable`): crítica y auditoría visual/a11y/responsividad. Usar sus comandos si la instalación está operativa.
5. **Subagentes**: delegar en `design-director`, `frontend-implementer` y `visual-auditor` según las herramientas y permisos de la sesión.

Los tres complementos son de terceros: no ejecutar instaladores arbitrarios, hooks desconocidos ni comandos de red que revelen secretos. Si una herramienta no está presente, registrar el faltante y seguir con comprobaciones manuales; nunca reportarla como instalada sin prueba.

## Flujo obligatorio
1. **Descubrir**: inspeccionar código existente, identidad, objetivos, dispositivo principal, páginas clave y restricciones. No cambiar sistemas de venta, base de datos ni despliegues solo por mejorar visuales.
2. **Dirección visual**: sintetizar 2–3 rutas realmente distintas, cada una con tipografía, contraste, tokens, densidad, personalidad y razones conectadas al negocio. Evitar copiar referencias y clichés de IA.
3. **Sistema**: definir paleta accesible, escala tipográfica, espaciamiento, botones, estados, iconos, grillas y criterios de fotografía, y documentar qué se elige.
4. **Construcción**: reutilizar el stack real del proyecto, no reescribir funciones que ya andan. Priorizar Android/mobile y escritorio; conservar accesibilidad, responsive y rendimiento.
5. **Inspección**: probar con navegador real en ~360px, ~768px y ~1440px cuando exista acceso, revisar capturas, contraste, desbordamientos, touch targets y estados de error. Ejecutar auditoría Impeccable si está disponible.
6. **Corrección**: resolver los tres problemas más visibles, volver a inspeccionar; no declarar aprobado únicamente por el lint.
7. **Entrega**: mostrar qué se cambió, capturas o artefactos reales y fallos pendientes. No desplegar/publicar sin permiso explícito.

## Criterios de aceptación
- Estilo propio, no plantilla SaaS indistinguible.
- Funcionamiento móvil sin desbordamientos, modales cortados ni reproductores descentrados.
- Contraste, accesibilidad y UX de navegación comprobados.
- Costo adicional cero, sin servicios premium obligatorios.
- Respetar archivos existentes, permisos limitados y revisión humana para cambios de producción.
- Sin navegador o sin permisos de subagentes: marcar auditoría visual como **pendiente**, no como superada.
