"""Validacion con rendimiento observado regional (DRAP, distrito x año). No hay rendimiento por finca.

Pregunta: ¿el clima POWER del año (lluvia, ET0, Tmax) que alimenta el modelo explica la variacion de rendimiento
mejor que el promedio historico del distrito? Dos esquemas:
  LOYO: leave-one-year-out (entrena con los otros años).
  GKF : GroupKFold por distrito (5 pliegues), referencia = media del cultivo en los otros distritos ese año.
"""
import os, pathlib, re, unicodedata
import numpy as np
import pandas as pd
from clima_fuente import DIR, ET0_MENSUAL, CLIMA, LLUVIA, leer  # ronda 4; ronda 5 LLUVIA
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

B = pathlib.Path(__file__).resolve().parents[1]
SEED = 42
BAJO = {"CATACAOS", "CURA MORI", "EL TALLAN", "LA ARENA", "LA UNION", "VEINTISEIS DE OCTUBRE"}
SANL = {"TAMBO GRANDE", "LAS LOMAS"}
def zona(prov, dist):
    if prov == "SECHURA" or dist in BAJO: return "bajo_piura"
    if dist in SANL: return "san_lorenzo"
    if prov in ("SULLANA", "PAITA", "TALARA"): return "chira_sullana"
    if prov == "MORROPON": return "alto_piura"
    if prov == "PIURA": return "medio_piura"
    return None  # Ayabaca y Huancabamba: sierra, sin punto POWER

# Ronda 5 (R6-1 de Piura Datos, regla A4 con factor 1,5 aceptada por el coordinador). ATIPICOS:
#   crudo        todas las filas DRAP (comportamiento de rondas 1-5; salidas de siempre)
#   sin_rescate  quita las cifras A4 que Piura Datos deja "desconocido" (las 41 A4 de rendimiento_desconocido_explicado.csv)
#   con_rescate  igual, pero devuelve las rescatadas por la variante 1,5 (marca rescate_a4), salvo la uva de Las Lomas 2016
ATIPICOS = os.environ.get("ATIPICOS", "crudo")
EXPL = B.parent / "restricciones/anexos/rendimiento_desconocido_explicado.csv"
MAPA_PD = {"algodón": "algodon", "camote": "camote", "frijol": "frijol", "frijol caupí": "caupi", "limón": "limon",
           "maíz amarillo duro": "maiz_amarillo_duro", "mango": "mango", "uva": "uva", "plátano": "banano"}
def _n(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper().strip()
def marcar_atipicos(r):
    """Agrega descartada_a4 y rescate_a4 por cultivo, distrito, año y cifra (±1 %)."""
    r = r.copy(); r["descartada_a4"] = False; r["rescate_a4"] = False
    for x in pd.read_csv(EXPL, dtype=str, keep_default_na=False).itertuples():
        c = MAPA_PD.get(x.cultivo); m = re.match(r"Distrito (.+) \((.+)\)", x.lugar)
        if x.regla != "A4" or not c or not m:
            continue
        k = (r.cultivo == c) & (r.DISTRITO == _n(m.group(1))) & (r.ANO == int(x.fecha_o_periodo)) \
            & ((r.rend_t_ha / float(x.cifra_publicada_t_ha) - 1).abs() < 0.01)
        r.loc[k, "descartada_a4"] = True
        if x.variante_estricta_factor_1_5.startswith("si") and not (c == "uva" and _n(m.group(1)) == "LAS LOMAS" and x.fecha_o_periodo == "2016"):
            r.loc[k, "rescate_a4"] = True
    return r

RNG_IC = np.random.default_rng(42)


def ic_skill(y, pa, pb, grupos, n=1000):
    """Ronda 5 (08:20): IC 95 % del skill por bootstrap de bloques (se remuestrean años o distritos enteros, no filas,
    porque las filas de un mismo año o distrito no son independientes)."""
    y, pa, pb, g = np.asarray(y, float), np.asarray(pa, float), np.asarray(pb, float), np.asarray(grupos)
    ok = ~(np.isnan(pa) | np.isnan(pb))
    y, pa, pb, g = y[ok], pa[ok], pb[ok], g[ok]
    u = np.unique(g)
    ea = {k: np.abs(pa[g == k] - y[g == k]) for k in u}
    eb = {k: np.abs(pb[g == k] - y[g == k]) for k in u}
    sk = []
    for _ in range(n):
        m = RNG_IC.choice(u, len(u))
        a = np.concatenate([ea[k] for k in m]).mean(); b = np.concatenate([eb[k] for k in m]).mean()
        sk.append((1 - b / a) * 100 if a > 0 else np.nan)
    return float(np.nanpercentile(sk, 2.5)), float(np.nanpercentile(sk, 97.5))


def main():
    r = pd.read_csv(B / "data/rendimientos_distrito_anio.csv")
    if ATIPICOS != "crudo":
        r = marcar_atipicos(r)
        quitar = r.descartada_a4 & ~r.rescate_a4 if ATIPICOS == "con_rescate" else r.descartada_a4
        print(f"ATIPICOS={ATIPICOS}: quito {int(quitar.sum())} filas, rescatadas {int((r.rescate_a4).sum()) if ATIPICOS == 'con_rescate' else 0}")
        r = r[~quitar]
    r["zona"] = [zona(p, d) for p, d in zip(r.PROVINCIA, r.DISTRITO)]
    r = r.dropna(subset=["zona"])
    cl = []
    for z in r.zona.unique():
        df = leer(z)  # ronda 5: lluvia según LLUVIA
        df["anio"] = df.fecha.dt.year
        g = df.groupby("anio").agg(lluvia=("PRECTOTCORR", "sum"), tmax=("T2M_MAX", "mean"), rh=("RH2M", "mean"))
        # ronda 2, eventos: lluvia dic(año-1)-abr(año) y dias calidos en feb-abr (Tmax >= p90 del mismo mes, 2000-2024)
        df["anio_camp"] = df.anio + (df.fecha.dt.month == 12)
        g["lluvia_dic_abr"] = df[df.fecha.dt.month.isin([12, 1, 2, 3, 4])].groupby("anio_camp").PRECTOTCORR.sum()
        p90 = df[df.anio <= 2024].groupby(df.fecha.dt.month).T2M_MAX.quantile(0.9)
        df["calido"] = df.T2M_MAX >= df.fecha.dt.month.map(p90)
        g["dias_calidos_feb_abr"] = df[df.fecha.dt.month.isin([2, 3, 4])].groupby("anio").calido.sum()
        cl.append(g.assign(zona=z).reset_index())
    cl = pd.concat(cl)
    e = pd.read_csv(ET0_MENSUAL)  # climatologia; ET0 anual por año se toma de demanda
    d = r.merge(cl, left_on=["zona", "ANO"], right_on=["zona", "anio"])
    d["log_lluvia"] = np.log1p(d.lluvia)
    ic = pd.read_csv(B.parent / "suelos/datos/clima/clasificacion_campanias_icen.csv")[["anio_lluvias", "icen_max_dic_abr", "enso_costero"]]
    d = d.merge(ic, left_on="ANO", right_on="anio_lluvias", how="left")
    d["log_lluvia_dic_abr"] = np.log1p(d.lluvia_dic_abr)
    BASEX = ["log_lluvia", "tmax", "rh"]
    EVX = BASEX + ["icen_max_dic_abr", "log_lluvia_dic_abr", "dias_calidos_feb_abr"]
    filas, evento = [], []
    for nombre, X in (("clima_v1", BASEX), ("clima_mas_eventos", EVX)):
      for cult, s in d.groupby("cultivo"):
          if s.ANO.nunique() < 5 or len(s) < 30:
              continue
          s = s.reset_index(drop=True)
          # LOYO
          pa, pb = np.full(len(s), np.nan), np.full(len(s), np.nan)
          for y in s.ANO.unique():
              te, tr = s.ANO == y, s.ANO != y
              mu = s[tr].groupby("UBIGEO").rend_t_ha.mean()
              base = s.loc[te, "UBIGEO"].map(mu).fillna(s[tr].rend_t_ha.mean())
              pa[te] = base
              res = s[tr].rend_t_ha - s[tr].UBIGEO.map(mu)
              m = Ridge(alpha=1.0).fit(s.loc[tr, X], res)
              pb[te] = base + m.predict(s.loc[te, X])
          for y in (2017, 2023):
              t = (s.ANO == y).to_numpy()
              if t.any():
                  evento.append(dict(cultivo=cult, variables=nombre, anio=y, n=int(t.sum()),
                                     rend_obs_mediana=float(np.median(s.rend_t_ha[t])),
                                     mae_referencia=float(np.mean(np.abs(pa[t] - s.rend_t_ha[t]))),
                                     mae_con_clima=float(np.mean(np.abs(pb[t] - s.rend_t_ha[t]))),
                                     sesgo_con_clima=float(np.mean(pb[t] - s.rend_t_ha[t]))))
          mae_a, mae_b = np.mean(np.abs(pa - s.rend_t_ha)), np.mean(np.abs(pb - s.rend_t_ha))
          lo, hi = ic_skill(s.rend_t_ha, pa, pb, s.ANO)
          filas.append(dict(cultivo=cult, variables=nombre, esquema="LOYO", n=len(s), anios=s.ANO.nunique(), distritos=s.UBIGEO.nunique(),
                            mae_referencia=mae_a, mae_con_clima=mae_b, skill_pct=(1 - mae_b / mae_a) * 100,
                            skill_ic95_lo=lo, skill_ic95_hi=hi, ic_bloque="anio"))
          # GroupKFold por distrito. Ronda 3 (objecion 1 de Piura Datos): la referencia v2 (media del año en los otros
          # distritos, sin zona) mezclaba zonas; ahora tambien se reporta referencia = media de la zona en ese año (otros
          # distritos de la misma zona), con respaldo media del año. El clima POWER es uno por zona y año, asi que con
          # esta referencia el clima no puede aportar nada nuevo: es la prueba honesta de que GKF no mide clima.
          k = min(5, s.UBIGEO.nunique())
          for ref in ("anio", "zona_anio"):
              pa, pb = np.full(len(s), np.nan), np.full(len(s), np.nan)
              for tr, te in GroupKFold(n_splits=k).split(s, groups=s.UBIGEO):
                  a, b = s.iloc[tr], s.iloc[te]
                  mu_a = b.ANO.map(a.groupby("ANO").rend_t_ha.mean()).fillna(a.rend_t_ha.mean())
                  if ref == "anio":
                      pa[te] = mu_a
                      m = Ridge(alpha=1.0).fit(a[X + ["ANO"]], a.rend_t_ha)
                      pb[te] = m.predict(b[X + ["ANO"]])
                  else:
                      mza = a.groupby(["zona", "ANO"]).rend_t_ha.mean()
                      ka = pd.MultiIndex.from_arrays([a.zona, a.ANO]); kb = pd.MultiIndex.from_arrays([b.zona, b.ANO])
                      ref_b = pd.Series(mza.reindex(kb).values, index=b.index).fillna(mu_a)
                      ref_a = pd.Series(mza.reindex(ka).values, index=a.index)
                      pa[te] = ref_b
                      m = Ridge(alpha=1.0).fit(a[X], a.rend_t_ha - ref_a)
                      pb[te] = ref_b + m.predict(b[X])
              mae_a, mae_b = np.mean(np.abs(pa - s.rend_t_ha)), np.mean(np.abs(pb - s.rend_t_ha))
              lo, hi = ic_skill(s.rend_t_ha, pa, pb, s.UBIGEO)
              filas.append(dict(cultivo=cult, variables=nombre, esquema="GroupKFold_distrito_ref_" + ref, n=len(s), anios=s.ANO.nunique(),
                                distritos=s.UBIGEO.nunique(), mae_referencia=mae_a, mae_con_clima=mae_b, skill_pct=(1 - mae_b / mae_a) * 100,
                                skill_ic95_lo=lo, skill_ic95_hi=hi, ic_bloque="distrito"))
          # Ronda 5 (08:20): partición cruzada distrito x año. No hay datos por chacra; la unidad mínima es distrito-año.
          # Se prueba cada distrito de un pliegue en cada año sin haber visto ni ese distrito ni ese año al entrenar.
          # Referencia = media de la zona en los años de entrenamiento (respaldo: media global de entrenamiento).
          pa, pb = np.full(len(s), np.nan), np.full(len(s), np.nan)
          for tr_d, te_d in GroupKFold(n_splits=k).split(s, groups=s.UBIGEO):
              en_te = np.zeros(len(s), bool); en_te[te_d] = True
              for y in s.ANO[en_te].unique():
                  te = en_te & (s.ANO == y).to_numpy(); tr = ~en_te & (s.ANO != y).to_numpy()
                  if tr.sum() < 5:
                      continue
                  a, b = s[tr], s[te]
                  mz = a.groupby("zona").rend_t_ha.mean()
                  ref_b = b.zona.map(mz).fillna(a.rend_t_ha.mean()); ref_a = a.zona.map(mz)
                  pa[te] = ref_b
                  pb[te] = ref_b + Ridge(alpha=1.0).fit(a[X], a.rend_t_ha - ref_a).predict(b[X])
          ok = ~np.isnan(pa)
          if ok.sum() >= 10:
              mae_a, mae_b = np.mean(np.abs(pa[ok] - s.rend_t_ha[ok])), np.mean(np.abs(pb[ok] - s.rend_t_ha[ok]))
              lo, hi = ic_skill(s.rend_t_ha, pa, pb, s.ANO.astype(str) + "_" + s.UBIGEO.astype(str))
              filas.append(dict(cultivo=cult, variables=nombre, esquema="distrito_x_anio_fuera", n=int(ok.sum()), anios=s.ANO.nunique(),
                                distritos=s.UBIGEO.nunique(), mae_referencia=mae_a, mae_con_clima=mae_b, skill_pct=(1 - mae_b / mae_a) * 100,
                                skill_ic95_lo=lo, skill_ic95_hi=hi, ic_bloque="distrito_anio"))
    out = pd.DataFrame(filas).round(3)
    out["clima"] = CLIMA  # ronda 4
    if ATIPICOS != "crudo":  # ronda 5: solo la comparación de atípicos, sin pisar las salidas de siempre
        out["atipicos"] = ATIPICOS
        out.to_csv(B / f"resultados/validacion_drap_atipicos_{ATIPICOS}.csv", index=False)
        print(out.to_string(index=False))
        return
    out.to_csv(B / "resultados/validacion_drap.csv", index=False)
    out.to_csv(B / f"resultados/validacion_drap_{CLIMA}.csv", index=False)
    out.to_csv(B / f"resultados/validacion_drap_{CLIMA}_{LLUVIA}.csv", index=False)
    print(out.to_string(index=False))
    ev = pd.DataFrame(evento).round(3)
    ev.to_csv(B / "resultados/validacion_eventos_2017_2023.csv", index=False)
    print(ev.to_string(index=False))
    d[["cultivo", "zona", "ANO", "UBIGEO", "rend_t_ha", "icen_max_dic_abr", "enso_costero", "lluvia_dic_abr", "dias_calidos_feb_abr"]].to_csv(B / "resultados/validacion_datos_eventos.csv", index=False)
    # años extremos
    print(d.groupby(["cultivo", "ANO"]).rend_t_ha.median().unstack().round(2).to_string())

if __name__ == "__main__":
    main()
