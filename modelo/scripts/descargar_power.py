"""Descarga clima diario NASA POWER (AG community) para los puntos de Piura y lo guarda en data/power/<zona>.csv."""
import json, sys, time, pathlib, requests
import pandas as pd

PUNTOS = json.load(open(pathlib.Path(__file__).parent / "puntos.json"))
PARAMS = "T2M,T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OUT = pathlib.Path(__file__).parent.parent / "data" / "power"

def bajar(zona, p, start="20000101", end="20251231"):
    dst = OUT / f"{zona}.csv"
    if dst.exists():
        return dst
    r = requests.get(URL, params=dict(parameters=PARAMS, community="AG", longitude=p["lon"],
                     latitude=p["lat"], start=start, end=end, format="JSON"), timeout=300)
    r.raise_for_status()
    j = r.json()
    df = pd.DataFrame(j["properties"]["parameter"])
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999.0, float("nan"))
    df["elev_m"] = j["geometry"]["coordinates"][2]
    df.to_csv(dst, index_label="fecha")
    return dst

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for zona, p in PUNTOS.items():
        print(zona, bajar(zona, p), flush=True)
        time.sleep(2)
