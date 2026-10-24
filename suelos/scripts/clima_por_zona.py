"""Clima por zona (contrato) con productos basados en estaciones SENAMHI y comparación con NASA POWER.

Referencias:
  - Lluvia: PISCOp v2.1 mensual 0.1° (SENAMHI; 1981-2019), doi 10.6084/m9.figshare.21127423, CC-BY 4.0.
  - Temperatura: PISCOt v1.2 diaria 0.1° (Tmax, Tmin; 1981-2020), doi 10.6084/m9.figshare.22712365, CC-BY 4.0.
    Tmedia = (Tmax + Tmin) / 2.
  - CHIRPS v2.0 mensual 0.05° (1981-2024), https://data.chc.ucsb.edu/products/CHIRPS-2.0/
  - NASA POWER (PRECTOTCORR_SUM, T2M) en el centro de cada caja, 1981-2024.
Valor de zona = media de las celdas cuyo centro cae en la caja, ponderada por la fracción de cultivo de
ESA WorldCover 2021 (clase 40) en cada celda; si la caja no tiene cultivo, media simple.
Temporada de lluvias = dic-abr, asignada al año de abril. Campaña = ago-jul, asignada al año de julio.
Años normales = campañas 'neutro' de datos/clima/clasificacion_campanias_icen.csv (ICEN oficial).
Salidas: datos/clima/clima_por_zona_series.csv, datos/clima_por_zona.csv (contrato).
"""
import os, sys, math
import numpy as np, pandas as pd, xarray as xr, rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
sys.path.insert(0, os.path.dirname(__file__))
from contrato import a_contrato

H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "..", "datos"); R = os.path.join(D, "clima", "raw")
ZONAS = {"Valle del Chira": (-81.0, -5.0, -80.5, -4.75), "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
         "Medio Piura": (-80.7, -5.2, -80.45, -5.0), "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
         "Alto Piura": (-80.25, -5.45, -79.85, -5.0), "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
         "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05)}
WIN = (-81.5, -5.8, -79.1, -4.2)
WC = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
U = dict(
    pisco="https://doi.org/10.6084/m9.figshare.21127423", piscot="https://doi.org/10.6084/m9.figshare.22712365",
    chirps="https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/", power="https://power.larc.nasa.gov/api/temporal/monthly/point")

# --- fracción de cultivo WorldCover en una malla fina (0.002°) para ponderar celdas
FR = 0.002
with rasterio.open(WC) as s:
    w, so, e, n = max(WIN[0], -81.0), WIN[1], WIN[2], WIN[3]
    shp = (round((n - so) / FR), round((e - w) / FR))
    lc = s.read(1, window=from_bounds(w, so, e, n, s.transform), out_shape=shp, resampling=Resampling.nearest)
crop_fine = (lc == 40).astype("float32"); fine_lat = n - FR * (np.arange(shp[0]) + 0.5); fine_lon = w + FR * (np.arange(shp[1]) + 0.5)


FB = set()  # (producto, subzona) con respaldo de caja completa
CELLS = {}  # (producto, subzona) -> (serie por celda [t, k], peso [k], times)


def pesos(lats, lons, res):
    """Fracción de cultivo por celda (centros lat, lon). Por zona: celdas de la caja con cultivo >5 %;
    si son menos de 3 (sierra: poco cultivo en WorldCover), todas las celdas de la caja con peso uniforme."""
    W = np.zeros((len(lats), len(lons)))
    for i, la in enumerate(lats):
        ri = np.where(np.abs(fine_lat - la) <= res / 2)[0]
        if not ri.size: continue
        for j, lo in enumerate(lons):
            ci = np.where(np.abs(fine_lon - lo) <= res / 2)[0]
            if ci.size: W[i, j] = crop_fine[np.ix_(ri, ci)].mean()
    out = {}
    for z, (zw, zs, ze, zn) in ZONAS.items():
        box = ((lats[:, None] >= zs) & (lats[:, None] <= zn) & (lons[None, :] >= zw) & (lons[None, :] <= ze))
        m = box & (W > 0.05)
        out[z] = (m, np.where(m, W, 0.0), False) if m.sum() >= 3 else (box, box.astype(float), True)
    return out


def zonal(arr, lats, lons, res, name, times):
    P = pesos(lats, lons, res); rows = []
    for z in ZONAS:
        m, w, fb = P[z]
        if fb: FB.add((name, z))
        cells = arr[:, m]; wk = w[m]
        ok = ~np.isnan(cells).all(0); cells, wk = cells[:, ok], wk[ok]
        CELLS[(name, z)] = (cells, wk / wk.sum(), times)
        v = np.nansum(cells * (wk / wk.sum())[None], axis=1)
        for k, (y, mo) in enumerate(times):
            rows.append(dict(subzona=z, year=y, month=mo, producto=name, valor=float(v[k]), celda_min=float(np.nanmin(cells[k])),
                             celda_max=float(np.nanmax(cells[k])), n_celdas=int(cells.shape[1])))
    return pd.DataFrame(rows)


series = []
# PISCOp
p = xr.open_dataset(os.path.join(R, "PISCOp_monthly.nc"), decode_times=False)
p = p.sel(lat=slice(WIN[3], WIN[1]), lon=slice(WIN[0], WIN[2]))
times = [(1981 + (k - 1) // 12, (k - 1) % 12 + 1) for k in p.z.values]
series.append(zonal(p.pc.values.astype(float), p.lat.values, p.lon.values, 0.1, "PISCOp_lluvia", times))
# PISCOt -> mensual
tm = []
for v in ("tmax", "tmin"):
    t = xr.open_dataset(os.path.join(R, f"{v}_daily_1981_2020_010.nc"))[v].sel(latitude=slice(WIN[3], WIN[1]), longitude=slice(WIN[0], WIN[2]))
    tm.append(t.resample(time="MS").mean().load())
tmean = (tm[0] + tm[1]) / 2
times = [(int(str(x)[:4]), int(str(x)[5:7])) for x in tmean.time.values]
series.append(zonal(tmean.values.astype(float), tmean.latitude.values, tmean.longitude.values, 0.1, "PISCOt_tmedia", times))
# CHIRPS
c = np.load(os.path.join(R, "chirps_ventana_piura.npz")); tr = c["transform"]
lons = tr[2] + tr[0] * (np.arange(c["rain"].shape[2]) + 0.5); lats = tr[5] + tr[4] * (np.arange(c["rain"].shape[1]) + 0.5)
series.append(zonal(c["rain"].astype(float), lats, lons, 0.05, "CHIRPS_lluvia", [tuple(x) for x in c["ym"]]))
# POWER
pw = pd.read_csv(os.path.join(R, "power_centro_caja.csv"))
for col, name in [("power_rain_mm", "POWER_lluvia"), ("power_t2m_c", "POWER_tmedia")]:
    series.append(pw.rename(columns={col: "valor"})[["subzona", "year", "month", "valor"]].assign(producto=name, celda_min=np.nan, celda_max=np.nan, n_celdas=1))
    for z, g_ in pw.groupby("subzona"):
        g_ = g_.sort_values(["year", "month"]); CELLS[(name, z)] = (g_[[col]].values.astype(float), np.array([1.0]), list(zip(g_.year, g_.month)))
S = pd.concat(series, ignore_index=True)
S.to_csv(os.path.join(D, "clima", "clima_por_zona_series.csv"), index=False)

# --- agregación estacional por celda; valor = media ponderada de celdas, cmin/cmax = celda mín/máx
def temporada(meses, fun, nmes, camp):
    rows = []
    for (prod, z), (cells, wk, times) in CELLS.items():
        if prod.endswith("lluvia") != (fun == "sum"): continue
        t = pd.DataFrame(times, columns=["year", "month"])
        t["anio"] = np.where(t.month >= 8, t.year + 1, t.year) if camp else np.where(t.month == 12, t.year + 1, t.year)
        sel = t.month.isin(meses).values
        for anio, idx in t[sel].groupby("anio").groups.items():
            if len(idx) != nmes: continue
            c = cells[np.array(idx)]
            if np.isnan(c).any(): continue
            a = c.sum(0) if fun == "sum" else c.mean(0)
            rows.append(dict(subzona=z, producto=prod, anio=int(anio), valor=float((a * wk).sum()), cmin=float(a.min()), cmax=float(a.max()), n=len(a)))
    return pd.DataFrame(rows)
T = {("lluvia", "dic_abr"): temporada([12, 1, 2, 3, 4], "sum", 5, False),
     ("lluvia", "ago_jul"): temporada(list(range(1, 13)), "sum", 12, True),
     ("tmedia", "dic_abr"): temporada([12, 1, 2, 3, 4], "mean", 5, False),
     ("tmedia", "ago_jul"): temporada(list(range(1, 13)), "mean", 12, True)}
cl = pd.read_csv(os.path.join(D, "clima", "clasificacion_campanias_icen.csv"))
normales = set(cl.loc[cl.enso_costero == "neutro", "anio_lluvias"].astype(int))
NINO = {1998: "El Niño costero extraordinario 1997-98", 2017: "El Niño costero 2017 (moderado, lluvias extremas en Piura)",
        2023: "El Niño costero 2023 (ciclón Yaku y lluvias de mar-2023)"}
ICEN = "datos/clima/clasificacion_campanias_icen.csv (ICEN oficial ENFEN NT 01-2024)"
filas = []
FUENTES = dict(PISCOp_lluvia=("PISCOp v2.1 (SENAMHI), estaciones + CHIRP", U["pisco"], "0.1° (~11 km)"),
               PISCOt_tmedia=("PISCOt v1.2 (SENAMHI/Huerta et al.), estaciones homogeneizadas", U["piscot"], "0.1° (~11 km)"),
               CHIRPS_lluvia=("CHIRPS v2.0 (UCSB CHC)", U["chirps"], "0.05° (~5.5 km)"),
               POWER_lluvia=("NASA POWER (MERRA-2/IMERG corregido)", U["power"], "0.5° x 0.625°"),
               POWER_tmedia=("NASA POWER (MERRA-2)", U["power"], "0.5° x 0.625°"))
for (var, per), g in T.items():
    ref = "PISCOp_lluvia" if var == "lluvia" else "PISCOt_tmedia"
    un = "mm" if var == "lluvia" else "°C"
    gi = g.set_index(["subzona", "producto", "anio"])
    for z in ZONAS:
        # 1) valores de zona del producto de referencia (estaciones)
        for prod in [ref] + (["CHIRPS_lluvia"] if var == "lluvia" else []):
            src, url, res = FUENTES[prod]
            try: r = g[(g.subzona == z) & (g.producto == prod)].set_index("anio")
            except KeyError: continue
            rn = r[r.index.isin(normales)]
            if len(rn):
                filas.append(dict(variable=f"{var}_{per}_normal", valor=round(rn.valor.mean(), 1), valor_min=round(rn.valor.quantile(.1), 1), valor_max=round(rn.valor.quantile(.9), 1),
                    unidad=un, subzona=z, fecha_o_periodo=f"años neutros {rn.index.min()}-{rn.index.max()} (n={len(rn)})", fuente=src, url_o_doi=url, resolucion=res,
                    metodo="Media de zona ponderada por cultivo WorldCover; rango = p10-p90 entre años neutros", tipo_evidencia="regional" if prod != "CHIRPS_lluvia" else "prediccion",
                    estado="estimado", notas=f"Años normales según ICEN: {ICEN}"))
            for y, txt in NINO.items():
                if y in r.index:
                    filas.append(dict(variable=f"{var}_{per}_nino_{y}", valor=round(r.loc[y, "valor"], 1), valor_min=round(r.loc[y, "cmin"], 1), valor_max=round(r.loc[y, "cmax"], 1),
                        unidad=un, subzona=z, fecha_o_periodo=f"{per} {y}", fuente=src, url_o_doi=url, resolucion=res,
                        metodo="Media de zona ponderada por cultivo; rango = celda mín-máx con cultivo dentro de la caja (dispersión espacial, no error)",
                        tipo_evidencia="regional" if prod != "CHIRPS_lluvia" else "prediccion", estado="estimado", notas=txt))
                else:
                    fin = "2019" if prod == "PISCOp_lluvia" else "2020" if prod == "PISCOt_tmedia" else "2024"
                    filas.append(dict(variable=f"{var}_{per}_nino_{y}", unidad=un, subzona=z, fecha_o_periodo=f"{per} {y}", fuente=src, url_o_doi=url, resolucion=res,
                        estado="desconocido", tipo_evidencia="regional", notas=f"{txt}. {prod} termina en {fin}: sin dato"))
        # 2) sesgos de POWER (y CHIRPS) frente a la referencia
        for prod in (["POWER_lluvia", "CHIRPS_lluvia"] if var == "lluvia" else ["POWER_tmedia"]):
            src, url, res = FUENTES[prod]
            a = g[(g.subzona == z) & (g.producto == prod)].set_index("anio"); b = g[(g.subzona == z) & (g.producto == ref)].set_index("anio")
            j = a[["valor"]].merge(b[["valor", "cmin", "cmax"]], left_index=True, right_index=True, suffixes=("", "_ref"))
            j["d"] = j.valor - j.valor_ref
            jn = j[j.index.isin(normales)]
            base = dict(subzona=z, url_o_doi=url + " ; " + FUENTES[ref][1], fuente=f"{src} frente a {FUENTES[ref][0]}",
                        resolucion=f"{res} frente a {FUENTES[ref][2]}", tipo_evidencia="regional", estado="estimado")
            tag = prod.split("_")[0]
            if len(jn):
                filas.append(dict(variable=f"sesgo_{var}_{per}_{tag}_normal", valor=round(jn.d.mean(), 1), valor_min=round(jn.d.quantile(.1), 1), valor_max=round(jn.d.quantile(.9), 1),
                    unidad=un, fecha_o_periodo=f"años neutros (n={len(jn)})", metodo=f"{tag} - referencia de estaciones, por año; valor = media; rango = p10-p90 entre años", **base,
                    notas=f"Sesgo relativo = {100 * jn.d.mean() / jn.valor_ref.mean():+.0f} % de la media de referencia ({jn.valor_ref.mean():.1f} {un}). Positivo = {tag} sobreestima."))
            for y, txt in NINO.items():
                if y in j.index:
                    d = j.loc[y]
                    filas.append(dict(variable=f"sesgo_{var}_{per}_{tag}_nino_{y}", valor=round(d.d, 1), valor_min=round(d.valor - d.cmax, 1), valor_max=round(d.valor - d.cmin, 1),
                        unidad=un, fecha_o_periodo=f"{per} {y}", metodo=f"{tag} - referencia; rango = {tag} menos la celda máx/mín de la referencia dentro de la caja", **base,
                        notas=f"{txt}. Sesgo relativo = {100 * d.d / d.valor_ref:+.0f} % (referencia {d.valor_ref:.1f} {un}, {tag} {d.valor:.1f} {un}). Un solo evento: el rango es espacial, no un intervalo de confianza."))
                elif tag == "POWER" and var == "lluvia":
                    c_ = g[(g.subzona == z) & (g.producto == "CHIRPS_lluvia") & (g.anio == y)]; pw_ = a.loc[y, "valor"] if y in a.index else None
                    if len(c_) and pw_ is not None:
                        cv = float(c_.valor.iloc[0])
                        filas.append(dict(variable=f"sesgo_{var}_{per}_POWER_vs_CHIRPS_nino_{y}", valor=round(pw_ - cv, 1), unidad=un, fecha_o_periodo=f"{per} {y}",
                            subzona=z, fuente="NASA POWER frente a CHIRPS v2.0", url_o_doi=U["power"] + " ; " + U["chirps"], resolucion="0.5° x 0.625° frente a 0.05°",
                            metodo="POWER - CHIRPS (PISCOp no cubre 2023)", tipo_evidencia="prediccion", estado="estimado",
                            notas=f"{txt}. Sin referencia de estaciones (PISCOp termina en 2019): diferencia entre dos productos, no sesgo. POWER {pw_:.0f} mm; CHIRPS {cv:.0f} mm. Sin rango: un solo valor por producto. CHIRPS subestima en la costa en Niños fuertes (ver 1998 y 2017)."))
                else:
                    filas.append(dict(variable=f"sesgo_{var}_{per}_{tag}_nino_{y}", unidad=un, fecha_o_periodo=f"{per} {y}", estado="desconocido", **{k: v for k, v in base.items() if k != "estado"},
                                      notas=f"{txt}. Referencia de estaciones sin dato para {y}"))
out = pd.DataFrame(filas)
fbz = {z for _, z in FB}
nota_fb = "Menos de 3 celdas con cultivo WorldCover >5 % en la caja: valor = media uniforme de todas las celdas de la caja (incluye laderas sin cultivo)"
for z in fbz:
    prods = ", ".join(sorted(p_ for p_, z_ in FB if z_ == z))
    out.loc[out.subzona == z, "notas"] = out.loc[out.subzona == z, "notas"].fillna("") + f". {prods}: " + nota_fb
print("respaldo caja completa:", sorted(FB))
out["zona"] = out.subzona; out = out.drop(columns="subzona")
out["metodo"] = out.metodo.fillna("")
out = a_contrato(out)
pth = os.path.join(D, "clima_por_zona.csv"); out.to_csv(pth, index=False)
print(pth, len(out))
