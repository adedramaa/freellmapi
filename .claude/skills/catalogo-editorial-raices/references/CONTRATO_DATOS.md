# Contrato de datos `catalogo.json`

Formato esperado, SIN contenido ficticio incluido en la skill:

```json
{
  "empresa": "Raíces Regalos",
  "titulo": "Catálogo mayorista",
  "moneda": "ARS",
  "fecha_corte": "AAAA-MM-DD",
  "fuentes": ["ruta o descripción inequívoca de lista oficial de precios"],
  "contacto": {"web": "https://URL-REAL-VERIFICADA"},
  "productos": [
    {
      "sku": "CODIGO-REAL",
      "nombre": "NOMBRE-REAL",
      "categoria": "CATEGORIA-REAL",
      "precio": 0,
      "fuente_precio": "identificador de fuente oficial",
      "imagen": "/ruta/absoluta/foto-oficial.jpg",
      "fuente_imagen": "origen verificable y autorizado",
      "verificado": true,
      "descripcion": "detalle técnico comprobado (opcional)"
    }
  ]
}
```

La estructura es demostrativa: `precio: 0` no es válido para publicación y deberá sustituirse por un importe real **verificado**. No copiar nombres/códigos de ejemplo en un catálogo.

- `verificado: true` debe significar que se comprobaron el producto, la foto y su precio mediante fuentes auténticas; no automatizar este campo sin prueba documental.
- `imagen` debe ser archivo local disponible; para URL remota, primero descargarla y asociarla al producto correcto con evidencia.
- `precio` es número positivo; `fuente_precio` indica una fuente inequívoca y de fecha vigente. Si hay IVA u otras condiciones de precios, reproducir SOLO aquellas autorizadas.
- `contacto.web` es opcional y se muestra solo cuando procede de fuente verificada. Nunca inventar teléfonos, emails o enlaces.
- La herramienta entregada es punto de partida tipográfico y de estructura; para complejidad, ampliar en Claude Code con plantilla/retícula aprobada.
