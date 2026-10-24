"""Ronda 5, punto 2, contra el MOTOR CONSOLIDADO (consolidado/motor): variantes (a)-(d) de la regla de CEw, por
monkeypatch en memoria (no se edita el motor). Uso (desde consolidado/motor): python3 ../../modelo/experimentos/cew_motor_variantes.py
Parcela tipo por zona = la de cew_motor.py (napa sin dato, agua sin dato).
  a  ignorar: si falta la CEw, la ECe tras la cosecha queda igual a la previa (parche a estado_suelo.actualizar_tras_cosecha).
  b  CEw conocida = mediana del río de la zona (suelos/datos/cew_por_zona.csv; Bajo sin río: 1.5, escenario del motor).
  c  motor actual: CEw faltante = ECe desconocida en la 2.a campaña (no evaluable).
  d  CEw faltante = sorteo en el rango de la zona: 9 valores puntuales en los cuantiles 0.1..0.9 de U(min, max)
     (Bajo: pozos 0.04-16.83, ANA ERH 2014, marcado); se reporta la fracción de sorteos con alguna secuencia viable.
Salida: modelo/experimentos/cew_motor_variantes.csv
"""
import collections, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cew_motor as CM  # noqa: E402
from motor_rotacion import estado_suelo as ES  # noqa: E402
import motor_rotacion.motor as MM  # noqa: E402

# central y rango del río leídos de suelos/datos/cew_por_zona.csv (resumen); Bajo sin río: central 1.5 (escenario del motor)
# y rango de pozos 0.04-16.83 (ANA ERH 2014, marcado)
def _rio_resumen(zm):
    for r in CM.CEW_CSV:
        if r["zona"] == zm and r["nivel"] == "resumen" and r["fuente_agua"] == "rio" and r["valor_min"]:
            return float(r["valor"]), (float(r["valor_min"]), float(r["valor_max"]))
    return None


CENTRAL, RANGO = {"bajo_piura": 1.5}, {"bajo_piura": (0.04, 16.83)}
for _zm in ("chira", "medio_piura", "alto_piura", "san_lorenzo"):
    CENTRAL[_zm], RANGO[_zm] = _rio_resumen(_zm)
_orig = ES.actualizar_tras_cosecha


def _ignorar(estado, cultivo, leguminosa, exportacion, riego, ecw, *a, **k):
    nuevo = _orig(estado, cultivo, leguminosa, exportacion, riego, ecw, *a, **k)
    if not ecw.conocido and estado.ece.conocido and not nuevo.ece.conocido:
        import dataclasses
        nuevo = dataclasses.replace(nuevo, ece=estado.ece)
    return nuevo


def main():
    filas = []
    for z, zm in CM.ZM.items():
        def fila(var, res, nota):
            filas.append(dict(zona=z, variante=var, **res, nota=nota))
        ES.actualizar_tras_cosecha = _ignorar
        MM.actualizar_tras_cosecha = _ignorar if hasattr(MM, "actualizar_tras_cosecha") else None
        fila("a_ignorar", CM.correr(CM.consulta(z)), "parche: ECe previa si falta la CEw")
        ES.actualizar_tras_cosecha = _orig
        if hasattr(MM, "actualizar_tras_cosecha"):
            MM.actualizar_tras_cosecha = _orig
        fila("b_conocida", CM.correr(CM.consulta(z, ecw=CENTRAL[zm])), f"CEw {CENTRAL[zm]}")
        fila("c_motor_actual", CM.correr(CM.consulta(z)), "CEw falta")
        lo, hi = RANGO[zm]
        res = [CM.correr(CM.consulta(z, ecw=round(lo + q / 10 * (hi - lo), 3))) for q in range(1, 10)]
        top = collections.Counter(r["sec_top"] for r in res).most_common(1)[0]
        fila("d_sorteo_rango", dict(n_aceptados=min(r["n_aceptados"] for r in res), top1=collections.Counter(r["top1"] for r in res).most_common(1)[0][0],
                                    top3="", sec_viables=round(sum(r["sec_viables"] for r in res) / 9, 1), sec_total=30,
                                    sec_top=f"{top[0]} ({top[1]}/9)"),
             f"9 cuantiles de U({lo}, {hi}); sorteos con alguna secuencia viable {sum(r['sec_viables'] > 0 for r in res)}/9; "
             f"aceptados min-max {min(r['n_aceptados'] for r in res)}-{max(r['n_aceptados'] for r in res)}")
    out = CM.B / f"modelo/experimentos/cew_motor_variantes{CM.SUF}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    for r in filas:
        print(r)


if __name__ == "__main__":
    main()
