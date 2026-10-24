#!/usr/bin/env python3
"""Lluvia PISCOp v2.1 por zona, año y mes -> datos_repo/lluvia_zona_pisco_anual.csv.

El motor necesita la lluvia de cada año (no solo la mediana del escenario) para sacar la necesidad de riego año por
año y su rango entre años. Este script no recalcula nada a su manera: importa series() y ZONAS del script de Piura Datos
(restricciones/tools/lluvia_zona_pisco.py, solo lectura) y escribe la suma mensual de cada caja de zona por año.
Comprueba que la mediana entre años de cada escenario reproduce lluvia_zona_pisco.csv (la copia de datos_repo/).
Uso: PYTHONDONTWRITEBYTECODE=1 ../../suelos/.venv/bin/python scripts/lluvia_pisco_anual.py  (desde motor/)"""
import csv
import statistics
import sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[1]
BASE = MOTOR.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(BASE / "restricciones/tools"))
import lluvia_zona_pisco as L  # noqa: E402  (script de Piura Datos)

OUT = MOTOR / "datos_repo/lluvia_zona_pisco_anual.csv"
FUENTE = ("SENAMHI, PISCOp v2.1 mensual 0,1° (Aybar et al. 2020), archivo de Piura Territorio "
          "(suelos/datos/clima/raw/PISCOp_monthly.nc); cajas de zona y media de celdas de "
          "restricciones/tools/lluvia_zona_pisco.py (Piura Datos)")


def main():
    S, ym = L.series()
    filas = []
    for nombre, (_, zona) in L.ZONAS.items():
        s, n = S[nombre]
        for k, (y, m) in enumerate(ym):
            filas.append({"zona": zona, "subzona": nombre, "anio": y, "mes": m, "lluvia_mm": f"{float(s[k]):.2f}",
                          "n_celdas": n, "fuente": FUENTE, "url_o_doi": "https://doi.org/10.6084/m9.figshare.21127423",
                          "metodo": "suma_mensual_media_de_celdas", "tipo_evidencia": "prediccion", "estado": "estimado"})
    # comprobación contra el resumen por escenario de Datos (mediana de los años del escenario, mismo mes)
    idx = {(f["subzona"], f["anio"], f["mes"]): float(f["lluvia_mm"]) for f in filas}
    cajas = {z: [n for n, (_, zz) in L.ZONAS.items() if zz == z] for _, z in L.ZONAS.values()}
    revisadas = 0
    for r in csv.DictReader((MOTOR / "datos_repo/lluvia_zona_pisco.csv").open(encoding="utf-8")):
        if r["variable"] != "precipitacion_mensual":
            continue
        mes = L.MESES.index(r["fecha_o_periodo"].split(",")[1].strip()) + 1
        caja = r["subzona"] or cajas[r["zona"]][0]
        anios = [int(x) for x in r["notas"].split("años [")[1].split("]")[0].split(",")]
        anios_mes = anios  # en lluvia_zona_pisco.csv los años de cada fila ya son años calendario del mes
        med = statistics.median(idx[(caja, a, mes)] for a in anios_mes if (caja, a, mes) in idx)
        assert abs(med - float(r["valor"])) <= 0.06, (r["zona"], caja, mes, r["escenario"], med, r["valor"])
        revisadas += 1
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"OK {len(filas)} filas -> {OUT.relative_to(MOTOR)}; {revisadas} medianas por escenario reproducen lluvia_zona_pisco.csv")


if __name__ == "__main__":
    main()
