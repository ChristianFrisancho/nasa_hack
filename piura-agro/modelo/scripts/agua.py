"""ET0 Penman-Monteith FAO-56 diaria desde NASA POWER o clima por zona (CLIMA=power|zona, ronda 4) y demanda de agua por cultivo, zona, mes y año de siembra.

Salida: data/demanda_agua.csv con ETc, Peff y riego neto (mm) por campaña.
Ecuaciones: FAO-56 eq. 6 (ET0), 7, 8, 11-13, 19 (RH media), 21-39 (radiacion), Kc por etapas (cap. 6, fig. 25).
Precipitacion efectiva: metodo de lluvia confiable FAO/AGLW (CROPWAT) sobre bloques de 30 dias.
"""
import json
import pathlib
import numpy as np
import pandas as pd

BASE = pathlib.Path(__file__).resolve().parents[1]
from clima_fuente import DIR, ET0_MENSUAL, CLIMA, LLUVIA, leer  # ronda 4; ronda 5 LLUVIA

def et0_pm(df: pd.DataFrame, lat_deg: float) -> pd.Series:
    z = df.elev_m.iloc[0]
    tmax, tmin, t = df.T2M_MAX, df.T2M_MIN, df.T2M
    u2, rh, rs = df.WS2M, df.RH2M, df.ALLSKY_SFC_SW_DWN  # MJ m-2 d-1 (POWER AG)
    p = 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26
    gamma = 0.000665 * p
    es_f = lambda T: 0.6108 * np.exp(17.27 * T / (T + 237.3))
    es = (es_f(tmax) + es_f(tmin)) / 2
    ea = rh / 100 * es  # eq. 19 con RH media
    delta = 4098 * es_f(t) / (t + 237.3) ** 2
    J = df.fecha.dt.day_of_year.values
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    dec = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(dec))
    ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    rso = (0.75 + 2e-5 * z) * ra
    rns = 0.77 * rs
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * np.clip(rs / rso, 0.25, 1.0) - 0.35)
    rn = rns - rnl
    et0 = (0.408 * delta * rn + gamma * 900 / (t + 273) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))
    return et0.clip(lower=0)

def curva_kc(c) -> np.ndarray:
    L = [int(c.L_ini), int(c.L_dev), int(c.L_mid), int(c.L_late)]
    ini = np.full(L[0], c.Kc_ini)
    dev = np.linspace(c.Kc_ini, c.Kc_mid, L[1] + 1)[1:]
    mid = np.full(L[2], c.Kc_mid)
    late = np.linspace(c.Kc_mid, c.Kc_end, L[3] + 1)[1:]
    return np.concatenate([ini, dev, mid, late])

def p_efectiva(p_mm: np.ndarray) -> float:
    """Lluvia confiable FAO/AGLW por bloque de 30 dias: 0.6P-10 si P<=70, 0.8P-24 si P>70, nunca negativa."""
    tot = 0.0
    for i in range(0, len(p_mm), 30):
        b = p_mm[i:i + 30]
        P = b.sum() * 30 / len(b)
        pe = 0.6 * P - 10 if P <= 70 else 0.8 * P - 24
        tot += max(pe, 0) * len(b) / 30
    return tot

def main():
    puntos = json.loads((BASE / "scripts/puntos.json").read_text())
    cult = pd.read_csv(BASE / "params/cultivos.csv")
    filas, clima = [], []
    for zona, pt in puntos.items():
        df = leer(zona)  # ronda 5: lluvia según LLUVIA
        df = df.interpolate(limit=3)
        df["ET0"] = et0_pm(df, pt["lat"])
        clima.append(df.assign(zona=zona)[["zona", "fecha", "ET0", "PRECTOTCORR"]])
        s = df.set_index("fecha")
        for _, c in cult.iterrows():
            kc = curva_kc(c)
            n = len(kc)
            for anio in range(2000, 2025):
                for mes in range(1, 13):
                    ini = pd.Timestamp(anio, mes, 1)
                    w = s.loc[ini: ini + pd.Timedelta(days=n - 1)]
                    if len(w) < n or w.ET0.isna().any():
                        continue
                    etc = float((kc * w.ET0.values).sum())
                    pe = p_efectiva(w.PRECTOTCORR.fillna(0).values)
                    filas.append(dict(zona=zona, cultivo=c.cultivo, anio=anio, mes_siembra=mes, dias=n,
                                      et0_mm=round(float(w.ET0.sum()), 1), etc_mm=round(etc, 1),
                                      lluvia_mm=round(float(w.PRECTOTCORR.sum()), 1), peff_mm=round(pe, 1),
                                      riego_neto_mm=round(max(etc + c.agua_extra_mm - pe, 0), 1)))
    out = pd.DataFrame(filas)
    out.to_csv(BASE / "data/demanda_agua.csv", index=False)  # la activa (ultima corrida)
    out.to_csv(BASE / f"data/demanda_agua_{CLIMA}.csv", index=False)  # ronda 4: una por fuente de clima
    out.to_csv(BASE / f"data/demanda_agua_{CLIMA}_{LLUVIA}.csv", index=False)  # ronda 5: y por fuente de lluvia
    cl = pd.concat(clima)
    cl["mes"] = cl.fecha.dt.month
    cl["anio"] = cl.fecha.dt.year
    m = cl.groupby(["zona", "anio", "mes"]).agg(et0=("ET0", "sum"), lluvia=("PRECTOTCORR", "sum")).groupby(["zona", "mes"]).mean().round(1)
    m.to_csv(ET0_MENSUAL)
    print(m.groupby("zona").sum())
    r = out.groupby(["zona", "cultivo", "mes_siembra"]).riego_neto_mm.median().unstack().round(0)
    r.to_csv(BASE / "resultados/riego_neto_mediana_mm.csv")
    r.to_csv(BASE / f"resultados/riego_neto_mediana_mm_{CLIMA}.csv")
    r.to_csv(BASE / f"resultados/riego_neto_mediana_mm_{CLIMA}_{LLUVIA}.csv")
    print(r.to_string())

if __name__ == "__main__":
    main()
