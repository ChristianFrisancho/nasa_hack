"""Escenarios climáticos por zona y campaña: El Niño costero, La Niña costera, normal y seco.

1. ICEN OFICIAL (ENFEN, Nota Técnica 01-2024) tal como lo publica el IGP:
   http://met.igp.gob.pe/datos/ICEN.txt  (copia en datos/clima/icen_oficial_enfen2024.csv;
   curl falla desde la caja, se obtuvo con tavily_extract el 24-oct-2026). Región Niño 1+2,
   ERSSTv5, media móvil de 3 meses, climatología 1991-2020.
   Se conserva la reconstrucción desde ERSSTv5 de NOAA CPC solo como validación.
2. Categorías mensuales oficiales (NT ENFEN 01-2024, Tabla 2,
   https://enfen.imarpe.gob.pe/download/nota-tecnica-enfen-01-2024-definicion-operacional-de-los-eventos-el-nino-costero-y-la-nina-costera-en-el-peru/?wpdmdl=1905):
   cálida débil >0.5 y <=1.3; moderada >1.3 y <=2.1; fuerte >2.1 y <=3.5; extraordinaria >3.5;
   neutra >=-0.7 y <=0.5; fría débil >=-1.1 y <-0.7; moderada >=-1.3 y <-1.1; fuerte <-1.3.
3. Eventos (NT ENFEN 01-2024, sección 4): El Niño Costero = periodo con condición cálida al menos
   3 meses consecutivos; La Niña Costera = condición fría al menos 3 meses consecutivos.
   Magnitud del evento = la mayor alcanzada durante el evento. Se buscan en toda la serie mensual,
   no dentro de una ventana (el error de la versión anterior: con ventana nov-abr, el evento 2023,
   que empezó en feb-mar, quedaba con 2 meses y la campaña 2022-23 salía "neutra").
4. Año-campaña Y = agosto de Y-1 a julio de Y. Campaña El Niño (La Niña) si algún mes de
   dic(Y-1)-abr(Y), la temporada de lluvias de Piura, pertenece a un evento El Niño (La Niña) costero.
   Regla operativa nuestra, no del ENFEN (el ENFEN define eventos, no campañas): al menos 2 de los
   5 meses dic-abr dentro del evento; si hay meses de ambos, gana el que tiene más.
   magnitud_evento = magnitud oficial de todo el evento; magnitud_en_campania = categoría del ICEN
   extremo en los meses del evento que caen en ago(Y-1)-jul(Y). Subescenario extraordinario:
   campaña El Niño con magnitud_en_campania extraordinaria (control: 1982-83 y 1997-98).
   Seco: campaña no-Niño con lluvia dic-abr <= P20 de la zona (1982-2025). Normal: el resto.
   El ONI (Niño 3.4, Pacífico central, NOAA CPC) se reporta solo como contraste; no clasifica.
Salidas en datos/clima/.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "datos")
CL = os.path.join(D, "clima")

# --- 1. ICEN reconstruido
e = pd.read_csv(os.path.join(CL, "ersst5_nino_mth_91-20.ascii"), sep=r"\s+")
e = e[["YR", "MON", "NINO1+2"]].rename(columns={"YR": "year", "MON": "month", "NINO1+2": "sst"})
anoms = []
for y, g in e.groupby("year"):
    if y >= 2006:
        b0, b1 = 1991, 2020
    else:
        b = 1951 + 5 * ((y - 1951) // 5)
        b0, b1 = max(b - 15, 1950), b + 14  # ERSST de CPC empieza en 1950: antes de 1966 la base se recorta
    clim = e[(e.year >= b0) & (e.year <= b1)].groupby("month").sst.mean()
    anoms.append(g.sst.values - clim.loc[g.month].values)
e["anom"] = np.concatenate(anoms)
e["icen"] = e["anom"].rolling(3, center=True).mean().round(2)

oficial = {(1983, 6): 4.32, (1998, 1): 3.49, (2017, 3): 1.31, (2023, 6): 2.57, (1987, 4): 1.63,
           (1997, 12): 4.06, (2010, 10): -1.25, (1992, 4): 1.99, (2002, 3): 0.57, (1985, 5): -1.18,
           (2026, 3): 0.96, (2026, 4): 1.34, (2026, 5): 1.98, (2025, 11): -0.50}
chk = [(y, m, v, float(e[(e.year == y) & (e.month == m)].icen.iloc[0])) for (y, m), v in oficial.items()]
chk = pd.DataFrame(chk, columns=["year", "month", "icen_oficial_igp", "icen_reconstruido"])
chk["dif"] = (chk.icen_reconstruido - chk.icen_oficial_igp).round(2)
chk.to_csv(os.path.join(CL, "icen_validacion.csv"), index=False)

ICEN_URL = "http://met.igp.gob.pe/datos/ICEN.txt"
NT_URL = "https://enfen.imarpe.gob.pe/download/nota-tecnica-enfen-01-2024-definicion-operacional-de-los-eventos-el-nino-costero-y-la-nina-costera-en-el-peru/?wpdmdl=1905"
P = {"calida_debil": 0.5, "calida_moderada": 1.3, "calida_fuerte": 2.1, "calida_extraordinaria": 3.5,
     "fria_debil": -0.7, "fria_moderada": -1.1, "fria_fuerte": -1.3}

def cat(v):
    if pd.isna(v): return ""
    if v > 3.5: return "calida_extraordinaria"
    if v > 2.1: return "calida_fuerte"
    if v > 1.3: return "calida_moderada"
    if v > 0.5: return "calida_debil"
    if v < -1.3: return "fria_fuerte"
    if v < -1.1: return "fria_moderada"
    if v < -0.7: return "fria_debil"
    return "neutra"

of = pd.read_csv(os.path.join(CL, "icen_oficial_enfen2024.csv")).rename(columns={"anio": "year", "mes": "month"})
val = of.merge(e[["year", "month", "icen"]].rename(columns={"icen": "icen_reconstruido"}), on=["year", "month"], how="left")
val["dif"] = (val.icen_reconstruido - val.icen).round(2)
chk = pd.DataFrame([dict(n_meses=int(val.dif.notna().sum()), dif_abs_max=val.dif.abs().max(), dif_abs_media=round(val.dif.abs().mean(), 3))])
chk.to_csv(os.path.join(CL, "icen_validacion.csv"), index=False)

e = of.sort_values(["year", "month"]).reset_index(drop=True)
e["categoria"] = e.icen.apply(cat)
e["signo"] = np.where(e.icen > 0.5, 1, np.where(e.icen < -0.7, -1, 0))
run = (e.signo != e.signo.shift()).cumsum()
e["evento"] = ""
eventos = []
for _, g in e.groupby(run):
    s0 = g.signo.iloc[0]
    if s0 != 0 and len(g) >= 3:
        tipo = "el_nino_costero" if s0 == 1 else "la_nina_costera"
        ext = g.icen.max() if s0 == 1 else g.icen.min()
        nombre = f"{tipo}_{g.year.iloc[0]}{g.month.iloc[0]:02d}"
        e.loc[g.index, "evento"] = nombre
        en_curso = bool(g.index[-1] == e.index[-1])
        eventos.append(dict(evento=nombre, tipo=tipo, inicio=f"{g.year.iloc[0]}-{g.month.iloc[0]:02d}",
                            fin=f"{g.year.iloc[-1]}-{g.month.iloc[-1]:02d}" + (" (en curso)" if en_curso else ""),
                            meses=len(g), icen_extremo=ext, magnitud=cat(ext).split("_")[1], fuente_url=ICEN_URL, regla_url=NT_URL))
ev = pd.DataFrame(eventos)
ev.to_csv(os.path.join(CL, "eventos_enso_costero_icen_oficial.csv"), index=False)
e[["year", "month", "icen", "categoria", "evento"]].to_csv(os.path.join(CL, "icen_oficial_categorias.csv"), index=False)
mag = ev.set_index("evento").magnitud
pd.DataFrame([P]).to_csv(os.path.join(CL, "icen_umbrales_oficiales.csv"), index=False)

# ONI (Niño 3.4) de CPC, sólo como contraste
oni = pd.read_csv(os.path.join(CL, "oni.ascii.txt"), sep=r"\s+")
seas = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
oni["month"] = oni.SEAS.map({s: i + 1 for i, s in enumerate(seas)})

def run3(mask):
    c = best = 0
    for v in mask:
        c = c + 1 if v else 0
        best = max(best, c)
    return best

rows = []
for Y in range(1982, 2027):
    w = e[((e.year == Y - 1) & (e.month == 12)) | ((e.year == Y) & (e.month <= 4))]
    wc = e[((e.year == Y - 1) & (e.month >= 8)) | ((e.year == Y) & (e.month <= 7))]
    o = oni[((oni.YR == Y - 1) & (oni.month == 12)) | ((oni.YR == Y) & (oni.month <= 4))]
    nino = w[w.evento.str.startswith("el_nino")]; nina = w[w.evento.str.startswith("la_nina")]
    if len(nino) >= 2 and len(nino) >= len(nina):
        enso, evn = "el_nino", nino.evento.iloc[0]
    elif len(nina) >= 2:
        enso, evn = "la_nina", nina.evento.iloc[0]
    else:
        enso, evn = "neutro", ""
    rows.append(dict(campania=f"{Y-1}-{Y}", anio_lluvias=Y, enso_costero=enso, evento_icen=evn,
                     magnitud_evento=mag.get(evn, ""),
                     magnitud_en_campania=(cat(wc[wc.evento == evn].icen.max()) if enso == "el_nino" else cat(wc[wc.evento == evn].icen.min())) if evn else "",
                     meses_evento_en_dic_abr=len(nino) if enso == "el_nino" else len(nina),
                     icen_max_dic_abr=w.icen.max(), icen_min_dic_abr=w.icen.min(),
                     categoria_max_dic_abr=cat(w.icen.max()) if enso != "la_nina" else cat(w.icen.min()),
                     icen_max_ago_jul=wc.icen.max(), n_meses_icen=int(w.icen.notna().sum()),
                     oni_pacifico_central_max_dic_abr=o.ANOM.max(), oni_pacifico_central_min_dic_abr=o.ANOM.min(),
                     fuente_icen=ICEN_URL, regla=NT_URL))
camp = pd.DataFrame(rows)

# --- 2. Lluvia por zona y campaña (repo, NASA POWER)
m = pd.read_csv(os.path.join(D, "repo_nasa_hack", "clima_piura_mensual_1981_2025.csv"))
m["zona"] = m.zone.str.replace(" - referencia regional", "", regex=False)
m["camp_y"] = np.where(m.month >= 8, m.year + 1, m.year)
m["lluvias"] = m.month.isin([12, 1, 2, 3, 4])
g = m.groupby(["zona", "camp_y"])
z = pd.DataFrame({"meses": g.size(),
                  "lluvia_campania_mm": g.rain_mm.sum(),
                  "lluvia_dic_abr_mm": m[m.lluvias].groupby(["zona", "camp_y"]).rain_mm.sum(),
                  "tmean_campania_c": g.Tmean_C.mean(),
                  "et0_campania_mm": g.ET0_approx_mm.sum(min_count=12)}).reset_index()
z = z[z.meses == 12].rename(columns={"camp_y": "anio_lluvias"})
z = z.merge(camp[["anio_lluvias", "campania", "enso_costero", "evento_icen", "magnitud_evento", "magnitud_en_campania", "icen_max_dic_abr", "oni_pacifico_central_max_dic_abr"]], on="anio_lluvias")
z["p20_dic_abr_zona"] = z.groupby("zona").lluvia_dic_abr_mm.transform(lambda s: s.quantile(0.2))
z["escenario"] = np.select(
    [z.enso_costero == "el_nino", z.lluvia_dic_abr_mm <= z.p20_dic_abr_zona],
    ["el_nino", "seco"], default=np.where(z.enso_costero == "la_nina", "la_nina", "normal"))
# CHIRPS como contraste si ya está extraído
cp = os.path.join(CL, "chirps_mensual_zonas.csv")
if os.path.exists(cp):
    c = pd.read_csv(cp)
    c["camp_y"] = np.where(c.month >= 8, c.year + 1, c.year)
    c = c[c.month.isin([12, 1, 2, 3, 4])].groupby(["zona", "camp_y"]).agg(chirps_dic_abr_mm=("rain_mm", "sum"), n=("rain_mm", "count")).reset_index()
    c = c[c.n == 5].rename(columns={"camp_y": "anio_lluvias"}).drop(columns="n")
    z = z.merge(c, on=["zona", "anio_lluvias"], how="left")
z["subescenario"] = np.where((z.escenario == "el_nino") & (z.magnitud_en_campania == "calida_extraordinaria"), "el_nino_extraordinario", z.escenario)
z.round(2).to_csv(os.path.join(CL, "campanias_por_zona.csv"), index=False)
camp.round(2).to_csv(os.path.join(CL, "clasificacion_campanias_icen.csv"), index=False)

def q(s, p): return s.quantile(p)
agg = {"lluvia_dic_abr_mm": ["count", "mean", "min", lambda s: q(s, .1), "median", lambda s: q(s, .9), "max"],
       "lluvia_campania_mm": ["mean", lambda s: q(s, .1), lambda s: q(s, .9)],
       "tmean_campania_c": ["mean", "min", "max"],
       "et0_campania_mm": ["mean", "min", "max"]}
zz = pd.concat([z, z[z.subescenario == "el_nino_extraordinario"].assign(escenario="el_nino_extraordinario")])
r = zz.groupby(["zona", "escenario"]).agg(agg)
r.columns = ["n_campanias", "lluvia_dic_abr_media", "lluvia_dic_abr_min", "lluvia_dic_abr_p10", "lluvia_dic_abr_mediana",
             "lluvia_dic_abr_p90", "lluvia_dic_abr_max", "lluvia_campania_media", "lluvia_campania_p10", "lluvia_campania_p90",
             "tmean_media", "tmean_min", "tmean_max", "et0_media", "et0_min", "et0_max"]
r = r.reset_index()
r["campanias"] = r.apply(lambda x: " ".join(zz[(zz.zona == x.zona) & (zz.escenario == x.escenario)].campania), axis=1)
r["fuente"] = "NASA POWER (repo nasa_hack, clima_piura_mensual_1981_2025.csv); ICEN oficial ENFEN NT 01-2024 (" + ICEN_URL + "), eventos segun seccion 4 de la NT"
r["estado"] = "estimado"; r["tipo_evidencia"] = "regional"
r["notas"] = "Celda POWER ~0.5x0.625 grados; lluvia de reanalisis, no de estacion. n pequeno en la_nina y el_nino_extraordinario: rango poco robusto"
r.round(1).to_csv(os.path.join(CL, "escenarios_clima_por_zona.csv"), index=False)
print("validacion reconstruccion vs oficial:", chk.to_dict("records"))
print(ev[ev.inicio >= "1981"].to_string(index=False))
print(camp[["campania", "enso_costero", "evento_icen", "magnitud_evento", "magnitud_en_campania", "meses_evento_en_dic_abr", "icen_max_dic_abr", "categoria_max_dic_abr", "oni_pacifico_central_max_dic_abr"]].to_string(index=False))
cols = ["zona", "escenario", "n_campanias", "lluvia_dic_abr_mediana", "lluvia_dic_abr_p10", "lluvia_dic_abr_p90", "tmean_media", "et0_media"]
print(r[cols].round(0).to_string(index=False))
if "chirps_dic_abr_mm" in z:
    print(z.groupby(["zona", "escenario"])[["lluvia_dic_abr_mm", "chirps_dic_abr_mm"]].median().round(0).to_string())
    print(z[z.anio_lluvias.isin([1983, 1998, 2017])][["zona", "campania", "lluvia_dic_abr_mm", "chirps_dic_abr_mm"]].round(0).to_string(index=False))
