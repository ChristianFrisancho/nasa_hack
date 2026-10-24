"""Añade zona_contrato (código del CONTRATO) a tablas por zona que usan nombres largos, y zona por ubigeo
(datos/distrito_zona.csv) a tablas por distrito. Idempotente. No renombra 'zona' para no romper scripts que la leen."""
import os, pandas as pd
from contrato import ZONA_COD, VALIDAS
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
for f in ["clima/campanias_por_zona.csv", "clima/chirps_mensual_zonas.csv", "clima/escenarios_clima_por_zona.csv",
          "ece_drenaje_hwsd_por_zona.csv", "fen/fen2017_emsr199_por_zona.csv"]:
    p = os.path.join(D, f); d = pd.read_csv(p)
    d["zona_contrato"] = d["zona"].map(ZONA_COD)
    assert d.zona_contrato.notna().all() and set(d.zona_contrato) <= VALIDAS, (f, set(d.zona[d.zona_contrato.isna()]))
    d.to_csv(p, index=False); print(f, dict(d.drop_duplicates("zona").set_index("zona").zona_contrato))
dz = pd.read_csv(os.path.join(D, "distrito_zona.csv"), dtype={"ubigeo": str}).set_index("ubigeo")
p = os.path.join(D, "peligros/cenepred_riesgo_inundacion_piura.csv"); d = pd.read_csv(p, dtype={"ubigeo": str})
d["zona"] = d.ubigeo.map(dz.zona); d["zona_alternativa"] = d.ubigeo.map(dz.zona_alternativa)
assert d.zona.notna().all(); d.to_csv(p, index=False); print("cenepred", d.zona.value_counts().to_dict())
