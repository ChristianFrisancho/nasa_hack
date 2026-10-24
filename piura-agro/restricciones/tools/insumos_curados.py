#!/usr/bin/env python3
"""Escribe en restricciones/insumos/ los registros curados a mano desde fuentes leídas
(ENA 2018, ESCO arroz Piura, ANA, EIA 1997, menciones n8n). Cada cifra lleva su fuente,
método y notas. Las cifras se copiaron del texto de la fuente; no hay cálculos.
Uso: python3 tools/insumos_curados.py
"""
import csv
from pathlib import Path
from zonas import zona_lugar
from contrato import normalizar

BASE = Path(__file__).resolve().parents[1]
INS = BASE / "insumos"
CAMPOS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona",
          "lugar", "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi", "metodo",
          "tipo_evidencia", "estado", "notas", "fecha_consulta"]
HOY = "2026-10-24"

def reg(**k):
    r = {c: "" for c in CAMPOS}
    r.update({c: ("" if v is None else str(v)) for c, v in k.items()})
    r["fecha_consulta"] = HOY
    if "zona" not in k:
        r["zona"], nz = zona_lugar(r["lugar"])
        if nz: r["notas"] = (r["notas"] + " " + nz).strip()
    if r["valor"] and not r["valor_min"] and not r["valor_max"] and "rango" not in r["notas"].lower():
        r["notas"] += " Sin rango: la fuente publica una sola cifra, sin error ni intervalo."
    return r

def escribir(nombre, filas):
    with (INS / nombre).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS + sorted({k for r in filas for k in r} - set(CAMPOS)))  # p. ej. subzona (opcional del CONTRATO)
        w.writeheader(); w.writerows([normalizar(r) for r in filas])
    print(f"OK {len(filas):3d} -> insumos/{nombre}")

# ---------- ENA 2018 (INEI, estudio de costos) ----------
ENA_F = "INEI, Costos de producción para la actividad agricultura, ganadería, caza y silvicultura en base a la ENA 2018 (marzo 2021)"
ENA_U = "https://www.inei.gob.pe/media/MenuRecursivo/investigaciones/costos-de-produccion-v7.pdf"
ENA_M = ("Costo de producción por UA de la ENA 2018, promedio departamental; excluye depreciación, gastos "
         "administrativos y otros (p. ~10158 del texto); UA pequeñas solo excedentarias (>=5 ha cosechadas)")
ena = []
for cultivo, ha, t, extra in [
    ("arroz", "5409.66", "682.34", ""), ("uva", "52821.17", "3386.35", ""),
    ("banano/plátano", "16570.81", "626.10", ""), ("limón", "6920.50", "515.30", ""),
    ("arveja grano seco", "1020.29", "1906.36", " Solo UA pequeñas en la muestra nacional de este cultivo."),
    ("ají piquillo", "34595.45", "1226.79", " Solo UA grandes en la muestra nacional de este cultivo."),
]:
    for var, val, un in (("costo_produccion", ha, "PEN/ha"), ("costo_produccion_por_t", t, "PEN/t")):
        ena.append(reg(variable=var, valor=val, unidad=un, cultivo=cultivo, etapa="campaña completa",
                       lugar="Piura (departamento)", fecha_o_periodo="2018 (ENA 2018)", fuente=ENA_F, url_o_doi=ENA_U,
                       metodo=ENA_M, tipo_evidencia="regional", estado="observado",
                       notas="Cifra departamental citada en el texto del estudio. Sin rango por departamento publicado." + extra))
ena.append(reg(variable="costo_produccion", valor="6067.6", valor_min="3835.9", valor_max="7285.0", unidad="PEN/ha",
               cultivo="caña etanol", etapa="campaña completa", lugar="Piura (departamento)",
               fecha_o_periodo="2018 (ENA 2018)", fuente=ENA_F, url_o_doi=ENA_U, metodo=ENA_M,
               tipo_evidencia="regional", estado="observado",
               notas="Solo 2 UA grandes en el país, ambas en Piura (agroindustria de etanol); min y max son esas 2 UA. No representa al pequeño productor."))
escribir("ena2018_costos.csv", ena)

# ---------- ESCO arroz Piura (MIDAGRI) ----------
ES_F = "MIDAGRI - DGESEP/DEIA, UEGPS-PIADER: Resultados de la Encuesta de Costos de Producción del cultivo de arroz, región Piura, ESCO 2024-2025"
ES_U = "copia local restricciones/fuentes/midagri_esco_arroz_piura.pdf (gob.pe/uegps; URL exacta no registrada)"
ES_M = "Encuesta por muestreo a productores (ESCO); estimación con error estándar (EE) e IC 95 %"
ES_P = "campaña 2024 (ESCO 2024-2025)"
esco = []
for var, val, ee, lo, hi, n, un, ref in [
    ("costo_directo", "8257", "175", "7905", "8608", "1513", "PEN/ha", False),
    ("costo_maquinaria", "1260", "62", "1136", "1383", "", "PEN/ha", False),
    ("costo_fertilizantes", "2053", "84", "1885", "2220", "", "PEN/ha", False),
    ("costo_abonos", "259", "41", "173", "346", "91", "PEN/ha", True),
    ("costo_plaguicidas", "738", "58", "622", "855", "", "PEN/ha", False),
    ("costo_semillas", "396", "15", "367", "426", "", "PEN/ha", False),
    ("costo_riego", "441", "14", "413", "469", "", "PEN/ha", False),
    ("costo_mano_obra", "3188", "122", "2943", "3433", "", "PEN/ha", False),
    ("costo_transporte", "126", "14", "98", "154", "", "PEN/ha", False),
    ("costo_envases_otros", "190", "95", "0", "380", "", "PEN/ha", True),
    ("costo_indirecto", "780", "102", "577", "984", "1118", "PEN/ha", False),
    ("costo_gastos_adm_financieros", "1049", "118", "812", "1286", "801", "PEN/ha", False),
    ("costo_seguro_agricola", "483", "107", "22", "943", "10", "PEN/ha", True),
    ("costo_otros_indirectos", "92", "7", "77", "106", "", "PEN/ha", False),
    ("rendimiento", "6641", "405", "5830", "7453", "1348", "kg/ha", False),
    ("ingreso_total", "10556", "1146", "8262", "12851", "", "PEN/ha", False),
    ("precio_chacra", "1.85", "0.03", "1.78", "1.92", "", "PEN/kg", False),
]:
    nt = [f"EE={ee}; valor_min/valor_max = IC 95 % publicado."]
    if n: nt.append(f"Casos: {n}.")
    if ref: nt.append("Referencial en la fuente (CV > 15 %): estado estimado.")
    if var == "costo_envases_otros": nt.append("IC inferior publicado '-0', se escribe 0.")
    if var == "costo_gastos_adm_financieros": nt.append("Supera al costo indirecto total (780) en la misma fuente: bases de casos distintas; inconsistencia de la fuente, no sumar.")
    if var == "rendimiento": nt.append("Campaña 2024 afectada por sequía (Poechos <2 %, San Lorenzo <5 % en oct-2024); por debajo del promedio regional MIDAGRI 9,2 t/ha.")
    if var == "precio_chacra": nt.append("Ingreso unitario del productor; 95,594 % de la producción se vende.")
    esco.append(reg(variable=var, valor=val, valor_min=lo, valor_max=hi, unidad=un, cultivo="arroz",
                    etapa="campaña completa", lugar="Piura (región)", fecha_o_periodo=ES_P, fuente=ES_F, url_o_doi=ES_U,
                    metodo=ES_M, tipo_evidencia="regional", estado="estimado" if ref else "observado", notas=" ".join(nt)))
esco.append(reg(variable="dosis_semilla", valor="116", unidad="kg/ha", cultivo="arroz", etapa="siembra",
                lugar="Piura (región)", fecha_o_periodo=ES_P, fuente=ES_F, url_o_doi=ES_U, metodo=ES_M,
                tipo_evidencia="regional", estado="observado", notas="Promedio estimado; 89,8 % usa semilla certificada. Sin rango publicado en el texto."))
for nut, lo, hi in (("N", "250", "270"), ("P", "80", "90"), ("K", "75", "100")):
    esco.append(reg(variable=f"dosis_recomendada_{nut}", valor_min=lo, valor_max=hi, unidad="kg/ha", cultivo="arroz",
                    etapa="crecimiento", lugar="Piura (región)", fecha_o_periodo=ES_P, fuente=ES_F, url_o_doi=ES_U,
                    metodo="Recomendación técnica citada en el informe, no medición", tipo_evidencia="bibliografico",
                    estado="estimado", notas="Rango recomendado; sin valor central publicado. La fuente no aclara si P y K son elemento u óxido."))
esco.append(reg(variable="volumen_embalse", valor_min="14", valor_max="26", unidad="hm3", cultivo="todos",
                lugar="Reservorio Poechos", lat="", lon="", fecha_o_periodo="2024-10", fuente=ES_F + " (cita a Infobae 2024)",
                url_o_doi=ES_U, metodo="Cita de prensa dentro del informe", tipo_evidencia="regional", estado="estimado",
                notas="Menos del 2 % de capacidad útil; San Lorenzo < 5 % el mismo mes. Fuente secundaria."))
escribir("esco_arroz_2024.csv", esco)

# ---------- ANA ----------
PG_F = "ANA, Plan de Gestión de los Recursos Hídricos de la cuenca Chira-Piura, cuadro de brechas línea base vs metas (p. 155)"
PG_U = "https://crhc.ana.gob.pe/chira-piura/sites/default/files/archivos/PLAN%20de%20GESTI%C3%93N%20de%20los%20RECURSOS%20H%C3%8DDRICOS%20de%20la%20CUENCA%20CHIRA-PIURA.pdf"
PG_P = "línea base PGRH (talleres 2012-2013; plan publicado oct-2015)"
PG_N = ("Texto completo del PDF obtenido con Tavily extract (r2, copia en fuentes/pgrh_chira_piura_ana2015.txt); ANA, oct-2015, ISBN 978-612-4273-02-5, cuadro p. 155. "
        "La línea base sale de talleres y reuniones con grupos de interés 2012-2013. Metas del plan excluidas por no ser observación.")
PG_ASIG = ("Dotación asignada por el plan de cuenca, no volumen entregado ni medido en parcela; por eso estado=estimado "
           "(el CONTRATO no tiene un estado 'asignada'; ver propuesta_contrato_zona.md). ")
ana = []
for sistema, zona, val in [("Chira", "Chira", "15399"), ("San Lorenzo", "San Lorenzo", "9528"),
                           ("Medio y Bajo Piura", "Medio y Bajo Piura", "11472"), ("promedio sistema regulado", "Regional", "12133")]:
    ana.append(reg(variable="dotacion_agua_riego", valor=val, unidad="m3/ha/año", cultivo="todos", lugar=f"Sistema regulado {sistema}",
                   fecha_o_periodo=PG_P, fuente=PG_F, url_o_doi=PG_U, metodo="Dotación agrícola por ha del plan de cuenca, línea base",
                   tipo_evidencia="regional", estado="estimado", notas=PG_ASIG + PG_N))
for sistema, zona, val in [("San Lorenzo", "San Lorenzo", "28000"), ("Alto Piura", "Alto Piura", "11807"), ("promedio no regulado", "Regional", "19903.5")]:
    ana.append(reg(variable="dotacion_agua_riego", valor=val, unidad="m3/ha/año", cultivo="todos", lugar=f"Sistema no regulado {sistema}",
                   fecha_o_periodo=PG_P, fuente=PG_F, url_o_doi=PG_U, metodo="Dotación agrícola por ha del plan de cuenca",
                   tipo_evidencia="regional", estado="estimado", notas=PG_ASIG + PG_N))
for sistema, val in [("Chira", "15664"), ("San Lorenzo", "1058"), ("Medio y Bajo Piura", "3469"), ("Sechura", "0"), ("Alto Piura", "2132")]:
    ana.append(reg(variable="area_riego_tecnificado", valor=val, unidad="ha", cultivo="todos", lugar=f"Sistema {sistema}",
                   fecha_o_periodo=PG_P, fuente=PG_F, url_o_doi=PG_U, metodo="Inventario del plan de cuenca",
                   tipo_evidencia="regional", estado="observado", notas="Total 22 323 ha. " + PG_N))
for sistema, val in [("Chira", "52"), ("San Lorenzo", "59"), ("Alto Piura", "60"), ("Medio y Bajo Piura", "57"), ("Sechura", "60")]:
    ana.append(reg(variable="eficiencia_operativa_riego", valor=val, unidad="%", cultivo="todos", lugar=f"Sistema {sistema}",
                   fecha_o_periodo=PG_P, fuente=PG_F, url_o_doi=PG_U, metodo="Eficiencia de conducción x distribución (Ec x Ed), uso agrario",
                   tipo_evidencia="regional", estado="observado", notas="Agua neta en parcela ≈ dotación x eficiencia; no aplicado aquí. " + PG_N))
DG_F = "ANA - Proyecto de Modernización de la Gestión de los Recursos Hídricos, Diagnóstico cuenca Chira-Piura, cuadro 2.2.3.a"
DG_U = "https://www.ana.gob.pe/sites/default/files/normatividad/files/caratula_diagnostico_chira_piura_0_2.pdf"
for valle, regable, regada in [("Alto Piura", "34000", "26500"), ("San Lorenzo", "43800", "43800"),
                               ("Medio y Bajo Piura", "43000", "37400"), ("Chira", "50700", "33300")]:
    for var, val in (("area_regable", regable), ("area_regada", regada)):
        ana.append(reg(variable=var, valor=val, unidad="ha", cultivo="todos", lugar=f"Valle {valle}", fecha_o_periodo="c. 2001 (diagnóstico ANA)",
                       fuente=DG_F, url_o_doi=DG_U, metodo="Cuadro de superficie de suelos irrigables del diagnóstico", tipo_evidencia="regional",
                       estado="observado", notas="Fragmento Tavily del PDF (no descargable, TLS). Año base inferido de la serie 2001-2026 del mismo documento; confirmar."))
ER_F = "ANA, Evaluación de Recursos Hídricos de la cuenca Piura (Valle Medio y Bajo Piura), inventario de aguas subterráneas"
ER_U = "https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf"
ana.append(reg(variable="ce_agua_subterranea", valor_min="0.04", valor_max="16.83", unidad="dS/m", cultivo="todos",
               lugar="Valle Medio y Bajo Piura (pozos IRHS)", fecha_o_periodo="desconocido (estudio ERH Piura, ANA)",
               fuente=ER_F, url_o_doi=ER_U, metodo="CE medida en pozos del inventario (IRHS); se publica solo el rango",
               tipo_evidencia="medicion_local", estado="observado",
               notas="Publicado en mmhos/cm (= dS/m). Mínimo IRHS-46 Piura, máximo IRHS-68 Catacaos. Sin valor central. 0,04 dS/m es inusualmente bajo para pozo; verificar en la tabla del estudio. Fragmento Tavily."))
escribir("ana_agua.csv", ana)

# ---------- EIA 1997 suelos (CE) ----------
SI_F = "Geoservice Ingeniería, Estudio de Impacto Ambiental (línea base de suelos, cap. 4), 1997; distritos Olmos y Sechura"
SI_U = "copia local restricciones/fuentes/siar_1997.pdf (repositorio SIAR/MINAM)"
siar = []
for suelo, textura, epi, sub in [
    ("Curva", "gruesa", ("5.0", "5.0"), ("10.53", "13.87")), ("Legía", "gruesa", ("2.66", "3.11"), ("3.32", "10.83")),
    ("Salinas", "gruesa", ("46.8", "46.8"), ("31.9", "38.4")), ("Lomas", "gruesa", ("3.65", "3.65"), ("3.51", "3.51")),
    ("Pampas", "gruesa", ("4.0", "9.17"), ("6.6", "16.0")), ("Cañamac", "gruesa", ("16.32", "33.00"), ("17.9", "36.2")),
    ("Ruinas", "gruesa", ("24.5", "24.5"), None), ("Desvío", "gruesa", ("27.70", "42.10"), ("12.51", "28.70")),
    ("Miramar", "gruesa", ("23.3", "44.0"), None), ("Panamericana", "fina", ("23.7", "59.0"), None),
    ("Logio", "gruesa", ("16.8", "16.8"), ("11.71", "11.71")), ("Gaviotas", "gruesa", ("18.3", "48.6"), None),
    ("Cóndores", "gruesa", ("16.55", "22.4"), None),
]:
    for etapa, rng in (("epipedón", epi), ("subsuelo", sub)):
        if not rng: continue
        lo, hi = rng
        unico = lo == hi
        siar.append(reg(variable="ce_suelo", valor=lo if unico else "", valor_min="" if unico else lo, valor_max="" if unico else hi,
                        unidad="dS/m", cultivo="ninguno", variedad="", etapa=etapa, lugar=f"Suelo {suelo}, área EIA Olmos-Sechura",
                        lat="-6.28", lon="-80.52", fecha_o_periodo="1997", fuente=SI_F, url_o_doi=SI_U,
                        metodo="CE del extracto de saturación en calicatas, descripción de unidades de suelo",
                        tipo_evidencia="medicion_local", estado="observado",
                        notas=(f"Textura {textura}; suelo de desierto NO agrícola, solo contraste de salinidad costera. "
                               "Coordenada = punto central del proyecto (UTM 17S N 9305723,9 E 553518,0, WGS84), no de la calicata. "
                               + ("Valor único publicado, sin rango." if unico else "Rango entre horizontes/calicatas; sin valor central."))))
# R4-2 (Modelos, ronda 4): suelos de desierto sin uso agrícola fuera de las zonas agrícolas del motor; la etapa ya separa epipedón y subsuelo.
for d in siar:
    d["zona"], d["subzona"] = "", "eia_olmos_sechura_no_agricola"
    d["notas"] += (" Zona no aplica: unidad de suelo de desierto sin uso agrícola (EIA Olmos-Sechura 1997), fuera de las parcelas cultivadas;"
                   " no agregar con ce_suelo de las zonas agrícolas.")
escribir("siar1997_suelos_ce.csv", siar)

# ---------- Menciones curadas de evidencia_n8n ----------
n8n = [
    reg(variable="rendimiento", valor="8.8", unidad="t/ha", cultivo="arroz", etapa="cosecha", lugar="Bajo Piura",
        fecha_o_periodo="2018", fuente="SENASA, nota de prensa 18-05-2018 (vía evidencia_n8n id 511)",
        url_o_doi="https://www.senasa.gob.pe/senasacontigo/acciones-en-predios-piloto-permiten-definir-estrategia-contra-plagas-del-arroz-en-valle-del-bajo-piura/",
        metodo="Cifra citada en texto de prensa ('llega hasta 8.8 toneladas por hectárea')", tipo_evidencia="regional", estado="estimado",
        notas="Es un máximo, no un promedio medido; sin método. Sin rango."),
    reg(variable="rendimiento", valor_min="13.1", valor_max="14.5", unidad="t/ha", cultivo="limón", etapa="cosecha", lugar="Piura (zona productora)",
        fecha_o_periodo="1997, 2007, 2014 (mejores años)", fuente="Andina / MINAGRI vía SENASA, 05-07-2017 (evidencia_n8n id 612)",
        url_o_doi="https://www.senasa.gob.pe/senasacontigo/andina-minagri-exportaciones-de-limon-crecieron-3218-entre-2002-y-2016/",
        metodo="Cifra citada en texto de prensa", tipo_evidencia="regional", estado="estimado",
        notas="Rango de rendimientos en los años más altos de 20 años; sesgado hacia arriba. Sin valor central."),
    reg(variable="rendimiento", valor="8", unidad="t/ha", cultivo="mango", variedad="", etapa="cosecha", lugar="Piura (departamento)",
        fecha_o_periodo="c. 2011-2012", fuente="BCRP Sucursal Piura, Caracterización del departamento de Piura (evidencia_n8n id 2687)",
        url_o_doi="https://www.bcrp.gob.pe/docs/Sucursales/Piura/Piura-Caracterizacion.pdf", metodo="Cifra redondeada citada en texto ('alrededor de las 8 TM/ha')",
        tipo_evidencia="bibliografico", estado="estimado", notas="~18 mil ha instaladas según la misma fuente. Cifra aproximada sin rango; contrastar con el Compendio INEI 2017 (tabla 12.8)."),
]
escribir("n8n_curado.csv", n8n)
