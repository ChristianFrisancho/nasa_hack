#!/usr/bin/env python3
"""R4-7..R4-11: lluvia PISCOp v2.1 y CHIRPS frente a las normales SENAMHI 1971-2000, por estación, zona y temporada,
y PISCOp frente a CHIRPS mes a mes (1981-2019) en seis estaciones de valle.

Entradas (solo lectura): suelos/datos/clima/raw/PISCOp_monthly.nc (PISCOp v2.1, SENAMHI, 0,1°, 468 meses 1981-01..2019-12,
https://doi.org/10.6084/m9.figshare.21127423), suelos/datos/clima/raw/chirps_ventana_piura.npz (CHIRPS 0,05°),
estaciones de tools/chirps_vs_senamhi.py (SENAMHI 2016, Tabla N°3, normal 1971-2000).
Años El Niño: clasificación ICEN oficial por campaña de Piura Territorio (tools/icen_campanias.py; antes de 1981-82, la
misma regla aplicada por Piura Datos). "sin El Niño" excluye toda campaña el_nino (débil, moderada, fuerte, extraordinaria).
La temporada SON del año Y pertenece a la campaña Y+1 (ago-jul); anual, DEF, MAM y JJA a la campaña Y. PISCOp mezcla estaciones SENAMHI con CHIRP: su acuerdo con las normales de
estación es en parte circular; no es una validación independiente.
Necesita rasterio: ../suelos/.venv/bin/python tools/pisco_vs_chirps.py
Salidas: clima/pisco_chirps_senamhi_estacion.csv, clima/pisco_vs_chirps_mensual.csv, clima/pisco_vs_chirps_resumen.txt
"""
import csv, sys
from pathlib import Path
import numpy as np
import rasterio
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chirps_vs_senamhi import EST, NPZ, TEMP
from icen_campanias import clasificacion
CLS = clasificacion()
BASE = Path(__file__).resolve().parents[1]
PISCO = BASE.parent / "suelos/datos/clima/raw/PISCOp_monthly.nc"
def esc(y, t):  # escenario de la campaña a la que pertenece la temporada t del año y
    return CLS[y + 1 if t == "SON" else y][0]
GRUPOS = ["sin_el_nino", "el_nino_debil", "el_nino_moderado", "el_nino_fuerte_extraordinario"]
SEIS = ["Mallares", "Miraflores", "Chusis", "San Miguel", "Chulucanas", "Morropón"]
T5 = ["anual", "DEF", "MAM", "JJA", "SON"]

def sumas(serie, ym, y0, y1, t):
    idx = {(a, m): k for k, (a, m) in enumerate(ym)}
    out = {}
    for y in range(y0, y1 + 1):
        ms = [(y, m) for m in range(1, 13)] if t == "anual" else [((y - 1) if (t == "DEF" and m == 12) else y, m) for m in TEMP[t]]
        ks = [idx.get(x) for x in ms]
        if None not in ks: out[y] = float(sum(serie[k] for k in ks))
    return out

def main():
    d = np.load(NPZ); ch, chym, tr = d["rain"], [(int(a), int(m)) for a, m in d["ym"]], d["transform"]
    pds = rasterio.open(PISCO); pym = [(1981 + k // 12, k % 12 + 1) for k in range(pds.count)]
    pts, est = [], []
    for n, v in EST.items():
        lat, lon = -(v[0] + v[1] / 60), -(v[2] + v[3] / 60)
        i, j = int((tr[5] - lat) / abs(tr[4])), int((lon - tr[2]) / tr[0])
        if not (0 <= i < ch.shape[1] and 0 <= j < ch.shape[2]): continue
        pts.append((lon, lat)); est.append((n, v, ch[:, i, j].astype(float)))
    psamp = np.array([s for s in pds.sample(pts)], float)  # (n_est, 468)
    psamp[psamp < -1e30] = np.nan
    filas, mens = [], []
    for (n, v, cs), ps in zip(est, psamp):
        obs = dict(zip(T5, v[6:11]))
        for t in T5:
            row = dict(estacion=n, zona=v[5], alt_m=v[4], grupo="costa" if v[4] < 600 else "sierra", temporada=t, senamhi_1971_2000=obs[t])
            for nom, s, ym in (("pisco", ps, pym), ("chirps", cs, chym)):
                x = sumas(s, ym, 1981, 2000, t); xs = [x[y] for y in x if esc(y, t) == "sin_el_nino"]
                for g in GRUPOS: row[f"{nom}_media_{g}"] = round(np.mean([x[y] for y in x if esc(y, t) == g]), 2)
                row[f"{nom}_media_8100"] = round(np.mean(list(x.values())), 1)
                row[f"{nom}_mediana_8100"] = round(np.median(list(x.values())), 1)
                row[f"{nom}_media_sin_fen"] = round(np.mean(xs), 1)
                row[f"razon_{nom}"] = round(row[f"{nom}_media_8100"] / obs[t], 3) if obs[t] > 0 else ""
                row[f"peso_fen_{nom}_pct"] = round(100 * (row[f"{nom}_media_8100"] / row[f"{nom}_media_sin_fen"] - 1), 0) if row[f"{nom}_media_sin_fen"] > 0 else ""
            filas.append(row)
        if n in SEIS:
            for k, (a, m) in enumerate(pym):
                if (a, m) in chym:
                    mens.append(dict(estacion=n, zona=v[5], anio=a, mes=m, pisco_mm=round(float(ps[k]), 1), chirps_mm=round(float(cs[chym.index((a, m))]), 1)))
    (BASE / "clima").mkdir(exist_ok=True)
    for nombre, F in (("pisco_chirps_senamhi_estacion.csv", filas), ("pisco_vs_chirps_mensual.csv", mens)):
        with (BASE / "clima" / nombre).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(F[0])); w.writeheader(); w.writerows(F)
    L = [f"PISCOp v2.1 ({PISCO.name}) y CHIRPS 1981-2000 frente a normales SENAMHI 1971-2000. Razón = producto / estación.",
         "PISCOp no es independiente de las estaciones (las asimila). 'sin FEN' = sin ninguna campaña El Niño según ICEN oficial (Territorio).", ""]
    L.append("1) Razón mediana por grupo y temporada (n estaciones)")
    for g in ("costa", "sierra"):
        for t in T5:
            F = [r for r in filas if r["grupo"] == g and r["temporada"] == t and r["razon_pisco"] != ""]
            L.append(f"  {g:6s} {t:5s} n={len(F):2d}  PISCOp {np.median([r['razon_pisco'] for r in F]):.2f}  CHIRPS {np.median([r['razon_chirps'] for r in F]):.2f}"
                     f"  | rango PISCOp {min(r['razon_pisco'] for r in F):.2f}-{max(r['razon_pisco'] for r in F):.2f}, CHIRPS {min(r['razon_chirps'] for r in F):.2f}-{max(r['razon_chirps'] for r in F):.2f}")
    L.append("\n2) Razón por zona del CONTRATO (mediana de estaciones), anual y MAM")
    for z in sorted({r["zona"] for r in filas}):
        for t in ("anual", "MAM"):
            F = [r for r in filas if r["zona"] == z and r["temporada"] == t and r["razon_pisco"] != ""]
            L.append(f"  {z:13s} {t:5s} n={len(F):2d}  PISCOp {np.median([r['razon_pisco'] for r in F]):.2f}  CHIRPS {np.median([r['razon_chirps'] for r in F]):.2f}")
    L.append("\n3) Por estación (anual y MAM): SENAMHI | PISCOp media, mediana, sin FEN | CHIRPS media, mediana, sin FEN (mm)")
    for r in filas:
        if r["temporada"] in ("anual", "MAM") and r["grupo"] == "costa":
            L.append(f"  {r['estacion']:13s} {r['temporada']:5s} {r['senamhi_1971_2000']:7.1f} | {r['pisco_media_8100']:7.1f} {r['pisco_mediana_8100']:7.1f} {r['pisco_media_sin_fen']:7.1f}"
                     f" | {r['chirps_media_8100']:7.1f} {r['chirps_mediana_8100']:7.1f} {r['chirps_media_sin_fen']:7.1f}  peso FEN PISCOp {r['peso_fen_pisco_pct']}% CHIRPS {r['peso_fen_chirps_pct']}%")
    L.append("\n4) PISCOp frente a CHIRPS mes a mes 1981-2019 (seis estaciones de valle)")
    for n in SEIS:
        M = [r for r in mens if r["estacion"] == n]
        p, c = np.array([r["pisco_mm"] for r in M]), np.array([r["chirps_mm"] for r in M])
        mam = [r for r in M if r["mes"] in (3, 4, 5)]
        pm, cm = sum(r["pisco_mm"] for r in mam), sum(r["chirps_mm"] for r in mam)
        m17 = next((r for r in M if (r["anio"], r["mes"]) == (2017, 3)), None)
        L.append(f"  {n:11s} r mensual {np.corrcoef(p, c)[0,1]:.2f} (n={len(M)}); total MAM CHIRPS/PISCOp {cm/pm:.2f}; "
                 f"mar-2017 PISCOp {m17['pisco_mm']} CHIRPS {m17['chirps_mm']} mm")
    n30 = {g: sum(esc(y, "MAM") == g for y in range(1971, 2001)) for g in GRUPOS}
    n20 = {g: sum(esc(y, "MAM") == g for y in range(1981, 2001)) for g in GRUPOS}
    L.append("\n5) Efecto del periodo: media de cada producto por escenario ICEN (1981-2000) reponderada a la frecuencia de "
             f"escenarios de 1971-2000 (30 campañas: {n30}; en 1981-2000: {n20}). Razón mediana.")
    L.append("   El grupo fuerte/extraordinario de 1981-2000 sólo tiene 1983 y 1998 (extraordinarios); 1972 y 1973 fueron fuertes. "
             "Cota alta: pesan como 1983/1998; cota baja: pesan como los moderados (1987, 1992).")
    for g in ("costa", "sierra"):
        for t in ("anual", "MAM"):
            out = []
            for nom in ("pisco", "chirps"):
                for alt in (False, True):  # alt: 1972 y 1973 (fuertes, sin análogo fuerte en 1981-2000) pesan como moderados
                    n = dict(n30)
                    if alt: n["el_nino_fuerte_extraordinario"] -= 2; n["el_nino_moderado"] += 2
                    rz = [sum(n[k] * r[f"{nom}_media_{k}"] for k in GRUPOS) / 30 / r["senamhi_1971_2000"]
                          for r in filas if r["grupo"] == g and r["temporada"] == t]
                    out.append(np.median(rz))
            L.append(f"  {g:6s} {t:5s} PISCOp {out[1]:.2f} a {out[0]:.2f}  CHIRPS {out[3]:.2f} a {out[2]:.2f}")
    txt = "\n".join(L); (BASE / "clima" / "pisco_vs_chirps_resumen.txt").write_text(txt + "\n", encoding="utf-8"); print(txt)
main()
