"""Ronda 2: demanda de agua de perennes, aparte de la rotacion anual.

Kc y duraciones: cultivos/perennes.csv (FAO-56 T11/T12, via Piura Agronomia). ET0 Penman-Monteith y lluvia: climatologia
mensual NASA POWER por zona (data/et0_pm_mensual_power.csv). Lluvia efectiva FAO/AGLW mensual (0.6P-10 si P<=70, 0.8P-24 si
no). El mes de inicio del ciclo no tiene fuente local: se recorren los 12 y se reporta min y max. Bruto = neto / eficiencia,
con eficiencia en [0.6*ef_op, ef_op] por zona (params/zonas.csv).
Ronda 3, mango: FAO-56 T12 no trae mango. Se usa Kc por fase de Silva Junior et al. 2023 (Engenharia Agricola 43(3) e20220189,
doi 10.1590/1809-4430-Eng.Agric.v43n3e20220189/2023; modelo/fuentes/palmer.txt Tablas 1 y 4): 'Palmer', Petrolina (Brasil,
semiarido), microaspersion, balance de energia Bowen. tipo_evidencia = analogo_externo: clima semiarido calido y riego
localizado como la costa de Piura, pero otra variedad (Piura: Kent, Edward, criollo), otro suelo y manejo de induccion floral.
Ciclo I (363 d) y ciclo II (295 d; los dias restantes del año cuentan 0, cota inferior).
Calor en floracion: resultados/mango_calor_floracion.csv cuenta por zona y mes dias con Tmax>32 y >33 C y noches Tmin<10 C
(NASA POWER 2000-2024). Umbrales: germinacion de polen <10% sobre 32 C (Tmax cardinal 30.4-34.3 C, PMC9837111); optimo
15-33 C y noches <10 C con viabilidad de polen <50% (Issarakraisila y Considine 1994, doi 10.1006/anbo.1994.1028).
Otras etapas: umbral de calor desconocido.
"""
import pathlib
import numpy as np
import pandas as pd
from clima_fuente import DIR, ET0_MENSUAL, CLIMA, LLUVIA, leer  # ronda 4; ronda 5 LLUVIA

B = pathlib.Path(__file__).resolve().parents[1]
P = pd.read_csv(B.parent / "cultivos/perennes.csv")
E = pd.read_csv(ET0_MENSUAL)
Z = pd.read_csv(B / "params/zonas.csv").set_index("zona")
CULT = ["banano (año 2)", "limon", "uva de mesa", "mango"]
EA_GOTEO, EA_SUP = 0.90, 0.60  # FAO Training Manual 4 (t7202e08) Tabla 8


def params(c):
    d = P[P.cultivo == c]
    kc = d[d.variable == "kc"].set_index("etapa").valor.astype(float)
    du = d[d.variable == "duracion_etapa_ciclo_anual"].set_index("etapa").valor.astype(float)
    if kc.empty or du.empty:
        return None
    return [kc.get("inicial"), kc.get("media"), kc.get("final")], [du.get(k) for k in ("inicial", "desarrollo", "media", "final")]


MANGO_KC = [0.81, 0.76, 0.85, 0.90, 0.95, 0.91]  # Tabla 4, promedio de los dos ciclos
MANGO_DU = {"ciclo_I": [57, 79, 40, 18, 110, 59], "ciclo_II": [61, 80, 11, 15, 94, 34]}  # Tabla 1
MANGO_FUENTE = "Silva Junior et al. 2023 doi 10.1590/1809-4430-Eng.Agric.v43n3e20220189/2023 (Palmer, Petrolina); analogo_externo"


def kc_mango(ciclo):
    return np.concatenate([np.full(d, k) for k, d in zip(MANGO_KC, MANGO_DU[ciclo])])


def calor_floracion():
    filas = []
    for z in Z.index:
        df = leer(z)  # ronda 5: lluvia según LLUVIA
        df = df[df.fecha.dt.year.between(2000, 2024)]
        g = df.groupby([df.fecha.dt.year.rename("anio"), df.fecha.dt.month.rename("mes")]).agg(
            d32=("T2M_MAX", lambda x: (x > 32).sum()), d33=("T2M_MAX", lambda x: (x > 33).sum()),
            n10=("T2M_MIN", lambda x: (x < 10).sum()), tmax=("T2M_MAX", "mean"), tmin=("T2M_MIN", "mean"))
        m = g.groupby("mes").mean().round(1)
        for mes, r in m.iterrows():
            filas.append(dict(zona=z, mes=mes, tmax_media=r.tmax, tmin_media=r.tmin, dias_tmax_gt32=r.d32, dias_tmax_gt33=r.d33,
                              noches_tmin_lt10=r.n10, fuente="NASA POWER diario 2000-2024 (reanalisis); umbrales PMC9837111 e Issarakraisila y Considine 1994"))
    out = pd.DataFrame(filas)
    out.to_csv(B / "resultados/mango_calor_floracion.csv", index=False)
    return out


def kc_diario(kc, du):
    ki, km, kf = kc
    li, ld, lm, ll = [int(x) for x in du]
    return np.concatenate([np.full(li, ki), np.linspace(ki, km, ld), np.full(lm, km), np.linspace(km, kf, ll)])


def main():
    filas = []
    dias_mes = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    for z, g in E.groupby("zona"):
        g = g.sort_values("mes")
        et0_d = np.repeat(g.et0.to_numpy() / dias_mes, dias_mes)  # mm/dia
        P_m = g.lluvia.to_numpy()
        pe_m = np.where(P_m <= 70, 0.6 * P_m - 10, 0.8 * P_m - 24).clip(0)
        pe_d = np.repeat(pe_m / dias_mes, dias_mes)
        ef = Z.loc[z, "eficiencia_operativa"]
        for c in CULT + ["mango_ciclo_I", "mango_ciclo_II"]:
            pr = params(c) if not c.startswith("mango") else None
            if c.startswith("mango_"):
                pr = "mango"
            if pr is None and c == "mango":
                continue  # ronda 3: el mango usa Kc de Silva Junior et al. 2023 (filas mango_ciclo_I y mango_ciclo_II)
            if pr is None:
                filas.append(dict(zona=z, cultivo=c, estado="desconocido", notas="sin Kc/duraciones en cultivos/perennes.csv"))
                continue
            kc = kc_mango(c[6:]) if pr == "mango" else kc_diario(*pr)
            n = len(kc)
            netos, etcs = [], []
            for m0 in range(12):
                ini = int(dias_mes[:m0].sum())
                idx = (ini + np.arange(n)) % 365
                # sin escalar: si el ciclo FAO dura menos de 365 d (uva 240 d) el resto del año cuenta 0, cota inferior
                etc = (kc * et0_d[idx]).sum()
                neto = np.clip(kc * et0_d[idx] - pe_d[idx], 0, None).sum()
                etcs.append(etc); netos.append(neto)
            nmin, nmax = min(netos), max(netos)
            filas.append(dict(zona=z, cultivo=c, etc_anual_mm_min=round(min(etcs)), etc_anual_mm_max=round(max(etcs)),
                              riego_neto_mm_min=round(nmin), riego_neto_mm_max=round(nmax),
                              ciclo_dias=n, neto_m3_ha_min=round(nmin * 10), neto_m3_ha_max=round(nmax * 10),
                              bruto_goteo_m3_ha=round(nmax * 10 / EA_GOTEO), bruto_gravedad_m3_ha=round(nmax * 10 / (EA_SUP * ef)),
                              dotacion_ana_m3_ha=Z.loc[z, "dotacion_m3_ha_anio"],
                              neto_sobre_dotacion=round(nmax * 10 / Z.loc[z, "dotacion_m3_ha_anio"], 2),
                              estado="calculado_analogo_externo" if pr == "mango" else "calculado",
                              fuente_kc=MANGO_FUENTE if pr == "mango" else "cultivos/perennes.csv (FAO-56 T11/T12)",
                              notas="ciclo FAO-56 sin escalar; inicio recorrido en 12 meses; bruto_goteo = neto max/0.90; bruto_gravedad = neto max/(0.60*ef_op ANA); neto_sobre_dotacion usa neto max"))
    d = pd.DataFrame(filas)
    d.to_csv(B / "resultados/perennes_agua.csv", index=False)
    print(d.drop(columns=["notas", "fuente_kc"]).to_string(index=False))
    cf = calor_floracion()
    print(cf.pivot_table(index="mes", columns="zona", values="dias_tmax_gt32").to_string())
    print(cf.pivot_table(index="mes", columns="zona", values="noches_tmin_lt10").to_string())


if __name__ == "__main__":
    main()
