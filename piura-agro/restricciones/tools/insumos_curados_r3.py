#!/usr/bin/env python3
"""Curado manual, ronda 3 (steering 06:48): costos de leguminosas y papaya, CE del agua de riego por zona,
CE de suelo de tesis con su extracto. Cada cifra fue leída en la fuente citada; sin cifra, fila 'desconocido'.
Escribe insumos/curado_r3.csv.  Uso: python3 tools/insumos_curados_r3.py
"""
import csv
from pathlib import Path
from zonas import zona_lugar
from contrato import normalizar
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "insumos" / "curado_r3.csv"
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
ENA = ("INEI, Costos de producción para la actividad agricultura, ganadería, caza y silvicultura en base a la ENA 2018 (marzo 2021)",
       "https://www.inei.gob.pe/media/MenuRecursivo/investigaciones/costos-de-produccion-v7.pdf")
M_ENA = ("Costo de producción por UA de la ENA 2018; excluye depreciación, gastos administrativos y otros; "
         "UA pequeñas solo excedentarias (>=5 ha cosechadas)")
PAXI = ("Paxi Mamani, A. Y. (2022). Tesis UNJBG 'Características financiero-comerciales y su efecto sobre la rentabilidad del cultivo de vainita "
        "en los productores del distrito de La Yarada - Los Palos', tabla 5 (p. 22-23)",
        "https://repositorio.unjbg.edu.pe/bitstreams/3772bb9d-e571-4493-b534-cb71b4f912f3/download")
DRAT = "Dirección Regional Agraria Tacna - Dirección de Estadística Agraria (DEA-DRAT, 2014), costo estimado de producción de vainita"
COR = ("Coronel Chávez, S. (2021). Tesis doctoral UNP 'Evaluación de la calidad del agua a partir de indicadores biológicos del río Chira' (resumen en ALICIA)",
       "https://alicia.concytec.gob.pe/vufind/Record/RUMP_d09e47b2e18ce642f9b68f9a40aad3fe")
ANA_CH = ("ANA, nota de prensa del 10-may-2023 sobre el 24.º monitoreo participativo de calidad de agua en la cuenca Chira (2022)",
          "https://www.gob.pe/institucion/ana/noticias/755335")
ANA_PI = ("ANA, nota de prensa del 7-feb-2024 'Autoridad Nacional del Agua realiza monitoreo de la calidad del agua en el río Piura'",
          "https://www.gob.pe/institucion/ana/noticias/903270-autoridad-nacional-del-agua-realiza-monitoreo-de-la-calidad-del-agua-en-el-rio-piura")
GAR = ("García Ramos, K. M. (2022). Tesis UNP sobre calidad fisicoquímica del agua del canal Biaggio Arbulú, Castilla - Piura (resumen en ALICIA)",
       "https://alicia.concytec.gob.pe/vufind/Record/RUMP_2d9b598e96d96609a3bec74516783a5a")
SECH = ("Tesis UNP sobre el acuífero Sechura-Parachique con clasificación Wilcox (espejo CORE 270312601; no se pudo leer)",
        "https://core.ac.uk/download/pdf/270312601.pdf")
SLO = ("Sin fuente con cifra: búsqueda ALICIA/Tavily ronda 3 (río Chira, Poechos, San Lorenzo)",
       "https://alicia.concytec.gob.pe/vufind/Search/Results?lookfor=calidad+agua+San+Lorenzo+Piura")
ATO = ("Atoche Alvarado, L. A. (2025). Tesis UCV 'Efecto del carbofuran en la fertilidad de suelos agrícolas productoras de limón, Sullana - Perú 2024', tabla 4",
       "https://hdl.handle.net/20.500.12692/170943")

rows = []
# ---------- 1. costos (steering 3, punto 1) ----------
PAP = "Perú (agregado nacional; la ENA registra papaya sólo en selva)"
COMP_PAP = ("Zona no aplica: agregado nacional fuera de Piura. Comparabilidad: promedio nacional de la ENA 2018 y la propia ENA dice que la producción registrada de papaya es sólo de selva "
            "(Ucayali 3345,81 PEN/ha; Madre de Dios 3925,63 PEN/ha). En Piura la papaya sería de costa con riego por gravedad o goteo; "
            "la cifra no incluye costo de agua de riego relevante ni depreciación, y los jornales son 54,9 % del costo. "
            "Probablemente subestima el costo en Piura; usar sólo como orden de magnitud. ")
rows += [
 r("costo_produccion", "3940.3", "PEN/ha", "papaya", PAP, "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   COMP_PAP + "Rango = mínimo y máximo departamental del cuadro N° 55 (p. 157-158). UA pequeñas 4428,76; medianas 3652,06 PEN/ha.",
   vmin="1092.1", vmax="9419.1", etapa="campaña completa", zona="", primaria="INEI, ENA 2018"),
 r("costo_produccion_por_t", "337.70", "PEN/t", "papaya", PAP, "2018 (ENA 2018)", ENA, M_ENA + "; costo por t = costo por ha / rendimiento medio 11668 kg/ha",
   "analogo_externo", "observado", COMP_PAP + "Sin rango por tonelada en la fuente; UA pequeñas 382,62, medianas 311,54 PEN/t (rango de referencia).",
   etapa="campaña completa", zona=""),
 r("rendimiento", "11668", "kg/ha", "papaya", PAP, "2018 (ENA 2018)", ENA, "Rendimiento medio declarado en la ENA 2018 (sección 8.1.53)", "analogo_externo", "estimado",
   COMP_PAP + "Rango de referencia por tecnología: UA pequeñas 11575, medianas 11723 kg/ha. Rendimiento declarado, no pesado.",
   etapa="cosecha", zona=""),
]
TAC = "Distrito La Yarada - Los Palos, Tacna"
COMP_V = ("Zona no aplica: Tacna, fuera de Piura. Comparabilidad: costa sur (Tacna), riego por goteo con bombeo (agua 720 + rebombeo 720 PEN/ha), tecnología media, variedad Venus, "
          "precios de 2014 (jornal 45 PEN). En Piura el riego es mayormente por gravedad con tarifa de agua menor y el jornal es distinto; "
          "no hay hoja de costos de vainita o frijol en verde para Piura en las fuentes revisadas. ")
rows += [
 r("costo_produccion", "10327.07", "PEN/ha", "frijol verde", TAC, "2014 (hoja DRA Tacna, citada en 2022)", PAXI,
   "Hoja de costo estimado de producción por ha (costos directos 9139,00 + indirectos 1188,07)", "analogo_externo", "estimado",
   COMP_V + "Mano de obra 3915; insumos 4739; envases y herramientas 485 PEN/ha. Es costo presupuestado, no encuesta: por eso estimado. Sin rango en la hoja.",
   etapa="campaña completa", variedad="vainita (vaina verde), var. Venus", zona="", primaria=DRAT),
 r("rendimiento", "8697", "kg/ha", "frijol verde", TAC, "2014 (hoja DRA Tacna, citada en 2022)", PAXI,
   "Rendimiento supuesto en la hoja de costos de la DRA Tacna", "analogo_externo", "estimado",
   COMP_V + "Rango regional de la misma tesis (tabla 3, Tacna 2012-2015): 6515,92 a 8696,68 kg/ha.",
   etapa="cosecha", variedad="vainita (vaina verde), var. Venus", zona="", primaria=DRAT),
]
COMP_C = ("Zona no aplica: agregado de la costa peruana. Comparabilidad: es el costo del frijol grano seco (Phaseolus vulgaris) de la costa peruana, no de caupí (Vigna unguiculata); "
          "la ENA 2018 no tiene sección de caupí. Ambas son leguminosas de grano de ciclo corto con labores parecidas, pero el caupí "
          "suele usar menos insumos; el agregado costa incluye Piura y excluye depreciación. Proxy, no medición del caupí. ")
rows += [
 r("costo_produccion", "1531.01", "PEN/ha", "frijol caupí", "Región natural costa (Perú)", "2018 (ENA 2018)", ENA, M_ENA + "; cifra de frijol grano seco usada como proxy",
   "analogo_externo", "estimado", COMP_C + "Rango de referencia del frijol grano seco por tecnología: UA pequeñas 1330,62, medianas 1116,42 PEN/ha (nacional).",
   etapa="campaña completa", zona="", primaria="INEI, ENA 2018, sección 8.1.25 Frijol grano seco"),
 r("costo_produccion", "", "PEN/ha", "frijol de palo", "Piura (departamento)", "2018-2026", ENA,
   "Búsqueda en el texto completo de la ENA 2018 y en ALICIA/Tavily (ronda 3)", "regional", "desconocido",
   "Sin cifra: el frijol de palo (Cajanus cajan) sólo aparece en el ranking de cultivos de la ENA, sin sección de costos; no se halló hoja de costos de DRA Piura ni tesis con costos. "
   "No se usa proxy porque es arbustivo semiperenne y su costo no se parece al de un frijol anual.",
   etapa="campaña completa", zona="piura_region"),
]
# ---------- 2. CE del agua de riego (steering 3, punto 2) ----------
rows += [
 r("ce_agua_riego", "", "dS/m", "ninguno", "Río Chira, tramo urbano de Sullana (Puente viejo)", "c. 2019-2021 (fechas de muestreo no están en el resumen)", COR,
   "Conductividad medida en agua del río en puntos de muestreo de la tesis (resumen)", "medicion_local", "observado",
   "Publicado como 373 a 1167 µS/cm; convertido a dS/m dividiendo entre 1000. Es agua del río que alimenta las tomas de riego del valle del Chira, no agua medida en el canal. "
   "TDS 187-550 mg/L; temperatura 27,4-28,9 °C. Número de muestras y fechas no figuran en el resumen; el PDF (repositorio UNP) no responde desde la caja. Sin valor central.",
   vmin="0.373", vmax="1.167", zona="chira"),
 r("ce_agua_riego", "", "dS/m", "ninguno", "Río Chira, puntos RChir6, RChir7 y RChir8 (ANA)", "2022 (24.º monitoreo)", ANA_CH,
   "Monitoreo participativo de calidad de agua de la ANA", "regional", "desconocido",
   "La nota dice que esos puntos superan el ECA-Agua categoría 3 en conductividad, es decir más de 2500 µS/cm (> 2,5 dS/m), pero no publica el valor. "
   "El informe técnico no se pudo descargar (repositorio ANA inaccesible). Señal cualitativa de agua salina en tramos del Chira; no hay cifra.", zona="chira"),
 r("ce_agua_riego", "", "dS/m", "ninguno", "Canal Biaggio Arbulú, Castilla (Medio Piura)", "2022", GAR,
   "Análisis fisicoquímico de 27 muestras en 3 tramos del canal (resumen)", "medicion_local", "desconocido",
   "La tesis midió conductividad pero el resumen no da cifras y el PDF (repositorio UNP) no responde. Un documento de Scribd sobre el mismo canal cita un máximo de 1948 µS/cm; "
   "no se carga porque no se pudo verificar autor ni original. Es el canal principal que lleva agua del río Piura (presa Los Ejidos) al Bajo Piura.", zona="medio_piura"),
 r("ce_agua_riego", "", "dS/m", "ninguno", "Bajo Piura: río Piura aguas abajo de Los Ejidos y canales de riego", "2020-2024", ANA_PI,
   "Mediciones de campo de conductividad de la ANA (ALA Medio y Bajo Piura), enero 2024", "regional", "desconocido",
   "La nota dice que la conductividad supera el ECA-Agua (> 2500 µS/cm, > 2,5 dS/m) en la quebrada Sofía por drenaje agrícola, sin dar valores para el río Piura ni los canales. "
   "El informe técnico N.° 011-2021-ANA-AAA-JZ-ALA-APH (monitoreo oct-2020, 11 puntos) sólo está en Scribd, sin texto extraíble. "
   "Para pozos del Medio y Bajo Piura ver la fila ce_agua_subterranea de la ANA (0,04-16,83 dS/m), que no es agua de canal.", zona="bajo_piura"),
 r("ce_agua_riego", "", "dS/m", "ninguno", "Tablazo Sur, pozos (La Unión - Sechura)", "sin fecha", SECH,
   "Clasificación Wilcox de pozos del acuífero Sechura-Parachique (no leída)", "medicion_local", "desconocido",
   "Fuente candidata con CE de pozos: el PDF en CORE devolvió 403 (Cloudflare), el espejo files01 dio 522 y la extracción Tavily falló. "
   "La salinidad de suelo del Tablazo Sur (Mendoza 2025, 3,44-8,2 dS/m) hace pensar en agua de pozo salina, pero no hay cifra de agua.",
   zona="bajo_piura", subzona="Tablazo Sur"),
 r("ce_agua_riego", "", "dS/m", "ninguno", "San Lorenzo: reservorio San Lorenzo y canales (agua del Chira vía Poechos)", "sin fecha", SLO,
   "Búsqueda ALICIA y Tavily", "regional", "desconocido",
   "No se halló medición de conductividad del agua de riego en San Lorenzo ni en Poechos. El río Chira en Sullana da 0,373-1,167 dS/m (otra fila), pero no se transfiere aquí sin dato.",
   zona="san_lorenzo"),
]
# ---------- 3. CE de suelo de tesis y su extracto (steering 3, punto 3) ----------
rows += [
 r("ce_suelo", "0.103", "dS/m", "limón", "Sullana, parcela de limón (muestra Base #00)", "2024-08-08", ATO,
   "Informe de laboratorio INIA, una muestra de línea base; la tesis no declara el extracto (pasta saturada u otro)", "medicion_local", "observado",
   "Publicado 10,3 mS/m; 1 mS/m = 0,01 dS/m, así que 0,103 dS/m. El texto de la tesis dice por error '10.3 dS/m'; el resumen y la tabla dicen mS/m. "
   "Suelo arenoso (arena 93,3 %), pH 7,8, MO 1,2 %. Rango de referencia de los tratamientos con carbofuran (no son línea base): 8 a 11,7 mS/m según el resumen.",
   zona="chira"),
]
# ---------- 4. camote (tarea 4): costo y rendimiento de costa central como análogo ----------
MCAM = ("MIDAGRI, El cultivo de camote, oportunidad comercial y sostenibilidad económica, N.° 003-2026 (mayo 2026)",
        "https://repositorio.midagri.gob.pe/bitstream/20.500.13036/2238/1/El%20Cultivo%20de%20Camote%2C%20Oportunidad%20Comercial%20y%20Sostenibilidad%20Econ%C3%B3mica.pdf")
COMP_CAM = ("Zona no aplica: valle de Cañete (Lima), fuera de Piura. Comparabilidad: costa central con riego por gravedad, variedad Jonathan mayoritaria; "
            "el costo incluye alquiler de terreno (36 %) y gastos administrativos y financieros (17 %), que el modelo de Piura quizá no cuente. ")
rows += [
 r("costo_produccion", "16340", "PEN/ha", "camote", "Valle de Cañete, Lima", "2024", MCAM,
   "Cifra aproximada que MIDAGRI cita de la Universidad Nacional de Cañete (2024); no es encuesta propia", "analogo_externo", "estimado",
   COMP_CAM + "Sin rango en la fuente ('aproximadamente'). Estructura: alquiler 36 %, insumos 12 %, mano de obra 28 %, administrativos y financieros 17 %, maquinaria 7 %.",
   zona="", primaria="Universidad Nacional de Cañete (2024), citada por MIDAGRI"),
 r("rendimiento", "", "kg/ha", "camote", "Valle de Cañete, Lima", "2024", MCAM,
   "Rango declarado por MIDAGRI citando a la Universidad Nacional de Cañete (2024); depende de manejo, suelo y agua", "analogo_externo", "estimado",
   COMP_CAM + "La fuente da sólo el rango de 25 a 40 t/ha, sin promedio.", vmin="25000", vmax="40000",
   zona="", primaria="Universidad Nacional de Cañete (2024), citada por MIDAGRI"),
]
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows([normalizar(x) for x in rows])
print(f"OK {len(rows)} -> {OUT.relative_to(BASE)}")
