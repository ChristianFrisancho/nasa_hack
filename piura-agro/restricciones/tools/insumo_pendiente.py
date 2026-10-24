"""Copia la pendiente por zona de Piura Territorio (suelos/datos/pendiente_por_zona.csv, sólo lectura) a insumos/.
No recalcula nada (orden del padre: la pendiente la saca Territorio). Sólo adapta al CONTRATO:
  - unidad '% del área de cultivo' -> '%' (la variable area_cultivo_pendiente_mayor_* ya dice de qué es el %);
  - la columna 'resolucion' (fuera del CONTRATO) pasa a notas; subzona se conserva (columna opcional);
  - rango: valor_min = DEM suavizado 5x5, valor_max = DEM sin suavizar (lo dice la nota de Territorio).
Si el archivo no existe, no escribe nada y lo dice."""
import csv, datetime, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from contrato import normalizar
B = Path(__file__).resolve().parents[1]
SRC = B.parent / "suelos" / "datos" / "pendiente_por_zona.csv"
OUT = B / "insumos" / "pendiente_territorio.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon","fecha_o_periodo",
     "fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fecha_consulta","fuente_primaria","subzona"]
if not SRC.exists():
    print(f"SIN ARCHIVO {SRC}: no escribo pendiente"); sys.exit(0)
hoy = datetime.datetime.fromtimestamp(SRC.stat().st_mtime, datetime.timezone.utc).date().isoformat()
rows = []
for r in csv.DictReader(SRC.open(encoding="utf-8")):
    o = {c: r.get(c, "") for c in C}
    if o["unidad"] == "% del área de cultivo": o["unidad"] = "%"; o["notas"] += " Unidad original: % del área de cultivo de la caja."
    if r.get("resolucion"): o["notas"] += f" Resolución: {r['resolucion']}."
    o["notas"] = (o["notas"] + " Rango = DEM suavizado 5x5 a DEM sin suavizar. Calculado por Piura Territorio (suelos/datos/pendiente_por_zona.csv); Piura Datos no recalcula.").strip()
    o["cultivo"] = o["cultivo"] or "todos"
    o["fecha_consulta"] = hoy
    rows.append(normalizar(o))
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows(rows)
print(f"OK {len(rows)} -> {OUT.relative_to(B)}")
