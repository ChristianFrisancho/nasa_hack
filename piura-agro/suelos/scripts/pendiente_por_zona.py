"""Pendiente por zona bajo riego (pedido de Piura Datos, 24-oct-2026).

DEM: Copernicus GLO-30 (COG en AWS, 1 arcseg). Máscara: ESA WorldCover 2021 v200, clase 40 (cultivo),
remuestreada por moda a la malla del DEM. Zonas: las mismas cajas de zonas_ece_drenaje_fen.py.
Pendiente: método de Horn (3x3) en %, con el espaciado métrico según la latitud de cada fila.
Sensibilidad al ruido: la misma pendiente sobre el DEM suavizado con una media móvil de 5x5 (~150 m).
Salida: datos/pendiente_por_zona.csv en formato CONTRATO.
"""
import math, os, sys
import numpy as np, pandas as pd, rasterio
from rasterio.merge import merge
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy.ndimage import uniform_filter
sys.path.insert(0, os.path.dirname(__file__))
# Copia literal de ZONAS en zonas_ece_drenaje_fen.py (importarlo ejecutaría ese script)
ZONAS = {"Valle del Chira": (-81.0, -5.0, -80.5, -4.75), "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
         "Medio Piura": (-80.7, -5.2, -80.45, -5.0), "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
         "Alto Piura": (-80.25, -5.45, -79.85, -5.0), "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
         "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05)}
from contrato import a_contrato

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WC = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
WC_URL = WC.replace("/vsicurl/", "")
DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/ (Copernicus_DSM_COG_10_S0[56]_00_W0(80|81)_00_DEM)"


def tiles(w, s, e, n):
    out = []
    for la in range(math.floor(s), math.floor(n) + 1):
        for lo in range(math.floor(w), math.floor(e) + 1):
            nm = f"Copernicus_DSM_COG_10_S{abs(la):02d}_00_W{abs(lo):03d}_00_DEM"
            out.append(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{nm}/{nm}.tif")
    return out


def horn(z, tr):
    rows = z.shape[0]
    lat = tr.f + tr.e * (np.arange(rows) + 0.5)
    dx = (tr.a * 111320 * np.cos(np.radians(lat)))[:, None]
    dy = abs(tr.e) * 110574
    p = np.pad(z, 1, mode="edge")
    a, b, c = p[:-2, :-2], p[:-2, 1:-1], p[:-2, 2:]
    d, f = p[1:-1, :-2], p[1:-1, 2:]
    g, h, i = p[2:, :-2], p[2:, 1:-1], p[2:, 2:]
    gx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * dx)
    gy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * dy)
    return np.hypot(gx, gy) * 100


def stats(v):
    return dict(media=float(v.mean()), p50=float(np.percentile(v, 50)), p90=float(np.percentile(v, 90)),
                **{f"gt{t}": float((v > t).mean() * 100) for t in (2, 5, 15)})


filas = []
ADV = ("El ruido vertical del DEM (GLO-30: error absoluto <4 m, ruido relativo ~1-2 m; es un modelo de superficie que incluye árboles, "
       "bordos y canales) infla la pendiente en terreno plano: en valles casi planos, buena parte de los píxeles con >2 % es ruido. "
       "No sirve para nivelación de la parcela ni para pendientes <1-2 %.")
for z, (w, s, e, n) in ZONAS.items():
    srcs = [rasterio.open(u) for u in tiles(w, s, e, n)]
    dem, tr = merge(srcs, bounds=(w, s, e, n)); dem = dem[0].astype("float32")
    for x in srcs: x.close()
    with rasterio.open(WC) as wc:
        lc = wc.read(1, window=from_bounds(w, s, e, n, wc.transform), out_shape=dem.shape, resampling=Resampling.mode)
    crop = (lc == 40) & np.isfinite(dem) & (dem > -100)
    crop[[0, -1], :] = False; crop[:, [0, -1]] = False
    sl = horn(dem, tr); sl_s = horn(uniform_filter(dem, 5), tr)
    npx = int(crop.sum())
    lat_c = (s + n) / 2
    ha = npx * (abs(tr.e) * 110574) * (tr.a * 111320 * math.cos(math.radians(lat_c))) / 1e4
    print(z, npx, round(ha))
    if npx < 100:
        for var, u in [("pendiente_media_cultivo", "%"), ("pendiente_p50_cultivo", "%"), ("pendiente_p90_cultivo", "%"),
                       ("area_cultivo_pendiente_mayor_2pct", "% del área de cultivo"), ("area_cultivo_pendiente_mayor_5pct", "% del área de cultivo"),
                       ("area_cultivo_pendiente_mayor_15pct", "% del área de cultivo")]:
            filas.append(dict(variable=var, unidad=u, zona=z, estado="desconocido", notas=f"Solo {npx} píxeles de cultivo WorldCover en la caja"))
        continue
    r, r_s = stats(sl[crop]), stats(sl_s[crop])
    comun = dict(zona=z, lugar=f"caja {(w, s, e, n)} (lon_min, lat_min, lon_max, lat_max)", lat=round(lat_c, 3), lon=round((w + e) / 2, 3),
                 fecha_o_periodo="DEM: adquisición 2011-2015; WorldCover: 2021",
                 fuente="Copernicus DEM GLO-30 (ESA/Airbus) + ESA WorldCover 2021 v200",
                 url_o_doi=DEM_URL + " ; " + WC_URL, tipo_evidencia="prediccion", estado="estimado",
                 resolucion="1 arcseg (~30 m); máscara WorldCover 10 m remuestreada por moda a 30 m")
    base_met = (f"Pendiente de Horn 3x3 sobre el DEM de 30 m, solo en píxeles de cultivo WorldCover clase 40 ({npx} píxeles, ~{ha:,.0f} ha). "
                "valor = DEM de 30 m sin suavizar (lo pedido); valor_min/valor_max = rango entre esa cifra y la misma estadística "
                "sobre el DEM suavizado 5x5 (~150 m), que reduce el ruido pero también borra pendientes reales cortas")
    for k, var, u in [("media", "pendiente_media_cultivo", "%"), ("p50", "pendiente_p50_cultivo", "%"), ("p90", "pendiente_p90_cultivo", "%"),
                      ("gt2", "area_cultivo_pendiente_mayor_2pct", "% del área de cultivo"),
                      ("gt5", "area_cultivo_pendiente_mayor_5pct", "% del área de cultivo"),
                      ("gt15", "area_cultivo_pendiente_mayor_15pct", "% del área de cultivo")]:
        a, b = r[k], r_s[k]
        nota = ADV + f" Sin suavizar: {a:.1f}; suavizado 5x5: {b:.1f}."
        if z.startswith("Sierra"):
            nota += (" En la sierra, WorldCover 2021 subrepresenta las chacras pequeñas en ladera (mosaicos con pasto o arbustos) y no distingue "
                     "riego de secano: la cifra describe el cultivo detectado, no solo el regado.")
        else:
            nota += " WorldCover no distingue riego de secano; en la costa casi todo el cultivo es de riego."
        filas.append(dict(variable=var, valor=round(a, 1), valor_min=round(min(a, b), 1), valor_max=round(max(a, b), 1), unidad=u,
                          metodo=base_met, notas=nota, **comun))

out = a_contrato(pd.DataFrame(filas))
p = os.path.join(BASE, "datos", "pendiente_por_zona.csv")
out.to_csv(p, index=False)
print(p, len(out))
print(out[["zona", "subzona", "variable", "valor", "valor_min", "valor_max"]].to_string())
