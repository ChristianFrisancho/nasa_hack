"""Ronda 4: clima diario por zona con mas resolucion que NASA POWER.

- Lluvia: CHIRPS v2.0 diario 0.05 grados (UCSB-CHC), media de una caja de 0.1 x 0.1 grados centrada en el punto de
  scripts/puntos.json, via la API publica ClimateSERV (SERVIR, NASA/USAID), datatype=0, operationtype=5 (promedio).
- Temperatura y humedad: ERA5-Land (ECMWF/Copernicus, 0.1 grados) via Open-Meteo Historical API.
- Viento, radiacion y lluvia ERA5 (0.25 grados, Open-Meteo models=era5): ERA5-Land en Open-Meteo devuelve null para
  viento, radiacion y lluvia en estos puntos (probado 2017-03-01..03). Viento de 10 m a 2 m con FAO-56 eq. 47.
- Lluvia usada (PRECTOTCORR): CHIRPS en Alto Piura y San Lorenzo; ERA5 en Chira, Medio y Bajo. Motivo: SENAMHI
  Miraflores (Piura, zona Medio) acumulo 506.3 mm del 1 al 27-mar-2017 (walac.pe, nota SENAMHI); CHIRPS da 19 mm en esa
  zona (-96 %), POWER 339 (-33 %), ERA5 624 (+23 %). CHIRPS en Chira y Bajo da 28 y 9 mm en el mismo lapso: se
  descarta en los tres valles costeros. En Alto y San Lorenzo CHIRPS da 483 y 429 mm y separa las dos zonas, que en
  ERA5 caen en la misma celda. Sin estacion de contraste en esas dos zonas (hipotesis). Ambas lluvias quedan en el CSV.
Salida: data/clima_zona/<zona>.csv con las columnas de data/power/<zona>.csv mas PREC_CHIRPS, PREC_ERA5 y la celda.
No rebaja si ya existe; los tramos descargados quedan en data/clima_zona/_cache.
"""
import json, pathlib, time, sys
import numpy as np, pandas as pd, requests

B = pathlib.Path(__file__).resolve().parents[1]
OUT = B / "data/clima_zona"
INI, FIN = "2000-01-01", "2025-12-31"  # ronda 4: hasta 2025 como POWER (siembras de 2024 que cosechan en 2025)
CS = "https://climateserv.servirglobal.net/api"

def chirps(z, lat, lon, h=0.05):
    g = {"type": "Polygon", "coordinates": [[[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]]]}
    partes = []
    for a0 in range(2000, 2026, 5):
        cache = OUT / "_cache" / f"{z}_chirps_{a0}.csv"  # tramo ya bajado: se reusa (la descarga puede cortarse)
        if cache.exists():
            partes.append(pd.read_csv(cache, parse_dates=["fecha"]))
            continue
        q = dict(datatype=0, begintime=f"01/01/{a0}", endtime=f"12/31/{min(a0 + 4, 2025)}", intervaltype=0, operationtype=5, geometry=json.dumps(g))
        rid = requests.get(f"{CS}/submitDataRequest/", params=q, timeout=120).json()[0]
        for _ in range(180):
            time.sleep(5)
            if requests.get(f"{CS}/getDataRequestProgress/", params={"id": rid}, timeout=60).json()[0] >= 100:
                break
        d = requests.get(f"{CS}/getDataFromRequest/", params={"id": rid}, timeout=300).json()["data"]
        t = pd.DataFrame({"fecha": pd.to_datetime([x["date"] for x in d], format="%m/%d/%Y"),
                          "PRECTOTCORR": [x["value"]["avg"] for x in d]})
        cache.parent.mkdir(parents=True, exist_ok=True)
        t.to_csv(cache, index=False)
        partes.append(t)
        print(" chirps", a0, len(d), flush=True)
    s = pd.concat(partes).sort_values("fecha")
    s.loc[s.PRECTOTCORR < 0, "PRECTOTCORR"] = np.nan  # -9999 = sin dato
    return s

def om(params):
    """Open-Meteo con reintentos (429 por cuota por minuto)."""
    for k in range(8):
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=300)
        if r.status_code == 200:
            return r.json()
        print(" open-meteo", r.status_code, r.text[:120], flush=True)
        time.sleep(30 * (k + 1))
    r.raise_for_status()


LLUVIA = {"alto_piura": "chirps", "san_lorenzo": "chirps"}  # el resto: era5 (ver docstring)


def era5(z, lat, lon):
    cache = OUT / "_cache" / f"{z}_era5.csv"
    if not cache.exists():
        r = om(dict(
            latitude=lat, longitude=lon, start_date=INI, end_date=FIN, daily="precipitation_sum,wind_speed_10m_mean,shortwave_radiation_sum",
            models="era5", timezone="America/Lima"))
        d = pd.DataFrame(r["daily"])
        cache.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"fecha": pd.to_datetime(d.time), "PREC_ERA5": d.precipitation_sum,
                      "WS2M": d.wind_speed_10m_mean / 3.6 * 4.87 / np.log(67.8 * 10 - 5.42),
                      "ALLSKY_SFC_SW_DWN": d.shortwave_radiation_sum, "lat_era5": r["latitude"], "lon_era5": r["longitude"]}).to_csv(cache, index=False)
    return pd.read_csv(cache, parse_dates=["fecha"])


def era5land(lat, lon):
    v = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean"
    r = om(dict(
        latitude=lat, longitude=lon, start_date=INI, end_date=FIN, daily=v, models="era5_land", timezone="America/Lima"))
    d = pd.DataFrame(r["daily"])
    return pd.DataFrame({"fecha": pd.to_datetime(d.time), "T2M": d.temperature_2m_mean, "T2M_MAX": d.temperature_2m_max,
                         "T2M_MIN": d.temperature_2m_min, "RH2M": d.relative_humidity_2m_mean, "elev_m": r["elevation"],
                         "lat_grid": r["latitude"], "lon_grid": r["longitude"]})

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = json.loads((B / "scripts/puntos.json").read_text())
    for z, p in pts.items():
        if len(sys.argv) > 1 and z not in sys.argv[1:]:
            continue
        f = OUT / f"{z}.csv"
        if f.exists():
            continue
        print(z, flush=True)
        e = era5land(p["lat"], p["lon"])
        c = chirps(z, p["lat"], p["lon"]).rename(columns={"PRECTOTCORR": "PREC_CHIRPS"})
        df = e.merge(era5(z, p["lat"], p["lon"]), on="fecha", how="left").merge(c, on="fecha", how="left")
        df["PRECTOTCORR"] = df.PREC_CHIRPS if LLUVIA.get(z) == "chirps" else df.PREC_ERA5
        cols = ["fecha", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "PREC_CHIRPS", "PREC_ERA5",
                "elev_m", "lat_grid", "lon_grid", "lat_era5", "lon_era5"]
        df[cols].round(3).to_csv(f, index=False)
        print(z, len(df), "faltan:", int(df[cols[1:8]].isna().sum().sum()), flush=True)

if __name__ == "__main__":
    main()
