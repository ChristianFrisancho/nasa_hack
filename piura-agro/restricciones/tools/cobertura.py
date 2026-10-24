#!/usr/bin/env python3
"""Cobertura de evidencia_observada.csv (versión final, ronda 7).
Salidas:
  cobertura.csv            cultivo x suelo x zona x grupo de variable: n, n con cifra, n por tipo_evidencia, estados, archivos.
  anexos/huecos_priorizados.csv  combinaciones cultivo x zona x feature del modelo sin cifra, ordenadas por importancia
                           (modelo/ranking_features.csv, método ablación, escenario normal, por cultivo y zona).
Uso: python3 tools/cobertura.py
Suelo: casi ningún registro dice la clase de suelo. Se marca 'salino_sódico' si la variable es de sales del suelo o el lugar/notas
hablan de suelo salino o sódico; 'tablazo_arenoso' si dicen tablazo o arenoso; si no, 'genérico'.
La zona es la columna `zona` del CONTRATO; vacía = 'fuera de Piura'.
"""
import csv
from collections import defaultdict
from pathlib import Path
B = Path(__file__).resolve().parents[1]
RANK = ["medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion"]
CULT = ["arroz", "maíz amarillo duro", "algodón", "frijol", "frijol caupí", "frijol verde", "frijol de palo", "papaya", "camote", "quinua",
        "limón", "mango", "uva", "todos"]
ZONAS = ["chira", "medio_piura", "bajo_piura", "medio_bajo_piura", "san_lorenzo", "alto_piura", "sierra_piura", "piura_region", "fuera de Piura"]
SUELOS = ["genérico", "salino_sódico", "tablazo_arenoso"]
GRUPO = {"rendimiento": "rendimiento", "precio_chacra": "precio", "costo_produccion": "costo", "costo_produccion_por_t": "costo",
         "ingreso_total": "costo"}
def grupo(v):
    if v in GRUPO: return GRUPO[v]
    if v.startswith(("agua_riego", "dotacion", "volumen", "disponibilidad")): return "agua"
    if v.startswith("eficiencia") or v == "area_riego_tecnificado": return "eficiencia"
    if v in ("ce_suelo", "psi_suelo"): return "ece_suelo"
    if v.startswith(("pendiente", "area_cultivo_pendiente")): return "pendiente"
    if v.startswith("ce_agua"): return "ce_agua"
    if v.startswith(("fraccion", "superficie_mal_drena", "superficie_con_sales")): return "drenaje_sales"
    return None
def suelo(r):
    t = (r["lugar"] + " " + r["notas"]).lower()
    if "tablazo" in t or "arenos" in t: return "tablazo_arenoso"
    if r["variable"] in ("ce_suelo", "psi_suelo") or "suelo salino" in t or "suelos salinos" in t or "sódic" in t: return "salino_sódico"
    return "genérico"

def leer():
    cel = defaultdict(lambda: dict(n=0, n_obs=0, tipos=defaultdict(int), est=set(), fuentes=set()))
    for r in csv.DictReader((B / "evidencia_observada.csv").open(encoding="utf-8")):
        g = grupo(r["variable"])
        if not g: continue
        c = r["cultivo"] if r["cultivo"] in CULT else ("todos" if r["cultivo"] in ("ninguno", "frutales") else None)
        if c is None: continue
        x = cel[(c, suelo(r), r["zona"] or "fuera de Piura", g)]
        x["n"] += 1; x["est"].add(r["estado"]); x["fuentes"].add(r["archivo_origen"])
        if r["estado"] != "desconocido": x["n_obs"] += 1; x["tipos"][r["tipo_evidencia"]] += 1
        else: x["tipos"]["desconocido"] += 1
    return cel

# feature del modelo -> grupo de variable de Restricciones; 'zonal' = cuenta cualquier registro de la zona, sea del cultivo que sea
# (una CE de suelo medida bajo limón vale para el frijol de la misma zona); agua cuenta el cultivo y 'todos'
FEAT = {"ece_ds_m": ("ece_suelo", True), "drenaje_malo": ("drenaje_sales", True), "factor_costo": ("costo", False),
        "pendiente_pct": ("pendiente", True), "agua_riego_mm": ("agua", False), "factor_rend": ("rendimiento", False),
        "factor_precio": ("precio", False), "eficiencia_riego": ("eficiencia", True)}
MC = {"algodon": "algodón", "arroz": "arroz", "camote": "camote", "caupi": "frijol caupí", "frijol": "frijol", "maiz_amarillo_duro": "maíz amarillo duro"}
MZ = {"chira_sullana": "chira", "medio_piura": "medio_piura", "bajo_piura": "bajo_piura", "alto_piura": "alto_piura", "san_lorenzo": "san_lorenzo"}

def huecos(cel):
    rk = [r for r in csv.DictReader((B.parent / "modelo" / "ranking_features.csv").open(encoding="utf-8"))
          if r["metodo"] == "ablacion" and r["escenario"] == "normal" and r["cultivo"] in MC and r["zona"] in MZ and r["feature"] in FEAT]
    def n_cifra(cs, z, g):
        return sum(x["n_obs"] for (c, s, zz, gg), x in cel.items() if c in cs and zz == z and gg == g)
    out = []
    for r in rk:
        c, z = MC[r["cultivo"]], MZ[r["zona"]]
        g, zonal = FEAT[r["feature"]]
        cs = set(CULT) if zonal else ({c, "todos"} if g == "agua" else {c})
        n_z = n_cifra(cs, z, g)
        if n_z: continue
        n_mb = n_cifra(cs, "medio_bajo_piura", g) if z in ("medio_piura", "bajo_piura") else 0
        n_reg = n_cifra(cs, "piura_region", g)
        n_fuera = n_cifra(cs, "fuera de Piura", g)
        cerca = ("medio_bajo_piura" if n_mb else "piura_region" if n_reg else "fuera de Piura" if n_fuera else "nada")
        out.append(dict(cultivo=c, zona=z, feature=r["feature"], grupo_variable=g, rango_en_cultivo_zona=int(r["rango"]),
                        importancia=float(r["importancia"]), cambio_top1_pct=r["cambio_top1_pct"], n_con_cifra_zona=0,
                        lo_mas_cercano=cerca, n_medio_bajo=n_mb, n_piura_region=n_reg, n_fuera_piura=n_fuera,
                        dato_del_modelo=r["fuente_dato"]))
    out.sort(key=lambda d: (-d["importancia"]))
    for i, d in enumerate(out, 1): d["prioridad"] = i
    return out

def main():
    cel = leer()
    T = RANK + ["desconocido"]
    with (B / "cobertura.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cultivo", "suelo", "zona", "grupo_variable", "n_registros", "n_con_cifra", *("n_" + t for t in T),
                    "mejor_tipo_evidencia", "estados", "archivos"])
        for k in sorted(cel, key=lambda k: (CULT.index(k[0]), k[3], SUELOS.index(k[1]), ZONAS.index(k[2]))):
            x = cel[k]
            con = [t for t in RANK if x["tipos"].get(t)]
            w.writerow([*k, x["n"], x["n_obs"], *(x["tipos"].get(t, 0) for t in T), con[0] if con else "",
                        "|".join(sorted(x["est"])), "|".join(sorted(x["fuentes"]))])
    H = huecos(cel)
    (B / "anexos").mkdir(exist_ok=True)
    with (B / "anexos" / "huecos_priorizados.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["prioridad", "cultivo", "zona", "feature", "grupo_variable", "rango_en_cultivo_zona", "importancia", "cambio_top1_pct",
                "n_con_cifra_zona", "lo_mas_cercano", "n_medio_bajo", "n_piura_region", "n_fuera_piura", "dato_del_modelo"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(H)
    print(f"OK {len(cel)} celdas -> cobertura.csv; {len(H)} huecos -> anexos/huecos_priorizados.csv")

if __name__ == "__main__":
    main()
