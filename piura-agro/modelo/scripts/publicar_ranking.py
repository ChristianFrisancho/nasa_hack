"""Arma ranking_features.csv desde resultados/importancia_detalle.csv (ronda 3).

Una fila por feature x cultivo x zona x escenario climatico x metodo, con su posicion (rango) dentro de ese grupo.
'cambio_top1_pct' (ablacion) responde 'cuanto cambia la recomendacion si falta el dato': % de escenarios en que el cultivo
entra o sale del puesto 1 cuando el feature se fija en su valor central. Se agrega el resumen zona='todas' (promedio de zonas).
"""
import pathlib
import numpy as np
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1]
COLS = ["feature", "cultivo", "zona", "escenario", "metodo", "rango", "importancia", "cambio_top1_pct", "cambio_top3_pct",
        "cambio_viable_pct", "cuota_top1_base_pct", "fuente_dato", "estado", "notas"]
NOTA = {
    "ablacion": "falta el dato: feature fijo en su valor central en 5000 escenarios; cambio_top1_pct = % de escenarios en que el cultivo (o el top-1 si cultivo=todos) entra o sale del puesto 1; importancia = cambio medio absoluto del margen en % del margen medio",
    "permutacion": "feature barajado entre 5000 escenarios; mismas metricas que ablacion",
    "OAT": "un factor a la vez desde el escenario central en los 12 meses de siembra; importancia = rango del margen top-1 en PEN/ha",
    "sobol_ST": "indice Sobol total del margen del cultivo (0 si no viable); SALib N=1024, semilla 42",
}
ESC = {"normal": "campañas 2001-2024 sin 2017 ni 2023", "fen_2017": "campaña 2016-17, El Niño costero moderado (ICEN max dic-abr 1,31; IGP)", "fen_2023": "campaña 2022-23, El Niño costero fuerte (ICEN max dic-abr 2,11; IGP)"}


def main():
    d = pd.read_csv(B / "resultados/importancia_detalle.csv")
    d["notas"] = [NOTA[m] + ". Escenario: " + ESC[e] + ". " + n for m, e, n in zip(d.metodo, d.escenario, d.notas)]
    num = ["importancia", "cambio_top1_pct", "cambio_top3_pct", "cambio_viable_pct", "cuota_top1_base_pct"]
    g = d.groupby(["feature", "cultivo", "escenario", "metodo"]).agg(**{k: (k, "mean") for k in num},
            fuente_dato=("fuente_dato", "first"), estado=("estado", "first"), notas=("notas", "first")).reset_index()
    g["zona"] = "todas"
    pz = g.feature.isin(["ece_ds_m", "drenaje_malo"])  # ronda 4: fuente por zona; ver las filas de cada zona
    g.loc[pz, "fuente_dato"] = "varia por zona (params/zonas.csv); ver filas por zona"
    g.loc[pz | (g.feature == "pendiente_pct"), "estado"] = "por_zona"
    g["notas"] = "promedio de 5 zonas. " + g.notas
    out = pd.concat([g, d], ignore_index=True)
    clave = np.where(out.metodo.isin(["ablacion", "permutacion", "OAT"]), out.cambio_top1_pct.fillna(0) * 1e6 + out.importancia, out.importancia)
    out["_k"] = clave
    out["rango"] = out.groupby(["cultivo", "zona", "escenario", "metodo"])._k.rank(ascending=False, method="first").astype(int)
    for k in num:
        out[k] = out[k].round(4 if k == "importancia" else 2)
    orden_m = {"ablacion": 0, "permutacion": 1, "OAT": 2, "sobol_ST": 3}
    orden_e = {"normal": 0, "fen_2017": 1, "fen_2023": 2}
    out = out.assign(_e=out.escenario.map(orden_e), _z=(out.zona != "todas"), _m=out.metodo.map(orden_m), _c=(out.cultivo != "todos"))
    out = out.sort_values(["_e", "_z", "zona", "_m", "_c", "cultivo", "rango"])[COLS]
    out.to_csv(B / "ranking_features.csv", index=False, encoding="utf-8")
    v = out.query("escenario=='normal' and metodo=='ablacion' and cultivo=='todos'")
    print(v.pivot_table(index="feature", columns="zona", values="cambio_top1_pct").round(1).sort_values("todas", ascending=False).to_string())


if __name__ == "__main__":
    main()
