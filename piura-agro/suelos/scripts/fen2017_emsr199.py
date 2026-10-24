"""Área inundada observada en el FEN costero 2017 por zona agrícola de Piura.

Fuente: Copernicus EMS, activación EMSR199 (Floods in Peru, 22-mar-2017),
capas crisis_information_poly (Flooded Area) de los AOI 08 SULLANA, 10 PIURA,
11 PARACHIQUE y 12 PIURANORTH. Se une la extensión de todas las fechas
(23, 26 y 30 de marzo de 2017) = extensión máxima observada, no la de un día.
Cultivo: ESA WorldCover 2021 v200 clase 40 (cropland), leído a ~30 m.
Uso: .venv/bin/python scripts/fen2017_emsr199.py
"""
import glob, os
import geopandas as gpd, numpy as np, pandas as pd
import rasterio
from rasterio import features
from rasterio.windows import from_bounds
from shapely.geometry import box
from shapely.ops import unary_union

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(BASE, "datos", "fen", "emsr199")
WC = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
ZONAS = {  # lon_min, lat_min, lon_max, lat_max (cajas aproximadas)
    "Valle del Chira": (-81.0, -5.0, -80.5, -4.75),
    "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
    "Medio Piura": (-80.7, -5.2, -80.45, -5.0),
    "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
    "Alto Piura": (-80.25, -5.45, -79.85, -5.0),
    "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
    "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05),
}
UTM = "EPSG:32717"

def leer(patron):
    gs = [gpd.read_file(f).to_crs(UTM) for f in sorted(glob.glob(os.path.join(DIR, "**", patron), recursive=True))]
    return unary_union([g.geometry.make_valid().union_all() for g in gs])

flood = leer("*crisis_information_poly.shp")
aoi = leer("*area_of_interest.shp")
zon = gpd.GeoDataFrame({"zona": list(ZONAS)}, geometry=[box(*b) for b in ZONAS.values()], crs="EPSG:4326").to_crs(UTM)

filas = []
with rasterio.open(WC) as src:
    for _, z in zon.iterrows():
        zg = z.geometry
        cob = zg.intersection(aoi).area / zg.area
        fz = zg.intersection(flood)
        a_ha = fz.area / 1e4
        crop_ha = crop_flood_ha = np.nan
        # cultivo dentro de la zona (para % inundado del cultivo)
        zll = gpd.GeoSeries([zg], crs=UTM).to_crs(4326).iloc[0]
        w = from_bounds(*zll.bounds, src.transform)
        shp = (max(1, int(w.height / 3)), max(1, int(w.width / 3)))  # ~30 m
        arr = src.read(1, window=w, out_shape=shp)
        tr = src.window_transform(w) * rasterio.Affine.scale(w.width / shp[1], w.height / shp[0])
        px_ha = abs(tr.a * tr.e) * (111320 ** 2) * np.cos(np.radians(abs(zll.centroid.y))) / 1e4
        crop = arr == 40
        crop_ha = crop.sum() * px_ha
        if not fz.is_empty:
            fll = gpd.GeoSeries([fz], crs=UTM).to_crs(4326).iloc[0]
            m = features.rasterize([(fll, 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
            crop_flood_ha = (crop & m).sum() * px_ha
        else:
            crop_flood_ha = 0.0
        filas.append(dict(zona=z.zona, cobertura_aoi_pct=round(100 * cob, 1),
                          inundado_ha=round(a_ha), cultivo_wc2021_ha=round(crop_ha),
                          cultivo_inundado_ha=round(crop_flood_ha),
                          cultivo_inundado_pct=round(100 * crop_flood_ha / crop_ha, 1) if crop_ha else np.nan))
df = pd.DataFrame(filas)
out = os.path.join(BASE, "datos", "fen", "fen2017_emsr199_por_zona.csv")
df.to_csv(out, index=False)
print(df.to_string(index=False))
print("total inundado en AOI (ha):", round(flood.area / 1e4), "| área AOI (ha):", round(aoi.area / 1e4))
