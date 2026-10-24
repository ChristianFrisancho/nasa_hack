#!/usr/bin/env python3
"""CHIRPS (ventana de Territorio) frente a la climatología de estaciones SENAMHI en Piura.

Estaciones: SENAMHI (2016) "Caracterización y escenarios climáticos de la región Piura", PNUD/GORE Piura,
https://siar.regionpiura.gob.pe/documentos/normativa/2584.pdf . Tabla N°3 (lluvia acumulada anual y estacional,
mm, periodo 1971-2000) y Cuadro N°1 (coordenadas). En el Cuadro N°1 el campo de segundos repite los minutos
(error de maquetación), así que sólo uso grados y minutos: error de posición ≤ 1' (≈1,8 km), menor que un píxel
CHIRPS de 0,05° (≈5,5 km).

CHIRPS: suelos/datos/clima/raw/chirps_ventana_piura.npz (Territorio; mm/mes, 1981-01..2024-12, rejilla 0,05°).
No se re-descarga nada. Comparo la climatología CHIRPS 1981-2000 (único tramo común) y, como sensibilidad, 1981-2010,
contra la normal 1971-2000 de cada estación. Los periodos no coinciden del todo: la normal de estación incluye
1971-1980 (con El Niño 1972-73) y CHIRPS no. Es una comparación de climatologías, no de series mes a mes; las
series mensuales de estación no se pudieron bajar (senamhi.gob.pe corta la conexión TLS desde la caja y la página
de descarga necesita JavaScript).

Salida: restricciones/clima/chirps_vs_senamhi.csv y un resumen por pantalla (sesgo, razón, correlación espacial).
"""
import csv, math
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parents[1]
NPZ = BASE.parent / "suelos/datos/clima/raw/chirps_ventana_piura.npz"
OUT = BASE / "clima/chirps_vs_senamhi.csv"
FUENTE = "SENAMHI (2016) Caracterización y escenarios climáticos de la región Piura, Tabla N°3 y Cuadro N°1"
URL = "https://siar.regionpiura.gob.pe/documentos/normativa/2584.pdf"

# nombre: (lat_g, lat_m, lon_g, lon_m, alt, zona_contrato, anual, DEF, MAM, JJA, SON)
EST = {
    "Miraflores":   (5, 10, 80, 35,   40, "medio_piura",   177.95,  74.61, 104.30,  5.33,  2.13),
    "Mallares":     (4, 51, 80, 44,   29, "chira",         197.03,  85.26, 116.09,  0.68,  2.12),
    "La Esperanza": (4, 55, 81,  4,    6, "chira",          98.33,  34.11,  56.82,  7.04,  0.86),
    "Chusis":       (5, 31, 80, 50,    6, "bajo_piura",     66.85,  31.27,  34.70,  1.64,  2.17),
    "Morropón":     (5, 11, 79, 59,  109, "alto_piura",    397.16, 148.83, 237.72,  3.49,  4.16),
    "Sausal de Culucan": (4, 45, 79, 46, 1015, "sierra_piura", 320.77, 135.27, 151.32, 9.00, 37.52),
    "San Miguel":   (5, 18, 80, 40,   20, "bajo_piura",    124.33,  53.73,  68.10,  0.39,  1.85),
    "Chulucanas":   (5,  6, 80, 10,   87, "alto_piura",    425.13, 164.58, 238.83,  9.15,  4.25),
    "San Pedro":    (5,  5, 80,  2,  309, "alto_piura",    609.97, 263.24, 354.44,  8.33,  8.36),
    "Bernal":       (5, 29, 80, 45,    7, "bajo_piura",     58.51,  32.72,  27.37,  0.49,  1.39),
    "Pananga":      (4, 33, 80, 53,  500, "chira",         265.94, 111.17, 149.23,  3.72,  1.80),
    "Lancones":     (4, 34, 80, 29,  123, "chira",         360.45, 137.39, 216.89,  7.97,  2.08),
    "Sapillica":    (4, 47, 79, 59, 1406, "sierra_piura",  663.80, 275.54, 366.07, 13.88, 18.04),
    "Santo Domingo": (5, 2, 79, 53, 1475, "sierra_piura", 1238.87, 505.84, 656.85, 19.21, 56.16),
    "Hacienda Bigote": (5, 20, 79, 47, 827, "sierra_piura", 461.84, 207.79, 262.76, 0.59, 5.19),
    "Chalaco":      (5,  2, 79, 49, 1791, "sierra_piura",  968.06, 427.46, 460.39, 18.32, 66.13),
    "Pacaypampa":   (4, 59, 79, 40, 2315, "sierra_piura",  952.09, 358.64, 441.04, 30.41, 127.90),
    "Ayabaca":      (4, 38, 79, 43, 2830, "sierra_piura", 1273.51, 512.09, 609.77, 41.94, 124.54),
    "Huancabamba":  (5, 15, 79, 33, 3177, "sierra_piura",  513.60, 182.19, 182.85, 39.64, 109.96),
    "Huarmaca":     (5, 33, 79, 31, 2244, "sierra_piura", 1006.45, 431.78, 480.96, 25.81, 89.97),
}
PEDIDAS = ["Miraflores", "Chulucanas", "Mallares", "San Miguel"]  # Malláritos no figura en la Tabla N°3
TEMP = {"DEF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}

def clim(serie, ym, y0, y1):
    """Climatología: anual = media de sumas ene-dic; DEF usa diciembre del año anterior."""
    idx = {(int(a), int(m)): k for k, (a, m) in enumerate(ym)}
    anual = np.mean([sum(serie[idx[(y, m)]] for m in range(1, 13)) for y in range(y0, y1 + 1)])
    out = {"anual": anual}
    for t, ms in TEMP.items():
        vals = []
        for y in range(y0, y1 + 1):
            ks = [idx.get((y - 1 if (t == "DEF" and m == 12) else y, m)) for m in ms]
            if None in ks: continue
            vals.append(sum(serie[k] for k in ks))
        out[t] = float(np.mean(vals))
    return out

def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.corrcoef(a, b)[0, 1])

def main():
    d = np.load(NPZ); rain, ym, tr = d["rain"], d["ym"], d["transform"]
    nlat, nlon = rain.shape[1:]
    filas = []
    for nombre, v in EST.items():
        lat = -(v[0] + v[1] / 60); lon = -(v[2] + v[3] / 60)
        i = int((tr[5] - lat) / abs(tr[4])); j = int((lon - tr[2]) / tr[0])
        if not (0 <= i < nlat and 0 <= j < nlon): continue
        serie = rain[:, i, j]
        obs = dict(zip(["anual", "DEF", "MAM", "JJA", "SON"], v[6:11]))
        for per in ((1981, 2000), (1981, 2010)):
            c = clim(serie, ym, *per)
            for t in ["anual", "DEF", "MAM", "JJA", "SON"]:
                o, p = obs[t], c[t]
                filas.append({"estacion": nombre, "zona": v[5], "lat": round(lat, 3), "lon": round(lon, 3), "alt_m": v[4],
                              "periodo_chirps": f"{per[0]}-{per[1]}", "periodo_estacion": "1971-2000", "temporada": t,
                              "senamhi_mm": o, "chirps_mm": round(p, 2), "sesgo_mm": round(p - o, 2),
                              "sesgo_pct": round(100 * (p - o) / o, 1) if o > 0 else "",
                              "razon_chirps_senamhi": round(p / o, 3) if o > 0 else "",
                              "pedida": "si" if nombre in PEDIDAS else "no"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    print(f"Fuente estaciones: {FUENTE} ({URL})\nCHIRPS: {NPZ.relative_to(BASE.parent)}\n")
    for per in ("1981-2000", "1981-2010"):
        F = [r for r in filas if r["periodo_chirps"] == per]
        an = [r for r in F if r["temporada"] == "anual"]
        print(f"== CHIRPS {per} vs SENAMHI 1971-2000: {len(an)} estaciones dentro de la ventana")
        print(f"  correlación espacial (anual, n={len(an)}): r = {pearson([r['senamhi_mm'] for r in an], [r['chirps_mm'] for r in an]):.3f}")
        hu = [r for r in F if r["temporada"] != "anual"]
        print(f"  correlación estaciones×temporadas (n={len(hu)}): r = {pearson([r['senamhi_mm'] for r in hu], [r['chirps_mm'] for r in hu]):.3f}")
        sesg = [r["sesgo_pct"] for r in an]
        print(f"  sesgo anual: mediana {np.median(sesg):+.1f} %, rango {min(sesg):+.1f} a {max(sesg):+.1f} %; "
              f"sesgo medio {np.mean([r['sesgo_mm'] for r in an]):+.1f} mm/año")
        costa = [r for r in an if r["alt_m"] < 600]; sierra = [r for r in an if r["alt_m"] >= 600]
        for nom, g in (("costa (<600 m)", costa), ("sierra (≥600 m)", sierra)):
            if g: print(f"  {nom}: n={len(g)}, sesgo mediano {np.median([r['sesgo_pct'] for r in g]):+.1f} %, "
                        f"r={pearson([r['senamhi_mm'] for r in g], [r['chirps_mm'] for r in g]):.3f}")
        for nombre in PEDIDAS:
            g = {r["temporada"]: r for r in F if r["estacion"] == nombre}
            print(f"  {nombre:11s} anual SENAMHI {g['anual']['senamhi_mm']:7.1f} | CHIRPS {g['anual']['chirps_mm']:7.1f} | "
                  f"sesgo {g['anual']['sesgo_pct']:+6.1f} % | MAM {g['MAM']['senamhi_mm']:.1f} vs {g['MAM']['chirps_mm']:.1f} | "
                  f"DEF {g['DEF']['senamhi_mm']:.1f} vs {g['DEF']['chirps_mm']:.1f}")
        print()

if __name__ == "__main__":
    main()
