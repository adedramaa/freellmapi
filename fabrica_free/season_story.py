"""Editorial fallback for a complete original, causally consistent six-part mystery season.
Conservatively authored text, not passed off as AI output.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Chapter:
    title:str
    lines:tuple[str,...]

CHAPTERS={
 1:Chapter("La llamada de mañana",(
  "A las tres y diecisiete, Vera despertó.",
  "Su teléfono mostraba una llamada perdida.",
  "Venía del número de su hermano.",
  "Pero Julián llevaba seis años desaparecido.",
  "Encontró un mensaje de apenas siete segundos.",
  "En la grabación escuchó su propia voz.",
  "Decía: nunca abras el cajón inferior.",
  "Vera miró hacia el escritorio vacío.",
  "El cajón ya estaba abierto.",
  "Dentro encontró una fotografía fechada mañana.",
  "La fotografía mostraba su habitación vacía.",
  "Alguien golpeó tres veces desde el armario."
 )),
 2:Chapter("El transmisor",(
  "Vera revisó el armario antes del amanecer.",
  "Detrás encontró un transmisor diminuto.",
  "Tenía una etiqueta escrita a mano: 47A.",
  "El aparato seguía enviando señales.",
  "Vera llamó a su antigua compañera Irene.",
  "Irene reconoció el código sin dudar.",
  "Pertenecía al Archivo Norte, donde trabajaba Julián.",
  "La última conexión ocurrió esa misma noche.",
  "Vera desconectó el transmisor con cuidado.",
  "Su teléfono se apagó de golpe.",
  "Entonces escuchó otra llamada desde el escritorio.",
  "Pero la pantalla seguía completamente negra."
 )),
 3:Chapter("Archivo Norte",(
  "Vera siguió el código hasta Archivo Norte.",
  "La entrada principal estaba sin vigilancia.",
  "Encontró el registro de visitas recientes.",
  "Allí figuraba el nombre de Julián.",
  "Alguien lo había firmado hacía dos días.",
  "Vera comparó la tinta con otra página.",
  "Ambas firmas estaban hechas por la misma mano.",
  "La segunda pertenecía al supervisor Leandro.",
  "Un guardia aseguró no reconocerla.",
  "Pero evitó mirarla cuando preguntó por Julián.",
  "Al salir encontró un sobre bajo su auto.",
  "Dentro había una llave marcada 47A."
 )),
 4:Chapter("La caja 47A",(
  "La llave llevó a Vera hasta un casillero.",
  "Dentro había fotografías editadas de su apartamento.",
  "Los archivos mostraban fechas que todavía no llegaban.",
  "Alguien fabricaba pruebas para asustarla.",
  "Vera encontró una lista de quienes tenían acceso.",
  "Entre ellos estaba Irene, su única aliada.",
  "Irene admitió haber entregado una llave.",
  "Dijo que Leandro amenazó a su familia.",
  "Pero Vera no sabía si creerle.",
  "Entonces Irene mostró una grabación secreta.",
  "Se veía a Julián entrando al archivo.",
  "Y la fecha correspondía a esa misma mañana."
 )),
 5:Chapter("La testigo",(
  "Irene entregó la grabación completa a Vera.",
  "Julián había descubierto archivos manipulados años atrás.",
  "Leandro ordenaba vigilar empleados y fabricar coartadas.",
  "Julián desapareció para proteger los documentos originales.",
  "Pero alguien descubrió su escondite hace dos días.",
  "La llamada era una advertencia grabada.",
  "El número de Julián había sido suplantado.",
  "Vera revisó las sombras de la grabación.",
  "Una señal indicaba el lugar donde se ocultaba.",
  "Irene reconoció una estación abandonada.",
  "Cuando llegaron, todas las puertas estaban abiertas.",
  "Al fondo se escuchó una voz familiar."
 )),
 6:Chapter("Las tres y diecisiete",(
  "Vera encontró a Julián detrás de una puerta.",
  "Estaba herido, pero llevaba consigo las pruebas.",
  "Leandro los había seguido hasta la estación.",
  "Irene activó la grabación de seguridad.",
  "Las amenazas quedaron registradas ante varios testigos.",
  "Vera entregó los documentos a la fiscalía.",
  "Julián explicó el truco de las llamadas.",
  "Un programa imitaba su número y su voz.",
  "Las fotografías eran montajes hechos para intimidar.",
  "Esa noche, por fin, pudieron dormir.",
  "Pero Vera encontró un expediente bajo su puerta.",
  "En la portada decía: caso 03:17."
 )),
}

def canonical_episode(part:int)->dict:
    if isinstance(part,bool) or not isinstance(part,int) or part not in CHAPTERS:
        raise ValueError("Solo episodios 1 a 6")
    chapter=CHAPTERS[part]
    for n,line in enumerate(chapter.lines,1):
        if not 8<=len(line)<=85 or len(line.split())>8:
            raise ValueError(f"Capitulo {part}, linea {n} no cumple el esquema")
    assert len(chapter.lines)==12
    return {"title":chapter.title,"lines":list(chapter.lines),
            "series":"EL ARCHIVO DE LAS 03:17","part":part}
