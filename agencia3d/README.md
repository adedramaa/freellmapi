# Agencia 3D — Blender real sin PC

Rama de prueba aislada, sin cambiar la rama principal.

Este prototipo ejecuta el programa **Blender de verdad** en un runner público estándar de GitHub Actions, sin GPU ni servicios pagados. El archivo `agencia3d/blender_pipeline.py` crea una figura de calibración (no el perro), renderiza dos imágenes y exporta archivos `.blend`, `.glb`, `.stl` y un manifiesto con SHA-256.

**Restricciones:** no ejecutar con runners grandes o privados; no agregar métodos de pago ni credenciales; el trabajo caduca a los 12 minutos y los artefactos se guardan solo un día.

**Importación de un GLB existente:** `blender -b --factory-startup --python agencia3d/blender_pipeline.py -- --out output --input modelo.glb`. Este modo está implementado pero no automatizado con TRELLIS.2.

**Pendiente:** aislar este proyecto en un repositorio público exclusivo, conectar imágenes con TRELLIS.2 y probar el resultado del perro. Esta prueba de Blender no demuestra fidelidad artística.
