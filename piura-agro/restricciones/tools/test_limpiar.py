#!/usr/bin/env python3
"""Pruebas de limpiar.py: un caso válido y casos que deben fallar con mensaje claro. Cada error que Modelos encontró
en la ronda 2 (unidades, duplicados, rangos, dotación asignada, La Libertad, zona) tiene su caso, y cada regla del
CONTRATO del 24-oct 06:41 (unidades ampliadas, medio_bajo_piura, dotacion_asignada, ce_extracto_no_declarado, columnas opcionales) también. Uso: python3 tools/test_limpiar.py"""
import csv, subprocess, sys, tempfile
from pathlib import Path
T = Path(__file__).resolve().parent / "limpiar.py"
INSUMOS = Path(__file__).resolve().parents[1] / "insumos"
C = ["fuente_primaria","subzona","rescatado_por_serie","variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fecha_consulta"]
OK = dict(variable="rendimiento", valor="8.0", valor_min="", valor_max="", unidad="t/ha", cultivo="arroz", variedad="",
          etapa="cosecha", zona="bajo_piura", lugar="Distrito Catacaos (Piura)", lat="", lon="", fecha_o_periodo="2020", fuente="F",
          url_o_doi="u", metodo="m", tipo_evidencia="regional", estado="observado", notas="Sin rango publicado.", fecha_consulta="2026-10-24")
DOT = dict(OK, variable="dotacion_agua_riego", unidad="m3/ha/año", valor="9528", estado="estimado", metodo="dotacion_asignada")
CE = dict(OK, variable="ce_suelo", unidad="dS/m", valor="0.95", metodo="ce_extracto_no_declarado")
VIRU = dict(OK, variable="fraccion_area_napa", unidad="%", valor="20", zona="", lugar="Valle de Virú (La Libertad)",
            notas="Sin rango. Zona no aplica: lugar fuera de Piura.")
CASOS = [("válido", [OK], 0, "OK 1"),
         ("duplicado idéntico", [OK, OK], 0, "fundidos: 1"),
         ("unidad mala", [dict(OK, unidad="qq/ha")], 1, "unidad 'qq/ha'"),
         # 1. unidades: las 8 nuevas del CONTRATO pasan también en --estricto; cualquier otra falla
         *[(f"{u} pasa en --estricto", [dict(OK, variable="v_" + u, unidad=u)], 0, "OK 1", ["--estricto"])
           for u in ("PEN/kg", "PEN/t", "PEN/m3", "USD/ha", "m3/ha", "m3/ha/año", "hm3", "ha")],
         ("USD/h (errata) falla", [dict(OK, variable="costo_produccion", unidad="USD/h")], 1, "no permitida"),
         ("m3/ha/ano sin tilde falla", [dict(OK, variable="agua", unidad="m3/ha/ano")], 1, "no permitida"),
         ("desconocido con valor", [dict(OK, estado="desconocido")], 1, "exige valor, valor_min y valor_max vacíos"),
         ("observado sin cifra", [dict(OK, valor="")], 1, "sin valor exige valor_min"),
         ("min>max", [dict(OK, valor="", valor_min="9", valor_max="3")], 1, "valor_min 9.0 > valor_max 3.0"),
         ("valor fuera de rango", [dict(OK, valor_min="1", valor_max="5")], 1, "> valor_max"),
         ("coma decimal", [dict(OK, valor="8,0")], 1, "no es número"),
         ("tipo inválido", [dict(OK, tipo_evidencia="medido")], 1, "tipo_evidencia 'medido'"),
         ("obligatorio vacío", [dict(OK, fuente="")], 1, "'fuente' vacío"),
         # 2. duplicados: misma clave con cifras distintas, aunque cambie el método
         ("duplicado con cifras distintas", [OK, dict(OK, valor="9.0")], 1, "cifras distintas"),
         ("duplicado que sólo cambia el método", [OK, dict(OK, valor="9.0", metodo="otro método")], 1, "aunque cambie el método"),
         # (antes: 'misma cifra en otra unidad no es duplicado' pasaba; desde R4-5 una variable lleva una sola unidad)
         ("misma variable en mm y m3/ha falla (R4-5)", [dict(OK, variable="agua", unidad="mm", valor="1200"),
                                                         dict(OK, variable="agua", unidad="m3/ha", valor="12000")], 1, "varias unidades"),
         # 3. cifra sin rango debe decir por qué
         ("sin rango y sin explicación", [dict(OK, notas="n")], 1, "notas no dicen por qué"),
         # 4. dotación o módulo: estado estimado y metodo dotacion_asignada (CONTRATO)
         ("dotación observada falla", [dict(DOT, estado="observado")], 1, "estado debe ser 'estimado'"),
         ("dotación desconocida falla", [dict(DOT, estado="desconocido", valor="", notas="Sin dato.")], 1, "estado debe ser 'estimado'"),
         ("módulo observado falla", [dict(DOT, variable="modulo_riego", estado="observado")], 1, "estado debe ser 'estimado'"),
         ("dotación sin metodo dotacion_asignada falla", [dict(DOT, metodo="Dotación del plan de cuenca")], 1, "metodo debe ser 'dotacion_asignada'"),
         ("dotación estimada con dotacion_asignada pasa", [DOT], 0, "OK 1"),
         ("disponibilidad programada observada falla", [dict(OK, variable="disponibilidad_hidrica", unidad="hm3", valor="600")], 1, "es programada"),
         # 4b. CE de suelo: extracto declarado o ce_extracto_no_declarado con estado observado
         ("CE sin método de extracto falla", [dict(CE, metodo="Análisis de laboratorio")], 1, "CE de suelo sin extracto"),
         ("CE con ce_extracto_no_declarado pasa", [CE], 0, "OK 1"),
         ("CE pasta saturada pasa", [dict(CE, metodo="Extracto de pasta saturada, laboratorio UNP")], 0, "OK 1"),
         ("CE 1:1 pasa", [dict(CE, metodo="CE en extracto suelo:agua 1:1")], 0, "OK 1"),
         ("CE 'no declara el extracto (pasta saturada u otro)' falla", [dict(CE, metodo="Laboratorio; la tesis no declara el extracto (pasta saturada u otro)")], 1, "CE de suelo sin extracto"),
         ("ce_extracto_no_declarado estimado falla", [dict(CE, estado="estimado")], 1, "va con estado 'observado'"),
         ("ce_agua_riego en dS/m no exige extracto de suelo", [dict(CE, variable="ce_agua_riego", metodo="Conductímetro de campo en canal")], 0, "OK 1"),
         ("ce_agua_riego en µS/cm falla (convertir a dS/m)", [dict(CE, variable="ce_agua_riego", unidad="µS/cm", metodo="m")], 1, "unidad"),
         ("ECe sin método falla", [dict(CE, variable="ece_0_30cm", metodo="m")], 1, "CE de suelo sin extracto"),
         # 5. lugar fuera de Piura: analogo_externo con Comparabilidad
         ("La Libertad como regional", [VIRU], 1, "fuera de Piura y de la costa norte"),
         ("analogo_externo sin Comparabilidad", [dict(VIRU, tipo_evidencia="analogo_externo")], 1, "exige 'Comparabilidad:'"),
         ("analogo_externo con Comparabilidad", [dict(VIRU, tipo_evidencia="analogo_externo", notas=VIRU["notas"] + " Comparabilidad: valle costero árido.")], 0, "OK 1"),
         ("Lambayeque regional pasa (costa norte)", [dict(OK, zona="", lugar="Lambayeque (departamento)", notas="Sin rango. Zona no aplica: lugar fuera de Piura.")], 0, "OK 1"),
         # 6. zona: sólo los valores del CONTRATO, en la columna, nunca en notas
         ("zona fuera del CONTRATO", [dict(OK, zona="Medio y Bajo Piura")], 1, "zona 'Medio y Bajo Piura' no permitida"),
         ("zona formato viejo", [dict(OK, zona="Chira")], 1, "zona 'Chira' no permitida"),
         ("zona en notas", [dict(OK, notas="Zona: Chira. Sin rango.")], 1, "zona escrita en notas"),
         ("Zona asignada en notas", [dict(OK, notas="Zona asignada: Sierra. Sin rango.")], 1, "zona escrita en notas"),
         ("zona vacía sin explicación", [dict(OK, zona="")], 1, "zona vacía sin explicación"),
         ("medio_bajo_piura pasa", [dict(OK, zona="medio_bajo_piura", lugar="Sistema Medio y Bajo Piura")], 0, "OK 1"),
         ("Medio y Bajo con zona vacía falla", [dict(OK, zona="", lugar="Sistema Medio y Bajo Piura", notas="Sin rango. Zona en conflicto: juntos.")], 1, "zona debe ser 'medio_bajo_piura'"),
         ("Medio y Bajo asignado a bajo_piura falla", [dict(OK, lugar="Valle Medio y Bajo Piura")], 1, "zona debe ser 'medio_bajo_piura'"),
         ("zona inventada falla", [dict(OK, zona="medio_y_bajo")], 1, "zona 'medio_y_bajo' no permitida"),
         ("fuente_primaria y subzona se copian", [dict(OK, fuente_primaria="MIDAGRI-SIEA", subzona="Tablazo Sur")], 0, "OK 1"),
         # ronda 7: rescate por serie (A4 factor 1,5, Piura Modelos)
         ("rescatado_por_serie=1 estimado con serie pasa", [dict(OK, estado="estimado", rescatado_por_serie="1",
                                                               notas="Sin rango publicado. Serie del distrito: 2016 13.20; 2017 12.00; 2018 14.60.")], 0, "OK 1"),
         ("rescatado_por_serie=1 observado falla", [dict(OK, rescatado_por_serie="1", notas="Sin rango. Serie: 2016 13.2; 2017 12; 2018 14.6.")], 1, "exige estado 'estimado'"),
         ("rescatado_por_serie=1 sin serie en notas falla", [dict(OK, estado="estimado", rescatado_por_serie="1")], 1, "palabra 'serie'"),
         ("rescatado_por_serie con valor raro falla", [dict(OK, rescatado_por_serie="si")], 1, "rescatado_por_serie 'si' inválido"),
         ("lugar fuera de Piura con zona", [dict(VIRU, zona="bajo_piura", tipo_evidencia="analogo_externo", notas="Sin rango. Comparabilidad: x.")], 1, "tiene zona"),
         ("falta columna zona", "SIN_ZONA", 1, "faltan columnas del CONTRATO ['zona']"),
         # 7. ronda 4 (objeciones de Modelos R4-1, R4-3, R4-4, R4-5 y steering 07:24)
         ("rendimiento kg/ha se convierte a t/ha", [dict(OK, valor="7800", unidad="kg/ha")], 0, "OK 1"),
         ("dos unidades en una variable falla", [OK, dict(OK, lugar="Otro lugar (Piura)", unidad="mm")], 1, "varias unidades"),
         ("costo PEN/ha y USD/ha permitido con razón", [dict(OK, variable="costo_produccion", unidad="PEN/ha"),
                                                        dict(OK, variable="costo_produccion", unidad="USD/ha", lugar="Otro (Piura)")], 0, "OK 2"),
         ("costo en PEN/t bajo costo_produccion falla", [dict(OK, variable="costo_produccion", unidad="PEN/ha"),
                                                          dict(OK, variable="costo_produccion", unidad="PEN/t", lugar="Otro (Piura)")], 1, "varias unidades"),
         ("CEw 4.98 dS/m pasa", [dict(CE, variable="ce_agua_riego", valor="4.98", metodo="m")], 0, "OK 1"),
         ("CEw 4980 dS/m (µS/cm sin convertir) falla", [dict(CE, variable="ce_agua_riego", valor="4980", metodo="m")], 1, "probable conversión mal hecha"),
         ("CEw 0.0049 dS/m (dividido de más) falla", [dict(CE, variable="ce_agua_riego", valor="0.0049", metodo="m")], 1, "probable conversión mal hecha"),
         ("CEw rango con máximo 40 falla", [dict(CE, variable="ce_agua_riego", valor="", valor_min="1", valor_max="40", metodo="m")], 1, "probable conversión mal hecha"),
         ("CEw de pozo con nota pasa aunque > 30", [dict(CE, variable="ce_agua_riego", valor="35", metodo="m", notas="Sin rango. Agua de pozo salobre.")], 0, "OK 1"),
         ("zona vacía con 'Zona no aplica:' pasa", [dict(OK, zona="", notas="Sin rango. Zona no aplica: suelo no agrícola.")], 0, "OK 1"),
         ("estimado sin valor pero con rango pasa", [dict(OK, valor="", valor_min="3", valor_max="5", estado="estimado")], 0, "OK 1"),
         ("estimado sin ninguna cifra falla", [dict(OK, valor="", estado="estimado")], 1, "si no hay cifra use 'desconocido'")]
fallos = 0
def correr(d, extra=()):
    p = subprocess.run([sys.executable, T, "--insumos", d, "--salida", f"{d}/out.csv", *extra], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr
for caso in CASOS:
    nombre, filas, rc, texto, extra = (caso + ([],))[:5]
    with tempfile.TemporaryDirectory() as d:
        cols = [c for c in C if c != "zona"] if filas == "SIN_ZONA" else C
        filas = [{k: v for k, v in OK.items() if k != "zona"}] if filas == "SIN_ZONA" else filas
        filas = [{c: x.get(c, "") for c in cols} for x in filas]
        with open(f"{d}/x.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(filas)
        code, out = correr(d, extra)
        bien = code == rc and texto in out
        if nombre.startswith("rendimiento kg/ha") and bien:
            fila = next(csv.DictReader(open(f"{d}/out.csv", encoding="utf-8")))
            bien = fila["unidad"] == "t/ha" and fila["valor"] == "7.8" and "Cifra original: valor=7800 kg/ha" in fila["notas"]
        if nombre.startswith("fuente_primaria") and bien:
            fila = next(csv.DictReader(open(f"{d}/out.csv", encoding="utf-8")))
            bien = fila["fuente_primaria"] == "MIDAGRI-SIEA" and fila["subzona"] == "Tablazo Sur"
        fallos += not bien
        print(("PASA " if bien else "FALLA"), nombre, "|", out.strip().splitlines()[-1])
# Insumos reales: pasan en modo normal y en --estricto (CONTRATO 24-oct 06:41 aceptó las unidades).
with tempfile.TemporaryDirectory() as d:
    for extra, rc, texto, nombre in (([], 0, "OK ", "insumos reales, modo normal"),
                                     (["--estricto"], 0, "OK ", "insumos reales pasan en --estricto")):
        p = subprocess.run([sys.executable, T, "--salida", f"{d}/out.csv", *extra], capture_output=True, text=True)
        out = p.stdout + p.stderr; bien = p.returncode == rc and texto in out; fallos += not bien
        print(("PASA " if bien else "FALLA"), nombre, "|", out.strip().splitlines()[-1])
sys.exit(1 if fallos else 0)
