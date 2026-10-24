"""Ronda 5 (R6-1 de Piura Datos, regla A4 con factor 1,5): validación con y sin los rendimientos rescatados.
Entradas: resultados/validacion_drap.csv (crudo) y validacion_drap_atipicos_{sin,con}_rescate.csv (scripts/validacion.py con ATIPICOS).
Salida: resultados/validacion_atipicos_comparacion.csv."""
import pathlib
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1] / "resultados"
k = ["cultivo", "variables", "esquema"]
a, s, c = (pd.read_csv(B / f).set_index(k) for f in
           ("validacion_drap.csv", "validacion_drap_atipicos_sin_rescate.csv", "validacion_drap_atipicos_con_rescate.csv"))
t = pd.DataFrame({"n_crudo": a.n, "n_sin_rescate": s.n, "n_con_rescate": c.n,
                  "skill_crudo": a.skill_pct, "skill_sin_rescate": s.skill_pct, "skill_con_rescate": c.skill_pct})
t["dif_con_menos_sin"] = (t.skill_con_rescate - t.skill_sin_rescate).round(3)
t = t.reset_index()
t.to_csv(B / "validacion_atipicos_comparacion.csv", index=False)
print(t.to_string(index=False))
