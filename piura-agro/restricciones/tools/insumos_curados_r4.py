#!/usr/bin/env python3
"""Curado manual, ronda 4 (steering 07:16): costo por ha de caupí (frijol castilla) en Piura y costa norte,
agua de riego (requerimiento bruto Alto Piura, módulos de fichas técnicas), CE de agua subterránea con fecha,
costos de frijol de palo y papaya. Cada cifra fue leída en la fuente citada; si la fuente es ambigua, valor vacío y rango.
Escribe insumos/curado_r4.csv.  Uso: python3 tools/insumos_curados_r4.py
"""
import csv
from pathlib import Path
from contrato import normalizar
from zonas import zona_lugar

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "insumos" / "curado_r4.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fuente_primaria","subzona","fecha_consulta"]

def r(variable, valor, unidad, cultivo, lugar, periodo, src, metodo, tipo, estado, notas, vmin="", vmax="", etapa="",
      variedad="", zona=None, primaria="", subzona=""):
    if zona is None:
        zona, nz = zona_lugar(lugar)
        if nz: notas = notas + " " + nz
    if valor and not vmin and not vmax and "rango" not in notas.lower():
        notas += " Sin rango: la fuente publica una sola cifra, sin error ni intervalo."
    return dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo, variedad=variedad,
                etapa=etapa, zona=zona, lugar=lugar, lat="", lon="", fecha_o_periodo=periodo, fuente=src[0], url_o_doi=src[1],
                metodo=metodo, tipo_evidencia=tipo, estado=estado, notas=notas, fuente_primaria=primaria, subzona=subzona,
                fecha_consulta="2026-10-24")


# ---------- fuentes ----------
PEIHAP = ("GORE Piura - PEIHAP (Proyecto Especial de Irrigación e Hidroenergético del Alto Piura), Agroboletín Año I N.º 1 (junio 2009), "
          "ficha técnica 'Características de mercado y producción del frejol castilla o chileno' (cuadros N.º 1 y costo de producción por ha); copia pública en Scribd",
          "https://es.scribd.com/document/43389676/agroboletin001-frijol")
LL = ("Hoja 'Costos de producción de cultivos transitorios', frijol castilla, provincia de Trujillo (La Libertad), costos al 28-feb-2021, nivel tecnológico medio; "
      "institución autora no indicada en la copia (formato de agencia agraria); copia pública en Scribd",
      "https://es.scribd.com/document/711097996/COSTO-DE-PRODUCCION-FRIJOL-TRUJILLO-2021")
INIA432 = ("Agraria.pe (5-dic-2013), 'EEA Vista Florida liberará variedad frijol caupí INIA-432 Vaina Verde' (entrevista al obtentor, Ing. Fernando Montero, INIA)",
           "https://agraria.pe/noticias/eea-vista-florida-liberara-variedad-frijol-caupi-%E2%80%9Cinia-432-v-5730")
DRA25 = ("DRA Piura, nota de prensa del 5-sep-2025 'Producción de frejol caupí en Piura casi quintuplica su volumen en un año'",
         "https://www.gob.pe/institucion/regionpiura-dra/noticias/1240664-produccion-de-frejol-caupi-en-piura-casi-quintuplica-su-volumen-en-un-ano")
ANA15 = ("ANA (oct-2015), Evaluación de recursos hídricos superficiales en la cuenca del río Piura, Tomo I (copia en la biblioteca SIGRID-CENEPRED)",
         "https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca//9277_evaluacion-de-recursos-hidricos-superficiales-en-la-cuenca-del-rio-piura-tomo-i.pdf")
EUMED = ("Amorós, W. et al. (2007), libro eumed.net 'Cultivos alternativos para la costa norte', capítulo frijol de palo (datos de Lambayeque c. 2003)",
         "https://www.eumed.net/libros-gratis/2007a/261/7.htm")
INFOM = ("Infomercado (8-sep-2022), nota sobre papaya en Miguel Pampa, San Juan de Bigote (Morropón), testimonio del productor Adelmo Mondragón",
         "https://infomercado.pe/agricultura-que-tan-rentable-es-tener-un-huerto-de-papaya-en-piura-cultivos-fertilizante-080922-mc")

COMP_LL = ("Zona no aplica: La Libertad, costa norte fuera de Piura. Comparabilidad: misma especie y tipo comercial (frijol castilla, Vigna unguiculata), "
           "costa norte con riego por surcos; jornal 30 PEN y agua por gravedad casi gratuita (0,001 USD/m3), como en Piura. "
           "Difiere en año (2021) y valle; es hoja presupuestada, no encuesta. ")
COMP_LAM = ("Zona no aplica: Lambayeque, costa norte fuera de Piura. Comparabilidad: valle costero vecino con el mismo régimen de riego por gravedad; "
            "la fuente dice que la variedad se desarrolló para Piura, Lambayeque, La Libertad y Lima norte. ")

rows = []
# ---------- 1. caupí (prioridad n.º 1) ----------
AP = "Valle del Alto Piura, Piura"
N_PEI = ("Ficha técnica del proyecto especial regional (presupuesto por ha, no encuesta): por eso estimado. Precio en chacra supuesto 2397,95 PEN/t; 69 jornales/ha; "
         "semilla 60 kg/ha; riego por surco. ")
rows += [
 r("costo_produccion", "2079.00", "PEN/ha", "frijol caupí", AP, "2009 (precios jun-2009)", PEIHAP,
   "Costo de producción por ha de la ficha técnica PEIHAP, situación actual (rendimiento 1000 kg/ha)", "regional", "estimado",
   N_PEI + "Situación actual con rendimiento 1000 kg/ha; la utilidad bruta declarada es 318 PEN/ha. Sin rango: una sola cifra presupuestada.",
   etapa="campaña completa", variedad="Castilla (chileno, boca negra) - tecnología actual", zona="alto_piura", primaria="GORE Piura - PEIHAP"),
 r("costo_produccion", "3181.30", "PEN/ha", "frijol caupí", AP, "2009 (precios jun-2009)", PEIHAP,
   "Costo de producción por ha detallado de la ficha PEIHAP, manejo optimizado (rendimiento 2000 kg/ha)", "regional", "estimado",
   N_PEI + "Rango interno de la propia fuente: el cuadro N.º 1 dice 3183,50 PEN/ha y el texto 3181,30; se toma la hoja detallada. "
   "Estructura: mano de obra 1312,3 (41,3 %); insumos y materiales 1226,9 (38,5 %), incluye tarifa de agua 60 PEN (6000 m3 a 0,01); maquinaria 276,08; "
   "gastos generales 8 % e imprevistos 5 %.",
   vmin="3181.30", vmax="3183.50", etapa="campaña completa", variedad="Castilla (chileno, boca negra) - tecnología optimizada", zona="alto_piura",
   primaria="GORE Piura - PEIHAP"),
 r("rendimiento", "1000", "kg/ha", "frijol caupí", AP, "2009", PEIHAP, "Rendimiento actual declarado en la ficha técnica PEIHAP", "regional", "estimado",
   N_PEI + "Sin rango estadístico; la ficha da 2000 kg/ha como rendimiento potencial con manejo óptimo.", etapa="cosecha", variedad="Castilla (chileno, boca negra)",
   zona="alto_piura"),
 r("modulo_riego", "6000", "m3/ha", "frijol caupí", AP, "2009", PEIHAP, "Módulo de riego por campaña de la ficha técnica PEIHAP", "regional", "estimado",
   "Módulo de ficha técnica (planificación), no entrega medida ni dotación de la ANA. Riegos frecuentes con poco volumen. Sin rango.",
   etapa="campaña completa", variedad="Castilla (chileno, boca negra)", zona="alto_piura"),
]
TRU = "Provincia de Trujillo, La Libertad"
rows += [
 r("costo_produccion", "3248.66", "PEN/ha", "frijol caupí", TRU, "2021 (costos al 28-feb-2021)", LL,
   "Hoja de costos de producción por ha, nivel tecnológico medio, riego por surcos (directos 782,88 + indirectos 109,60 USD, a 3,64 PEN/USD)",
   "analogo_externo", "estimado",
   COMP_LL + "Equivale a 892,49 USD/ha. Rendimiento supuesto 2000 kg/ha y precio en chacra 2,18 PEN/kg. "
   "Ojo: la hoja rotula 'Utilidad S/ 4045,28', pero 4360 - 3248,66 = 1111,34 PEN/ha; el error está en la fuente. Sin rango.",
   etapa="campaña completa", variedad="Castilla", zona=""),
 r("modulo_riego", "5000", "m3/ha", "frijol caupí", TRU, "2021 (costos al 28-feb-2021)", LL, "Volumen de agua presupuestado en la hoja de costos",
   "analogo_externo", "estimado", COMP_LL + "Agua de gravedad presupuestada en la hoja, no medida. Sin rango.", etapa="campaña completa", variedad="Castilla", zona=""),
]
VF = "EEA Vista Florida, Lambayeque"
rows += [
 r("requerimiento_hidrico_cultivo", "3000", "m3/ha", "frijol caupí", VF, "2013", INIA432, "Requerimiento hídrico por campaña (4 meses) declarado por el obtentor",
   "analogo_externo", "estimado", COMP_LAM + "Declaración del obtentor en entrevista, no ensayo publicado. Sin rango.", etapa="campaña completa",
   variedad="INIA 432 Vaina Verde", zona=""),
 r("rendimiento", "3500", "kg/ha", "frijol caupí", VF, "2013", INIA432, "Rendimiento declarado por el obtentor al liberar la variedad",
   "analogo_externo", "estimado", COMP_LAM + "Rendimiento potencial de estación, no de agricultor. Sin rango.", etapa="cosecha",
   variedad="INIA 432 Vaina Verde", zona=""),
]
PIU = "Región Piura (total departamental)"
rows += [
 r("rendimiento", "1459.7", "kg/ha", "frijol caupí", PIU, "2025", DRA25, "Cociente calculado: producción 14324 t / área cosechada 9813 ha (nota DRA Piura)",
   "regional", "estimado", "Cálculo propio a partir de dos cifras oficiales; no es un rendimiento publicado. Sin rango.", etapa="cosecha", zona="piura_region"),
 r("rendimiento", "2013.5", "kg/ha", "frijol caupí", PIU, "2024", DRA25, "Cociente calculado: producción 2982 t / área cosechada 1481 ha (nota DRA Piura)",
   "regional", "estimado", "Cálculo propio a partir de dos cifras oficiales; no es un rendimiento publicado. Sin rango.", etapa="cosecha", zona="piura_region"),
]
# ---------- 2. agua ----------
rows += [
 r("requerimiento_riego_bruto", "", "m3/ha/año", "todos", "Valle del Alto Piura (10 comisiones de usuarios, 49 bloques)", "cédula de cultivo usada en 2015", ANA15,
   "Requerimiento bruto = neto (cédula de cultivo) / eficiencia de riego 30-45 %, cuadro N.º 4.17", "regional", "estimado",
   "La fuente dice 'requerimiento promedio por hectárea de 10274,00 m3/ha', pero 330,23 MMC / 19678,25 ha = 16781 m3/ha. No sé cuál es el correcto: "
   "dejo el valor vacío y el rango entre ambas cifras. Requerimiento neto 136,88 MMC (unos 6956 m3/ha). No es dotación asignada ni dato 2023-26.",
   vmin="10274", vmax="16781", zona="alto_piura"),
]
# ---------- 3. CE agua subterránea ----------
rows += [
 r("ce_agua_subterranea", "", "dS/m", "todos", "Valle Medio y Bajo Piura (pozos IRHS)", "c. 2014 (estudio publicado oct-2015)", ANA15,
   "CE medida en laboratorio (UDEP y EQUAS) en 18 pozos del inventario, más 1 pozo adicional en EQUAS", "regional", "observado",
   "Rango de la fuente: 0,04 (IRHS-46, Piura) a 16,83 mmhos/cm (IRHS-68, Catacaos); 1 mmho/cm = 1 dS/m. Clases C3S1 a C3S4. "
   "Es el mismo rango que la fila 421935e783db, ahora con fuente fechada y legible. Boro 0,24-2,68 ppm. La fecha exacta del muestreo no está en el texto extraído.",
   vmin="0.04", vmax="16.83", zona="medio_bajo_piura"),
]
# ---------- 4. frijol de palo y papaya ----------
COMP_FP = ("Zona no aplica: Lambayeque, costa norte fuera de Piura. Comparabilidad: valle costero vecino, pero datos de c. 2003 en USD corrientes; "
           "no hay costo de frijol de palo para Piura en las fuentes revisadas. ")
rows += [
 r("costo_produccion", "1000", "USD/ha", "frijol de palo", "Lambayeque (costa norte)", "c. 2003", EUMED, "Costo de cultivo (400 USD/ha) más cosecha (600 USD/ha) citado en el libro",
   "analogo_externo", "estimado", COMP_FP + "Rendimiento 10 t/ha de vaina verde; precio en chacra 0,5 PEN/kg (rango 0,30-0,60). Sin rango para el costo.",
   etapa="campaña completa", zona=""),
 r("requerimiento_hidrico_cultivo", "5000", "m3/ha", "frijol de palo", "Lambayeque (costa norte)", "c. 2003", EUMED, "Requerimiento de agua citado en el libro",
   "analogo_externo", "estimado", COMP_FP + "El libro dice que de esos 5000 m3/ha sólo hay disponibles 2000-3000 (rango de disponibilidad). Sin rango para el requerimiento.",
   etapa="campaña completa", zona=""),
 r("costo_instalacion", "", "PEN/ha", "papaya", "Miguel Pampa, San Juan de Bigote (Morropón), Alto Piura", "2022", INFOM,
   "Inversión de instalación (plantas y asistencia) declarada por un productor", "regional", "estimado",
   "Testimonio de un productor en prensa, no hoja de costos: usar sólo como orden de magnitud. Rango declarado 30000-40000 PEN/ha; 2000-2500 plantas/ha; "
   "precio 0,60-1,20 PEN/kg. No cargo rendimiento: los 180 kg/planta darían 360-450 t/ha, una cifra no creíble por campaña.",
   vmin="30000", vmax="40000", zona="alto_piura"),
]

if __name__ == "__main__":
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows([normalizar(x) for x in rows])
    print(f"OK {len(rows)} -> {OUT.relative_to(BASE)}")
