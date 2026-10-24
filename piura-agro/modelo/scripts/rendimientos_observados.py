"""Rendimiento observado (t/ha) y precio en chacra (PEN/kg) por distrito, campaña-año y cultivo desde el dataset DRAP/MIDAGRI Piura 2015-2024."""
import pathlib
import json, urllib.request
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parents[2]
SRC = RAIZ / "cultivos/raw/drap_dataset.csv"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data"
MAPA = {
    "ARROZ": "arroz",
    "MAIZ AMARILLO DURO": "maiz_amarillo_duro",
    "ALGODON PIMA": "algodon",
    "ALGODON": "algodon",  # ronda 3: objecion 2 de Piura Datos (3404 ha en 2015-24); HAZERA queda fuera (hibrido aparte)
    "FRIJOL GRANO SECO": "frijol",
    "FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO SECO": "caupi",
    "CAMOTE": "camote",
    "SORGO GRANO": "sorgo",
    "LIMON SUTIL": "limon", "MANGO": "mango", "VID": "uva", "BANANO (Musa acuminata)": "banano",
}

IPC_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/json/2014-1/2024-12"
IPC_CSV = OUT / "ipc_lima_bcrp.csv"


def ipc_anual():
    """Indice IPC Lima Metropolitana promedio anual, base 2018 = 1. BCRP serie PN01271PM (var % mensual).
    Ronda 3, objecion 6 de Piura Datos: los costos son ENA 2018 y los precios DRAP 2015-24 van en soles de 2018."""
    if not IPC_CSV.exists():
        j = json.load(urllib.request.urlopen(IPC_URL, timeout=60))
        filas = [(p["name"], float(p["values"][0])) for p in j["periods"]]
        pd.DataFrame(filas, columns=["periodo", "var_pct_mensual"]).to_csv(IPC_CSV, index=False)
    m = pd.read_csv(IPC_CSV)
    m["anio"] = m.periodo.str[-4:].astype(int)
    m["indice"] = (1 + m.var_pct_mensual / 100).cumprod()
    a = m.groupby("anio").indice.mean()
    return a / a.loc[2018]


def main():
    d = pd.read_csv(SRC)
    d = d[d.CULTIVO.isin(MAPA)].copy()
    d["cultivo"] = d.CULTIVO.map(MAPA)
    d["ingreso"] = d.PRODUCCION * d.PRECIO_CHACRA
    g = d.groupby(["cultivo", "PROVINCIA", "DISTRITO", "UBIGEO", "ANO"]).agg(
        cosecha_ha=("COSECHA", "sum"), produccion_t=("PRODUCCION", "sum"),
        siembra_ha=("SIEMBRA", "sum"), ingreso=("ingreso", "sum")).reset_index()
    g = g[(g.cosecha_ha >= 10) & (g.produccion_t > 0)]
    g["rend_t_ha"] = g.produccion_t / g.cosecha_ha
    g["precio_pen_kg"] = g.ingreso / g.produccion_t
    defl = ipc_anual()
    g["precio_pen2018_kg"] = g.precio_pen_kg / g.ANO.map(defl)
    g = g.drop(columns="ingreso")
    g.to_csv(OUT / "rendimientos_distrito_anio.csv", index=False)
    w = g.assign(p=g.precio_pen_kg * g.produccion_t, pr=g.precio_pen2018_kg * g.produccion_t)
    res = w.groupby("cultivo").agg(n_distrito_anio=("rend_t_ha", "size"), n_distritos=("UBIGEO", "nunique"),
                                   anios=("ANO", lambda s: f"{s.min()}-{s.max()}"),
                                   prod_t=("produccion_t", "sum"), cos_ha=("cosecha_ha", "sum"), p=("p", "sum"), pr=("pr", "sum"),
                                   rend_p10=("rend_t_ha", lambda s: s.quantile(.1)),
                                   rend_p50=("rend_t_ha", "median"),
                                   rend_p90=("rend_t_ha", lambda s: s.quantile(.9)))
    res["rend_ponderado_t_ha"] = res.prod_t / res.cos_ha
    res["precio_ponderado_pen_kg"] = res.p / res.prod_t
    res["precio_ponderado_pen2018_kg"] = res.pr / res.prod_t
    res = res.drop(columns=["p", "pr"]).round(3)
    res.to_csv(OUT / "rendimientos_resumen.csv")
    print(res.to_string())
    # params/cultivos.csv toma rendimiento regional y precio en soles de 2018 (mismo año que los costos ENA)
    cu = pd.read_csv(OUT.parent / "params/cultivos.csv")
    for i, c in enumerate(cu.cultivo):
        if c in res.index:
            cu.loc[i, "rend_ref_t_ha"] = res.loc[c, "rend_ponderado_t_ha"]
            cu.loc[i, "precio_pen_kg"] = res.loc[c, "precio_ponderado_pen2018_kg"]
    cu["fuente_rend_precio"] = ("DRAP/MIDAGRI Piura 2015-2024 cultivos/raw/drap_dataset.csv; precio ponderado por produccion "
                                "en soles de 2018 deflactado con IPC Lima BCRP PN01271PM (ronda 3)")
    cu.to_csv(OUT.parent / "params/cultivos.csv", index=False)

if __name__ == "__main__":
    main()
