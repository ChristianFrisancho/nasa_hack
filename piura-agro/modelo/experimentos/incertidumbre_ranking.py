"""Ronda 5 (08:20): incertidumbre del ranking de features de mi modelo.

Para cada feature y zona (cultivo=todos, escenario normal, ablación) junta:
- cambio_top1_pct con semilla 42 (ranking_features.csv);
- IC 95 % binomial de Wilson con N=5000 sorteos (error de muestreo de una corrida);
- rango entre las 20 semillas 100-119 de estabilidad.py (resultados/estabilidad_corridas.csv, alternativa base).
"todas" = promedio de las 5 zonas; su rango de semillas promedia las zonas dentro de cada semilla.
Salida: resultados/ranking_features_ic.csv
"""
import math, pathlib
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1]
N = 5000


def wilson(p, n=N, z=1.96):
    p = p / 100
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(100 * (c - h), 2), round(100 * (c + h), 2)


rf = pd.read_csv(B / "ranking_features.csv")
rf = rf[(rf.cultivo == "todos") & (rf.escenario == "normal") & (rf.metodo == "ablacion")]
es = pd.read_csv(B / "resultados/estabilidad_corridas.csv")
es = es[(es.alternativa == "base") & (es.cultivo == "todos")]
tod = es.groupby(["semilla", "feature"]).cambio_top1_pct.mean().reset_index().assign(zona="todas")
es = pd.concat([es[["semilla", "feature", "zona", "cambio_top1_pct"]], tod])
rg = es.groupby(["feature", "zona"]).cambio_top1_pct.agg(["min", "max", "count"]).reset_index()
filas = []
for r in rf.itertuples():
    lo, hi = wilson(r.cambio_top1_pct)
    m = rg[(rg.feature == r.feature) & (rg.zona == r.zona)]
    filas.append(dict(feature=r.feature, zona=r.zona, cambio_top1_pct_s42=r.cambio_top1_pct, ic95_binomial_lo=lo,
                      ic95_binomial_hi=hi,
                      rango_semillas_min=float(m["min"].iloc[0]) if len(m) else None,
                      rango_semillas_max=float(m["max"].iloc[0]) if len(m) else None,
                      n_semillas=int(m["count"].iloc[0]) if len(m) else 0))
out = pd.DataFrame(filas)
out.to_csv(B / "resultados/ranking_features_ic.csv", index=False)
print(out[out.zona == "todas"].sort_values("cambio_top1_pct_s42", ascending=False).to_string(index=False))
