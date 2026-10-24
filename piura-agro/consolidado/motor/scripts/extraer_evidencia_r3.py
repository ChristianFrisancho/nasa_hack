"""Ronda 3: extrae de datos_repo/evidencia_observada.csv (copia de restricciones/, Piura Datos) solo las filas que
la ronda pidió integrar, a datos_repo/evidencia_observada_r3.csv. Se integran con Catalogo.integrar_csv_contrato.

- costos análogos externos: caupí (ENA 2018, Phaseolus), frijol verde (Tacna), papaya (ENA 2018, selva; también la
  fila en PEN/t, que el motor ignora por unidad), camote (Cañete; fuera del catálogo).
- ce_agua_riego: todas las filas (solo la de Chira trae valor; las otras son 'desconocido' y no reemplazan nada).
- pendiente_* y area_cultivo_pendiente_*: las 42 filas de Territorio (predicción DEM 30 m).
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ORIGEN = BASE / "datos_repo" / "evidencia_observada.csv"
DESTINO = BASE / "datos_repo" / "evidencia_observada_r3.csv"
IDS_COSTOS = {"ddf95b71cd9e", "e789514c737b", "af593d78c9d8", "5e0599d5cde9", "1a6b5fe734ec"}


def elegir(r: dict) -> bool:
    v = r["variable"]
    return (r["id_registro"] in IDS_COSTOS or v == "ce_agua_riego" or v.startswith("pendiente_")
            or v.startswith("area_cultivo_pendiente"))


def main():
    with open(ORIGEN, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        cab, filas = lector.fieldnames, [r for r in lector if elegir(r)]
    with open(DESTINO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cab, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} filas -> {DESTINO}")


if __name__ == "__main__":
    main()
