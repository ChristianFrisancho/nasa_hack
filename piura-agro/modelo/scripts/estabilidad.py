"""Estabilidad del ranking de features (ronda 3).

Bootstrap sobre semillas (20 semillas, N=2000 escenarios por zona) y rangos alternativos defendibles, escenario climatico
'normal'. Metodo: ablacion ('falta el dato'), metrica cambio_top1_pct, por cultivo (incluye 'todos') y zona.
Salidas:
  resultados/estabilidad_corridas.csv  posicion de cada feature en cada corrida (alternativa x semilla x zona x cultivo)
  resultados/estabilidad_top5.csv      para el top-5 de la corrida principal (ranking_features.csv): % de corridas en que
                                       el feature queda en la misma posicion y % en que queda dentro del top-5
Alternativas (cada una cambia un supuesto; las demas quedan como la base). Ronda 4: la base usa ECe, P de drenaje y
pendiente por zona con fuente (params/zonas.csv):
  base; ece_global_r3 (0.5-12 en todas, hipotesis r3); ece_medio_como_bajo (Medio con el rango del Bajo, Territorio marca
  HWSD dudoso); drenaje_mod_severa (DelaTorre 1986 solo moderada a severa); drenaje_santayana_0341 (P comun r3);
  pendiente_0_2 (riego nivelado, hipotesis); costo_hasta_167 (factor_costo 1.0-1.67, solo ESCO arroz 2024).
  Ronda 4 tambien: ece_campo_alto_medio y ece_campo_bajo (CE de campo de Piura Datos leida como ECe, extracto sin confirmar);
  drenaje_bajo_napa_perm_0212 y drenaje_bajo_napa_total_0534 (Bajo Piura, estudio 1978); clima_power y clima_zona
  (demanda de agua con NASA POWER o con clima por zona; la base usa el clima activo de run_all.sh).
  Ronda 5: pendiente_dem_suavizado, pendiente_bajo_dem, pendiente_supuesta_r4 (ver zonas.csv fuente_pendiente).
"""
import pathlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import modelo as M
from importancia import importancia_zona

SEMILLAS = list(range(100, 120))
N = 2000
OUT = M.BASE / "resultados"


def alternativas():
    R0, P0 = M.RANGOS.copy(), list(M.P_DREN)
    Z0 = {k: list(v) for k, v in M.ZR.items()}
    nan3 = (np.nan, np.nan, np.nan)

    def con(f=None, vals=None, p=None, zr=None, dem=None):
        def aplicar():
            M.RANGOS = R0.copy()
            M.usar_demanda(dem if dem is not None else M.DEM)
            M.P_DREN[:] = P0
            for k in Z0:
                M.ZR[k] = list(Z0[k])
            if f:  # rango global: anula el rango por zona de ese feature
                M.RANGOS.loc[f, ["minimo", "central", "maximo"]] = vals
                if f in M.ZR:
                    M.ZR[f] = [nan3] * 5
            if p:
                for zi, v in p.items():
                    M.P_DREN[zi] = v
            if zr:
                for (k, zi), v in zr.items():
                    M.ZR[k][zi] = v
        return aplicar
    pb = list(M.ZPAR.p_drenaje_malo_bajo)
    return {"base": con(),
            "ece_global_r3": con("ece_ds_m", [0.5, 2.0, 12.0]),  # rango hipotesis de la ronda 3
            "ece_medio_como_bajo": con(zr={("ece_ds_m", 2): M.ZR["ece_ds_m"][1]}),  # Medio con el rango de Bajo (napa somera compartida)
            "drenaje_mod_severa": con(p=dict(enumerate(pb))),  # DelaTorre 1986 solo moderada a severa
            "drenaje_santayana_0341": con(p={i: 0.341 for i in range(5)}),  # P comun de la ronda 3
            "pendiente_0_2": con("pendiente_pct", [0.0, 1.0, 2.0]),
            "costo_hasta_167": con("factor_costo", [1.0, 1.0, 1.67]),
            # ronda 4, respuestas_a_modelos.md (Piura Datos) pedidos 12 y 13:
            "ece_campo_alto_medio": con(zr={("ece_ds_m", 3): (0.46, 0.53, 0.60), ("ece_ds_m", 2): (0.95, 0.95, 0.95)}),  # CE de campo leida como ECe (extracto sin confirmar)
            "ece_campo_bajo": con(zr={("ece_ds_m", 1): (3.44, 4.0, 8.2)}),  # CE de campo Tablazo Sur (Mendoza Flores 2025) leida como ECe; central 4.0 = el de zonas.csv
            "drenaje_bajo_napa_perm_0212": con(p={1: 0.212}),  # Bajo, estudio 1978 via Castillo Albines c. 2001: napa alta permanente
            "drenaje_bajo_napa_total_0534": con(p={1: 0.534}),  # idem, permanente + temporal
            # ronda 5: la base usa clima por zona con lluvia PISCOp (LLUVIA=pisco); alternativas de demanda de agua:
            "clima_power": con(dem=pd.read_csv(M.BASE / "data/demanda_agua_power_power.csv")),  # todo NASA POWER (ronda 4 alternativa)
            "lluvia_r4": con(dem=pd.read_csv(M.BASE / "data/demanda_agua_zona_r4.csv")),  # lluvia ERA5/CHIRPS en el punto (base de la ronda 4)
            "lluvia_chirps": con(dem=pd.read_csv(M.BASE / "data/demanda_agua_zona_chirps.csv")),  # CHIRPS zonal
            "lluvia_power": con(dem=pd.read_csv(M.BASE / "data/demanda_agua_zona_power.csv")),  # POWER del punto, solo lluvia
            # ronda 5: ECe zonal desconocida en Chira, Medio, Alto y San Lorenzo (HWSD descartado por Territorio); base = 0.5-2-12
            # alternativa 1: CE de campo puntual como cota baja, x1.8 central y x3 tope (factor 1:1 -> pasta, Territorio decision r5)
            "ece_campo_x1_x3": con(zr={("ece_ds_m", 0): (0.103, 0.185, 0.309), ("ece_ds_m", 2): (0.95, 1.71, 2.85),
                                       ("ece_ds_m", 3): (0.46, 0.83, 1.8)}),  # San Lorenzo sin CE de campo: queda en 0.5-2-12
            # alternativa 2: HWSD v2 D1 Q05-central-Q95 (base de la ronda 4; ahora solo contexto)
            "ece_hwsd_contexto_r4": con(zr={("ece_ds_m", 0): (1.0, 1.36, 4.3), ("ece_ds_m", 2): (1.2, 2.74, 4.3),
                                            ("ece_ds_m", 3): (0.8, 1.15, 4.3), ("ece_ds_m", 4): (0.6, 1.63, 4.3)}),
            # ronda 5: pendiente por zona de Piura Territorio (pendiente_por_zona.csv, GLO-30 + WorldCover) en la base;
            # alternativas: DEM suavizado 5x5 (menos ruido, borra pendientes cortas), Bajo con el DEM en vez de
            # Banco Mundial 1979, y el rango global supuesto de la ronda 4 (0-1-5)
            "pendiente_dem_suavizado": con(zr={("pendiente_pct", 0): (0.0, 0.6, 2.2), ("pendiente_pct", 2): (0.0, 1.1, 2.9),
                                               ("pendiente_pct", 3): (0.0, 0.8, 2.6), ("pendiente_pct", 4): (0.0, 1.6, 3.5),
                                               ("pendiente_pct", 1): (0.0, 0.3, 1.3)}),
            "pendiente_bajo_dem": con(zr={("pendiente_pct", 1): (0.0, 0.8, 2.6)}),
            "pendiente_supuesta_r4": con("pendiente_pct", [0.0, 1.0, 5.0])}, con()


def main():
    alts, reset = alternativas()
    filas = []
    for nombre, aplicar in alts.items():
        aplicar()
        for sem in SEMILLAS:
            rng = np.random.default_rng(sem)
            for zi, zona in enumerate(M.ZONAS):
                fz, _, _ = importancia_zona(zi, "normal", rng, n=N)
                d = pd.DataFrame(fz).query("metodo == 'ablacion'")
                d["k"] = d.cambio_top1_pct * 1e6 + d.importancia
                d["pos"] = d.groupby("cultivo").k.rank(ascending=False, method="first").astype(int)
                for r in d.itertuples():
                    filas.append(dict(alternativa=nombre, semilla=sem, zona=zona, cultivo=r.cultivo, feature=r.feature, pos=r.pos,
                                      cambio_top1_pct=round(r.cambio_top1_pct, 2)))
        print(nombre, "listo", flush=True)
    reset()
    c = pd.DataFrame(filas)
    c.to_csv(OUT / "estabilidad_corridas.csv", index=False)
    rk = pd.read_csv(M.BASE / "ranking_features.csv").query("escenario=='normal' and metodo=='ablacion' and zona!='todas' and rango<=5")
    res = []
    for r in rk.itertuples():
        s = c[(c.zona == r.zona) & (c.cultivo == r.cultivo) & (c.feature == r.feature)]
        sb = s[s.alternativa == "base"]
        res.append(dict(zona=r.zona, cultivo=r.cultivo, posicion=r.rango, feature=r.feature, cambio_top1_pct=r.cambio_top1_pct,
                        misma_pos_semillas_pct=round((sb.pos == r.rango).mean() * 100, 1),
                        top5_semillas_pct=round((sb.pos <= 5).mean() * 100, 1),
                        misma_pos_todas_alt_pct=round((s.pos == r.rango).mean() * 100, 1),
                        top5_todas_alt_pct=round((s.pos <= 5).mean() * 100, 1),
                        peor_pos=int(s.pos.max()), alternativa_peor=s.loc[s.pos.idxmax(), "alternativa"],
                        robusta=bool((sb.pos == r.rango).mean() >= 0.8 and (s.pos <= 5).mean() >= 0.9)))
    res = pd.DataFrame(res)
    res.to_csv(OUT / "estabilidad_top5.csv", index=False)
    print(res[res.cultivo == "todos"].to_string(index=False))


if __name__ == "__main__":
    main()
