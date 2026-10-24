"""Escenario central por zona y mes (previo = arroz). Prueba del motor, no es recomendacion."""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import modelo as M

filas = []
for zi, z in enumerate(M.ZONAS):
    for mes in range(1, 13):
        r = M.evaluar(M.central(1, zi).assign(mes_siembra=mes, cultivo_previo=0))
        m = np.where(r["viable"][0], r["margen"][0], -np.inf)
        o = [k for k in np.argsort(-m) if np.isfinite(m[k])][:3]
        filas.append(dict(zona=z, mes=mes, top3=", ".join(f"{M.CROPS[k]}({m[k]:.0f})" for k in o),
                          no_viables="|".join(c for k, c in enumerate(M.CROPS) if not r["viable"][0, k])))
d = pd.DataFrame(filas)
d.to_csv(M.BASE / "resultados/escenario_central_top3.csv", index=False)
print(d.to_string(index=False))
