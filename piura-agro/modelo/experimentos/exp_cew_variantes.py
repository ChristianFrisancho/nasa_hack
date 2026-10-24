"""Ronda 5, punto 2: variantes de la regla de CEw en MI MODELO PROPIO (scripts/modelo.py), sin tocar el motor oficial.

ECe_efectiva = max(ECe_suelo, 1.5·CEw) (FAO-29, Ayers y Westcot 1985; vale con fracción de lavado 0.15-0.20 y napa ≥ 2 m).
Variantes:
  a   ignorar la CEw (lo que hacía mi modelo hasta la ronda 4).
  b1  CEw conocida = valor central de la zona (mediana del río, suelos/datos/cew_por_zona.csv), sin condición de napa.
  b2  igual que b1, pero la regla se aplica solo si la napa está a ≥ 2 m, como el motor consolidado. P(napa ≥ 2 m) por
      sorteo: Bajo U(0.20, 0.51) (49-80 % del área con napa < 2 m), Medio U(0.51, 1.0) (≤ 49 % con napa < 2 m), ambos de
      suelos/datos/profundidad_ph_por_zona.csv. Chira, Alto y San Lorenzo: napa sin dato, la regla no se aplica (motor).
  c   CEw faltante = bloqueo: el sorteo queda sin cultivo viable. Por construcción da 100 % donde falta la CEw.
  d1  CEw faltante = sorteo uniforme en el rango de la zona (río; Bajo sin río, usa pozos 0.04-16.83 de ANA ERH 2014,
      marcado), sin condición de napa.
  d2  d1 con la condición de napa de b2.
  b3  CEw de canal o toma (agua que entra a la chacra), sin condición de napa: Chira 0.59 (salida de Poechos, ANA
      oct-2024) y San Lorenzo 0.47 (reservorio, PSI c. 2011, una muestra). Las demás zonas no tienen canal: quedan como a.
  d3  CEw de pozo de tesis, U(rango), con la condición de napa de b2: Bajo Cura Mori 0.13-1.12 (5 pozos, UNP 2019) y
      Medio Castilla/Progreso Bajo 0.16-3.83 (7 pozos, UNP 2018). Las demás zonas quedan como a.
Todo lo de CEw se lee de suelos/datos/cew_por_zona.csv. Es de estiaje (sep-nov) o de estación desconocida; no hay medidas
de avenida, cuando la dilución baja la CEw: los valores son un techo estacional, no un promedio anual.
  d1sd d1 sin las 4 lecturas ANA 2024 de unidad ambigua (QCarn1, QSFran1, RPiur4, RPiur5), que el motor rechaza
      (consolidado/motor/motor_rotacion/catalogo.py, CEW_EN_DISPUTA). Desde 07:57 Territorio publica RPiur4 = 9.03 y
      RPiur5 = 9.92 dS/m como "estimado" por balance iónico (suelos/datos/balance_ionico_ana2024.csv), igual que Piura
      Datos (restricciones/aviso_territorio_cew.md); Agronomía da otras cifras (RPiur4 5.1-5.8). d1 usa el rango publicado.
La CEw "falta" en c y d en todas las zonas (caso del agricultor que no la informa). En b, Bajo no tiene valor de río y
queda como en a.
Salida: experimentos/exp_cew_variantes.csv (zona, variante, % sin cultivo viable, top-1 modal y % de cambio frente a a).
"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import modelo as M

N, SEED, K = 5000, 42, 1.5
NAN = (np.nan, np.nan, np.nan)
CEW = pd.read_csv(pathlib.Path(__file__).resolve().parents[2] / "suelos/datos/cew_por_zona.csv", dtype=str)
ZM = {"chira_sullana": "chira", "bajo_piura": "bajo_piura", "medio_piura": "medio_piura", "alto_piura": "alto_piura",
      "san_lorenzo": "san_lorenzo"}


def _num(r):
    if isinstance(r.valor_min, str) and isinstance(r.valor_max, str):
        return float(r.valor_min), float(r.valor_max)
    return (float(r.valor), float(r.valor)) if isinstance(r.valor, str) else None


def _fila(zona, fuente, nivel="resumen", punto=None):
    """Desde 07:55 Territorio usa una sola variable (ce_agua_riego) y el origen en fuente_agua."""
    d = CEW[(CEW.zona == ZM[zona]) & (CEW.nivel == nivel) & (CEW.fuente_agua == fuente)]
    if punto:
        d = d[d.punto == punto]
    d = d[[_num(r) is not None for r in d.itertuples()]]
    return None if d.empty else d.iloc[0]


def _rio(zona):
    r = _fila(zona, "rio")
    return NAN if r is None else (float(r.valor_min), float(r.valor), float(r.valor_max))


RIO = {i: _rio(z) for i, z in enumerate(M.ZONAS)}
CANAL = {}
for i, z in enumerate(M.ZONAS):
    for f in ("canal", "reservorio", "toma"):
        r = _fila(z, f)
        if r is not None:
            CANAL[i] = _num(r)[0]
            break
EN_DISPUTA = ("QCarn1", "QSFran1", "RPiur4", "RPiur5")
RIO_SD = {}
for i, z in enumerate(M.ZONAS):
    d = CEW[(CEW.zona == ZM[z]) & (CEW.nivel == "punto") & (CEW.fuente_agua == "rio")]
    d = d[~(d.punto.isin(EN_DISPUTA) & d.fecha_o_periodo.fillna("").str.startswith("2024"))]
    v = [x for r in d.itertuples() if _num(r) for x in _num(r)]
    if v and not np.isnan(RIO[i][0]):
        RIO_SD[i] = (min(v), max(v))
POZO_TESIS = {}
for i, z in enumerate(M.ZONAS):
    for pt in ("UNP2019_CuraMori", "UNP2018_Castilla"):
        r = _fila(z, "pozo", "punto", pt)
        if r is not None:
            POZO_TESIS[i] = _num(r)
POZO_BAJO = (0.04, 16.83)
P_NAPA_OK = {1: (0.20, 0.51), 2: (0.51, 1.0)}  # P(napa >= 2 m); resto: desconocida -> regla no aplica


def CEW_TXT(v, zi, ce, dlo, dhi):
    if v == "a":
        return "ignorada"
    if v == "b3":
        return f"canal {CANAL[zi]}" if zi in CANAL else "sin canal: como a"
    if v == "d1sd":
        return f"rio sin lecturas en disputa U{RIO_SD[zi]}" if zi in RIO_SD else f"U({dlo}, {dhi})"
    if v == "d3":
        return f"pozo tesis U{POZO_TESIS[zi]}" if zi in POZO_TESIS else "sin pozo de tesis: como a"
    return f"central {ce}" if v.startswith("b") else f"U({dlo}, {dhi})"


def aplicar(esc, cw, napa_ok):
    e = esc.copy()
    cw = np.broadcast_to(np.asarray(cw, float), (len(e),))
    usa = ~np.isnan(cw) & napa_ok
    e["ece_ds_m"] = np.where(usa, np.fmax(e["ece_ds_m"].values, K * np.nan_to_num(cw)), e["ece_ds_m"].values)
    return e


def main():
    rng = np.random.default_rng(SEED)
    filas = []
    nombres = list(M.CULT.cultivo)
    for zi, zona in enumerate(M.ZONAS):
        esc = M.muestrear(N, zi, rng, "normal")
        lo, ce, hi = RIO[zi]
        if zi in P_NAPA_OK:
            p = rng.uniform(*P_NAPA_OK[zi], N)
            napa_ok = rng.uniform(size=N) < p
        else:
            napa_ok = np.zeros(N, bool)
        todos = np.ones(N, bool)
        dlo, dhi = (lo, hi) if not np.isnan(lo) else POZO_BAJO
        cw_d = rng.uniform(dlo, dhi, N)
        V = {"a": esc,
             "b1": aplicar(esc, ce, todos), "b2": aplicar(esc, ce, napa_ok),
             "d1": aplicar(esc, cw_d, todos), "d2": aplicar(esc, cw_d, napa_ok),
             "b3": aplicar(esc, CANAL.get(zi, np.nan), todos)}
        cw_p = rng.uniform(*POZO_TESIS[zi], N) if zi in POZO_TESIS else np.full(N, np.nan)
        V["d3"] = aplicar(esc, cw_p, napa_ok)
        cw_s = rng.uniform(*RIO_SD[zi], N) if zi in RIO_SD else cw_d
        V["d1sd"] = aplicar(esc, cw_s, todos)
        t_a = M.ranking(M.evaluar(esc))[0]
        for v, e in V.items():
            t = M.ranking(M.evaluar(e))[0]
            s = pd.Series(t)
            modal = s.mode().iloc[0]
            filas.append(dict(zona=zona, variante=v, sin_cultivo_pct=round(100 * float(np.mean(t == -1)), 1),
                              top1_modal="ninguno" if modal == -1 else nombres[modal], top1_modal_pct=round(100 * float(np.mean(t == modal)), 1),
                              cambio_top1_vs_a_pct=round(100 * float(np.mean(t != t_a)), 1),
                              regla_aplicada_pct=round(100 * float(np.mean(napa_ok)), 1) if v in ("b2", "d2", "d3") else (100.0 if v != "a" else 0.0),
                              cew_usada=CEW_TXT(v, zi, ce, dlo, dhi), estacion="estiaje o desconocida; sin avenida"))
        filas.append(dict(zona=zona, variante="c", sin_cultivo_pct=100.0, top1_modal="ninguno", top1_modal_pct=100.0,
                          cambio_top1_vs_a_pct=round(100 * float(np.mean(t_a != -1)), 1), regla_aplicada_pct=100.0,
                          cew_usada="falta: bloqueo", estacion="no aplica"))
    out = pd.DataFrame(filas)
    sin = out.cew_usada.str.contains("como a|nan")  # sin valor de CEw: la regla no se aplicó
    out.loc[sin, "regla_aplicada_pct"] = 0.0
    out.to_csv(pathlib.Path(__file__).parent / "exp_cew_variantes.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    main()
