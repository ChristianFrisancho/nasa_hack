#!/usr/bin/env python3
"""Tmáx y Tmín medias mensuales por zona (media de los valores diarios) con NASA POWER (API diaria, community=AG, sin cuenta).

Por qué: el motor usaba como Tmáx mensual la del día más caluroso del mes; aquí va la media de las máximas diarias.
Puntos: los de Territorio (suelos/datos/clima/chirps_mensual_zonas.csv). medio_piura no tiene punto allí: uso Piura-Castilla (-5.18, -80.62).
POWER sirve la celda nativa MERRA-2 (0,5° lat x 0,625° lon): si dos puntos caen en la misma celda se dice en notas.
valor = media 2001-2025 de las medias mensuales; valor_min/valor_max = P10/P90 entre años.
Uso: ../suelos/.venv/bin/python tools/temperatura_power.py [--offline]  (con rasterio añade el contraste PISCO; con python3 sin rasterio lo omite)
       (--offline usa sólo el caché clima/power_raw/)
Salida: temperatura_media_max_min_zona.csv
"""
import csv, json, sys, urllib.request
from collections import defaultdict
from pathlib import Path
from statistics import mean

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "clima" / "power_raw"
OUT = BASE / "temperatura_media_max_min_zona.csv"
A0, A1 = 2001, 2025
API = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN&community=AG"
       "&longitude={lon}&latitude={lat}&start={a0}0101&end={a1}1231&format=JSON")
# (zona, subzona, lat, lon, origen del punto)
PUNTOS = [
    ("alto_piura", "Chulucanas", -5.09, -80.16, "Territorio"),
    ("medio_piura", "Piura-Castilla", -5.18, -80.62, "Piura Datos (Territorio no tiene punto de medio_piura)"),
    ("bajo_piura", "Bajo Piura", -5.42, -80.74, "Territorio"),
    ("chira", "Chira Sullana", -4.90, -80.69, "Territorio"),
    ("san_lorenzo", "San Lorenzo", -4.85, -80.25, "Territorio"),
    ("sierra_piura", "Ayabaca", -4.64, -79.71, "Territorio"),
    ("sierra_piura", "Huancabamba", -5.24, -79.45, "Territorio"),
]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","setiembre","octubre","noviembre","diciembre"]
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","subzona"]

def celda(lat, lon):  # índice de la celda nativa MERRA-2 que usa POWER
    return (round(lat / 0.5), round(lon / 0.625))

def p(xs, q):  # percentil con interpolación lineal (igual que numpy por defecto)
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

PISCO = BASE.parent / "suelos" / "datos" / "clima" / "raw" / "{v}_mean_1981-2010_005.nc"  # PISCO-SENAMHI, climatología 1981-2010 (lectura)

def pisco(lat, lon):
    """Climatología mensual PISCO (tmax, tmin) en el punto, o {} si no hay rasterio o archivo."""
    try:
        import rasterio
    except ImportError:
        return {}
    out = {}
    for v in ("tmax", "tmin"):
        f = Path(str(PISCO).format(v=v))
        if not f.exists(): return {}
        with rasterio.open(f) as ds: out[v] = [float(x) for x in next(ds.sample([(lon, lat)]))]
    return out

def bajar(sub, lat, lon, offline):
    f = RAW / f"power_{sub.replace(' ', '_')}_{A0}_{A1}.json"
    if not f.exists():
        if offline: sys.exit(f"falta caché {f}")
        url = API.format(lat=lat, lon=lon, a0=A0, a1=A1)
        with urllib.request.urlopen(url, timeout=180) as r: f.write_bytes(r.read())
    return json.loads(f.read_text())

def main():
    offline = "--offline" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    datos, elev = {}, {}
    for z, sub, lat, lon, _ in PUNTOS:
        d = bajar(sub, lat, lon, offline)
        datos[sub] = d["properties"]["parameter"]; elev[sub] = d["geometry"]["coordinates"][2]
    por_celda = defaultdict(list)
    for z, sub, lat, lon, _ in PUNTOS: por_celda[celda(lat, lon)].append(f"{sub} ({z})")
    filas = []
    for z, sub, lat, lon, origen in PUNTOS:
        comp = [x for x in por_celda[celda(lat, lon)] if not x.startswith(sub + " ")]
        nota_celda = (f"Misma celda POWER/MERRA-2 que {', '.join(comp)}: mismas cifras, no son independientes. " if comp else "")
        ref = pisco(lat, lon)
        for var, par, pv in (("temperatura_max_media_mensual", "T2M_MAX", "tmax"), ("temperatura_min_media_mensual", "T2M_MIN", "tmin")):
            serie = datos[sub][par]
            ym, faltan = defaultdict(list), 0
            for fecha, v in serie.items():
                if v is None or v <= -998: faltan += 1; continue
                ym[(int(fecha[:4]), int(fecha[4:6]))].append(v)
            for m in range(1, 13):
                anual = [mean(ym[(a, m)]) for a in range(A0, A1 + 1) if ym.get((a, m))]
                contraste = ""
                if ref:
                    dif = mean(anual) - ref[pv][m - 1]
                    contraste = (f"Contraste: PISCO-SENAMHI 1981-2010 (rejilla 0,05°, interpolada de estaciones) da {ref[pv][m-1]:.1f} °C en el punto; "
                                 f"POWER - PISCO = {dif:+.1f} °C. " + ("Diferencia mayor de 3 °C: no usar esta fila sin corregir. " if abs(dif) > 3 else ""))
                filas.append(dict(
                    variable=var, valor=f"{mean(anual):.2f}", valor_min=f"{p(anual, .10):.2f}", valor_max=f"{p(anual, .90):.2f}",
                    unidad="°C", cultivo="todos", variedad="", etapa="", zona=z, lugar=f"{sub}, Piura (celda POWER)", lat=f"{lat}", lon=f"{lon}",
                    fecha_o_periodo=f"{A0}-{A1}, {MESES[m-1]}",
                    fuente=f"NASA POWER API diaria v2 (community=AG, {par}), fuente nativa MERRA-2/GEOS; consulta 2026-10-24",
                    url_o_doi=API.format(lat=lat, lon=lon, a0=A0, a1=A1), metodo="media_mensual_de_diarios",
                    tipo_evidencia="prediccion", estado="estimado",
                    notas=(f"NASA POWER, reanálisis, no estación. Modelo: reanálisis MERRA-2 (GEOS) a 2 m, celda nativa 0,5° x 0,625°; entradas: punto {lat}, {lon} "
                           f"(origen del punto: {origen}); elevación de la celda {elev[sub]:.0f} m. valor = media de {len(anual)} años de la media mensual de los diarios; "
                           f"rango = P10/P90 entre años. Días sin dato en toda la serie: {faltan}. {nota_celda}{contraste}"
                           "En la sierra la celda promedia valles y cumbres: no representa la altitud de una chacra."),
                    subzona=sub))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows(filas)
    for k, v in por_celda.items():
        if len(v) > 1: print("misma celda:", " + ".join(v))
    print(f"OK {len(filas)} filas -> {OUT.relative_to(BASE)}")

if __name__ == "__main__":
    main()
