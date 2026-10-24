#!/usr/bin/env python3
"""Rendimiento y precio en chacra por distrito y año desde el dataset DRAP (GORE Piura, datos abiertos).
Lee (solo lectura) cultivos/raw/drap_dataset.csv y escribe insumos/drap_distrito_anual.csv.
rendimiento = suma anual de PRODUCCION (t) / suma anual de COSECHA (ha), por distrito, cultivo y año.
precio_chacra = promedio mensual ponderado por producción (PEN/kg, sin IGV).
Atípico A4: rendimiento > 3 x mediana del mismo cultivo en la misma zona (todos los distrito-años; si la zona
tiene < 5 casos, mediana del cultivo en toda la región) -> desconocido, cifra en notas.
Rescate por serie (regla A4 aceptada por Piura Modelos, ronda 7, factor 1,5): un atípico A4 vuelve como 'estimado' si el
mismo distrito publica para el mismo cultivo cifras dentro de un factor 1,5 (arriba o abajo) en >= 3 años distintos, contando
ese año y cifras observadas o descartadas. La serie (años y valores) va en notas y la columna opcional
`rescatado_por_serie` = 1. EXCLUIDOS queda desconocido con 'pendiente revisión manual'.
Uso: python3 tools/extraer_drap.py
"""
import csv, statistics as st, sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE.parent / "cultivos" / "raw" / "drap_dataset.csv"
OUT = BASE / "insumos" / "drap_distrito_anual.csv"
URL = "https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp"
FUENTE = "GORE Piura - DRA Piura, Campaña agrícola de los principales cultivos de la región Piura (datos abiertos, corte 2025-05-27; códigos SIEA)"
CAMPOS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
          "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas", "fecha_consulta", "rescatado_por_serie"]
F_SERIE, MIN_ANIOS = 1.5, 3
EXCLUIDOS = {("uva", "Distrito Las Lomas (Piura)", "2016")}  # 64,47 t/ha: Modelos pidió revisión manual
CULT = {"ARROZ": "arroz", "MAIZ AMARILLO DURO": "maíz amarillo duro", "MAIZ AMILACEO": "maíz amiláceo",
        "TRIGO BLANDO": "trigo", "FRIJOL GRANO SECO": "frijol", "FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO SECO": "frijol caupí",
        "ARVEJA GRANO SECO": "arveja grano seco", "PAPA (agrupa mejoradas y nativas)": "papa", "ALGODON PIMA": "algodón",
        "ALGODON": "algodón", "YUCA": "yuca", "CAMOTE": "camote", "HABA GRANO SECO": "haba", "SANDIA": "sandía",
        "PAPRIKA": "páprika", "PIQUILLO (T.)": "ají piquillo", "SOYA": "soya", "CEBADA GRANO": "cebada",
        "ZARANDAJA GRANO SECO": "zarandaja", "MAIZ CHOCLO": "choclo", "MANGO": "mango", "LIMON SUTIL": "limón",
        "PLATANOS Y BANANAS PARA COCCI N (M X paradisiaca)": "plátano", "VID": "uva", "CA A DE AZUCAR (PARA ALCOHOL)": "caña etanol"}
VARIEDAD = {"ALGODON PIMA": "Pima", "ALGODON": ""}
SIERRA = {"AYABACA", "HUANCABAMBA"}
MORR_SIERRA = {"CHALACO", "SANTO DOMINGO", "SANTA CATALINA DE MOSSA", "YAMANGO"}
from zonas import zona_distrito
def zona(prov, dist):  # macrozona antigua, sólo para la regla A4 (no cambia los atípicos de la ronda 1)
    if prov in SIERRA or (prov == "MORROPON" and dist in MORR_SIERRA): return "Sierra"
    if prov == "MORROPON": return "Alto Piura"
    if prov in ("SULLANA", "PAITA"): return "Chira"
    if prov == "PIURA" and dist in ("TAMBO GRANDE", "LAS LOMAS"): return "San Lorenzo"
    if prov in ("PIURA", "SECHURA"): return "Medio y Bajo Piura"
    sys.exit(f"ERROR: distrito sin zona asignada: {prov}/{dist}")

def num(s):
    s = (s or "").strip()
    return float(s) if s else None

agg = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0])  # prod, cosecha, sum p*q, q con precio, meses
for x in csv.DictReader(SRC.open(encoding="utf-8", errors="replace")):
    if x["CULTIVO"] not in CULT: continue
    k = (x["PROVINCIA"], x["DISTRITO"], x["UBIGEO"], x["CULTIVO"], x["ANO"])
    q, h, p = num(x["PRODUCCION"]), num(x["COSECHA"]), num(x["PRECIO_CHACRA"])
    a = agg[k]
    # totales anuales independientes: la DRA anota la producción mes a mes y el área cosechada al cerrar la cosecha
    if q: a[0] += q
    if h: a[1] += h; a[4] += 1
    if p and q: a[2] += p * q; a[3] += q

rend = {k: a[0] / a[1] for k, a in agg.items() if a[1] >= 1}
medc, medz = defaultdict(list), defaultdict(list)
for k, v in rend.items():
    medc[CULT[k[3]]].append(v); medz[(CULT[k[3]], zona(k[0], k[1]))].append(v)
def ref(c, z):
    vz = medz.get((c, z), [])
    return (st.median(vz), f"mediana {c} en {z}") if len(vz) >= 5 else (st.median(medc[c]), f"mediana regional de {c}")

rows = []
for k, a in sorted(agg.items()):
    prov, dist, ubi, craw, ano = k
    c = CULT[craw]; z = zona(prov, dist)
    base = dict(cultivo=c, variedad=VARIEDAD.get(craw, ""), etapa="cosecha", zona=zona_distrito(prov, dist), lugar=f"Distrito {dist.title()} ({prov.title()})",
                fecha_o_periodo=ano, fuente=FUENTE, url_o_doi=URL, tipo_evidencia="regional", fecha_consulta="2026-10-24",
                valor_min="", valor_max="", lat="", lon="")
    if k in rend:
        v = rend[k]; nt = f"UBIGEO {ubi}. Cosecha {a[1]:.0f} ha, producción {a[0]:.0f} t, {a[4]} meses con cosecha. Sin rango publicado."
        r = dict(base, variable="rendimiento", unidad="t/ha", metodo="Suma anual de producción / suma anual de superficie cosechada (registro mensual DRA)")
        m, txt = ref(c, z)
        if v > 3 * m:
            r.update(valor="", estado="desconocido", notas=nt + f" Atípico A4: {v:.2f} t/ha > 3 x {txt} ({m:.2f}); descartado.")
            ser = sorted((k2[4], v2) for k2, v2 in rend.items() if k2[:4] == k[:4] and v / F_SERIE <= round(v2, 2) <= v * F_SERIE)
            if len({x[0] for x in ser}) >= MIN_ANIOS:
                det = "; ".join(f"{an} {x:.2f}" for an, x in ser)
                txs = (f" Serie del distrito ({len(ser)} años con cifra entre {v/F_SERIE:.2f} y {v*F_SERIE:.2f} t/ha, factor 1,5): {det}.")
                if (c, r["lugar"], ano) in EXCLUIDOS:
                    r["notas"] += txs + " La regla de serie la rescataría, pero queda desconocido: pendiente revisión manual (Piura Modelos, ronda 7)."
                else:
                    r.update(valor=f"{v:.2f}", estado="estimado", rescatado_por_serie="1",
                             notas=nt + f" Atípico A4: {v:.2f} t/ha > 3 x {txt} ({m:.2f})." + txs
                             + " Rescatado por serie (regla A4 factor 1,5 aceptada por Piura Modelos, ronda 7): estimado, no observado.")
        else:
            r.update(valor=f"{v:.2f}", estado="observado", notas=nt)
        rows.append(r)
    if a[3] > 0:
        rows.append(dict(base, variable="precio_chacra", unidad="PEN/kg", valor=f"{a[2]/a[3]:.2f}", estado="observado",
                         metodo="Promedio anual del precio en chacra mensual ponderado por producción (sin IGV)",
                         notas=f"UBIGEO {ubi}. Producción con precio {a[3]:.0f} t. Sin rango publicado."))
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(rows)
print(f"OK {len(rows)} -> {OUT.relative_to(BASE)} ; desconocidos A4: {sum(r['estado']=='desconocido' for r in rows)}; "
      f"rescatados por serie: {sum(r.get('rescatado_por_serie')=='1' for r in rows)}")
