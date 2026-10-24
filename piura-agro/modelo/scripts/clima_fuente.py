"""Ronda 4: selector de clima diario. CLIMA=power (NASA POWER 0.5x0.625, una celda para Chira, Medio y San Lorenzo)
o CLIMA=zona (ERA5-Land T/HR 0.1, ERA5 viento/radiacion 0.25, lluvia CHIRPS o ERA5 segun zona; ver descargar_clima_zona.py)."""
import os
import pathlib

B = pathlib.Path(__file__).resolve().parents[1]
CLIMA = os.environ.get("CLIMA", "power")
assert CLIMA in ("power", "zona"), CLIMA
DIR = B / "data" / ("power" if CLIMA == "power" else "clima_zona")
ET0_MENSUAL = B / "data" / f"et0_pm_mensual_{CLIMA}.csv"

# Ronda 5: selector de lluvia mensual. LLUVIA=pisco (PISCOp v2.1 media por zona ponderada por cultivo; 2020-2025 relleno
# marcado), chirps (CHIRPS v2.0 zonal), power (NASA POWER del punto) o r4 (lluvia diaria de la ronda 4, sin cambio).
# Ver scripts/lluvia_mensual.py. La lluvia diaria se reescala para que cada mes sume el total de la fuente elegida;
# si el mes diario suma 0 y la fuente no, se reparte uniforme. T, HR, viento y radiación siguen saliendo de CLIMA.
import numpy as _np
import pandas as _pd

LLUVIA = os.environ.get("LLUVIA", "pisco")
assert LLUVIA in ("pisco", "chirps", "power", "r4"), LLUVIA
LLUVIA_MENSUAL = B / "data" / "lluvia_mensual_zona.csv"


def leer(zona: str) -> "_pd.DataFrame":
    df = _pd.read_csv(DIR / f"{zona}.csv", parse_dates=["fecha"])
    if LLUVIA == "r4":
        return df
    m = _pd.read_csv(LLUVIA_MENSUAL).query("zona == @zona").set_index(["anio", "mes"])[LLUVIA]
    a, ms = df.fecha.dt.year, df.fecha.dt.month
    p = df.PRECTOTCORR.fillna(0.0)
    tot = p.groupby([a, ms]).transform("sum")
    n = p.groupby([a, ms]).transform("size")
    obj = _pd.Series(m.reindex(_pd.MultiIndex.from_arrays([a, ms])).values, index=df.index)
    nuevo = _np.where(tot > 0, p * obj / tot.where(tot > 0, 1.0), obj / n)
    df["PRECTOTCORR"] = _np.where(obj.notna(), nuevo, _np.nan)
    return df
