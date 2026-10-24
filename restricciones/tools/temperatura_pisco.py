#!/usr/bin/env python3
"""Tmáx y Tmín medias mensuales por zona con PISCOt v1.2 diaria (SENAMHI, 0,1°, 1981-2020), en los mismos puntos que
temperatura_media_max_min_zona.csv (POWER), para que el motor use la temperatura interpolada de estaciones.

Entradas (lectura): suelos/datos/clima/raw/{tmax,tmin}_daily_1981_2020_010.nc (PISCOt v1.2, doi 10.6084/m9.figshare.22712365,
descargados por Territorio); restricciones/temperatura_media_max_min_zona.csv (POWER, para comparar).
Método: celda 0,1° más cercana al punto; media de los diarios de cada mes y año; valor = media de los 40 años (1981-2020);
valor_min/valor_max = P10/P90 entre años. En notas: misma cifra para 2001-2020 y diferencia con POWER 2001-2025.
Uso: ../suelos/.venv/bin/python tools/temperatura_pisco.py   Salida: temperatura_pisco_zona.csv
"""
import csv, sys
from pathlib import Path
import numpy as np, xarray as xr, rasterio
sys.path.insert(0, str(Path(__file__).resolve().parent))
from temperatura_power import PUNTOS, MESES, C
BASE = Path(__file__).resolve().parents[1]
RAW = BASE.parent / "suelos/datos/clima/raw"
OUT = BASE / "temperatura_pisco_zona.csv"
POWER = BASE / "temperatura_media_max_min_zona.csv"
DOI = "https://doi.org/10.6084/m9.figshare.22712365"
VAR = {"tmax": "temperatura_max_media_mensual", "tmin": "temperatura_min_media_mensual"}

def main():
    pw = {(r["subzona"], r["variable"], r["fecha_o_periodo"].split(", ")[1]): float(r["valor"])
          for r in csv.DictReader(POWER.open(encoding="utf-8"))}
    filas = []
    for v, var in VAR.items():
        cl = rasterio.open(RAW / f"{v}_mean_1981-2010_005.nc")  # contraste: climatología PISCO 0,05°
        ds = xr.open_dataset(RAW / f"{v}_daily_1981_2020_010.nc")[v]
        for z, sub, lat, lon, origen in PUNTOS:
            s = ds.sel(latitude=lat, longitude=lon, method="nearest")
            clat, clon = float(s.latitude), float(s.longitude)
            m = s.load().to_series().resample("MS").mean()
            nan = int(np.isnan(s.values).sum())
            for k, mes in enumerate(MESES, start=1):
                x = m[m.index.month == k]; xa = x.values; x2 = x[x.index.year >= 2001].values
                val, p10, p90, v2 = float(np.mean(xa)), float(np.percentile(xa, 10)), float(np.percentile(xa, 90)), float(np.mean(x2))
                p = pw.get((sub, var, mes)); dif = f"{p - v2:+.1f}" if p is not None else "sin dato"
                cc = float(next(cl.sample([(lon, lat)], indexes=k))[0]); ii, jj = cl.index(lon, lat)
                nb = cl.read(k, window=((ii - 1, ii + 2), (jj - 1, jj + 2)))
                aviso = ""
                if abs(val - cc) > 1.5 or (z == "sierra_piura" and not nb.min() - 0.5 <= val <= nb.max() + 0.5):
                    aviso = (f" Discrepa con PISCO 1981-2010 a 0,05° ({cc:.1f} °C en el punto, {nb.min():.1f}-{nb.max():.1f} °C en las 3x3 "
                             f"celdas vecinas; diferencia {val - cc:+.1f} °C): en la sierra los dos productos PISCO no coinciden y no hay "
                             f"estación cargada para decidir; usar con cautela.")
                juicio = "POWER no usable aquí sin corregir" if p is not None and abs(p - v2) > 3 else "POWER cercano"
                filas.append(dict(variable=var, valor=f"{val:.2f}", valor_min=f"{p10:.2f}", valor_max=f"{p90:.2f}", unidad="°C",
                    cultivo="todos", variedad="", etapa="", zona=z, lugar=f"{sub}, Piura (celda PISCOt 0,1°)", lat=f"{lat}", lon=f"{lon}",
                    fecha_o_periodo=f"1981-2020, {mes}", fuente="SENAMHI, PISCOt v1.2 diaria 0,1° (Huerta et al.), archivo descargado por Piura Territorio",
                    url_o_doi=DOI, metodo="media_mensual_de_diarios", tipo_evidencia="prediccion", estado="estimado", subzona=sub,
                    notas=(f"Producto interpolado de estaciones SENAMHI (PISCOt v1.2), no medición en chacra. Modelo: interpolación de "
                           f"estaciones con covariables (relieve, LST MODIS); entradas: celda 0,1° más cercana al punto {lat}, {lon} "
                           f"(centro {clat:.3f}, {clon:.3f}; origen del punto: {origen}). valor = media 1981-2020 de la media mensual "
                           f"de los diarios; rango = P10/P90 entre 40 años. Días sin dato: {nan}. Mismo periodo que POWER: "
                           f"media 2001-2020 = {v2:.2f} °C; POWER 2001-2025 = {p if p is not None else 'sin dato'} °C; "
                           f"POWER - PISCOt = {dif} °C ({juicio}). Recomendación: el motor usa esta fila (PISCOt), no la de POWER. "
                           f"En la sierra una celda de ~11 km mezcla altitudes." + aviso)))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows(filas)
    difs = [abs(float(r["notas"].split("POWER - PISCOt = ")[1].split(" ")[0])) for r in filas if "sin dato" not in r["notas"].split("POWER - PISCOt = ")[1][:9]]
    print(f"OK {len(filas)} filas -> {OUT.name}; |POWER-PISCOt| mediana {np.median(difs):.1f} °C, >3 °C en {sum(d > 3 for d in difs)} filas")
main()
