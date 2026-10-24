#!/usr/bin/env python3
"""Tmáx y Tmín medias mensuales (media de los diarios) de PISCOt v1.2 por zona y escenario ENSO costero (ICEN)
-> temperatura_pisco_zona_enso.csv.
Puntos, celdas y serie: los mismos de temperatura_pisco.py (PUNTOS de temperatura_power.py, celda 0,1° más cercana).
Campaña ago-jul con año = julio, regla de lluvia_zona_pisco.py: mes m del año Y -> campaña Y+1 si m >= 8, si no Y.
Clasificación: icen_campanias.clasificacion() (Territorio). Escenarios: sin_el_nino (neutro o La Niña), el_nino_moderado,
el_nino_fuerte_extraordinario. Las campañas El Niño débil quedan fuera de los tres, igual que en lluvia_zona_pisco.csv.
valor = media entre años del escenario; valor_min/valor_max = P10/P90 entre esos años (np.percentile, interpolación lineal).
PISCOt llega a 2020-12, PISCOp a 2019-12: aquí entran además ene-jul 2020 (campaña 2019-20) y ago-dic 2020 (2020-21), ambas sin El Niño.
Uso: ../suelos/.venv/bin/python tools/temperatura_pisco_enso.py"""
import csv, sys
from pathlib import Path
import numpy as np, xarray as xr
sys.path.insert(0, str(Path(__file__).resolve().parent))
from temperatura_power import PUNTOS, MESES, C
from icen_campanias import clasificacion, FUENTE as FUENTE_ICEN
BASE = Path(__file__).resolve().parents[1]
RAW = BASE.parent / "suelos/datos/clima/raw"
OUT = BASE / "temperatura_pisco_zona_enso.csv"
DOI = "https://doi.org/10.6084/m9.figshare.22712365"
VAR = {"tmax": "temperatura_max_media_mensual", "tmin": "temperatura_min_media_mensual"}
ESCS = ["sin_el_nino", "el_nino_moderado", "el_nino_fuerte_extraordinario"]
CLS = clasificacion()
POCOS = 5

def campania(y, m): return y + 1 if m >= 8 else y
def etiqueta(c): return f"{c - 1}-{str(c)[2:]}"

def series():
    """{(v, sub): {(y, m): media mensual}}"""
    out = {}
    for v in VAR:
        ds = xr.open_dataset(RAW / f"{v}_daily_1981_2020_010.nc")[v]
        for z, sub, lat, lon, _ in PUNTOS:
            m = ds.sel(latitude=lat, longitude=lon, method="nearest").load().to_series().resample("MS").mean()
            out[(v, sub)] = {(t.year, t.month): float(x) for t, x in m.items()}
    return out

def main():
    S = series()
    filas = []
    for v, var in VAR.items():
        for z, sub, lat, lon, origen in PUNTOS:
            s = S[(v, sub)]
            for k, mes in enumerate(MESES, start=1):
                por_y = {y: x for (y, m), x in s.items() if m == k}
                total = float(np.mean(list(por_y.values())))
                debil = sorted(etiqueta(campania(y, k)) for y in por_y if CLS[campania(y, k)][0] == "el_nino_debil")
                for esc in ESCS:
                    ys = sorted(y for y in por_y if CLS[campania(y, k)][0] == esc)
                    a = np.array([por_y[y] for y in ys])
                    camps = [etiqueta(campania(y, k)) for y in ys]
                    aviso = (f" Solo {len(ys)} campañas: P10/P90 interpolados entre {len(ys)} valores, poco fiables; léase como "
                             f"rango mínimo-máximo aproximado." if len(ys) < POCOS else "")
                    extra = (" 2017 cuenta como El Niño moderado por ICEN (máx. 1,31), aunque en Piura llovió como en un evento fuerte."
                             if esc == "el_nino_moderado" else "")
                    filas.append(dict(variable=var, valor=f"{a.mean():.2f}", valor_min=f"{np.percentile(a, 10):.2f}",
                        valor_max=f"{np.percentile(a, 90):.2f}", unidad="°C", cultivo="todos", variedad="", etapa="", zona=z,
                        lugar=f"{sub}, Piura (celda PISCOt 0,1°)", lat=f"{lat}", lon=f"{lon}",
                        fecha_o_periodo=f"1981-2020, {mes}, {esc}",
                        fuente="SENAMHI, PISCOt v1.2 diaria 0,1° (Huerta et al.), archivo descargado por Piura Territorio; " + FUENTE_ICEN,
                        url_o_doi=DOI, metodo="media_mensual_de_diarios_por_escenario_icen", tipo_evidencia="prediccion",
                        estado="estimado", subzona=sub, escenario=esc, mes=mes,
                        notas=(f"Modelo: PISCOt v1.2 (interpolación de estaciones SENAMHI con relieve y LST MODIS); entradas: celda 0,1° "
                               f"más cercana al punto {lat}, {lon} (origen del punto: {origen}), mismo punto que temperatura_pisco_zona.csv. "
                               f"No es medición en chacra. valor = media entre años de la media mensual de los diarios; rango = P10/P90 "
                               f"entre años. Escenario {esc} por ICEN oficial de la campaña ago-jul: n={len(ys)} campañas {camps}.{aviso}"
                               f"{extra} Excluidas por El Niño débil: {debil}, por eso la media ponderada de los tres escenarios difiere hasta 0,1 °C de la media sin separar. "
                               f"Los escenarios no controlan la tendencia: la Tmáx de PISCOt en la costa sube en 1981-2020 y 2016 es el único año fuerte reciente, así que parte de la diferencia entre escenarios es tendencia. Media sin separar 1981-2020 = {total:.2f} °C.")))
    cols = C + ["escenario", "mes"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(filas)
    print(f"OK {len(filas)} filas -> {OUT.name}")
    # resumen: Tmáx feb-abr costa, fuerte - sin
    idx = {(r["subzona"], r["variable"], r["mes"], r["escenario"]): float(r["valor"]) for r in filas}
    for z, sub, *_ in PUNTOS:
        if z == "sierra_piura": continue
        d = [idx[(sub, VAR["tmax"], m, "el_nino_fuerte_extraordinario")] - idx[(sub, VAR["tmax"], m, "sin_el_nino")] for m in ("febrero", "marzo", "abril")]
        dm = [idx[(sub, VAR["tmax"], m, "el_nino_moderado")] - idx[(sub, VAR["tmax"], m, "sin_el_nino")] for m in ("febrero", "marzo", "abril")]
        print(f"{z:12s} Tmáx feb/mar/abr fuerte-sin {d[0]:+.2f} {d[1]:+.2f} {d[2]:+.2f} | moderado-sin {dm[0]:+.2f} {dm[1]:+.2f} {dm[2]:+.2f}")

if __name__ == "__main__":
    main()
