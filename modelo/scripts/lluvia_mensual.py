"""Ronda 5: lluvia mensual por zona para el motor propio (Piura Modelos), con PISCOp como referencia.

Fuentes (todas ya en el box):
- PISCOp v2.1 mensual 0.1° (SENAMHI, doi 10.6084/m9.figshare.21127423), 1981-2019, y CHIRPS v2.0 mensual (1981-2024),
  como media por zona ponderada por cultivo WorldCover 2021: Piura Territorio, suelos/datos/clima/clima_por_zona_series.csv
  (script suelos/scripts/clima_por_zona.py). PISCOp usa CHIRP como covariable: no es independiente de CHIRPS.
- NASA POWER diario en el punto de cada zona: data/power/<zona>.csv (PRECTOTCORR).
- Lluvia diaria de la ronda 4 en el punto: data/clima_zona/<zona>.csv (PREC_CHIRPS, PREC_ERA5; PRECTOTCORR = la elegida).
Relleno 2020-2025 de PISCOp (no existe PISCOp después de 2019): mapeo de cuantiles por zona y mes calendario desde NASA
POWER del punto, ajustado en 2000-2019 (el cuantil de POWER ese mes se traduce al mismo cuantil de PISCOp; por encima del
máximo de entrenamiento se escala por max PISCOp / max POWER). Elegido entre 9 variantes (CHIRPS, ERA5 y POWER; crudo,
razón anual, cuantiles) por menor error en la prueba fuera de muestra: ajuste 2000-2014, aplicado a 2015-2019 (incluye FEN
2017); error en resultados/lluvia_relleno_prueba.csv. Cada fila rellena va marcada relleno=1.
Salida: data/lluvia_mensual_zona.csv (zona, anio, mes, pisco, chirps, power, r4, relleno).
"""
import pathlib
import numpy as np
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1]
SUB = {"Valle del Chira": "chira_sullana", "Bajo Piura": "bajo_piura", "Medio Piura": "medio_piura",
       "Alto Piura": "alto_piura", "San Lorenzo": "san_lorenzo"}
ZONAS = list(SUB.values())
A0, A1 = 2000, 2025


def mensual_diario(path, col):
    d = pd.read_csv(path, parse_dates=["fecha"])
    d = d[(d.fecha.dt.year >= A0) & (d.fecha.dt.year <= A1)]
    return d.groupby([d.fecha.dt.year.rename("anio"), d.fecha.dt.month.rename("mes")])[col].sum(min_count=20)


def cuantiles(p_tr, c_tr, c_ap):
    """Mapeo de cuantiles empírico por mes calendario: c_ap (POWER) -> escala PISCOp, ajustado con (p_tr, c_tr)."""
    out = []
    for (a, m), v in c_ap.items():
        ct, pt = c_tr.xs(m, level="mes").dropna(), p_tr.xs(m, level="mes").dropna()
        if np.isnan(v):
            out.append(np.nan)
        elif v <= ct.max():
            out.append(float(np.quantile(pt, (ct <= v).mean())))
        else:
            out.append(v * pt.max() / max(ct.max(), 1e-6))
    return pd.Series(out, index=c_ap.index)


def main():
    S = pd.read_csv(B.parent / "suelos/datos/clima/clima_por_zona_series.csv")
    S = S[S.subzona.isin(SUB)].assign(zona=lambda d: d.subzona.map(SUB))
    filas, prueba = [], []
    for z in ZONAS:
        t = S[S.zona == z].pivot_table(index=["year", "month"], columns="producto", values="valor")
        t.index = t.index.set_names(["anio", "mes"])
        idx = pd.MultiIndex.from_product([range(A0, A1 + 1), range(1, 13)], names=["anio", "mes"])
        pis = t["PISCOp_lluvia"].reindex(idx)
        chz = t["CHIRPS_lluvia"].reindex(idx)
        chp = mensual_diario(B / f"data/clima_zona/{z}.csv", "PREC_CHIRPS").reindex(idx)
        r4 = mensual_diario(B / f"data/clima_zona/{z}.csv", "PRECTOTCORR").reindex(idx)
        pw = mensual_diario(B / f"data/power/{z}.csv", "PRECTOTCORR").reindex(idx)
        anios = idx.get_level_values("anio")
        tr0 = anios <= 2019
        fill = cuantiles(pis[tr0], pw[tr0], pw)
        relleno = pis.isna().values
        pis_f = np.where(relleno, fill.values, pis.values)
        chz_f = np.where(chz.isna(), chp.values, chz.values)  # CHIRPS 2025: el del punto
        mes = idx.get_level_values("mes")
        filas.append(pd.DataFrame({"zona": z, "anio": anios, "mes": mes, "pisco": pis_f.round(2), "chirps": chz_f.round(2),
                                   "power": pw.values.round(2), "r4": r4.values.round(2), "relleno": relleno.astype(int)}))
        tr, te = (anios <= 2014), (anios >= 2015) & (anios <= 2019)
        pred = cuantiles(pis[tr], pw[tr], pw[te])
        ye = pd.DataFrame({"anio": anios[te], "obs": pis[te].values, "pred": pred.values, "chirps": chz[te].values,
                           "power": pw[te].values}).groupby("anio").sum()
        for a, r in ye.iterrows():
            prueba.append(dict(zona=z, anio=a, pisco_obs_mm=round(r.obs, 1), relleno_mm=round(r.pred, 1),
                               chirps_sin_corregir_mm=round(r.chirps, 1), power_sin_corregir_mm=round(r.power, 1),
                               error_relleno_pct=round(100 * (r.pred - r.obs) / r.obs, 1),
                               error_chirps_pct=round(100 * (r.chirps - r.obs) / r.obs, 1),
                               error_power_pct=round(100 * (r.power - r.obs) / r.obs, 1)))
    out = pd.concat(filas)
    out.to_csv(B / "data/lluvia_mensual_zona.csv", index=False)
    pr = pd.DataFrame(prueba)
    pr.to_csv(B / "resultados/lluvia_relleno_prueba.csv", index=False)
    print(pr.to_string())
    an = out.groupby(["zona", "anio"])[["pisco", "chirps", "power", "r4"]].sum().groupby("zona").mean().round(0)
    print(an)


if __name__ == "__main__":
    main()
