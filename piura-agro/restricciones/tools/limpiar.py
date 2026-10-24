#!/usr/bin/env python3
"""Genera restricciones/evidencia_observada.csv a partir de los crudos de restricciones/insumos/*.csv.

Valida cada fila y falla (exit 1) con un mensaje que dice archivo, línea y problema:
  - cabecera = columnas del CONTRATO, incluida `zona` (+ fecha_consulta);
  - campos obligatorios no vacíos;
  - unidad: una de las del CONTRATO (lista ampliada el 24-oct 06:41); cualquier otra falla;
  - estado y tipo_evidencia dentro de las listas permitidas;
  - números válidos y valor_min <= valor <= valor_max;
  - estado 'desconocido' => valor, valor_min y valor_max vacíos;
  - estado 'observado'/'estimado' => valor, o bien valor_min y valor_max;
  - cifra sin rango => `notas` dice por qué (debe contener la palabra 'rango');
  - dotaciones, módulos, licencias y volúmenes asignados: estado 'estimado' y metodo 'dotacion_asignada' (CONTRATO);
    disponibilidad hídrica programada no puede ser 'observado';
  - CE de suelo (ce_suelo*, ece*): metodo declara el extracto (pasta saturada, 1:1, 1:2,5, 1:5) o es
    'ce_extracto_no_declarado', y en ese caso estado 'observado' (CONTRATO);
  - lugar fuera de Piura y de la costa norte (La Libertad, Ica, Lima, Perú...) no puede ser medicion_local ni regional;
  - analogo_externo exige 'Comparabilidad:' en notas (CONTRATO);
  - zona: columna del CONTRATO, uno de zonas.ZONAS o vacío; vacío exige 'Zona no aplica:' en notas; lugar con
    'Medio y Bajo Piura' va en medio_bajo_piura (o piura_region si abarca todos los valles), nunca en uno de los dos ni vacío; lugar fuera de Piura no lleva zona; la zona no se escribe en notas.
  - R4 (Modelos): rendimiento en kg/ha se convierte a t/ha (cifra original en notas); una sola unidad por variable salvo
    UNIDADES_MULTIPLES con razón; ce_agua_riego en dS/m fuera de [0,01; 30] falla salvo 'pozo' en notas;
  - columnas opcionales del CONTRATO `fuente_primaria` y `subzona`: se copian si vienen.
  - columna opcional `rescatado_por_serie` (ronda 7, regla A4 de Piura Modelos; aún no está en CONTRATO.md): '', '0' o '1';
    '1' exige estado 'estimado' y la palabra 'serie' en notas.
id_registro = sha1(variable|cultivo|variedad|etapa|lugar|fecha_o_periodo|unidad|fuente)[:12]. El método NO entra:
dos filas que sólo difieren en método son la misma clave para quien consume la tabla. Duplicados idénticos se
funden; misma clave con cifras distintas falla (distinga lugar, etapa, fecha o variable, o junte un rango).
--estricto se mantiene por compatibilidad: hoy no hay avisos que endurecer, así que valida lo mismo.
Uso: python3 tools/limpiar.py [--insumos DIR] [--salida FILE] [--estricto]
"""
import argparse, csv, hashlib, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from zonas import ZONAS, FUERA, MEDIO_BAJO
from contrato import DOTACION, CE_SUELO, declara_extracto, M_DOT, M_CE
CONTRATO = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
            "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]
OPCIONALES = ["fuente_primaria", "subzona", "rescatado_por_serie"]
SALIDA = ["id_registro"] + CONTRATO + OPCIONALES + ["fecha_consulta", "archivo_origen"]
OBLIGATORIOS = ["variable", "unidad", "cultivo", "lugar", "fecha_o_periodo", "fuente", "url_o_doi", "metodo",
                "tipo_evidencia", "estado", "notas"]
UNIDADES_CONTRATO = {"mm", "mm/día", "kg/ha", "t/ha", "dS/m", "cmol/kg", "%", "°C", "días", "ha", "PEN/ha", "PEN/kg", "PEN/t",
                     "PEN/m3", "USD/ha", "m3/ha", "m3/ha/año", "hm3"}
ESTADOS = {"observado", "estimado", "desconocido"}
TIPOS = ["medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion"]
# Conversiones en origen (R4-5): la unidad canónica por variable; la cifra original queda en notas.
CONVERSIONES = {("rendimiento", "kg/ha"): ("t/ha", 0.001)}
# Variables que pueden llevar más de una unidad, con la razón. Toda otra variable debe tener una sola unidad en la tabla.
UNIDADES_MULTIPLES = {
    "costo_produccion": ({"PEN/ha", "USD/ha"}, "convertir USD a PEN exige un tipo de cambio por fecha que la fuente no da; agrupe por (variable, unidad)"),
    "modulo_riego": ({"m3/ha", "m3/ha/año"}, "por campaña frente a por año: magnitudes distintas, no convertibles sin el n.º de campañas"),
    "agua_riego_consumo": ({"m3/ha", "m3/ha/año"}, "por campaña frente a por año: magnitudes distintas, no convertibles sin el n.º de campañas"),
}
# CE de agua de riego en dS/m: fuera de [0,01; 30] casi seguro es una conversión mal hecha (µS/cm o mS/cm), salvo pozos con nota.
CEW_MIN, CEW_MAX = 0.01, 30.0
PROGRAMADAS = re.compile(r"^disponibilidad_hidrica")
IGNORADOS = {"evidencia_n8n.csv": "crudo de n8n con otro esquema (payload_json); sus cifras útiles van curadas en n8n_curado.csv"}
csv.field_size_limit(10**9)

def falla(msg):
    sys.exit(f"ERROR limpiar.py: {msg}")

def num(s, donde, campo):
    s = s.strip()
    if not s: return None
    try: return float(s)
    except ValueError: falla(f"{donde}: '{campo}'='{s}' no es número (use punto decimal, sin separador de miles)")

def id_registro(r):
    k = "|".join(r[c].strip() for c in ("variable", "cultivo", "variedad", "etapa", "lugar", "fecha_o_periodo", "unidad", "fuente"))
    return hashlib.sha1(k.encode("utf-8")).hexdigest()[:12]

def validar_zona(r, donde):
    if re.search(r"Zona( asignada)?: ", r["notas"]):
        falla(f"{donde}: zona escrita en notas ('Zona: X.'); la zona va sólo en la columna `zona` del CONTRATO")
    z = r["zona"]
    if z and z not in ZONAS: falla(f"{donde}: zona '{z}' no permitida; CONTRATO: {ZONAS} o vacío")
    fuera = bool(FUERA.search(r["lugar"])) and "Piura" not in r["lugar"]
    if z and fuera: falla(f"{donde}: lugar '{r['lugar']}' está fuera de Piura y tiene zona '{z}'; deje zona vacía con 'Zona no aplica:'")
    if "Medio y Bajo" in r["lugar"] and z in ("", "medio_piura", "bajo_piura"):  # piura_region vale si el lugar abarca todos los valles
        falla(f"{donde}: lugar '{r['lugar']}' junta Medio y Bajo Piura; zona debe ser '{MEDIO_BAJO}' (CONTRATO), no '{z}'")
    if not z and "Zona no aplica:" not in r["notas"]:
        falla(f"{donde}: zona vacía sin explicación; notas debe decir 'Zona no aplica: ...' (Medio y Bajo juntos = {MEDIO_BAJO})")

def convertir(r):
    k = (r["variable"], r["unidad"])
    if k not in CONVERSIONES: return
    u, f = CONVERSIONES[k]
    orig = {c: r[c] for c in ("valor", "valor_min", "valor_max") if r[c].strip()}
    for c, x in orig.items(): r[c] = f"{float(x) * f:.6g}"
    txt = ", ".join(f"{c}={x}" for c, x in orig.items())
    r["notas"] = (r["notas"] + f" Cifra original: {txt} {k[1]}; convertida a {u} por limpiar.py.").strip()
    r["unidad"] = u

def validar(r, donde):
    for c in OBLIGATORIOS:
        if not r[c].strip(): falla(f"{donde}: campo obligatorio '{c}' vacío")
    u = r["unidad"]
    if u not in UNIDADES_CONTRATO:
        falla(f"{donde}: unidad '{u}' no permitida; CONTRATO: {sorted(UNIDADES_CONTRATO)}")
    if r["estado"] not in ESTADOS: falla(f"{donde}: estado '{r['estado']}' inválido; use {sorted(ESTADOS)}")
    if r["tipo_evidencia"] not in TIPOS: falla(f"{donde}: tipo_evidencia '{r['tipo_evidencia']}' inválido; use {TIPOS}")
    v, lo, hi = (num(r[c], donde, c) for c in ("valor", "valor_min", "valor_max"))
    for c in ("lat", "lon"): num(r[c], donde, c)
    if r["estado"] == "desconocido" and any(x is not None for x in (v, lo, hi)):
        falla(f"{donde}: estado 'desconocido' exige valor, valor_min y valor_max vacíos (la cifra dudosa va en notas)")
    if r["estado"] != "desconocido" and v is None and (lo is None or hi is None):
        falla(f"{donde}: estado '{r['estado']}' sin valor exige valor_min y valor_max; si no hay cifra use 'desconocido'")
    if lo is not None and hi is not None and lo > hi: falla(f"{donde}: valor_min {lo} > valor_max {hi}")
    if v is not None and lo is not None and v < lo: falla(f"{donde}: valor {v} < valor_min {lo}")
    if v is not None and hi is not None and v > hi: falla(f"{donde}: valor {v} > valor_max {hi}")
    if v is not None and lo is None and hi is None and "rango" not in r["notas"].lower():
        falla(f"{donde}: cifra sin valor_min/valor_max y notas no dicen por qué (CONTRATO); escriba p. ej. 'Sin rango: ...'")
    if DOTACION.match(r["variable"]):
        if r["estado"] != "estimado":
            falla(f"{donde}: '{r['variable']}' es dotación o módulo asignado; estado debe ser 'estimado' (CONTRATO), no '{r['estado']}'")
        if r["metodo"] != M_DOT:
            falla(f"{donde}: '{r['variable']}' es dotación o módulo asignado; metodo debe ser '{M_DOT}' (CONTRATO), no '{r['metodo'][:40]}'")
    if PROGRAMADAS.match(r["variable"]) and r["estado"] == "observado":
        falla(f"{donde}: '{r['variable']}' es programada, no agua entregada medida; use estado 'estimado'")
    if CE_SUELO.match(r["variable"]):
        if r["metodo"] != M_CE and not declara_extracto(r["metodo"]):
            falla(f"{donde}: CE de suelo sin extracto en metodo; declare el extracto (pasta saturada, 1:1, 1:2,5, 1:5) o use '{M_CE}' (CONTRATO)")
        if r["metodo"] == M_CE and r["estado"] != "observado":
            falla(f"{donde}: '{M_CE}' va con estado 'observado' (CONTRATO), no '{r['estado']}'")
    if r["variable"] == "ce_agua_riego" and r["unidad"] == "dS/m" and "pozo" not in r["notas"].lower():
        for x in (v, lo, hi):
            if x is not None and not CEW_MIN <= x <= CEW_MAX:
                falla(f"{donde}: ce_agua_riego {x} dS/m fuera de [{CEW_MIN}; {CEW_MAX}]: probable conversión mal hecha (µS/cm o mS/cm); "
                      "revise la unidad original en la fuente (o declare 'pozo' en notas si es agua de pozo)")
    rs = r.get("rescatado_por_serie", "")
    if rs not in ("", "0", "1"): falla(f"{donde}: rescatado_por_serie '{rs}' inválido; use vacío, 0 o 1")
    if rs == "1" and r["estado"] != "estimado":
        falla(f"{donde}: rescatado_por_serie=1 exige estado 'estimado' (regla A4 de serie), no '{r['estado']}'")
    if rs == "1" and "serie" not in r["notas"].lower():
        falla(f"{donde}: rescatado_por_serie=1 exige la serie del distrito (años y valores) en notas con la palabra 'serie'")
    validar_zona(r, donde)
    fuera = FUERA.search(r["lugar"]) and "Piura" not in r["lugar"] and "Lambayeque" not in r["lugar"]  # Lambayeque = costa norte (CONTRATO)
    if fuera and r["tipo_evidencia"] in ("medicion_local", "regional"):
        falla(f"{donde}: lugar '{r['lugar']}' está fuera de Piura y de la costa norte; tipo_evidencia debe ser 'analogo_externo' (o bibliografico)")
    if r["tipo_evidencia"] == "analogo_externo" and "Comparabilidad:" not in r["notas"]:
        falla(f"{donde}: analogo_externo exige 'Comparabilidad:' en notas (por qué es comparable y cuánto difiere de Piura)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", default=str(BASE / "insumos"))
    ap.add_argument("--salida", default=str(BASE / "evidencia_observada.csv"))
    ap.add_argument("--estricto", action="store_true", help="compatibilidad; hoy valida lo mismo que el modo normal")
    a = ap.parse_args()
    archivos = sorted(Path(a.insumos).glob("*.csv"))
    if not archivos: falla(f"no hay CSV en {a.insumos}")
    vistos, dup = {}, 0
    for f in archivos:
        if f.name in IGNORADOS:
            print(f"ignorado {f.name}: {IGNORADOS[f.name]}"); continue
        with f.open(encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            falt = [c for c in CONTRATO if c not in (rd.fieldnames or [])]
            if falt: falla(f"{f.name}: faltan columnas del CONTRATO {falt}")
            n = 0
            for i, r in enumerate(rd, start=2):
                r = {k: (v or "").strip() for k, v in r.items() if k is not None}
                for c in OPCIONALES + ["fecha_consulta"]: r.setdefault(c, "")
                donde = f"{f.name} línea {i}"
                convertir(r)
                validar(r, donde)
                r["id_registro"], r["archivo_origen"] = id_registro(r), f.name
                k = r["id_registro"]
                if k in vistos:
                    o = vistos[k]
                    if any(o[c] != r[c] for c in ("valor", "valor_min", "valor_max", "unidad", "estado")):
                        falla(f"{donde}: duplica id {k} de {o['archivo_origen']} con cifras distintas "
                              f"({o['valor'] or o['valor_min']+'-'+o['valor_max']} vs {r['valor'] or r['valor_min']+'-'+r['valor_max']}); "
                              "la clave (variable, cultivo, variedad, etapa, lugar, fecha, unidad, fuente) es la misma aunque cambie el método: "
                              "distinga lugar/etapa/fecha/variable, junte un rango o descarte una")
                    dup += 1; continue
                vistos[k] = r; n += 1
            print(f"leído {f.name}: {n} registros")
    unid = {}
    for r in vistos.values(): unid.setdefault(r["variable"], {}).setdefault(r["unidad"], r["archivo_origen"])
    for var, us in unid.items():
        permit = UNIDADES_MULTIPLES.get(var, (set(),))[0]
        if len(us) > 1 and not set(us) <= permit:
            falla(f"variable '{var}' con varias unidades {dict(us)}: una sola unidad por variable (convierta en origen o añada a "
                  "UNIDADES_MULTIPLES con la razón)")
    filas = sorted(vistos.values(), key=lambda r: (TIPOS.index(r["tipo_evidencia"]), r["variable"], r["cultivo"], r["lugar"], r["fecha_o_periodo"]))
    with open(a.salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SALIDA, extrasaction="ignore"); w.writeheader(); w.writerows(filas)
    print(f"OK {len(filas)} registros -> {a.salida} (duplicados idénticos fundidos: {dup})")

if __name__ == "__main__":
    main()
