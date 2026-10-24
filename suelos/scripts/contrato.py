"""Pasa un DataFrame al formato de /workspace/piura-agro/CONTRATO.md.
zona -> código del contrato; el nombre largo original va a 'subzona'.
Orden: campos del contrato primero, columnas extra al final.
Uso CLI: python scripts/contrato.py archivo.csv [...]  (reescribe en sitio)"""
import sys
import pandas as pd

CAMPOS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
          "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]
ZONA_COD = {"Valle del Chira": "chira", "Chira Sullana": "chira", "San Lorenzo": "san_lorenzo", "Medio Piura": "medio_piura",
            "Bajo Piura": "bajo_piura", "Sechura": "bajo_piura", "Alto Piura": "alto_piura", "Chulucanas": "alto_piura",
            "Sierra Ayabaca": "sierra_piura", "Ayabaca": "sierra_piura", "Sierra Huancabamba": "sierra_piura",
            "Huancabamba": "sierra_piura", "Departamento Piura": "piura_region"}
VALIDAS = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura", "piura_region", ""}


def a_contrato(df):
    df = df.copy()
    if "subzona" not in df.columns:
        df["subzona"] = df["zona"]
        df["zona"] = df["zona"].map(lambda z: ZONA_COD.get(z, z if z in VALIDAS else ""))
    malas = set(df.zona.fillna("")) - VALIDAS
    assert not malas, f"zonas fuera del contrato: {malas}"
    for c in CAMPOS:
        if c not in df.columns: df[c] = ""
    return df[CAMPOS + [c for c in df.columns if c not in CAMPOS]]


if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = a_contrato(pd.read_csv(p)); d.to_csv(p, index=False)
        print(p, len(d), sorted(d.zona.dropna().unique()))
