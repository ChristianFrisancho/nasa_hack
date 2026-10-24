#!/usr/bin/env python3
"""Curado manual, ronda 7: CE de agua de pozo en el acuífero Medio y Bajo Piura y en el Alto Piura.
Cada cifra fue leída en la fuente citada (texto guardado en fuentes_r7/). No hay CE de canal del Bajo Piura en fuentes
públicas legibles: esa fila sigue desconocida en curado_r3.csv. Escribe insumos/curado_r7.csv.
Uso: python3 tools/insumos_curados_r7.py
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "insumos" / "curado_r7.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fuente_primaria","subzona","fecha_consulta"]
ERH = ("ANA (oct-2015), Estudio de Evaluación de Recursos Hídricos de la Cuenca Piura (Valle Medio y Bajo Piura), cap. 9 hidrogeoquímica "
       "(copia SIGRID-CENEPRED, documento 9277)",
       "https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca//9277_evaluacion-de-recursos-hidricos-superficiales-en-la-cuenca-del-rio-piura-tomo-i.pdf")
OIEA = ("OIEA (2009), IAEA-TECDOC-1611 Estudios de hidrología isotópica en América Latina 2006, cap. 'El acuífero Alto Piura' "
        "(Universidad de Piura, IHHS), p. 159", "https://www-pub.iaea.org/MTCD/publications/PDF/TE_1611s_web.pdf")
FILAS = [
    dict(variable="ce_agua_riego", valor="", valor_min="0.75", valor_max="2.25", unidad="dS/m", cultivo="todos", zona="medio_bajo_piura",
         lugar="Pozos del acuífero Medio y Bajo Piura (mayoría de los 18 pozos IRHS analizados)", fecha_o_periodo="2014 (muestreo de sep-2014; estudio publicado 2015)",
         fuente=ERH[0], url_o_doi=ERH[1], tipo_evidencia="regional", estado="estimado",
         metodo="Clase de salinidad C3 (Richards, USSL 1954: 0,75-2,25 dS/m) que la fuente asigna a la mayoría de los pozos",
         notas=("Agua de pozo. La fuente dice: 'según el RAS y la conductividad eléctrica, las aguas para riego en la mayoría de las zonas que "
                "conforman el acuífero, se clasifican como C3S2, C3S1, C3S3 y C3S4'. El rango 0,75-2,25 dS/m es la definición de la clase C3, "
                "no una medición publicada pozo por pozo (las tablas del estudio son imágenes sin texto). El rango completo medido es "
                "0,04-16,83 dS/m (fila ce_agua_subterranea de curado_r4). Sólo el pozo IRHS-01 (Castilla) es apto sin restricción; "
                "IRHS-06 es el más salino y sódico. Muestreo bacteriológico fechado 19/09/2014; la fecha de las muestras de CE no está en el texto.")),
    dict(variable="ce_agua_subterranea", valor="", valor_min="", valor_max="", unidad="dS/m", cultivo="todos", zona="alto_piura",
         lugar="Acuífero Alto Piura, margen izquierda del río Piura (pozos)", fecha_o_periodo="desconocido (publicado 2009)",
         fuente=OIEA[0], url_o_doi=OIEA[1], tipo_evidencia="regional", estado="desconocido",
         metodo="Conductividad eléctrica de campo en pozos (sólo umbral cualitativo publicado)",
         notas=("Sin cifra puntual ni rango cerrado: la fuente dice que en la margen izquierda la CE 'fue superior a 1000 µS/cm' (> 1 dS/m; "
                "pozos ID 12-14, 25, 26, 28, 35, 36, 39, 17, 68, 69, 72, 73, 78-80, 96) y que en la margen derecha (NE) es menor a 1000 µS/cm. "
                "Un umbral abierto no cabe en valor_min/valor_max sin inventar el máximo.")),
]
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C); w.writeheader()
    for r in FILAS: w.writerow({c: r.get(c, "") for c in C} | {"fecha_consulta": "2026-10-24"})
print(f"OK {len(FILAS)} -> insumos/curado_r7.csv")
