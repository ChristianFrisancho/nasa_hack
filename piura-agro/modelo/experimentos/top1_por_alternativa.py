"""Ronda 5: cuota de top-1 por cultivo y zona (escenario normal) con la base y con las alternativas de ECe y lluvia de
estabilidad.py. Sirve para ver de dónde venía el ascenso del camote en la ronda 4. N=5000, semilla 42 por zona.
Uso: CLIMA=zona LLUVIA=pisco python experimentos/top1_por_alternativa.py"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import modelo as M
import estabilidad as E
from importancia import importancia_zona

alts, reset = E.alternativas()
filas = []
for nombre in ["base", "ece_hwsd_contexto_r4", "ece_campo_x1_x3", "lluvia_r4", "clima_power"]:
    alts[nombre]()
    for zi, zona in enumerate(M.ZONAS):
        _, t1, _ = importancia_zona(zi, "normal", np.random.default_rng(42), n=5000, feats=["taw_mm_m"])
        for k, cult in [(-1, "ninguno")] + list(enumerate(M.CROPS)):
            filas.append(dict(alternativa=nombre, zona=zona, cultivo=cult, top1_pct=round(float(np.mean(t1 == k)) * 100, 1)))
reset()
d = pd.DataFrame(filas)
d.to_csv(M.BASE / "experimentos/top1_por_alternativa.csv", index=False)
p = d.pivot_table(index=["zona", "cultivo"], columns="alternativa", values="top1_pct")
print(p[p.max(axis=1) >= 10].to_string())
