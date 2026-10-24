"""Deriva rendimiento (t/ha) y precio en chacra (PEN/kg) por cultivo desde el dataset DRAP de Piura.

Entrada: cultivos/raw/drap_dataset.csv (DRAP/MIDAGRI, siembras y cosechas mensuales por distrito, 2015-2024).
Salida: datos_motor/rendimiento_precio_drap.csv en formato CONTRATO.md.
Rendimiento = producción / superficie cosechada por distrito-año (solo distrito-años con >= 1 ha cosechada).
"""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
ENTRADA = RAIZ / "cultivos/raw/drap_dataset.csv"
SALIDA = Path(__file__).resolve().parents[1] / "datos_motor/rendimiento_precio_drap.csv"

MAPA = {
    "arroz": ["ARROZ"],
    "maiz amarillo duro": ["MAIZ AMARILLO DURO"],
    "maiz choclo": ["MAIZ CHOCLO"],
    "frijol grano": ["FRIJOL GRANO SECO"],
    "caupi": ["FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO SECO"],
    "arveja": ["ARVEJA GRANO SECO"],
    "algodon": ["ALGODON", "ALGODON PIMA", "ALGODON HIBRIDO HAZERA"],
    "papa": ["PAPA (agrupa mejoradas y nativas)"],
    "yuca": ["YUCA"],
    "zapallo": ["ZAPALLO"],
    "cebolla": ["CEBOLLA"],
    "piquillo": ["PIQUILLO (T.)"],
    "frijol de palo": ["FRIJOL DE PALO GRANO SECO (T.)", "FRIJOL DE PALO GRANO SECO (01)(PODUCTO)"],
    "mango": ["MANGO"],
    "limon": ["LIMON SUTIL", "LIMON TAHITI"],
    "banano": ["BANANO (Musa acuminata)"],
    "uva": ["VID"],
    "cacao": ["CACAO"],
    "cafe": ["CAFETO"],
    "papaya": ["PAPAYA"],
}
COLS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar",
        "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]


def filas_para(cultivo, d, lugar):
    filas = []
    g = d.groupby(["DISTRITO", "ANO"]).agg(cos=("COSECHA", "sum"), prod=("PRODUCCION", "sum")).reset_index()
    g = g[g.cos >= 1]
    if len(g) >= 3:
        r = g["prod"] / g["cos"]
        filas.append(dict(variable="rendimiento", valor=round(r.median(), 3), valor_min=round(r.quantile(0.1), 3),
                          valor_max=round(r.quantile(0.9), 3), unidad="t/ha", cultivo=cultivo, lugar=lugar,
                          fecha_o_periodo=f"{int(g.ANO.min())}-{int(g.ANO.max())}",
                          metodo=f"mediana y p10-p90 de {len(g)} distrito-años (producción/cosecha)",
                          notas=f"ponderado por superficie: {round(g['prod'].sum() / g['cos'].sum(), 3)} t/ha"))
    p = d[(d.PRODUCCION > 0) & (d.PRECIO_CHACRA > 0)]
    if len(p) >= 3:
        w = p.sort_values("PRECIO_CHACRA")
        cum = w.PRODUCCION.cumsum() / w.PRODUCCION.sum()
        q = lambda f: float(w.PRECIO_CHACRA[cum >= f].iloc[0])
        filas.append(dict(variable="precio_chacra", valor=round(q(0.5), 3), valor_min=round(q(0.1), 3),
                          valor_max=round(q(0.9), 3), unidad="PEN/kg", cultivo=cultivo, lugar=lugar,
                          fecha_o_periodo=f"{int(p.ANO.min())}-{int(p.ANO.max())}",
                          metodo=f"mediana y p10-p90 ponderados por producción de {len(p)} distrito-meses",
                          notas="soles nominales, sin deflactar"))
    return filas


def main():
    d = pd.read_csv(ENTRADA)
    salida = []
    for cultivo, nombres in MAPA.items():
        sub = d[d.CULTIVO.isin(nombres)]
        if sub.empty:
            continue
        salida += filas_para(cultivo, sub, "Piura (departamento)")
        for prov, sp in sub.groupby("PROVINCIA"):
            salida += filas_para(cultivo, sp, f"Piura/{prov.title()}")
    df = pd.DataFrame(salida)
    df["fuente"] = "DRAP Piura / MIDAGRI, estadística agrícola mensual por distrito"
    df["url_o_doi"] = "repo nasa_hack (copia en cultivos/raw/drap_dataset.csv)"
    df["tipo_evidencia"] = "regional"
    df["estado"] = "observado"
    # zona (CONTRATO.md): el agregado departamental es piura_region; una provincia no coincide con una zona -> vacío
    df["zona"] = df["lugar"].map(lambda l: "piura_region" if l == "Piura (departamento)" else "")
    for c in COLS:
        if c not in df:
            df[c] = ""
    df[COLS].to_csv(SALIDA, index=False)
    print(f"{len(df)} filas -> {SALIDA}")


if __name__ == "__main__":
    main()
