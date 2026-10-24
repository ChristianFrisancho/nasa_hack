#!/usr/bin/env python3
"""Curado manual, ronda 2: ECe de chacra, napa/salinidad por zona, agua San Lorenzo, costos MAD y algodón.
Cada cifra fue leída en la fuente citada (PDF, texto extraído o resumen ALICIA). Escribe insumos/curado_r2.csv.
Uso: python3 tools/insumos_curados_r2.py
"""
import csv, re, statistics as st
from pathlib import Path
from zonas import zona_lugar
from contrato import normalizar
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "insumos" / "curado_r2.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fecha_consulta"]

def r(variable, valor, unidad, cultivo, lugar, periodo, src, metodo, tipo, estado, notas, vmin="", vmax="", etapa="", variedad="", zona=None, lat="", lon=""):
    if zona is None:
        zona, nz = zona_lugar(lugar)
        if nz: notas = notas + " " + nz
    if valor and not vmin and not vmax and "rango" not in notas.lower():
        notas += " Sin rango: la fuente publica una sola cifra, sin error ni intervalo."
    return dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo, variedad=variedad,
                etapa=etapa, zona=zona, lugar=lugar, lat=lat, lon=lon, fecha_o_periodo=periodo, fuente=src[0], url_o_doi=src[1],
                metodo=metodo, tipo_evidencia=tipo, estado=estado, notas=notas, fecha_consulta="2026-10-24")

MEN = ("Mendoza Flores, E. C. (2025). Tesis UCV 'Análisis de la salinización antropogénica de suelos agrícolas usando tecnología satelital en Tablazo Sur, Piura 2024', tablas 2 y 3",
       "https://hdl.handle.net/20.500.12692/170594")
HUA = ("La Rosa Reyes, L. F. (2021). Tesis UCV sobre suelos agrícolas con siembra intensiva de arroz en el sector El Huaro, distrito Buenos Aires, Morropón, Piura (resumen en ALICIA)",
       "https://hdl.handle.net/20.500.12692/76359")
QUI = ("Vite Córdova, M. A. (2015). Tesis UNP sobre fenología y adaptabilidad de la quinua en el valle Medio Piura (resumen en ALICIA)",
       "https://repositorio.unp.edu.pe/handle/UNP/408")
CAS = ("Castillo Albines, C. (s. f., c. 2001). 'Mapa de peligros de las cuencas de los ríos Piura y Chira'; cita a Colombi-Mendivil (1978) y Asociación de Consultores Proyecto Chira-Piura (1978)",
       "http://peru.inka.free.fr/peru/pdf/cuencpi.pdf")
PG = ("ANA (2015). Plan de Gestión de los Recursos Hídricos de la cuenca Chira-Piura, ISBN 978-612-4273-02-5",
      "https://crhc.ana.gob.pe/chira-piura/sites/default/files/archivos/PLAN%20de%20GESTI%C3%93N%20de%20los%20RECURSOS%20H%C3%8DDRICOS%20de%20la%20CUENCA%20CHIRA-PIURA.pdf")
GS = ("García Samamé, E. (2024). Tesis de maestría UNALM sobre gestión del agua en organizaciones de usuarios a trece años de la ANA; capítulo Junta de Usuarios San Lorenzo",
      "https://hdl.handle.net/20.500.12996/6245")
RVT = ("Rodríguez Valdez, D. E. Tesis de maestría UNALM sobre semilla certificada de maíz amarillo duro en el Bajo Piura, tabla 15 (encuestas 2021)",
       "https://hdl.handle.net/20.500.12996/5797")
RVA = ("Rodríguez Valdez, D. E. et al. (2025). Artículo en LATAM Rev. Latinoam. Cienc. Soc. Humanid. VI(3) sobre MAD con semilla certificada en el Bajo Piura, tabla 1",
       "https://dialnet.unirioja.es/descarga/articulo/10209389.pdf")
DRA = ("DRA Piura, nota de prensa sobre impulso al algodón (24-mar-2022)",
       "https://www.gob.pe/institucion/regionpiura-dra/noticias/621688")
DRAP = ("GORE Piura - DRA Piura, Campaña agrícola de los principales cultivos (datos abiertos); cálculo propio sobre insumos/drap_distrito_anual.csv",
        "https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp")

TS = "Tablazo Sur, distrito La Unión (Piura)"
M_MEN = "Análisis de laboratorio de 40 predios agrupados en 8 puntos (Río, Vega, Tendido medio, Los Hornos); la tesis no declara el extracto (pasta saturada u otro)"
rows = [
 r("ce_suelo", "", "dS/m", "todos", TS, "2024", MEN, M_MEN, "medicion_local", "observado",
   "Mínimo Río M2 (3,44; sódico), máximo Tendido medio M6 (8,2; salino sódico). Valores por punto: 5,53; 3,44; 6,05; 3,60; 7,8; 8,2; 3,64; 4,68. Unidad no escrita en la tabla; la tesis usa el umbral de 4 dS/m (USDA), así que se lee en dS/m. Extracto no declarado: no tratar como ECe de pasta saturada sin confirmar. Sin valor central: la tabla no da media.",
   vmin="3.44", vmax="8.2"),
 r("psi_suelo", "", "%", "todos", TS, "2024", MEN, M_MEN, "medicion_local", "observado",
   "Porcentaje de sodio intercambiable por punto: 7,30; 17,73; 17,61; 16,63; 15,98; 15,11; 15,20; 16,27. Sin valor central publicado.", vmin="7.30", vmax="17.73"),
 r("fraccion_predios_salinos", "5", "%", "todos", TS, "2024", MEN, "Clasificación USDA (CE>=4, PSI<15) de 40 predios", "medicion_local", "observado",
   "2 de 40 predios. Normal 0 %. Conteo exacto de una muestra no probabilística, por eso sin rango."),
 r("fraccion_predios_sodicos", "52.5", "%", "todos", TS, "2024", MEN, "Clasificación USDA (CE<4, PSI>=15) de 40 predios", "medicion_local", "observado",
   "21 de 40 predios. Conteo exacto de una muestra no probabilística, por eso sin rango."),
 r("fraccion_predios_salino_sodicos", "42.5", "%", "todos", TS, "2024", MEN, "Clasificación USDA (CE>=4, PSI>=15) de 40 predios", "medicion_local", "observado",
   "17 de 40 predios; la tabla 3 imprime 42 % (17/40 = 42,5 %). Conteo exacto, por eso sin rango."),
]
HU = "Sector El Huaro, distrito Buenos Aires, provincia Morropón (Piura)"
M_HU = "Análisis de suelo de laboratorio en 3 estaciones de muestreo del sector; extracto de CE no indicado en el resumen"
NOTA_HU = "Leído en el resumen (ALICIA); el PDF no responde desde la caja. Suelo con arroz en monocultivo y riego por inundación. "
rows += [
 r("ce_suelo", "", "dS/m", "arroz", HU, "2021", HUA, M_HU, "medicion_local", "observado",
   NOTA_HU + "Estación 1: 0,46; estación 2: 0,58; estación 3: 0,6 dS/m ('muy ligera'). Extracto no declarado. Sin valor central publicado. PDF completo revisado en ronda 3 (fuentes_r3/larosa.pdf): el informe del laboratorio de la UNP da la CE en dS/m sin nombrar el extracto; sólo el pH declara suelo:agua 1:2,5, así que el extracto de la CE sigue sin declarar.", vmin="0.46", vmax="0.6", zona="alto_piura"),
 r("materia_organica", "", "%", "arroz", HU, "2021", HUA, M_HU, "medicion_local", "observado",
   NOTA_HU + "Estaciones 1-3: 0,18; 0,69; 0,8 % ('muy bajo'). Sin valor central publicado.", vmin="0.18", vmax="0.8", zona="alto_piura"),
 r("cic", "", "cmol/kg", "arroz", HU, "2021", HUA, M_HU, "medicion_local", "observado",
   NOTA_HU + "Publicado en meq/100 g (= cmol/kg). Estaciones 1-3: 4,52; 12,20; 14,86. Texturas: franco arenoso, franco, franco arcilloso. Sin valor central publicado.", vmin="4.52", vmax="14.86", zona="alto_piura"),
 r("nitrogeno_total", "", "%", "arroz", HU, "2021", HUA, M_HU, "medicion_local", "observado",
   NOTA_HU + "Estaciones 1-3: 0,01; 0,03; 0,04 %. P disponible 9-12 ppm y K 139-188 ppm no se cargan (ppm no está en el CONTRATO); pH 7,08-7,2 y CaCO3 0,15-0,31 % tampoco. Sin valor central publicado.", vmin="0.01", vmax="0.04", zona="alto_piura"),
 r("rendimiento", "7800", "kg/ha", "arroz", HU, "c. 2021", HUA, "Promedio declarado por agricultores encuestados", "medicion_local", "estimado",
   NOTA_HU + "Declaración de productores, no pesaje; por eso estimado. Hace 5 años declaraban 9204 kg/ha. 91 % aplica más de 13 bolsas de fertilizante/ha; 74 % riega a diario.", zona="alto_piura", etapa="cosecha"),
 r("ce_suelo", "0.95", "dS/m", "quinua", "Parcela Experimental Túpac Amaru, Facultad de Agronomía UNP (valle Medio Piura)", "sep-2013 a feb-2014", QUI,
   "Análisis de suelo de la parcela experimental; extracto no indicado en el resumen", "medicion_local", "observado",
   "Publicado como 0,95 mmhos/cm (= dS/m). Suelo franco arcillo arenoso, pH moderadamente alcalino. Ubicación publicada: lat 5°10'45'' S; la longitud sale ilegible en el OCR y no se carga. ETo del ensayo 3,7 mm/día; lluvia 2,1 mm en todo el periodo. Leído en el resumen (ALICIA); el repositorio UNP no responde desde la caja.",
   zona="medio_piura", lat="-5.1792"),
]
BP = "Valle Bajo Piura (área agrícola neta con aptitud para riego, 34721 ha)"
M_CAS = "Estudio agrológico Colombi-Mendivil (1978) citado por Castillo Albines"
N_CAS = "Cifra de 1977-1978 en fuente secundaria; vieja, pero es la única fracción de napa alta por zona encontrada para Piura. "
rows += [
 r("fraccion_area_napa_alta_permanente", "21.2", "%", "todos", BP, "dic-1977 a ene-1977 (estudio 1978)", CAS, M_CAS, "regional", "observado",
   N_CAS + "7451 ha. Ojo: 7451/34721 = 21,5 %; la fuente imprime 21,2 % (denominador no explicado). La fuente escribe 'Dic - Ene 1977'. Permeabilidad mayoritaria 1,5 a >6,0 m/día, solo 4 % entre 0,025 y 0,5 m/día (m/día no está en el CONTRATO)."),
 r("fraccion_area_napa_alta_temporal", "32.2", "%", "todos", BP, "1977-1978", CAS, M_CAS, "regional", "observado", N_CAS + "11607 ha (11607/34721 = 33,4 %; la fuente imprime 32,2 %)."),
 r("fraccion_area_salina", "33", "%", "todos", BP, "1978", CAS, M_CAS, "regional", "observado", N_CAS + "Salinos sin alcalinidad; umbral de CE no indicado."),
 r("fraccion_area_salino_alcalina", "59", "%", "todos", BP, "1978", CAS, M_CAS, "regional", "observado", N_CAS + "92 % con algún problema de sales (33 + 59)."),
 r("fraccion_area_con_sales", "92", "%", "todos", BP, "1978", CAS, M_CAS, "regional", "observado", N_CAS + "Suma de salinos (33 %) y salino-alcalinos (59 %). Comparar con Santayana 2012: 75 % (fila de r1b)."),
]
for clase, ha, pct in (("2", "5165", "14.9"), ("3", "10440", "30.0"), ("4", "11104", "32.0"), ("5", "8012", "23.1")):
    rows.append(r(f"fraccion_area_clase_{clase}_riego", pct, "%", "todos", BP, "1978", CAS, M_CAS + "; clasificación por aptitud para riego", "regional", "observado",
                  N_CAS + f"{ha} ha de 34721. Clase 1: 0 ha."))
AP = "Valle Alto Piura"
rows += [
 r("superficie_con_sales", "6595", "ha", "todos", AP, "jun-ago 1987", CAS, "Estudio especial de salinidad citado por Castillo Albines", "regional", "observado",
   "Síntomas de salinidad de leve a fuerte; 18 % del área cultivada (fila aparte). En el estudio agrológico de 1972 eran 3365 ha (fila aparte). La fuente escribe 1987 y luego 1988 para el mismo dato."),
 r("fraccion_area_con_sales", "18", "%", "todos", AP, "jun-ago 1987", CAS, "Estudio especial de salinidad citado por Castillo Albines", "regional", "observado",
   "6595 ha sobre el área cultivada del Alto Piura (área no indicada en el pasaje)."),
 r("superficie_con_sales", "3365", "ha", "todos", AP, "1972", CAS, "Estudio agrológico de 1972 citado por Castillo Albines", "regional", "observado", "Línea de comparación del dato de 1987."),
 r("superficie_mal_drenaje_salinidad", "32000", "ha", "todos", "Cuenca Chira-Piura", "diagnóstico PGRH (2012-2013; plan oct-2015)", PG,
   "Cifra del diagnóstico del plan de cuenca", "regional", "estimado",
   "Texto: '32 000 ha afectadas por mal drenaje y salinidad, debido a malas prácticas agrícolas'. Cifra redonda sin método ni reparto por valle; por eso estimado. Superficie bajo riego de la cuenca 177414,91 ha (fila aparte): ~18 % (cálculo propio). La cifra PECHP de 7980 ha no aparece en el plan."),
 r("superficie_bajo_riego", "177414.91", "ha", "todos", "Cuenca Chira-Piura", "línea base PGRH (2012-2013; plan oct-2015)", PG, "Indicador de línea base del plan", "regional", "observado",
   "Oferta hídrica media 3074,10 hm3/año. 36833 ha de arroz con altas pérdidas de agua según el diagnóstico."),
]
for sistema, pct in (("Chira", "95"), ("San Lorenzo", "70"), ("Medio y Bajo Piura", "93"), ("Alto Piura", "71")):
    rows.append(r("fraccion_superficie_con_derechos_agua", pct, "%", "todos", f"Sistema {sistema}", "línea base PGRH (2012-2013; plan oct-2015)", PG,
                  "Indicador de línea base del plan (cuadro de brechas, p. 155)", "regional", "observado",
                  "Red de drenaje del mismo cuadro: Chira 211 km, San Lorenzo 251 km, Medio y Bajo Piura 454 km, Alto Piura 0 km (km no está en el CONTRATO)."))
SLR = "Distrito de riego San Lorenzo (zona regulada)"
N_GS = "Supervisión de la ANA a la Junta de Usuarios San Lorenzo citada en la tesis; datos de distribución 2013-2018. "
rows += [
 r("modulo_riego", "9800", "m3/ha/año", "frutales", SLR, "c. 2018 (planificación de la junta)", GS, "Módulo de planificación de la junta", "regional", "estimado",
   N_GS + "Módulo asignado, no entregado. Para el cálculo de tarifa la tesis usa 9875 m3/año."),
 r("modulo_riego", "15000", "m3/ha", "arroz", SLR, "c. 2018, campaña grande", GS, "Módulo de planificación de la junta", "regional", "estimado", N_GS + "Campaña chica: 13500 m3/ha (fila aparte).", etapa="campaña grande"),
 r("modulo_riego", "13500", "m3/ha", "arroz", SLR, "c. 2018, campaña chica", GS, "Módulo de planificación de la junta", "regional", "estimado", N_GS, etapa="campaña chica"),
 r("agua_riego_consumo", "6234", "m3/ha/año", "frutales", SLR, "2013-2018", GS, "Volumen distribuido / área instalada (evaluación de la supervisión)", "regional", "observado",
   N_GS + "36 % menos que el módulo de 9800. Es volumen entregado, no consumo medido en parcela."),
 r("agua_riego_consumo", "13563", "m3/ha", "arroz", SLR, "2013-2018", GS, "Volumen distribuido / área instalada (evaluación de la supervisión)", "regional", "observado",
   N_GS + "10 % menos que el módulo de 15000. La fuente no aclara si es campaña grande o promedio de campañas."),
 r("perdidas_distribucion_agua", "39", "%", "todos", SLR, "promedio 2013-2018", GS, "Auditoría de la supervisión ANA", "regional", "estimado",
   N_GS + "Eficiencia de distribución implícita ~61 % (cálculo propio, no en la fuente). Las pérdidas se estiman con la experiencia del personal; por eso estimado. Promedio de 6 años sin dispersión publicada."),
 r("volumen_usado_zona_no_regulada", "143.76", "hm3", "todos", "Distrito de riego San Lorenzo (zona no regulada)", "promedio anual (c. 2013-2018)", GS,
   "Volumen promedio anual usado; área del estudio FODUA-Enmiendas 2019", "regional", "observado",
   N_GS + "22 % del volumen que entra al sistema. Para 3759,95 ha bajo riego la demanda bruta sería 71,06 hm3. 143,76 hm3 / 3759,95 ha ≈ 38235 m3/ha (cálculo propio)."),
 r("tarifa_agua", "0.028896", "PEN/m3", "todos", SLR, "2018", GS, "Tarifa por m3 (recibo único)", "regional", "observado",
   N_GS + "Comisiones Chipillico Bajo y Somate Bajo: 0,034381666 PEN/m3. Con 9875 m3 de módulo frutal: 285,35 PEN/ha/año (339,53 en Chipillico/Somate)."),
]
BPV = "Valle Bajo Piura"
rows += [
 r("costo_produccion", "5253.2", "PEN/ha", "maíz amarillo duro", BPV, "2021", RVT, "Encuesta a productores de MAD (tabla 15: mínimo, media, moda, máximo, DE; costos armados con las encuestas y datos de la Agencia Agraria Piura; semilla certificada y no certificada juntas)", "regional", "observado",
   "Rango = mínimo y máximo de la encuesta; DE 1529,0; moda 6375,0. Costo de agua: media 228 PEN/ha (rango 150-350). Precio medio 1,32 PEN/kg (0,90-1,70). PDF y texto en fuentes/rodriguez_valdez_tesis_mad_bajo_piura.*.",
   vmin="2470.0", vmax="8810.0", etapa="campaña completa"),
 r("rendimiento", "7227.3", "kg/ha", "maíz amarillo duro", BPV, "2021", RVT, "Encuesta a productores de MAD (tabla 15)", "regional", "estimado",
   "Rendimiento declarado, no pesado; por eso estimado. Rango mínimo-máximo; DE 2412,5; moda 9200,0.", vmin="2576.0", vmax="12650.0", etapa="cosecha"),
 r("agua_riego_presupuestada", "7500", "m3/ha", "maíz amarillo duro", BPV, "c. 2021", RVT, "Partida 'Agua m3 7500' de las hojas de costo por ha de la DRA Piura (anexos)", "regional", "estimado",
   "Volumen presupuestado en la hoja de costos, no medido; costo 225 PEN/ha.", etapa="campaña completa"),
 r("costo_produccion", "1849.06", "USD/ha", "maíz amarillo duro", BPV, "sin año (encuesta probablemente 2021)", RVA,
   "Encuesta no probabilística a 70 pequeños productores, semilla no certificada", "regional", "observado",
   "La tabla 1 dice '(S/)' en el título pero 'US$' en las filas; se carga en USD/ha como dicen las filas, sin convertir. Con semilla certificada: 1994,23 USD/ha (fila aparte). Precio 0,37 USD/kg. Difiere de la tesis del mismo autor (5253,2 PEN/ha).",
   variedad="semilla no certificada", etapa="campaña completa"),
 r("costo_produccion", "1994.23", "USD/ha", "maíz amarillo duro", BPV, "sin año (encuesta probablemente 2021)", RVA,
   "Encuesta no probabilística a 70 pequeños productores, semilla certificada", "regional", "observado",
   "Misma tabla y misma ambigüedad S/ vs US$.", variedad="semilla certificada", etapa="campaña completa"),
 r("rendimiento", "8142", "kg/ha", "maíz amarillo duro", BPV, "sin año (encuesta probablemente 2021)", RVA, "Encuesta, semilla no certificada", "regional", "estimado",
   "Declarado por productores. Con semilla certificada 10500 kg/ha (fila aparte). Difiere de la media de la tesis (7227,3) sin explicación.", variedad="semilla no certificada", etapa="cosecha"),
 r("rendimiento", "10500", "kg/ha", "maíz amarillo duro", BPV, "sin año (encuesta probablemente 2021)", RVA, "Encuesta, semilla certificada", "regional", "estimado",
   "Declarado por productores.", variedad="semilla certificada", etapa="cosecha"),
 r("costo_produccion", "13500", "PEN/ha", "algodón", "Piura (región)", "2022 (campaña vigente a mar-2022)", DRA, "Costo total por ha declarado por la DRA Piura", "regional", "estimado",
   "Cifra institucional sin desglose ni método; por eso estimado. Algodón Pima. La nota proyecta además 80 QQ rama/ha y 25,39 QQ fibra/ha con paquete tecnológico: es meta, no observación, y QQ no es unidad del CONTRATO; no se carga.",
   variedad="Pima", etapa="campaña completa", zona="piura_region"),
]
def stats_algodon():
    src = BASE / "insumos" / "drap_distrito_anual.csv"
    x = [d for d in csv.DictReader(src.open(encoding="utf-8")) if d["cultivo"] == "algodón" and d["variable"] == "rendimiento"
         and d["zona"] == "bajo_piura" and d["valor"] and 2016 <= int(d["fecha_o_periodo"][:4]) <= 2023]
    ht = [tuple(float(g.replace(",", "")) for g in re.search(r"Cosecha ([\d.,]+) ha, producción ([\d.,]+) t", d["notas"]).groups()) for d in x]
    v = sorted(float(d["valor"]) for d in x); q = st.quantiles(v, n=4)
    return len(x), sum(b for a, b in ht) / sum(a for a, b in ht), st.median(v), q[0], q[2], sum(a for a, b in ht)
n, pond, med, p25, p75, ha = stats_algodon()
M_A = f"n={n} filas distrito-año de DRAP (2016-2023), zona bajo_piura"
rows += [
 r("rendimiento", f"{pond:.2f}", "t/ha", "algodón", "Valle Bajo Piura (distritos DRAP)", "2016-2023", DRAP, "Media ponderada por superficie (suma producción / suma cosecha); " + M_A, "regional", "observado",
   f"Rango = P25-P75 de los rendimientos distritales. {ha:.0f} ha cosechadas en total. Se excluye 2015 porque en DRAP es un año parcial; con 2015 la ponderada baja a 2,75 t/ha (n=93). Cifra recomendada para el desacuerdo 2,75 vs 3,48.",
   vmin=f"{p25:.2f}", vmax=f"{p75:.2f}", etapa="cosecha"),
 r("rendimiento_mediana_distrital", f"{med:.2f}", "t/ha", "algodón", "Valle Bajo Piura (distritos DRAP)", "2016-2023", DRAP, "Mediana de rendimientos distrito-año sin ponderar; " + M_A, "regional", "observado",
   "Rango = P25-P75. Pesa igual a distritos chicos y grandes; por eso queda sobre la ponderada.", vmin=f"{p25:.2f}", vmax=f"{p75:.2f}", etapa="cosecha"),
]
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows([normalizar(x) for x in rows])
print(f"OK {len(rows)} -> {OUT.relative_to(BASE)}  (algodón Bajo Piura: n={n} pond={pond:.2f} med={med:.2f} P25-P75={p25:.2f}-{p75:.2f})")
