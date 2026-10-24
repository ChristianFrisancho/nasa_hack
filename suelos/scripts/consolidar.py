"""Une las tablas por zona (formato CONTRATO) en suelos_piura.csv, con columna 'tabla_origen'."""
import os, pandas as pd
from contrato import a_contrato, CAMPOS
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(B, "datos")
partes = []
for f in ["zonas_ece_drenaje_fen.csv", "profundidad_ph_por_zona.csv", "pendiente_por_zona.csv", "clima_por_zona.csv", "cew_por_zona.csv", "fen_por_zona.csv"]:
    d = a_contrato(pd.read_csv(os.path.join(D, f))); d["tabla_origen"] = "datos/" + f; partes.append(d)
out = pd.concat(partes, ignore_index=True)
# ronda 8: una fila 'desconocido' de zonas_ece_drenaje_fen.csv queda sustituida si fen_por_zona.csv trae la misma variable y zona con dato
fen = out[(out.tabla_origen == "datos/fen_por_zona.csv") & (out.estado != "desconocido")]
clave = set(zip(fen.variable, fen.zona))
sust = (out.tabla_origen == "datos/zonas_ece_drenaje_fen.csv") & (out.estado == "desconocido") & pd.Series([k in clave for k in zip(out.variable, out.zona)], index=out.index)
print("filas desconocido sustituidas por fen_por_zona:", int(sust.sum()))
out = out[~sust].reset_index(drop=True)
out = out[CAMPOS + [c for c in out.columns if c not in CAMPOS]]
# reglas del contrato: desconocido -> sin valor
bad = out[(out.estado == "desconocido") & out.valor.notna() & (out.valor.astype(str) != "")]
assert bad.empty, bad[["variable", "zona", "valor"]]
assert set(out.estado.dropna()) <= {"observado", "estimado", "desconocido"}, set(out.estado)
assert set(out.tipo_evidencia.dropna()) <= {"medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion"}, set(out.tipo_evidencia)
# P4 (ronda 8): representatividad espacial de cada fila y control de completitud (resolución, fecha, rango, estado)
def repres(r):
    res = str(r.resolucion).lower()
    if r.get("nivel", "") == "punto" or any(k in res for k in ("punto", "calicata", "estacion", "estación", "parcela", "pozos")): return "punto"
    if r.zona == "piura_region" or any(k in res for k in ("0.5°", "1:5 000 000", "departamento", "criterio general")): return "regional"
    return "zona"
out["representatividad"] = out.apply(repres, axis=1)
def falta(r):
    f = []
    if str(r.resolucion).strip() in ("", "nan"): f.append("resolucion")
    if str(r.fecha_o_periodo).strip() in ("", "nan"): f.append("fecha")
    if r.estado != "desconocido" and str(r.valor_min).strip() in ("", "nan") and str(r.valor_max).strip() in ("", "nan"): f.append("rango")
    if str(r.estado).strip() in ("", "nan"): f.append("estado")
    return ";".join(f)
out["campos_faltantes"] = out.apply(falta, axis=1)
inc = out[out.campos_faltantes != ""]
inc[["tabla_origen", "variable", "zona", "lugar", "valor", "estado", "representatividad", "campos_faltantes"]].to_csv(os.path.join(B, "filas_incompletas.csv"), index=False)
print("representatividad:", out.representatividad.value_counts().to_dict(), "| filas incompletas:", len(inc), inc.campos_faltantes.value_counts().to_dict())
out.to_csv(os.path.join(B, "suelos_piura.csv"), index=False)
print(len(out), out.groupby("tabla_origen").size().to_dict(), out.zona.value_counts(dropna=False).to_dict())
