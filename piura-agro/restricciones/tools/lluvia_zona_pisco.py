#!/usr/bin/env python3
"""Lluvia por zona con PISCOp v2.1 mensual (SENAMHI, 0,1°, 1981-01..2019-12) -> lluvia_zona_pisco.csv.
Zona = caja de Piura Territorio (suelos/scripts/clima_por_zona.py, ZONAS); valor de la zona cada mes = media simple de las
celdas 0,1° cuyo centro cae en la caja (sin ponderar por cobertura). Periodos: 12 meses, ene-abr y may-dic.
Escenarios ICEN (tools/icen_campanias.py, clasificación oficial de Territorio):
  sin_el_nino: mediana y P10/P90 entre años, excluyendo toda campaña El Niño (débil incluida).
  el_nino_moderado, el_nino_fuerte_extraordinario: mediana y mínimo/máximo de los pocos años del grupo.
Asignación de campaña (ago-jul, año = julio): mes m del año Y -> campaña Y+1 si m >= 8, si no Y; ene-abr Y -> campaña Y;
may-dic Y (cruza dos campañas) -> la más fuerte de Y e Y+1.
Uso: ../suelos/.venv/bin/python tools/lluvia_zona_pisco.py"""
import csv
from pathlib import Path
import numpy as np
import rasterio
from icen_campanias import clasificacion, FUENTE as FUENTE_ICEN

BASE = Path(__file__).resolve().parents[1]
PISCO = BASE.parent / "suelos/datos/clima/raw/PISCOp_monthly.nc"
OUT = BASE / "lluvia_zona_pisco.csv"
ZONAS = {  # caja (lon0, lat0, lon1, lat1) de Territorio -> (zona, subzona)
    "Valle del Chira": ((-81.0, -5.0, -80.5, -4.75), "chira"),
    "San Lorenzo": ((-80.55, -5.05, -80.2, -4.75), "san_lorenzo"),
    "Medio Piura": ((-80.7, -5.2, -80.45, -5.0), "medio_piura"),
    "Bajo Piura": ((-80.85, -5.55, -80.55, -5.2), "bajo_piura"),
    "Alto Piura": ((-80.25, -5.45, -79.85, -5.0), "alto_piura"),
    "Sierra Ayabaca": ((-79.9, -4.8, -79.5, -4.45), "sierra_piura"),
    "Sierra Huancabamba": ((-79.6, -5.45, -79.3, -5.05), "sierra_piura"),
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]
PERIODOS = [(MESES[m - 1], [m]) for m in range(1, 13)] + [("ene-abr", [1, 2, 3, 4]), ("may-dic", list(range(5, 13)))]
ORDEN = {"sin_el_nino": 0, "el_nino_debil": 1, "el_nino_moderado": 2, "el_nino_fuerte_extraordinario": 3}
ESCS = ["sin_el_nino", "el_nino_moderado", "el_nino_fuerte_extraordinario"]
CLS = clasificacion()
ICEN_2026 = ("Evento en curso 2026-27: el ICEN oficial (met.igp.gob.pe/datos/ICEN.txt, leído el 24-oct-2026) da 3,98 en agosto de "
             "2026, sobre el umbral extraordinario (3,5); ENFEN mantiene la Alerta de El Niño Costero (Comunicado Oficial 18-2026, "
             "16-oct-2026; el PDF no se pudo leer desde la caja). Este escenario no es teórico para la campaña 2026-27.")
NINO_OM = (" Escenario El Niño: léase como orden de magnitud. Validación mar-2017 (anexos/validacion_pisco_2017.md, Rollenbeck et al. "
           "2022, doi 10.3390/rs14040824): PISCOp da 553,7 mm en Piura ciudad frente a unos 481 (+15 %) y 957,5 en Chulucanas frente a unos "
           "1130 (-15 %); ambas cifras de referencia son aproximadas: están citadas en el texto del artículo sin estación ni fuente primaria. Chusis (Sechura) mar-2017: desconocido, sin fuente primaria; el Informe Técnico Extraordinario 001-2017/ENFEN "
           "no publica su total mensual, sólo dice que el acumulado ene-mar en las zonas bajas de Piura fue menor que en 1997-98 y "
           "parecido al de 1982-83 (búsqueda ronda 7).")
C = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
     "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas", "subzona", "escenario"]

def campania(y, nombre, meses):
    if nombre == "ene-abr": return [y]
    if nombre == "may-dic": return [y, y + 1]
    return [y + 1 if meses[0] >= 8 else y]

def esc_periodo(y, nombre, meses):
    return max((CLS[c][0] for c in campania(y, nombre, meses)), key=ORDEN.get)

def series():
    ds = rasterio.open(PISCO)
    arr = ds.read().astype(float)
    if ds.nodata is not None: arr[arr == ds.nodata] = np.nan
    arr[arr < 0] = np.nan
    rows, cols = np.meshgrid(np.arange(ds.height), np.arange(ds.width), indexing="ij")
    xs, ys = rasterio.transform.xy(ds.transform, rows.ravel(), cols.ravel())
    xs = np.array(xs).reshape(rows.shape); ys = np.array(ys).reshape(rows.shape)
    out = {}
    for nombre, ((x0, y0, x1, y1), _) in ZONAS.items():
        msk = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)
        out[nombre] = (np.nanmean(arr[:, msk], axis=1), int(msk.sum()))
    ym = [(1981 + k // 12, k % 12 + 1) for k in range(ds.count)]
    return out, ym

def main():
    S, ym = series()
    anios = sorted({y for y, _ in ym})
    filas = []
    for nombre, ((x0, y0, x1, y1), zona) in ZONAS.items():
        s, n = S[nombre]
        idx = {k: i for i, k in enumerate(ym)}
        for per, meses in PERIODOS:
            tot = {y: float(sum(s[idx[(y, m)]] for m in meses)) for y in anios if all((y, m) in idx for m in meses)}
            for esc in ESCS:
                ys_ = [y for y in tot if esc_periodo(y, per, meses) == esc]
                v = np.array([tot[y] for y in ys_])
                if esc == "sin_el_nino":
                    lo, hi = np.percentile(v, 10), np.percentile(v, 90); rango = "P10/P90 entre años"
                else:
                    lo, hi = v.min(), v.max(); rango = "mínimo/máximo de esos años (pocos años: no se calculan percentiles)"
                otros = {e: [y for y in tot if esc_periodo(y, per, meses) == e] for e in ORDEN}
                media_todos = np.mean(list(tot.values()))
                nota = (f"Modelo: PISCOp v2.1 (interpolación de estaciones SENAMHI con CHIRP, 0,1°); entradas: {n} celdas con centro en la "
                        f"caja de Territorio '{nombre}' (lon {x0} a {x1}, lat {y0} a {y1}), media simple sin ponderar por cobertura. "
                        f"Método: suma mensual de la zona por año, {'mediana' } entre años del escenario; rango = {rango}. "
                        f"Escenario {esc} según ICEN oficial por campaña (ago-jul) de Territorio: años {ys_} (n={len(ys_)}). "
                        + ("Excluye toda campaña El Niño, también las débiles " + str(otros['el_nino_debil']) + ". " if esc == "sin_el_nino" else "")
                        + (f"El may-dic de un año cruza dos campañas y toma la más fuerte. " if per == "may-dic" else "")
                        + f"Media de todos los años {anios[0]}-{anios[-1]} = {media_todos:.1f} mm (con El Niño). "
                        "No es medición en chacra; PISCOp asimila estaciones SENAMHI (ver clima/pisco_vs_chirps_resumen.txt: en la costa "
                        "PISCOp 1981-2000 da 1,29 veces la normal SENAMHI 1971-2000, y 1,06-1,48 tras reponderar por escenarios ICEN). "
                        + ("2017 cuenta como El Niño moderado por ICEN (máx. 1,31), aunque en Piura llovió como en un evento fuerte. " if esc == "el_nino_moderado" else "")
                        + (ICEN_2026 if esc == "el_nino_fuerte_extraordinario" else "")
                        + (NINO_OM if esc != "sin_el_nino" else ""))
                filas.append(dict(
                    variable="precipitacion_mensual" if len(meses) == 1 else "precipitacion_temporada",
                    valor=f"{np.median(v):.1f}", valor_min=f"{lo:.1f}", valor_max=f"{hi:.1f}", unidad="mm", cultivo="todos",
                    zona=zona, lugar=f"{nombre}, Piura (caja de Territorio, {n} celdas PISCOp 0,1°)",
                    lat=f"{(y0 + y1) / 2:.3f}", lon=f"{(x0 + x1) / 2:.3f}",
                    fecha_o_periodo=f"{anios[0]}-{anios[-1]}, {per}, {esc.replace('_', ' ')}",
                    fuente="SENAMHI, PISCOp v2.1 mensual 0,1° (Aybar et al. 2020), archivo descargado por Piura Territorio; " + FUENTE_ICEN,
                    url_o_doi="https://doi.org/10.6084/m9.figshare.21127423", metodo="mediana_entre_anios_por_escenario_icen",
                    tipo_evidencia="prediccion", estado="estimado", notas=nota,
                    subzona=nombre if zona == "sierra_piura" else "", escenario=esc))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=C, restval=""); w.writeheader(); w.writerows(filas)
    print(f"OK {len(filas)} filas -> {OUT.name}")

if __name__ == "__main__":
    main()
