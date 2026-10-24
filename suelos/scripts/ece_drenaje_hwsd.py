"""ECe y drenaje por zona desde HWSD v2.0 (FAO/IIASA 2023), ponderado por área de cultivo.

Para cada celda HWSD (30" ~ 0.9 km) dentro de la caja de la zona:
  - fracción de cultivo = píxeles WorldCover 2021 clase 40 (leído a ~50 m) / total;
  - EC_celda = suma(SHARE_i * ELEC_COND_i) / suma(SHARE_i) por capa (D1 0-20 cm, D3 40-60 cm);
  - p_mal_drenaje = suma(SHARE_i de componentes con drenaje I, P o VP) / 100.
Resumen por zona: media ponderada por ha de cultivo, Q05 y Q95 ponderados entre celdas,
% de cultivo en componentes con EC D1 >= 4 dS/m (umbral salino USDA).
HWSD trae valores de perfiles tipo por suelo (transferencia taxonómica), no mediciones locales.
Uso: .venv/bin/python scripts/ece_drenaje_hwsd.py
"""
import os
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(BASE, "datos", "hwsd2")
WC = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
ZONAS = {
    "Valle del Chira": (-81.0, -5.0, -80.5, -4.75),
    "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
    "Medio Piura": (-80.7, -5.2, -80.45, -5.0),
    "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
    "Alto Piura": (-80.25, -5.45, -79.85, -5.0),
    "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
    "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05),
}
MAL = {"I", "P", "VP"}

lay = pd.read_csv(os.path.join(H, "HWSD2_LAYERS.csv"), low_memory=False)
lay = lay[lay.LAYER.isin(["D1", "D3"])]
ec = lay.pivot_table(index=["HWSD2_SMU_ID", "SEQUENCE"], columns="LAYER", values="ELEC_COND", aggfunc="first")
esp = lay.pivot_table(index=["HWSD2_SMU_ID", "SEQUENCE"], columns="LAYER", values="ESP", aggfunc="first")
meta = lay.drop_duplicates(["HWSD2_SMU_ID", "SEQUENCE"]).set_index(["HWSD2_SMU_ID", "SEQUENCE"])[["SHARE", "WRB4", "DRAINAGE"]]
comp = meta.join(ec.add_prefix("EC_")).join(esp.add_prefix("ESP_")).reset_index()
comp = comp[comp.EC_D1 >= 0]  # valores negativos = sin dato

def smu_stats(g):
    w = g.SHARE.astype(float)
    return pd.Series(dict(
        ec_d1=np.average(g.EC_D1, weights=w), ec_d3=np.average(g.EC_D3.clip(lower=0), weights=w),
        p_mal=w[g.DRAINAGE.str.strip().isin(MAL)].sum() / w.sum(),
        p_sal=w[g.EC_D1 >= 4].sum() / w.sum(),
        esp_max=g.ESP_D1.max(), suelos="; ".join(f"{r.WRB4} {int(r.SHARE)}% {str(r.DRAINAGE).strip()} EC{r.EC_D1:g}/{r.EC_D3:g}" for r in g.itertuples())))
smu = comp.groupby("HWSD2_SMU_ID").apply(smu_stats, include_groups=False)

def wq(x, w, q):
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w) / w.sum()
    return float(np.interp(q, c, x))

filas = []
with rasterio.open(os.path.join(H, "HWSD2.bil")) as hs, rasterio.open(WC) as wc:
    for zona, b in ZONAS.items():
        win = from_bounds(*b, hs.transform).round_offsets().round_lengths()
        ids = hs.read(1, window=win)
        tr = hs.window_transform(win)
        ny, nx = ids.shape
        # array_bounds devuelve (oeste, sur, este, norte); 18x18 subpíxeles por celda HWSD = ~50 m
        w2 = from_bounds(*rasterio.transform.array_bounds(ny, nx, tr), wc.transform)
        crop = wc.read(1, window=w2, out_shape=(ny * 18, nx * 18))
        frac = (crop == 40).reshape(ny, 18, nx, 18).mean(axis=(1, 3))
        cell_ha = (1 / 120 * 111.32) ** 2 * np.cos(np.radians(abs((b[1] + b[3]) / 2))) * 100
        df = pd.DataFrame({"smu": ids.ravel(), "crop_ha": frac.ravel() * cell_ha})
        df = df.join(smu, on="smu")
        tot = df.crop_ha.sum()
        ok = df.dropna(subset=["ec_d1"])
        ok = ok[ok.crop_ha > 0]
        cov = ok.crop_ha.sum() / tot if tot else 0
        w = ok.crop_ha.values
        r = dict(zona=zona, cultivo_ha=round(tot), cultivo_con_dato_pct=round(100 * cov, 1))
        if len(ok):
            for v in ["ec_d1", "ec_d3", "p_mal", "p_sal"]:
                x = ok[v].values.astype(float)
                r[v + "_media"] = round(np.average(x, weights=w), 2)
                r[v + "_q05"] = round(wq(x, w, 0.05), 2)
                r[v + "_q95"] = round(wq(x, w, 0.95), 2)
            top = ok.groupby("smu").crop_ha.sum().sort_values(ascending=False).head(3)
            r["smu_principales"] = " | ".join(f"{s} ({100*h/tot:.0f}%): {smu.loc[s,'suelos']}" for s, h in top.items())
        filas.append(r)
out = pd.DataFrame(filas)
REPR = {"Bajo Piura": "baja: no usar como valor central; usar datos/zonas_ece_drenaje_fen.csv (FAO/UNALM 1990 ECe 4-12 dS/m, SIAR 584 Aquisalids, napa salina ANA hasta 16.83 dS/m)",
        "Medio Piura": "dudosa: napa somera compartida con el Bajo Piura; HWSD da p_mal 0"}
out["representatividad"] = out.zona.map(REPR).fillna("no contrastada con mediciones locales")
out.to_csv(os.path.join(BASE, "datos", "ece_drenaje_hwsd_por_zona.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200)
print(out.drop(columns="smu_principales").to_string(index=False))
for r in filas: print(r["zona"], "->", r.get("smu_principales"))
