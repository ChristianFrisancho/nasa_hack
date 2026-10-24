"""Ronda 2: intervalo del margen por zona, mes de siembra y cultivo, propagando los rangos de los datos faltantes.

Se fijan los datos que el agricultor conoce o decide (zona, mes de siembra, cultivo previo = arroz, el mas sembrado) y se
muestrean al azar (uniforme, semilla 42) todos los features con estado hipotesis o parcial, mas el año climatico.
Salida: resultados/intervalo_margen.csv con P(viable), P10/P50/P90 del margen condicionado a viable y P(top-1).
"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import modelo as M

SEED, N = 42, 20000
# ronda 4: ensancha el intervalo cuando el rendimiento de referencia de la celda (zona, cultivo) sale de pocos
# distrito-año. Multiplicador por cultivo ~ U(1-w, 1+w), w = CV del cultivo (DRAP 2015-2024, todos los distrito-año
# de las 5 zonas) / sqrt(n), n = n_distrito_anio de params/rend_zona.csv (n=0 se trata como 1), w <= 0.9.
# Es el error estandar relativo de una media; con n grande w se acerca a 0 y no cambia nada.
_R = pd.read_csv(M.BASE / "data/rendimientos_distrito_anio.csv")
_CV = _R.groupby("cultivo").rend_t_ha.agg(lambda x: x.std() / x.mean())
_N = pd.read_csv(M.BASE / "params/rend_zona.csv").pivot(index="zona", columns="cultivo", values="n_distrito_anio").loc[M.ZONAS, M.CROPS]
W = np.minimum(np.array([[_CV.get(c, np.nan) for c in M.CROPS]]) / np.sqrt(_N.clip(lower=1).to_numpy()), 0.9)
MESES = [12, 1, 3, 6, 9]  # dic y ene: ventana DRA del arroz; mar: ventana del algodon; jun y sep: contraste


def main():
    rng = np.random.default_rng(SEED)
    filas = []
    for zi, z in enumerate(M.ZONAS):
        for mes in MESES:
            e = M.muestrear(N, zi, rng)
            e["mes_siembra"] = mes
            e["cultivo_previo"] = 0
            for j, c in enumerate(M.CROPS):
                e["mrend_" + c] = 1 + W[zi, j] * (2 * rng.random(N) - 1)
            r = M.evaluar(e)
            t1, _, _ = M.ranking(r)
            for j, c in enumerate(M.CROPS):
                v = r["viable"][:, j]
                m = r["margen"][v, j]
                q = np.percentile(m, [10, 50, 90]) if v.any() else [np.nan] * 3
                filas.append(dict(zona=z, mes_siembra=mes, cultivo=c, n_rend=int(_N.iloc[zi, j]), w_rend=round(float(W[zi, j]), 3), p_viable=v.mean().round(3),
                                  margen_p10=round(q[0]), margen_p50=round(q[1]), margen_p90=round(q[2]),
                                  p_top1=(t1 == j).mean().round(3), p_ninguno=(t1 == -1).mean().round(3)))
    d = pd.DataFrame(filas)
    d["notas"] = f"N={N} por zona-mes, semilla {SEED}; margen PEN/ha condicionado a viable; previo=arroz"
    d.to_csv(M.BASE / "resultados/intervalo_margen.csv", index=False)
    top = d.sort_values("p_top1", ascending=False).groupby(["zona", "mes_siembra"]).head(3)
    print(top.sort_values(["zona", "mes_siembra", "p_top1"], ascending=[True, True, False])
          [["zona", "mes_siembra", "cultivo", "p_viable", "margen_p10", "margen_p50", "margen_p90", "p_top1", "p_ninguno"]].to_string(index=False))


if __name__ == "__main__":
    main()
