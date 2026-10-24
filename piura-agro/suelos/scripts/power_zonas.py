"""NASA POWER mensual (PRECTOTCORR_SUM, T2M) en el centro de cada caja de zona, 1981-2024.
Salida: datos/clima/raw/power_centro_caja.csv"""
import os, json, requests, pandas as pd
ZONAS = {"Valle del Chira": (-81.0, -5.0, -80.5, -4.75), "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
         "Medio Piura": (-80.7, -5.2, -80.45, -5.0), "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
         "Alto Piura": (-80.25, -5.45, -79.85, -5.0), "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
         "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05)}
U = "https://power.larc.nasa.gov/api/temporal/monthly/point"
rows = []
for z, (w, s, e, n) in ZONAS.items():
    lat, lon = (s + n) / 2, (w + e) / 2
    r = requests.get(U, params=dict(parameters="PRECTOTCORR_SUM,T2M", community="AG", latitude=round(lat, 3), longitude=round(lon, 3),
                                    start=1981, end=2024, format="JSON"), timeout=120)
    r.raise_for_status(); d = r.json(); p = d["properties"]["parameter"]
    elev = d["geometry"]["coordinates"][2] if len(d["geometry"]["coordinates"]) > 2 else None
    for k, v in p["PRECTOTCORR_SUM"].items():
        if k[4:] == "13": continue
        rows.append(dict(subzona=z, lat=lat, lon=lon, year=int(k[:4]), month=int(k[4:]), power_rain_mm=v, power_t2m_c=p["T2M"][k], power_elev_m=elev))
    print(z, lat, lon, elev)
pd.DataFrame(rows).replace(-999, float("nan")).to_csv(os.path.join(os.path.dirname(__file__), "..", "datos", "clima", "raw", "power_centro_caja.csv"), index=False)
