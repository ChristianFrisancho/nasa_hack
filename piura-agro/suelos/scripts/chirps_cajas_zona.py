"""CHIRPS v2.0 mensual (0.05°) recortado a una ventana que cubre las 7 cajas de zona; guarda la grilla completa
(no solo la media) para luego ponderarla por cultivo. Lee los COG por /vsicurl/.
Salida: datos/clima/raw/chirps_ventana_piura.npz (rain[t, y, x], years, months, transform)"""
import os, numpy as np, rasterio, time
from rasterio.windows import from_bounds
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR"); os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4"); os.environ.setdefault("GDAL_HTTP_TIMEOUT", "40")
B = (-81.05, -5.6, -79.25, -4.4)
URL = "/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/chirps-v2.0.{y}.{m:02d}.cog"
out = os.path.join(os.path.dirname(__file__), "..", "datos", "clima", "raw", "chirps_ventana_piura.npz")
from concurrent.futures import ThreadPoolExecutor
CACHE = os.path.join(os.path.dirname(out), "chirps_cache"); os.makedirs(CACHE, exist_ok=True)
def leer(ym_):
    y, m = ym_
    fc = os.path.join(CACHE, f"{y}{m:02d}.npz")
    if os.path.exists(fc):
        z = np.load(fc); return z["a"], tuple(z["t"])
    for k in range(5):
        try:
            with rasterio.open(URL.format(y=y, m=m)) as s:
                w = from_bounds(*B, s.transform).round_offsets().round_lengths()
                a = s.read(1, window=w).astype("float32"); a[a < 0] = np.nan
                t = s.window_transform(w); np.savez(fc, a=a, t=np.array(t)[:6]); time.sleep(1)
                return a, t
        except Exception as e:
            print(y, m, "reintento", k, e, flush=True); time.sleep(20 * (k + 1))
    print(y, m, "FALLO", flush=True); return None, None
ym = [(y, m) for y in range(1981, 2025) for m in range(1, 13)]
with ThreadPoolExecutor(int(os.environ.get('HILOS', '2'))) as ex:
    res = list(ex.map(leer, ym))
arr = [r[0] for r in res]; tr = next(r[1] for r in res if r[1] is not None)
faltan = [ym[i] for i, r in enumerate(res) if r[0] is None]; print('faltan', len(faltan), faltan[:20])
shape = next(a.shape for a in arr if a is not None)
R = np.stack([a if a is not None else np.full(shape, np.nan, "float32") for a in arr])
np.savez(out, rain=R, ym=np.array(ym), transform=np.array(tuple(tr))[:6])
print("FIN", R.shape)
