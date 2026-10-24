"""Motor de rotacion: filtros duros primero, luego margen esperado por cultivo. Vectorizado sobre escenarios.

Entrada: DataFrame de escenarios (una fila por parcela-campaña) con las columnas de params/escenario_rangos.csv.
Salida: margen (PEN/ha) por cultivo, mascara de viabilidad y motivo del primer filtro que falla.
"""
import pathlib
import numpy as np
import pandas as pd

BASE = pathlib.Path(__file__).resolve().parents[1]
CULT = pd.read_csv(BASE / "params/cultivos.csv")
CROPS = list(CULT.cultivo)
ZONAS = ["chira_sullana", "bajo_piura", "medio_piura", "alto_piura", "san_lorenzo"]
RANGOS = pd.read_csv(BASE / "params/escenario_rangos.csv").set_index("feature")
DEM = pd.read_csv(BASE / "data/demanda_agua.csv")
# hipotesis declaradas (estado=hipotesis en ranking_features.csv)
SW0_FRAC = 0.5          # fraccion de TAW llena al sembrar
REC_N, REC_P, REC_K = 0.5, 0.25, 0.6  # eficiencia de recuperacion del fertilizante
PEN_MISMA_FAMILIA = 0.10  # perdida de rendimiento por repetir familia
UMBRAL_PERDIDA = 0.5    # filtro duro: perdida esperada >50% por agua o sal = no viable

_etc = DEM.pivot_table(index=["zona", "anio", "mes_siembra"], columns="cultivo", values="etc_mm")[CROPS]
_pef = DEM.pivot_table(index=["zona", "anio", "mes_siembra"], columns="cultivo", values="peff_mm")[CROPS]
ANIOS = sorted(DEM.anio.unique())


def evaluar(esc: pd.DataFrame):
    n = len(esc)
    z = np.asarray(esc.zona).astype(int).clip(0, 4)
    an = np.asarray(esc.anio).astype(int)
    ms = np.asarray(esc.mes_siembra).astype(int).clip(1, 12)
    idx = pd.MultiIndex.from_arrays([np.array(ZONAS)[z], an, ms])
    etc = _etc.reindex(idx).values
    pef = _pef.reindex(idx).values
    c = {k: CULT[k].to_numpy(dtype=object if CULT[k].dtype.kind not in "fi" else float)[None, :] for k in CULT.columns}
    col = lambda k: np.asarray(esc[k], float)[:, None]
    # agua (FAO-56 + Ky FAO-33)
    sw0 = SW0_FRAC * col("taw_mm_m") * c["Zr_m"]  # agua almacenada util al sembrar
    oferta = pef + col("agua_riego_mm") * col("eficiencia_riego") + sw0 - c["agua_extra_mm"]
    eta = np.clip(oferta, 0, etc)
    yw = np.clip(1 - c["Ky"] * (1 - eta / etc), 0, 1)
    # salinidad Maas-Hoffman
    ys = np.clip(1 - c["b_pct"] / 100 * np.clip(col("ece_ds_m") - c["ECe_umbral"], 0, None), 0, 1)
    # sanidad: repetir familia
    prev = np.asarray(esc.cultivo_previo).astype(int).clip(0, len(CROPS) - 1)
    fam_prev = CULT.familia.to_numpy(dtype=object)[prev][:, None]
    misma = fam_prev == c["familia"]
    yh = np.where(misma, 1 - PEN_MISMA_FAMILIA, 1.0)
    rend = c["rend_ref_t_ha"] * col("factor_rend") * yw * ys * yh
    # NPK
    leg_prev = (fam_prev == "Fabaceae")
    n_ofer = col("n_suelo_kg_ha") + np.where(leg_prev, col("credito_n_leguminosa"), 0)
    def_n = np.clip(rend * c["N_kg_t"] * np.where(c["familia"] == "Fabaceae", 0.0, 1.0) - n_ofer, 0, None) / REC_N
    def_p = np.clip(rend * c["P2O5_kg_t"] - col("p_suelo_kg_ha"), 0, None) / REC_P
    def_k = np.clip(rend * c["K2O_kg_t"] - col("k_suelo_kg_ha"), 0, None) / REC_K
    costo_f = def_n * col("precio_fert_n_pen_kg") + def_p * col("precio_fert_p_pen_kg") + def_k * col("precio_fert_k_pen_kg")
    ingreso = rend * 1000 * c["precio_pen_kg"] * col("factor_precio")
    # el costo ENA ya incluye fertilizacion tipica: solo se suma la diferencia frente al suelo central
    costo_f0 = _costo_fert_central(c, rend)
    margen = ingreso - c["costo_pen_ha"] * col("factor_costo") - (costo_f - costo_f0)
    # filtros duros (antes del puntaje)
    f_sal = ys < UMBRAL_PERDIDA
    f_agua = yw < UMBRAL_PERDIDA
    f_dren = (col("drenaje_malo") > 0.5) & (c["drena_mal_tolera"] == "no")
    f_pend = col("pendiente_pct") > c["pend_max_pct"]
    viable = ~(f_sal | f_agua | f_dren | f_pend)
    return dict(margen=margen, viable=viable, yw=yw, ys=ys, rend=rend, costo_f=costo_f,
                f_sal=f_sal, f_agua=f_agua, f_dren=f_dren, f_pend=f_pend)


def _costo_fert_central(c, rend):
    R = RANGOS.central
    dn = np.clip(rend * c["N_kg_t"] * np.where(c["familia"] == "Fabaceae", 0.0, 1.0) - R.n_suelo_kg_ha, 0, None) / REC_N
    dp = np.clip(rend * c["P2O5_kg_t"] - R.p_suelo_kg_ha, 0, None) / REC_P
    dk = np.clip(rend * c["K2O_kg_t"] - R.k_suelo_kg_ha, 0, None) / REC_K
    return dn * R.precio_fert_n_pen_kg + dp * R.precio_fert_p_pen_kg + dk * R.precio_fert_k_pen_kg


def ranking(res, k=3):
    m = np.where(res["viable"], res["margen"], -np.inf)
    orden = np.argsort(-m, axis=1)
    top1 = np.where(np.isfinite(m.max(1)), orden[:, 0], -1)  # -1 = ningun cultivo evaluado es viable
    topk = [set(o[:k][np.isfinite(mm[o[:k]])]) for o, mm in zip(orden, m)]
    return top1, topk, np.where(np.isfinite(m.max(1)), m.max(1), 0.0)


FEATURES = [f for f in RANGOS.index if f not in ("zona",)] + ["anio"]
CATEG = {"mes_siembra", "cultivo_previo", "drenaje_malo", "anio"}


def muestrear(n, zona, rng):
    d = {}
    for f in RANGOS.index:
        lo, hi = RANGOS.loc[f, "minimo"], RANGOS.loc[f, "maximo"]
        if f == "zona":
            d[f] = np.full(n, zona)
        elif f == "drenaje_malo":
            d[f] = (rng.random(n) < 0.2).astype(int)  # hipotesis P=0.2
        elif f in CATEG:
            d[f] = rng.integers(int(lo), int(hi) + 1, n)
        else:
            d[f] = rng.uniform(lo, hi, n)
    d["anio"] = rng.choice(ANIOS, n)
    return pd.DataFrame(d)


def central(n, zona):
    d = {f: np.full(n, RANGOS.loc[f, "central"]) for f in RANGOS.index}
    d["zona"] = np.full(n, zona)
    d["anio"] = np.full(n, int(np.median(ANIOS)))
    return pd.DataFrame(d)
