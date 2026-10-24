"""Vuelve a pedir, en serie y con pausa, los meses que chirps_cajas_zona.py dejó vacíos (403 del servidor CHC)."""
import os, time, numpy as np, rasterio
from rasterio.windows import from_bounds
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR"); os.environ.setdefault("GDAL_HTTP_TIMEOUT", "40")
B = (-81.05, -5.6, -79.25, -4.4)
URL = "/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/chirps-v2.0.{y}.{m:02d}.cog"
p = os.path.join(os.path.dirname(__file__), "..", "datos", "clima", "raw", "chirps_ventana_piura.npz")
z = dict(np.load(p)); R, ym = z["rain"], z["ym"]
falt = [i for i in range(len(ym)) if np.isnan(R[i]).all()]
print("faltan", len(falt), flush=True)
for i in falt:
    y, m = map(int, ym[i])
    for k in range(6):
        try:
            with rasterio.open(URL.format(y=y, m=m)) as s:
                w = from_bounds(*B, s.transform).round_offsets().round_lengths()
                a = s.read(1, window=w).astype("float32"); a[a < 0] = np.nan; R[i] = a; break
        except Exception as e:
            print(y, m, "reintento", k, e, flush=True); time.sleep(15 * (k + 1))
    else:
        print(y, m, "FALLO", flush=True)
    time.sleep(2)
z["rain"] = R; np.savez(p, **z)
print("FIN faltan", sum(np.isnan(R[i]).all() for i in range(len(ym))))
