"""Extrae lluvia mensual CHIRPS v2.0 (0.05°) en los puntos de zona del repo y en Chulucanas.
Lee los COG mensuales por /vsicurl/ sin descargar el archivo completo.
Fuente: https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/
Salida: datos/clima/chirps_mensual_zonas.csv (zona, lat, lon, year, month, rain_mm)
"""
import os, sys, csv, time
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "60")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")
import rasterio

# Coordenadas de las celdas NASA POWER usadas en el repo (piura-data/power_*_1981_2025.json)
ZONAS = {
    "Bajo Piura": (-5.42, -80.74),
    "Chira Sullana": (-4.90, -80.69),
    "San Lorenzo": (-4.85, -80.25),
    "Ayabaca": (-4.64, -79.71),
    "Huancabamba": (-5.24, -79.45),
    "Chulucanas": (-5.09, -80.16),
}
BASE = "/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/chirps-v2.0.{y}.{m:02d}.cog"
out = os.path.join(os.path.dirname(__file__), "..", "datos", "clima", "chirps_mensual_zonas.csv")
y0, y1 = int(sys.argv[1]) if len(sys.argv) > 1 else 1981, int(sys.argv[2]) if len(sys.argv) > 2 else 2025
done = set()
if os.path.exists(out):
    with open(out) as f:
        for r in csv.DictReader(f):
            done.add((int(r["year"]), int(r["month"])))
new = not os.path.exists(out)
with open(out, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["zona", "lat", "lon", "year", "month", "rain_mm"])
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            if (y, m) in done:
                continue
            for intento in range(3):
                try:
                    with rasterio.open(BASE.format(y=y, m=m)) as ds:
                        vals = [v[0] for v in ds.sample([(lon, lat) for lat, lon in ZONAS.values()])]
                        nod = ds.nodata
                    break
                except Exception as e:
                    print("reintento", y, m, e, file=sys.stderr); time.sleep(30 * (intento + 1))
            else:
                print("FALLO", y, m, file=sys.stderr); continue
            for (z, (lat, lon)), v in zip(ZONAS.items(), vals):
                w.writerow([z, lat, lon, y, m, "" if (nod is not None and v == nod) or v < 0 else round(float(v), 2)])
            f.flush(); time.sleep(1.5)
        print("año", y, "ok", flush=True)
