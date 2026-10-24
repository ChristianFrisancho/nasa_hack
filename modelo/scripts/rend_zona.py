"""Rendimiento de referencia por zona y cultivo (ronda 2). Fuente: DRAP distrito x año (data/rendimientos_distrito_anio.csv).

Referencia = produccion total / cosecha total de la zona (ponderado por area). Si la zona tiene menos de 5 distrito-año
o menos de 200 ha cosechadas en total, se usa el ponderado regional (columna origen lo dice). Tambien se guarda la mediana
y p10/p90 por zona para la pasada adversarial (ponderado vs mediana).
"""
import pathlib, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from validacion import zona

B = pathlib.Path(__file__).resolve().parents[1]
CROPS = list(pd.read_csv(B / "params/cultivos.csv").cultivo)
ZONAS = ["chira_sullana", "bajo_piura", "medio_piura", "alto_piura", "san_lorenzo"]


def main():
    r = pd.read_csv(B / "data/rendimientos_distrito_anio.csv")
    r["zona"] = [zona(p, d) for p, d in zip(r.PROVINCIA, r.DISTRITO)]
    # ronda 4 (Piura Datos, respuestas_a_modelos.md punto 1): algodon 2015 es año parcial en el DRAP (ponderado regional
    # 0,71 t/ha frente a 2,71-4,33 en 2016-2022); los otros cultivos no muestran ese salto en 2015. Se excluye solo algodon 2015.
    r = r[~((r.cultivo == "algodon") & (r.ANO == 2015))]
    reg = r.groupby("cultivo").apply(lambda g: g.produccion_t.sum() / g.cosecha_ha.sum())
    r = r.dropna(subset=["zona"])
    # ronda 3 (objecion 3 de Piura Datos): si la zona no alcanza, antes que el regional se usa la mediana DRAP de la zona
    # de Piura Datos (Medio y Bajo juntos), si tiene n>=3; se marca n_bajo. Fuente: data/evidencia_modelo.csv
    ev = pd.read_csv(B / "data/evidencia_modelo.csv").query("variable == 'rendimiento'").set_index(["cultivo", "zona"])
    filas = []
    for c in CROPS:
        for z in ZONAS:
            g = r[(r.cultivo == c) & (r.zona == z)]
            ok = len(g) >= 5 and g.cosecha_ha.sum() >= 200
            e = ev.loc[(c, z)] if (c, z) in ev.index else None
            usa_ev = (not ok) and e is not None and e.n >= 3
            ref = (g.produccion_t.sum() / g.cosecha_ha.sum()) if ok else (e.valor if usa_ev else reg[c])
            org = ("zona_ponderado" if ok else f"zona_mediana_PiuraDatos_n_bajo (n={int(e.n)}, ids {e.ids})" if usa_ev
                   else "regional_ponderado (zona sin datos suficientes; n_bajo)")
            if c == "frijol" and len(g) == 0:  # ronda 4, punto 11 de Piura Datos
                org += "; frijol comun sin registro DRAP en la zona: la leguminosa costera es caupi (fila propia)"
            filas.append(dict(cultivo=c, zona=z, n_distrito_anio=len(g), cosecha_ha=g.cosecha_ha.sum(),
                              rend_ponderado=g.produccion_t.sum() / g.cosecha_ha.sum() if len(g) else float("nan"),
                              rend_p10=g.rend_t_ha.quantile(.1) if len(g) else float("nan"),
                              rend_p50=g.rend_t_ha.median() if len(g) else float("nan"),
                              rend_p90=g.rend_t_ha.quantile(.9) if len(g) else float("nan"),
                              rend_ref_t_ha=ref, origen=org,
                              fuente="DRAP/GORE Piura datos abiertos 2015-2024, cultivos/raw/drap_dataset.csv"))
    out = pd.DataFrame(filas).round(3)
    out.to_csv(B / "params/rend_zona.csv", index=False)
    print(out.drop(columns="fuente").to_string())


if __name__ == "__main__":
    main()
