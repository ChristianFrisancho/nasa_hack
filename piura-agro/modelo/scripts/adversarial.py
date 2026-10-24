"""Ronda 2: pasada adversarial. Para cada supuesto, cambia solo ese supuesto y mira si cambia el top-1 central y P(top-1).

Escenario central por zona con mes de siembra enero (ventana DRA del arroz) y previo = arroz. P(top-1) con N=20000, semilla 42.
"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import modelo as M

SEED, N, MES = 42, 20000, 1


def correr(etiqueta, fijo=None, parche=None):
    fijo = fijo or {}
    guard = {}
    if parche:
        for k, v in parche.items():
            guard[k] = getattr(M, k); setattr(M, k, v)
    try:
        filas = []
        rng = np.random.default_rng(SEED)
        for zi, z in enumerate(M.ZONAS):
            c = M.central(1, zi).assign(mes_siembra=MES, cultivo_previo=0, **{k: (v(zi) if callable(v) else v) for k, v in fijo.items()})
            r = M.evaluar(c); t1, t3, _ = M.ranking(r)
            e = M.muestrear(N, zi, rng).assign(mes_siembra=MES, cultivo_previo=0)
            for k, v in fijo.items():
                e[k] = v(zi) if callable(v) else v
            rr = M.evaluar(e); tt, _, _ = M.ranking(rr)
            pt = {cc: round(float((tt == j).mean()), 3) for j, cc in enumerate(M.CROPS)}
            filas.append(dict(supuesto=etiqueta, zona=z, top1_central=M.CROPS[t1[0]] if t1[0] >= 0 else "ninguno",
                              top3_central="|".join(M.CROPS[k] for k in sorted(t3[0], key=lambda k: -r["margen"][0, k])),
                              p_top1_lider=max(pt, key=pt.get), p_top1_arroz=pt["arroz"], p_top1_camote=pt["camote"],
                              p_top1_caupi=pt["caupi"], p_top1_algodon=pt["algodon"], p_ninguno=round(float((tt == -1).mean()), 3)))
        return filas
    finally:
        for k, v in guard.items():
            setattr(M, k, v)


def main():
    out = []
    out += correr("base_v2")
    # agua del arroz
    for agua in (10000, 18000):
        for extra in (150, 780):
            out += correr(f"agua_arroz={agua} m3/ha (ESCO) extra_arroz={extra} mm",
                          fijo={"agua_arroz_m3_ha": agua, "agua_extra_arroz_mm": extra})
    # pendiente: rango 0-5 % uniforme es hipotesis y el arroz tiene tope 1 % (hipotesis)
    out += correr("pendiente fija 0.3 % (valor por defecto del esquema)", fijo={"pendiente_pct": 0.3})
    out += correr("pendiente 0.3 % y ECe 2 dS/m (parcela arrocera tipica supuesta)", fijo={"pendiente_pct": 0.3, "ece_ds_m": 2.0})
    # camote y rendimientos: mediana en vez de ponderado
    rz = pd.read_csv(M.BASE / "params/rend_zona.csv")
    reg_med = pd.read_csv(M.BASE / "data/rendimientos_resumen.csv").set_index("cultivo").rend_p50
    rz["med"] = np.where(rz.origen == "zona_ponderado", rz.rend_p50, rz.cultivo.map(reg_med))
    out += correr("rendimiento de referencia = mediana (no ponderado)",
                  parche={"REND_Z": rz.pivot(index="zona", columns="cultivo", values="med").loc[M.ZONAS, M.CROPS]})
    # corte del filtro duro
    for u in (0.3, 0.7):
        out += correr(f"umbral de perdida del filtro duro = {u}", parche={"UMBRAL_PERDIDA": u})
    # drenaje
    out += correr("drenaje malo en toda la parcela", fijo={"drenaje_malo": 1})
    # costos
    for f in (1.67, 2.11):
        out += correr(f"factor_costo fijo = {f}", fijo={"factor_costo": f})
    # Ky analogos +-20 %
    for k in (0.8, 1.2):
        cu = M.CULT.copy(); cu["Ky"] = cu.Ky * k
        out += correr(f"Ky x{k}", parche={"CULT": cu})
    # ECe
    for ece in (0.5, 4.0, 8.0):
        out += correr(f"ECe fija = {ece} dS/m", fijo={"ece_ds_m": ece})
    d = pd.DataFrame(out)
    d.to_csv(M.BASE / "resultados/adversarial.csv", index=False)
    print(d.to_string(index=False))


if __name__ == "__main__":
    main()
