"""Experimento ronda 4 (pedido del coordinador): ¿cambia el ranking de features si entra la CE del agua de riego (CEw)?

El motor (scripts/modelo.py) NO usa CEw: la salinidad sale solo de ece_ds_m (rango de suelo por zona). Este script
no toca el motor. Prueba una regla explícita y la reporta aparte:
  ECe_efectiva = max(ECe_suelo, 1.5 * CEw)
1.5 = factor de concentración FAO-29 (Ayers y Westcot 1985, Tabla 4 nota 2: ECe = 1.5 ECw con fracción de lavado
0.15-0.20; no vale con napa freática somera). El max hace que la CE medida del suelo domine salvo que el agua
proyecte más sal.
Rangos CEw de suelos/datos/cew_por_zona.csv (filas nivel=resumen, agua superficial de riego) y Coronel 2021 (Chira).
Uso: .venv/bin/python experimentos/exp_cew.py
"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import modelo as M
import importancia as I

N, SEED, K = 5000, 42, 1.5
NAN = (np.nan, np.nan, np.nan)
# (min, central, max) dS/m. central = 'valor' (mediana con >=3 puntos) de cew_por_zona.csv; si no hay, punto medio (marcado)
CEW = {
    "zona_csv": {  # cew_por_zona.csv, río (Alto, Chira, Medio, San Lorenzo); Bajo: río y canal = sin_dato
        0: (0.373, 0.888, 4.98), 1: NAN, 2: (0.74, 3.32, 9.92), 3: (0.345, 0.51, 0.741), 4: (0.417, 1.384, 9.03)},
    "chira_coronel": {  # Chira 0.373-1.167 (Coronel 2021, río Chira en Sullana); central = punto medio; resto igual
        0: (0.373, 0.77, 1.167), 1: NAN, 2: (0.74, 3.32, 9.92), 3: (0.345, 0.51, 0.741), 4: (0.417, 1.384, 9.03)},
    "bajo_pozo": {  # Bajo con el rango de pozo Medio+Bajo ANA 2014 (0.04-16.83); central = punto medio; resto zona_csv
        0: (0.373, 0.888, 4.98), 1: (0.04, 8.435, 16.83), 2: (0.74, 3.32, 9.92), 3: (0.345, 0.51, 0.741), 4: (0.417, 1.384, 9.03)},
}
_ev = M.evaluar


def ev_cew(esc):
    if "cew" not in esc:
        return _ev(esc)
    e = esc.copy()
    cw = np.asarray(e["cew"], float)
    e["ece_ds_m"] = np.where(np.isnan(cw), e["ece_ds_m"], np.fmax(e["ece_ds_m"], K * cw))
    return _ev(e)


def correr(cfg, ece_v3=False):
    zr_bak = list(M.ZR["ece_ds_m"])
    if ece_v3:  # rango ECe global de la ronda 3 (escenario_rangos.csv 0.5-12) en todas las zonas
        M.ZR["ece_ds_m"] = [NAN] * 5
    rng = np.random.default_rng(SEED)
    filas, resumen = [], []
    for zi, zona in enumerate(M.ZONAS):
        esc = M.muestrear(N, zi, rng, "normal")
        r0 = _ev(esc); t0, t30, s0 = M.ranking(r0)  # motor actual: CEw ausente = se ignora
        lo, ce, hi = CEW[cfg][zi]
        if np.isnan(lo):
            esc["cew"] = np.nan
        else:
            esc["cew"] = rng.uniform(lo, hi, N)
        base = ev_cew(esc); t1, t3, s = M.ranking(base)
        domina = float(np.mean(K * esc["cew"].fillna(-1) > esc["ece_ds_m"]) * 100)
        resumen.append(dict(config=cfg, ece="v3_global" if ece_v3 else "r4_zona", zona=zona, cew_min=lo, cew_central=ce, cew_max=hi,
                            pct_agua_domina=round(domina, 1),
                            cambio_top1_ausente_vs_con_cew_pct=round(float(np.mean(t0 != t1) * 100), 1),
                            ninguno_sin_cew=round(float(np.mean(t0 == -1) * 100), 1), ninguno_con_cew=round(float(np.mean(t1 == -1) * 100), 1)))
        if not np.isnan(lo):  # peor caso: CEw ausente reemplazada por el máximo de la zona
            e_w = esc.copy(); e_w["cew"] = hi
            tw = M.ranking(ev_cew(e_w))[0]
            resumen[-1]["cambio_top1_si_ausente_usa_max_pct"] = round(float(np.mean(tw != t1) * 100), 1)
        for f in M.FEATURES + ["cew"]:
            if f == "cew" and np.isnan(lo):
                continue
            c = ce if f == "cew" else M.rango(f, zi)[1]
            e2 = esc.copy(); e2[f] = c
            r2 = ev_cew(e2)
            e3 = esc.copy(); e3[f] = rng.permutation(e3[f].values)
            r3 = ev_cew(e3)
            for met, rr in (("ablacion", r2), ("permutacion", r3)):
                d = I.metricas(base, t1, t3, s, rr, *M.ranking(rr))[0]
                filas.append(dict(config=cfg, ece="v3_global" if ece_v3 else "r4_zona", zona=zona, feature=f, metodo=met,
                                  cambio_top1_pct=round(d["cambio_top1_pct"], 2)))
    M.ZR["ece_ds_m"] = zr_bak
    return filas, resumen


if __name__ == "__main__":
    M.evaluar = ev_cew
    F, R = [], []
    for cfg in CEW:
        for v3 in (False, True):
            f, r = correr(cfg, v3); F += f; R += r
    out = pathlib.Path(__file__).parent
    pd.DataFrame(F).to_csv(out / "exp_cew_importancia.csv", index=False)
    pd.DataFrame(R).to_csv(out / "exp_cew_resumen.csv", index=False)
    print(pd.DataFrame(R).to_string())
