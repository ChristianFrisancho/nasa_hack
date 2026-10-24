"""Ronda 5: compara las fuentes de lluvia (LLUVIA = pisco | chirps | power | r4; CLIMA=zona) en tres cosas:
1) si las 5 zonas dejan de compartir clima (correlación de lluvia mensual entre zonas, 2000-2025),
2) riego neto mediano por zona (promedio sobre cultivos y meses de siembra),
3) habilidad LOYO del clima (validacion_drap_zona_{LLUVIA}.csv; etiquetas ICEN corregidas de Territorio).
Entradas: data/lluvia_mensual_zona.csv, resultados/riego_neto_mediana_mm_zona_*.csv, resultados/validacion_drap_zona_*.csv.
Salidas: resultados/lluvia_correlacion_zonas.csv, resultados/lluvia_riego_neto.csv, resultados/lluvia_loyo.csv"""
import itertools, pathlib
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1]
FUENTES = ["pisco", "chirps", "power", "r4"]
L = pd.read_csv(B / "data/lluvia_mensual_zona.csv")
filas = []
for f in FUENTES:
    w = L.pivot_table(index=["anio", "mes"], columns="zona", values=f)
    c = w.corr()
    pares = [c.loc[a, b] for a, b in itertools.combinations(w.columns, 2)]
    ident = sum((w[a] - w[b]).abs().max() < 1e-6 for a, b in itertools.combinations(w.columns, 2))
    filas.append(dict(fuente=f, r_media_pares=round(sum(pares) / len(pares), 3), r_min=round(min(pares), 3),
                      r_max=round(max(pares), 3), pares_identicos=int(ident), n_pares=len(pares)))
pd.DataFrame(filas).to_csv(B / "resultados/lluvia_correlacion_zonas.csv", index=False)
print(pd.DataFrame(filas).to_string(index=False))

r = []
for f in FUENTES:
    d = pd.read_csv(B / f"resultados/riego_neto_mediana_mm_zona_{f}.csv")
    d["riego_neto_mm"] = d[[str(m) for m in range(1, 13)]].mean(axis=1)
    r.append(d.groupby("zona")["riego_neto_mm"].mean().round(0).rename(f))
R = pd.concat(r, axis=1)
R.to_csv(B / "resultados/lluvia_riego_neto.csv")
print(R.to_string())

v = []
for f in FUENTES:
    d = pd.read_csv(B / f"resultados/validacion_drap_zona_{f}.csv")
    d = d[d.esquema == "LOYO"]
    v.append(d.set_index(["cultivo", "variables"])["skill_pct"].round(1).rename(f))
V = pd.concat(v, axis=1).reset_index()
V.to_csv(B / "resultados/lluvia_loyo.csv", index=False)
print(V.to_string(index=False))
print(V.groupby("variables")[FUENTES].median().round(1).to_string())
