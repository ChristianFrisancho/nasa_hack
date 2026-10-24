#!/usr/bin/env python3
"""Curado manual, ronda 1 (tramo b): agua por campaña/dotación y costos ENA 2018 de cultivos anuales.
Cada cifra fue leída en la fuente citada (texto de la página o PDF descargado). Escribe insumos/curado_r1b.csv.
Uso: python3 tools/insumos_curados_r1b.py
"""
import csv
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "insumos" / "curado_r1b.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fecha_consulta"]
AG16 = ("Agraria.pe, 'Cultivos de uvas instalados en zonas eriazas de Piura consumen más agua que el arroz' (22-dic-2016), declaraciones de Ángel Zapata (presidente APEAR)",
        "https://agraria.pe/noticias/cultivos-de-uvas-instalados-en-zonas-eriazas-de-piura-consum-12848")
AG18 = ("Agraria.pe, 'Piura siembra 16.500 hectáreas de arroz en la presente campaña grande' (21-mar-2018), declaraciones de Ángel Zapata (APEAR-Chira)",
        "https://agraria.pe/noticias/piura-siembra-16500-hectareas-de-arroz-en-la-presente-campan-16214")
PADH = ("ANA, nota 'ANA aprueba plan hídrico ... sistema Chira Piura' (11-ago-2025), R.D. N.° 1429-2025-ANA-AAA.JZ, PADH ago-2025 a jul-2026",
        "https://www.gob.pe/institucion/ana/noticias/1224425-ana-aprueba-plan-hidrico-para-garantizar-el-abastecimiento-multisectorial-en-el-sistema-chira-piura")
PCR = ("DRA Piura, nota 'Gore Piura aprueba calendario oficial de la Campaña Agrícola Grande 2025-2026 de arroz y algodón' (18-nov-2025)",
       "https://www.gob.pe/institucion/regionpiura-dra/noticias/1291910-gore-piura-aprueba-calendario-oficial-de-la-campana-agricola-grande-2025-2026-de-los-cultivos-de-arroz-y-algodon")
SL = ("Castillo Mimbela, M. D. (2007). Tesina 'Informalidad en el uso del agua y sus impactos en el afianzamiento del sistema hidráulico San Lorenzo-Piura', Programa GIRH Macro Región Norte",
      "https://iragerblog.wordpress.com/wp-content/uploads/2016/06/tesina-informalidad-en-el-uso-del-agua-y-sus-impactos-en-el-afianzamiento-del-sistema-hidraulico-san-lorenzo-piura-marcos-castillo.pdf")
ENA = ("INEI, Costos de producción para la actividad agricultura, ganadería, caza y silvicultura en base a la ENA 2018 (marzo 2021)",
       "https://www.inei.gob.pe/media/MenuRecursivo/investigaciones/costos-de-produccion-v7.pdf")
M_ENA = "Costo de producción por UA de la ENA 2018; excluye depreciación, gastos administrativos y otros; UA pequeñas solo excedentarias (>=5 ha cosechadas)"
from zonas import zona_lugar
from contrato import normalizar
def r(variable, valor, unidad, cultivo, lugar, periodo, src, metodo, tipo, estado, notas, vmin="", vmax="", etapa="campaña completa", variedad="", zona=None):
    if zona is None:
        zona, nz = zona_lugar(lugar)
        if nz: notas = notas + " " + nz
    return dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo, variedad=variedad,
                etapa=etapa, zona=zona, lugar=lugar, lat="", lon="", fecha_o_periodo=periodo, fuente=src[0], url_o_doi=src[1], metodo=metodo,
                tipo_evidencia=tipo, estado=estado, notas=_rango(valor, vmin, vmax, notas), fecha_consulta="2026-10-24")
def _rango(valor, vmin, vmax, notas):
    if valor and not vmin and not vmax and "rango" not in notas.lower():
        notas += " Sin rango: la fuente publica una sola cifra, sin error ni intervalo."
    return notas
DECL = "Declaración de un dirigente gremial recogida por prensa especializada; no es medición. "
rows = [
 r("agua_riego_consumo", "12000", "m3/ha/año", "arroz", "Piura (valles con arroz: Chira, San Lorenzo, Medio y Bajo Piura, Sechura)", "c. 2016", AG16,
   "Consumo promedio declarado", "regional", "estimado", DECL + "Texto: 'el consumo de agua en arroz en Piura es en promedio 12.000 m3 anuales (ya no se inundan los cultivos)'. Ambiguo si es por campaña o por año con dos campañas. Modelos lo atribuye a la DRA: la cifra es de APEAR."),
 r("agua_riego_consumo", "8000", "m3/ha/año", "arroz", "Piura (valles con arroz)", "c. 2016", AG16, "Consumo declarado con secas intermitentes", "regional", "estimado",
   DECL + "Texto: 'con la técnica de riego de secas intermitentes es de 8.000 m3 por ha'.", variedad=""),
 r("dotacion_asignada", "16000", "m3/ha/año", "arroz", "Piura (valles con arroz)", "c. 2016", AG16, "Cuota anual de agua por licencia declarada", "regional", "estimado",
   DECL + "La cuota anual cubre campaña grande y chica según el declarante."),
 r("dotacion_asignada", "19000", "m3/ha/año", "uva", "Piura (zonas eriazas habilitadas)", "c. 2016", AG16, "Cuota anual asignada declarada", "regional", "estimado", DECL),
 r("superficie_sembrada", "32000", "ha", "arroz", "Piura (región)", "c. 2016, campaña grande", AG16, "Área típica declarada por campaña", "regional", "estimado", DECL + "Campaña chica: 24000 ha (fila aparte)."),
 r("superficie_sembrada", "24000", "ha", "arroz", "Piura (región)", "c. 2016, campaña chica", AG16, "Área típica declarada por campaña", "regional", "estimado", DECL),
 r("agua_riego_consumo", "", "m3/ha", "arroz", "Piura (región)", "campaña grande 2018", AG18,
   "Rango declarado por campaña: 10000 m3/ha con secas intermitentes a 18000 m3/ha con inundación", "regional", "estimado",
   DECL + "Por campaña; variedades precoces de ~120 días (Tinajones, La Puntilla). Antes eran dos filas (10000 y 18000) con la misma clave; se juntan como rango porque son los dos extremos de manejo que da la misma declaración.",
   vmin="10000", vmax="18000"),
 r("disponibilidad_hidrica", "325.8", "hm3", "todos", "Ámbito Agencia Agraria Piura (Medio y Bajo Piura, sistema Chira-Piura)", "campaña grande 2025-2026", PCR,
   "Disponibilidad confirmada en sesión del Comité del PCR (11-nov-2025) con ANA, PECHP y juntas", "regional", "estimado",
   "Volumen previsto para la campaña, no entregado. Calendario: almácigo y siembra directa 15-dic-2025 a 30-ene-2026; trasplante 10-ene a 28-feb-2026; algodón 15-mar a 30-abr-2026. Sin desglose por ha."),
 r("volumen_asignado_agrario", "2073.14", "hm3", "todos", "Sistema hidráulico Chira-Piura (provincias de Piura y Sechura)", "ago-2025 a jul-2026", PADH,
   "Volumen programado al uso agrario en el PADH", "regional", "estimado",
   "Programado, no medido. Demanda consuntiva total 2149,53 hm3; disponibilidad proyectada 3630,69 hm3. Sin desglose por junta ni por ha."),
 r("superficie_bajo_riego", "64550", "ha", "todos", "Distrito de riego San Lorenzo", "c. 2007", SL, "Ámbito administrativo bajo riego", "regional", "observado",
   "Solo se atienden 38550 ha por el régimen irregular de los ríos Quiroz y Chipillico (fila aparte)."),
 r("superficie_atendida", "38550", "ha", "todos", "Distrito de riego San Lorenzo", "c. 2007", SL, "Área efectivamente atendida", "regional", "observado",
   "Cultivos: mango 21000 ha, limón 8200 ha, arroz 6500 ha, marigold y maíz amarillo duro en menor escala."),
 r("volumen_licencia", "578.4", "hm3", "todos", "Distrito de riego San Lorenzo", "c. 2007", SL, "Volumen con fines de riego asignado por el PROFODUA (D.S. 041-2005-AG)", "regional", "estimado",
   "Volumen asignado en licencias, no entregado; por eso estado=estimado. 578,4 hm3 / 38550 ha atendidas = ~15000 m3/ha (cálculo propio, no en la fuente)."),
 r("dotacion_asignada", "15191", "m3/ha/año", "todos", "Distrito de riego San Lorenzo", "c. 2007", SL, "Volumen de derecho por ha en licencias", "regional", "estimado",
   "Dotación de derecho (asignada), no volumen entregado; por eso estado=estimado. La fuente dice que 'en la práctica este parámetro no es utilizado': la entrega la decide el personal de campo."),
 r("dotacion_asignada", "9000", "m3/ha/año", "frutales", "Distrito de riego San Lorenzo", "c. 2007", SL, "Módulo frutal usado para estimar tarifa", "regional", "estimado",
   "Mencionado como 'módulo frutal' en un cálculo de tarifa no recaudada."),
 # ENA 2018: cultivos anuales sin cifra de Piura
 r("costo_produccion", "5411.65", "PEN/ha", "maíz amarillo duro", "Región natural costa (Perú)", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   "Comparabilidad: agregado de la costa peruana, que incluye a Piura; mismo sistema de riego por gravedad. Diferencia con Piura: no hay costo ENA de MAD para Piura; Rodríguez Valdez (UNALM, encuesta 2021, Bajo Piura) da media 5253,2 PEN/ha, 3 % menos que esta cifra, con otro año y otro método. Agregado de la costa, que incluye Piura pero no es Piura. 716,66 PEN/t; 7551 kg/ha (línea ~2600 del texto)."),
 r("costo_produccion", "3067.23", "PEN/ha", "maíz amarillo duro", "Perú", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   "Comparabilidad: promedio nacional (costa, sierra y selva); débil para Piura. Diferencia con Piura: 42 % por debajo del agregado costa (5411,65). Cuadro 2: DE 2145,28; máx 16450,00; mín 88,00; n=846 UA; costo 0,66 PEN/kg; precio productor 0,91 PEN/kg.", vmin="88.00", vmax="16450.00"),
 r("costo_produccion", "1531.01", "PEN/ha", "frijol", "Región natural costa (Perú)", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   "Comparabilidad: agregado de la costa peruana, incluye Piura. Diferencia con Piura: no hay costo de frijol de Piura para comparar. Frijol grano seco. 1014,11 PEN/t; 1510 kg/ha (línea ~4291)."),
 r("costo_produccion", "3010.98", "PEN/ha", "camote", "Perú", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   "Comparabilidad: promedio nacional; el camote ENA sólo aparece en costa, como en Piura. Diferencia con Piura: no hay costo de camote de Piura para comparar. Cuadro 2: DE 1677,47; máx 9548,01; mín 649,29; n=37 UA; costo 0,20 PEN/kg; precio productor 0,62 PEN/kg. Producción registrada solo en costa.", vmin="649.29", vmax="9548.01"),
 r("costo_produccion", "3893.55", "PEN/ha", "camote", "Lima (departamento)", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado", "Comparabilidad: costa central con riego por gravedad. Diferencia con Piura: no hay costo de camote de Piura para comparar. 218,72 PEN/t (línea ~4913)."),
 r("costo_produccion", "3013.33", "PEN/ha", "camote", "Ica (departamento)", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado", "Comparabilidad: costa sur con riego (en parte por pozo). Diferencia con Piura: no hay costo de camote de Piura para comparar. 305,76 PEN/t (línea ~4913)."),
 r("costo_produccion", "5003.86", "PEN/ha", "algodón", "Perú", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado",
   "Comparabilidad: promedio nacional; el algodón ENA sólo aparece en costa. Diferencia con Piura: no hay costo ENA de algodón de Piura; Lambayeque (costa norte) da 4599,14, 8 % menos. Cuadro 2: DE 2182,80; máx 9842,91; mín 943,70; n=42 UA; costo 1,85 PEN/kg; precio productor 3,29 PEN/kg. Producción registrada solo en costa.", vmin="943.70", vmax="9842.91"),
 r("costo_produccion", "4599.14", "PEN/ha", "algodón", "Lambayeque (departamento)", "2018 (ENA 2018)", ENA, M_ENA, "regional", "observado", "Costa norte (el CONTRATO admite la costa norte como regional); no es Piura. 1339,16 PEN/t (línea ~5091)."),
 r("costo_produccion", "4593.69", "PEN/ha", "algodón", "Ica (departamento)", "2018 (ENA 2018)", ENA, M_ENA, "analogo_externo", "observado", "Comparabilidad: costa sur, algodón Tangüis más que Pima. Diferencia con Piura: no hay costo de Piura; 0,1 % distinto de Lambayeque. 1896,99 PEN/t (línea ~5091)."),
 r("precio_chacra", "3.29", "PEN/kg", "algodón", "Perú", "2018 (ENA 2018)", ENA, "Precio productor promedio de la muestra ENA", "analogo_externo", "observado",
   "Comparabilidad: promedio nacional. Diferencia con Piura: DRAP Piura 2018 da mediana 3,58 y ponderada 3,32 PEN/kg (1 % y 9 % más). Cuadro 2. Consistente con DRAP Piura 2018 (mediana 3,58; ponderada 3,32): apoya que el precio DRAP es de algodón en rama."),
 r("costo_produccion", "", "PEN/ha", "frijol caupí", "Piura (departamento)", "2018 (ENA 2018)", ENA, "Búsqueda en el texto completo de la ENA 2018", "regional", "desconocido",
   "El caupí no figura entre los 70 productos del cuadro 2 ni en el texto."),
]
SANT = ("Santayana Vela, S. (2012). 'Problemas de drenaje y salinidad en la costa peruana', XI Congreso Nacional de Ingeniería Agrícola, UNALM (presentación)",
        "https://es.slideshare.net/slideshow/drenaje-salinidad-costa-peruana1/60880717")
FOX = ("Fox Llerena, E. C. (2013). Tesis PUCP 'Evaluación de pérdida de suelo por salinización en la parte baja de la cuenca del Jequetepeque: San Pedro de Lloc (1980-2003)'",
       "http://hdl.handle.net/20.500.12404/4809")
PRES = "Presentación de congreso de un docente de la UNALM; no indica método ni año de la cifra. "
rows += [
 r("fraccion_area_con_sales", "75", "%", "todos", "Valle Bajo Piura", "c. 2012 (sin año de medición)", SANT, "Afirmación en diapositiva 19, sin método", "regional", "estimado",
   PRES + "Texto: 'Salinización: 75% de área agrícola con problemas de sales por mal uso de agua de riego; exceso de áreas con arroz'. No separa sal de mal drenaje ni da umbral de CE. Diapositiva 18: la segunda etapa del Proyecto Chira-Piura construyó 421 km de drenes parcelarios, 108,3 km de colectores primarios y 230,3 km secundarios; la 19 dice que el drenaje parcelario no se concluyó y no tiene mantenimiento."),
 r("fraccion_area_drenaje_salinidad", "34.1", "%", "todos", "Costa peruana (870000 ha bajo riego)", "2007", SANT, "Inventario INRENA - A. De La Torre citado en diapositiva 10", "bibliografico", "estimado",
   PRES + "298461 ha con problemas de drenaje y salinidad; promedio de toda la costa, no de Piura. Serie: 30,0 % (1964), 33,5 % (1974), 32,2 % (1986), 31,2 % (2004)."),
 r("fraccion_area_napa_menor_1m", "11.2", "%", "todos", "Valle de Virú (La Libertad)", "c. 2012", SANT, "Área con napa freática < 1,0 m (diapositiva 47)", "analogo_externo", "estimado",
   PRES + "Comparabilidad: valle costero árido del norte con napa alta, como el Bajo Piura; difiere en la fuente de agua (Chavimochic, no Chira-Piura) y en suelos. Diferencia con Piura: no hay fracción de napa por zona medida en Piura para comparar. Costa norte, no Piura. 1700 ha; napa 1,0-1,5 m: 3790 ha (24,8 %). Virú tiene riego por Chavimochic, distinto al Chira-Piura."),
 r("fraccion_area_napa_1_a_1_5m", "24.8", "%", "todos", "Valle de Virú (La Libertad)", "c. 2012", SANT, "Área con napa freática entre 1,0 y 1,5 m (diapositiva 47)", "analogo_externo", "estimado", PRES + "Comparabilidad: igual que la fila de napa < 1 m de Virú. Diferencia con Piura: sin cifra de Piura para comparar. 3790 ha."),
 r("ce_suelo", "", "dS/m", "todos", "San Pedro de Lloc, subsector medio (cuenca baja del Jequetepeque, La Libertad)", "c. 2012-2013", FOX,
   "CE en extracto suelo:agua 1:1 (no pasta saturada)", "analogo_externo", "observado",
   "Comparabilidad: cuenca baja costera árida con arroz por inundación y salinización, como el Bajo Piura. Diferencia con Piura: la única CE de Piura en suelo agrícola es Tablazo Sur (Mendoza 2025, 3,44-8,2 dS/m, extracto no declarado), dentro del rango de este estudio pero con otro extracto. Costa norte, suelo agrícola. Extracto 1:1 no equivale a ECe de pasta saturada; no convierto. Subsector alto 0,1-2,4; bajo 4,8-9,5 (filas aparte).", vmin="1.3", vmax="4.7"),
]
for lugar, a, b in (("subsector alto", "0.1", "2.4"), ("subsector bajo", "4.8", "9.5")):
    rows.append(r("ce_suelo", "", "dS/m", "todos", f"San Pedro de Lloc, {lugar} (cuenca baja del Jequetepeque, La Libertad)", "c. 2012-2013", FOX,
                  "CE en extracto suelo:agua 1:1 (no pasta saturada)", "analogo_externo", "observado",
                  "Comparabilidad: cuenca baja costera árida con arroz por inundación y salinización, como el Bajo Piura. Diferencia con Piura: la única CE de Piura en suelo agrícola es Tablazo Sur (Mendoza 2025, 3,44-8,2 dS/m, extracto no declarado), dentro del rango de este estudio pero con otro extracto. Costa norte, suelo agrícola. Extracto 1:1 no equivale a ECe de pasta saturada; no convierto.", vmin=a, vmax=b))

with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows([normalizar(x) for x in rows])
print(f"OK {len(rows)} -> {OUT.relative_to(BASE)}")
