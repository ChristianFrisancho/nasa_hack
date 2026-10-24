"""Ronda 5: arma datos_repo/evidencia_integrar_r5.csv para Catalogo.integrar_csv_contrato.

Entradas (copias fechadas en datos_repo/, ver SHA256SUMS):
- evidencia_observada.csv (Piura Datos, restricciones/): costos elegidos por id, todas las filas ce_agua_riego y
  todas las de pendiente.
- cew_por_zona.csv (Piura Territorio, suelos/datos/): solo las filas nivel=punto que la ronda 5 nombró (agua de
  reservorio o toma que llega a los canales, y pozos de tesis UNP como aviso).

Territorio usa nombres que no son del contrato (CE_agua_riego_reservorio, CE_agua_napa_pozo...). El motor los rechaza
(test_nombre_de_variable_desconocido_se_rechaza_con_mensaje_claro). Esta conversión es explícita, fila por fila, y
deja el nombre original en notas; no es un alias del motor. El tipo de agua va en la columna fuente_agua.
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "datos_repo/evidencia_observada.csv"
TERRITORIO = BASE / "datos_repo/cew_por_zona.csv"
SALIDA = BASE / "datos_repo/evidencia_integrar_r5.csv"

# costos: caupí con Vigna de Piura (PEIHAP actual y optimizada, Alto Piura) y el análogo de Trujillo; ddf95b71cd9e
# (Phaseolus, ENA 2018) sale en la ronda 5. Los otros cuatro siguen de la ronda 3.
IDS_COSTOS = {"c3de5a91d1fe", "8e714fc4563e", "f6471d3a3c47",
              "e789514c737b", "af593d78c9d8", "e6bc216fce1e", "1a6b5fe734ec"}
# (punto en cew_por_zona.csv, fuente_agua esperada): las tres de canal que nombró la ronda 5 y los pozos de tesis UNP
PUNTOS_TERRITORIO = {"PSI2011_SanLorenzo": "reservorio", "RChir3": "reservorio", "RMaca1": "toma",
                     "UNP2019_CuraMori": "pozo", "UNP2018_Castilla": "pozo"}

CONTRATO = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar",
            "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]
EXTRA = ["id_registro", "fuente_primaria", "subzona", "fuente_agua", "estacion", "archivo_origen"]


def main():
    out = []
    for r in csv.DictReader(open(DATOS, encoding="utf-8")):
        v = r["variable"]
        if r["id_registro"] in IDS_COSTOS or v == "ce_agua_riego" or v.startswith(("pendiente_", "area_cultivo_pendiente")):
            fila = {k: r.get(k, "") for k in CONTRATO + EXTRA}
            if v == "ce_agua_riego":  # Datos: puntos de río y quebrada; la ronda 5 dice que todos son de estiaje
                fila["fuente_agua"] = ""
                fila["estacion"] = "estiaje" if r["fecha_o_periodo"].startswith("2024-10") else ""
            out.append(fila)
    vistos = set()
    for r in csv.DictReader(open(TERRITORIO, encoding="utf-8")):
        punto = r.get("punto", "")
        if r.get("nivel") != "punto" or punto not in PUNTOS_TERRITORIO:
            continue
        if r["fuente_agua"] != PUNTOS_TERRITORIO[punto]:
            raise SystemExit(f"{punto}: fuente_agua '{r['fuente_agua']}' distinta de la esperada")
        fila = {k: r.get(k, "") for k in CONTRATO + ["fuente_primaria", "subzona", "fuente_agua", "estacion"]}
        fila["notas"] = f"{r['notas']} [nombre original en suelos/: {r['variable']}; convertido a ce_agua_riego por scripts/extraer_evidencia_r5.py]".strip()
        fila["variable"] = "ce_agua_riego"
        fila["id_registro"] = f"territorio:{punto}:{r['zona']}"
        fila["subzona"] = fila["subzona"] or punto
        fila["archivo_origen"] = "suelos/datos/cew_por_zona.csv"
        vistos.add(punto)
        out.append(fila)
    faltan = set(PUNTOS_TERRITORIO) - vistos
    if faltan:
        raise SystemExit(f"faltan puntos de Territorio: {sorted(faltan)}")
    with open(SALIDA, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CONTRATO + EXTRA)
        w.writeheader()
        w.writerows(out)
    print(f"{SALIDA.name}: {len(out)} filas")


if __name__ == "__main__":
    main()
