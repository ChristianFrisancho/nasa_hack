"""Importancia de features: ablacion, permutacion, OAT y Sobol (SALib). Semilla fija. Uso: python scripts/importancia.py"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import modelo as M
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol

SEED = 42
N = 5000
OUT = M.BASE / "resultados"
FUENTE = {
    "mes_siembra": "variable de decision; clima NASA POWER diario 2000-2024 (reanalisis) + FAO-56 Kc",
    "agua_riego_mm": "dotacion ASIGNADA ANA PGRH p.155 por zona (San Lorenzo 9528-15191, Castillo Mimbela 2007) x fraccion por campaña supuesta 0.5-1.0",
    "eficiencia_riego": "eficiencia operativa ANA por zona; interpretacion (conduccion o total) supuesta",
    "agua_arroz_m3_ha": "ESCO arroz Piura 2024 (MIDAGRI) 10000-18000 m3/ha citando INIA 2020",
    "agua_extra_arroz_mm": "acotado por FAO Irrigation Water Needs (max) y 12000 m3/ha declarado por el presidente de APEAR (Agraria.pe 2016, estimado, no DRA) (min)",
    "pen_sanidad": "agentes compartidos de plagas_hospedantes_condiciones_v2.csv; magnitud supuesta",
    "ece_ds_m": "rango por zona en params/zonas.csv (fuente_ece); umbrales FAO-56 T23", "taw_mm_m": "FAO-56 T19",
    "n_suelo_kg_ha": "rango supuesto", "p_suelo_kg_ha": "rango supuesto", "k_suelo_kg_ha": "rango supuesto",
    "credito_n_leguminosa": "FAO PNB16 T22 (max 60)", "precio_fert_n_pen_kg": "rango supuesto",
    "precio_fert_p_pen_kg": "rango supuesto", "precio_fert_k_pen_kg": "rango supuesto",
    "pendiente_pct": "umbral y rango supuestos", "drenaje_malo": "P por valle, DelaTorre (ILRI) Tabla 2 evaluacion 1986, salinidad y drenaje (params/zonas.csv)", "cultivo_previo": "variable de decision; familia botanica",
    "factor_costo": "ENA 2018 (piso), ESCO arroz 2024 (1.67x) y LATAM 2025 maiz (2.11x)", "factor_precio": "DRAP precio chacra en soles 2018 (IPC BCRP), rango supuesto", "factor_rend": "DRAP rendimiento, rango supuesto",
}

# ronda 3 (objecion 5): 'medido' no existe. Estados: variable_de_decision, observado_asignado, bibliografico, mixto, hipotesis
ESTADO = {
    "mes_siembra": "variable_de_decision", "cultivo_previo": "variable_de_decision",
    "agua_riego_mm": "mixto_dotacion_asignada_mas_hipotesis", "eficiencia_riego": "mixto_observado_regional_mas_hipotesis",
    "agua_arroz_m3_ha": "bibliografico_regional", "agua_extra_arroz_mm": "mixto_bibliografico_mas_estimado",
    "factor_costo": "mixto_observado_mas_hipotesis", "taw_mm_m": "bibliografico", "credito_n_leguminosa": "bibliografico",
    "drenaje_malo": "bibliografico_por_valle_1986",
}
# ronda 4: fuente y estado por zona para features con rango por zona (params/zonas.csv)
_EST_ECE = {"bajo_piura": "mixto_clase_observada_mas_hipotesis"}
def _zona_fuente(f, z):
    zp = M.ZPAR.loc[z]
    if f == "ece_ds_m":
        lo, ce, hi = M.rango("ece_ds_m", list(M.ZPAR.index).index(z))  # ronda 5: zonas sin ECe usan el rango global
        return "ECe %s-%s dS/m: %s" % (lo, hi, zp.fuente_ece), _EST_ECE.get(z, "hipotesis_ece_zonal_desconocida")
    if f == "pendiente_pct" and not np.isnan(float(zp.pend_min)):
        est = "bibliografico_regional" if z == "bajo_piura" else "estimado_dem_30m"  # ronda 5: GLO-30 (Territorio)
        return "pendiente %s-%s %%: %s" % (zp.pend_min, zp.pend_max, zp.fuente_pendiente), est
    if f == "drenaje_malo":
        return "P=%s: %s" % (zp.p_drenaje_malo, zp.fuente_drenaje), "bibliografico_por_valle_1986"
    return None


def _estado(f):
    return ESTADO.get(f, "hipotesis")


def jacc(a, b):
    return np.array([len(x & y) / max(len(x | y), 1) for x, y in zip(a, b)])


def metricas(res0, t1, t3, s, res1, a1, a3, s1):
    """Filas 'todos' y por cultivo para un cambio (ablacion o permutacion)."""
    out = [dict(cultivo="todos", importancia=float(np.mean(np.abs(s1 - s)) / max(np.mean(np.abs(s)), 1e-9) * 100),
                cambio_top1_pct=float(np.mean(a1 != t1) * 100), cambio_top3_pct=float((1 - jacc(a3, t3).mean()) * 100),
                cambio_viable_pct=np.nan, cuota_top1_base_pct=np.nan)]
    m0 = np.where(res0["viable"], res0["margen"], 0.0)
    m1 = np.where(res1["viable"], res1["margen"], 0.0)
    for j, c in enumerate(M.CROPS):
        out.append(dict(cultivo=c, importancia=float(np.mean(np.abs(m1[:, j] - m0[:, j])) / max(np.mean(np.abs(m0[:, j])), 1e-9) * 100),
                        cambio_top1_pct=float(np.mean((t1 == j) != (a1 == j)) * 100),
                        cambio_top3_pct=float(np.mean([(j in x) != (j in y) for x, y in zip(t3, a3)]) * 100),
                        cambio_viable_pct=float(np.mean(res0["viable"][:, j] != res1["viable"][:, j]) * 100),
                        cuota_top1_base_pct=float(np.mean(t1 == j) * 100)))
    return out


def importancia_zona(zi, escenario, rng, n=N, feats=None):
    """Ablacion (fijar en el central = 'falta el dato') y permutacion, por cultivo y zona."""
    zona = M.ZONAS[zi]
    filas = []
    esc = M.muestrear(n, zi, rng, escenario)
    base = M.evaluar(esc)
    t1, t3, s = M.ranking(base)
    for f in feats or M.FEATURES:
        e2 = esc.copy()
        e2[f] = M.rango(f, zi)[1]
        r2 = M.evaluar(e2)
        for d in metricas(base, t1, t3, s, r2, *M.ranking(r2)):
            filas.append(dict(feature=f, zona=zona, escenario=escenario, metodo="ablacion", **d))
        e3 = esc.copy()
        e3[f] = rng.permutation(e3[f].values)
        r3 = M.evaluar(e3)
        for d in metricas(base, t1, t3, s, r3, *M.ranking(r3)):
            filas.append(dict(feature=f, zona=zona, escenario=escenario, metodo="permutacion", **d))
    return filas, t1, t3


def main():
    rng = np.random.default_rng(SEED)
    filas, top = [], []
    for escenario in M.ESCENARIOS:
        for zi, zona in enumerate(M.ZONAS):
            fz, t1, t3 = importancia_zona(zi, escenario, rng)
            filas += fz
            for k, cult in [(-1, "ninguno")] + list(enumerate(M.CROPS)):
                top.append(dict(escenario=escenario, zona=zona, cultivo=cult, top1_pct=round(float(np.mean(t1 == k)) * 100, 1),
                                top3_pct=round(float(np.mean([k in x for x in t3])) * 100, 1) if k >= 0 else np.nan))
            if escenario != "normal":
                continue
            # OAT desde el escenario central, recorriendo cada mes de siembra
            for f in M.FEATURES:
                lo, _, hi = M.rango(f, zi)
                vals = np.arange(int(lo), int(hi) + 1) if f in M.CATEG else np.linspace(lo, hi, 11)
                cambios, rangos_s = [], []
                for mes in range(1, 13):
                    c = M.central(len(vals), zi)
                    c["mes_siembra"] = mes
                    c[f] = vals
                    o1, _, os_ = M.ranking(M.evaluar(c))
                    b1, _, _ = M.ranking(M.evaluar(M.central(1, zi).assign(mes_siembra=mes)))
                    cambios.append(np.mean(o1 != b1[0]))
                    rangos_s.append(os_.max() - os_.min())
                filas.append(dict(feature=f, cultivo="todos", zona=zona, escenario=escenario, metodo="OAT", importancia=float(np.mean(rangos_s)),
                                  cambio_top1_pct=float(np.mean(cambios) * 100)))
            # Sobol del margen por cultivo (campaña sorteada en el escenario normal)
            prob = {"num_vars": len(M.FEATURES), "names": M.FEATURES,
                    "bounds": [[M.rango(f, zi)[0], M.rango(f, zi)[2] + (0.999 if f in M.CATEG else 0)] for f in M.FEATURES]}
            X = sobol_sample.sample(prob, 1024, calc_second_order=False, seed=SEED)
            e = pd.DataFrame(X, columns=M.FEATURES)
            for f in M.CATEG & set(M.FEATURES):
                e[f] = np.floor(e[f]).astype(int)
            e["zona"] = zi
            e["campania"] = np.random.default_rng(SEED).choice(M.ESCENARIOS["normal"], len(e))
            r = M.evaluar(e)
            for j, cult in enumerate(M.CROPS):
                Y = np.where(r["viable"][:, j], r["margen"][:, j], 0.0)
                if Y.std() == 0:
                    continue
                Si = sobol.analyze(prob, Y, calc_second_order=False, seed=SEED)
                for f, st in zip(M.FEATURES, Si["ST"]):
                    filas.append(dict(feature=f, cultivo=cult, zona=zona, escenario=escenario, metodo="sobol_ST", importancia=float(st)))
        print(escenario, "listo")
    df = pd.DataFrame(filas)
    df["fuente_dato"] = df.feature.map(FUENTE)
    df["estado"] = df.feature.map(_estado)
    for (f, z), i in df.groupby(["feature", "zona"]).groups.items():
        r = _zona_fuente(f, z) if z in M.ZONAS else None
        if r:
            df.loc[i, "fuente_dato"], df.loc[i, "estado"] = r
    df["notas"] = ("importancia = salida del modelo mecanico FAO-56/FAO-33/Maas-Hoffman con N=%d escenarios por zona y escenario climatico, "
                   "semilla %d; no validada contra rendimiento por parcela" % (N, SEED))
    df.to_csv(OUT / "importancia_detalle.csv", index=False)
    pd.DataFrame(top).to_csv(OUT / "top_por_escenario.csv", index=False)
    return df


if __name__ == "__main__":
    main()
