# Catálogo Editorial Raíces — instalación en Claude Code sin PC

## Qué contiene
Skill personalizada `/catalogo-editorial-raices`, documentación de diseño/auditoría y herramientas gratuitas para validar JSON, crear HTML editorial y exportar a PDF con Playwright.

## Instalación en el entorno de Claude Code que TIENE acceso al proyecto
1. Adjunta este ZIP a una sesión/agente que pueda acceder a sus archivos (o súbelo al repositorio en el que corre Claude Code).
2. Pídele: «Extrae este ZIP en la raíz de mi proyecto, conservando la carpeta oculta `.claude/skills/catalogo-editorial-raices/`. No sobrescribas otras skills. Muéstrame los archivos instalados y verifica que Claude Code reconoce `/catalogo-editorial-raices`. No publiques nada todavía.»
3. Si prefieres todas tus sesiones locales/servidor del mismo usuario: copiar la carpeta `catalogo-editorial-raices` a `~/.claude/skills/`. Esto NO equivale a instalarla en Claude.ai o en sesiones de nube aisladas.
4. Si tu Claude está funcionando en una sesión cloud: habilita la skill desde la configuración de skills en claude.ai, o verifica si tu tipo de sesión carga las skills del repositorio. Las reglas de cloud y las de terminal son distintas.

## Skills oficiales recomendadas (instalar en Claude Code donde funcione /plugin)
```
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```
Estas dos colecciones incluyen `pdf`, `canvas-design` y `frontend-design`; primero verifica si ya se encuentran activas y evita duplicar instalaciones innecesarias.

## Primer encargo sugerido
«Usa `/catalogo-editorial-raices`. Audita el catálogo anterior de Raíces, con los productos/fotos/precios oficiales accesibles. No sustituyas ni inventes imágenes, precios, sets ni productos. Haz una primera prueba con portada y dos páginas internas, renderízalas e inspecciónalas, corrige problemas y luego genera el PDF candidato completo. Presenta log de fuentes y errores, sin publicarlo hasta mi aprobación.»

## Uso de herramientas incluidas
Instalar dependencias en el servidor/agente si ya no están disponibles (Playwright es gratuito, pero debe existir un navegador Chromium instalado con permisos adecuados):
```
python .claude/skills/catalogo-editorial-raices/scripts/validar_catalogo.py catalogo.json
python .claude/skills/catalogo-editorial-raices/scripts/construir_catalogo.py catalogo.json --out salida/catalogo.html
node .claude/skills/catalogo-editorial-raices/scripts/exportar_pdf.cjs salida/catalogo.html salida/catalogo.pdf
python .claude/skills/catalogo-editorial-raices/scripts/auditar_pdf.py salida/catalogo.pdf --catalogo catalogo.json --out salida/vistas
```
Si el comando de exportación informa que falta `playwright`, puedes instalar la dependencia en el servidor autorizado según tu entorno (`npm install playwright` y, si fuera necesario, `npx playwright install chromium`). Estas descargas son gratuitas pero requieren capacidad de servidor y red; no requieren que tú tengas una PC.

No se ha ejecutado esta skill en tu Claude Code: el ZIP está listo para instalar, NO representa una instalación ya hecha.

Fuentes:
- Anthropic Skills: https://github.com/anthropics/skills
- Claude Code Skills: https://code.claude.com/docs/en/skills
- Playwright PDF: https://playwright.dev/docs/api/class-page#page-pdf
