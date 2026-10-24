"""FEN 2017 y 2023 por zona (ronda 8, prioridad 3) -> datos/fen_por_zona.csv (CONTRATO) y datos/fen/ingemmet_flujos_por_zona.csv.
Fuentes:
- INDECI IE 607 (05/06/2017) e IE 2186 (27/07/2023): ha de cultivo afectado y perdido por distrito (datos/fen/indeci_cultivos_*_distrito.csv),
  sumadas por zona con datos/distrito_zona.csv (cruce por provincia + distrito, abreviaturas de INDECI expandidas).
- UNOSAT 2023 (mapa Lambayeque-Piura, 22-mar y 1-abr-2023): km2 de agua detectada por provincia -> ha.
- INGEMMET GEOCATMIN, inventario de peligros geológicos: flujos (huaicos, TIP_PELIGRO 1000|1500) por zona vía UBIGEO.
- Consistencia con datos/clima/clasificacion_campanias_icen.csv (2016-2017 moderada, 2022-2023 fuerte por ICEN).
No inventa: si la provincia viene en 0 en todos sus distritos (Piura 2017), la zona queda como cota inferior o desconocido."""
import os, pandas as pd, numpy as np
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(B, "datos")
DZ = pd.read_csv(os.path.join(D, "distrito_zona.csv"), dtype=str)
DZ["k"] = DZ.provincia.str.upper() + "|" + DZ.distrito.str.upper()
ABR = {"S. J. DE BIGOTE": "SAN JUAN DE BIGOTE", "STA. C. DE MOSSA": "SANTA CATALINA DE MOSSA", "S. M. DE EL FAIQUE": "SAN MIGUEL DE EL FAIQUE",
       "EL C. DE LA FRONTERA": "EL CARMEN DE LA FRONTERA", "BELLAV. DE LA UNION": "BELLAVISTA DE LA UNION"}
SRC = {2017: ("INDECI, Informe de Emergencia N° 607 - 05/06/2017 (COEN), Piura, cuadro de daños por distrito",
              "https://portal.indeci.gob.pe/ (IE 607-2017; copia local suelos/fuentes/fen/indeci_ie607_2017.pdf)"),
       2023: ("INDECI, Informe de Emergencia N° 2186 - 27/07/2023 (COEN), Lluvias intensas Piura, cuadro de daños por distrito",
              "https://portal.indeci.gob.pe/ (IE 2186-2023; copia local suelos/fuentes/fen/indeci_ie2186_2023.pdf)")}
ZONAS = ["chira", "san_lorenzo", "medio_piura", "bajo_piura", "alto_piura", "sierra_piura"]  # Talara (piura_region) fuera: 0 en ambos años y sin zona agrícola propia


def indeci(yr):
    t = pd.read_csv(os.path.join(D, "fen", f"indeci_cultivos_{yr}_distrito.csv"))
    prov, out = None, []
    for r in t.itertuples():
        if r.nivel == "PROV": prov = r.nombre; continue
        if r.nivel != "DIST": continue
        d = ABR.get(r.nombre, r.nombre)
        k = f"{prov}|{d}"
        m = DZ[DZ.k == k]
        assert len(m) == 1, f"{yr}: sin cruce {k}"
        out.append(dict(anio=yr, provincia=prov, distrito=d, zona=m.zona.iloc[0], afectado=r.cultivo_afectado_ha, perdido=r.cultivo_perdido_ha))
    o = pd.DataFrame(out)
    falt = set(DZ.k) - set(o.provincia + "|" + o.distrito)
    return o, falt


rows, det = [], []
for yr in (2017, 2023):
    o, falt = indeci(yr); det.append(o)
    provs0 = [p for p, g in o.groupby("provincia") if (g.afectado + g.perdido).sum() == 0]
    fuente, url = SRC[yr]
    for z in ZONAS:
        g = o[o.zona == z]
        if g.empty: continue
        ceros = sorted(set(g.provincia) & set(provs0))
        dist_cero = g[g.provincia.isin(ceros)].distrito.tolist()
        for var, col in (("cultivo_afectado", "afectado"), ("cultivo_perdido", "perdido")):
            s = round(float(g[col].sum()), 1)
            detalle = "; ".join(f"{r.distrito} {r[col]:g}" for _, r in g[g[col] > 0].iterrows()) or "todos los distritos en 0"
            todo_cero = len(dist_cero) == len(g)
            nota = (f"Suma de {len(g)} distritos de la zona ({', '.join(sorted(g.distrito))}). Distritos con valor: {detalle}. ")
            if todo_cero:
                val, vmin, est = "", "", "desconocido"
                nota += (f"Todos los distritos de la zona están en provincias ({', '.join(ceros)}) que el informe reporta íntegramente en 0, "
                         "lo que en un año con desborde del río Piura (27-mar-2017) indica falta de registro, no ausencia de daño. Sin rango porque no hay dato.")
            elif dist_cero:
                val, vmin, est = "", s, "estimado"
                nota += (f"Cota inferior: {len(dist_cero)} distritos ({', '.join(dist_cero)}) pertenecen a provincias ({', '.join(ceros)}) "
                         "reportadas íntegramente en 0 (falta de registro probable), así que la cifra real es mayor. Sin máximo publicado.")
            else:
                val, vmin, est = s, "", "observado"
                nota += "Cifra de registro EDAN acumulada a la fecha del informe; sin rango porque el informe no da incertidumbre."
            ausentes = sorted(k.split("|")[1] for k in falt if DZ.set_index("k").zona.get(k) == z)
            if ausentes: nota += f" Distritos de la zona que no aparecen en el cuadro del informe (sin registro): {', '.join(ausentes)}."
            if yr == 2017 and z == "bajo_piura" and col in ("afectado", "perdido"):
                nota += (" Ojo: VICE aporta 10 000 ha afectadas y 5 000 perdidas, cifras redondas y mayores que todo el resto del departamento juntas en "
                         "perdidas; sospechosas de estimación gruesa municipal. Sin VICE la suma sería "
                         f"{round(float(g[g.distrito != 'VICE'][col].sum()), 1)} ha.")
            rows.append(dict(variable=f"{var}_FEN{yr}", valor=val, valor_min=vmin, valor_max="", unidad="ha", zona=z,
                             lugar=f"Distritos de la zona {z} (datos/distrito_zona.csv)", fecha_o_periodo=("2017-01-05/2017-03-30 (corte 05-jun-2017)" if yr == 2017 else "2023-01/2023-05 (corte 27-jul-2023)"),
                             fuente=fuente, url_o_doi=url, metodo="Suma por zona de las ha por distrito del cuadro de daños INDECI (EDAN/SINPAD); cruce distrito-zona por provincia y nombre",
                             tipo_evidencia="regional", estado=est, notas=nota, resolucion="distrito agregado a zona", representatividad="zona"))
    if falt: print(yr, "distritos del mapa sin fila INDECI:", sorted(falt))

# UNOSAT 2023: agua detectada por provincia (km2 -> ha). Incluye cuerpos de agua y lagunas temporales; no es área de cultivo.
UN = [("Sechura", "bajo_piura", 566, 604, 4812, 4925, ""), ("Piura", "", 14, 13, 3037, 2900, "medio_piura;bajo_piura;san_lorenzo"),
      ("Morropon", "alto_piura", 2, 1, 1323, 374, "")]
for prov, z, a1, a2, s1, s2, za in UN:
    lo, hi = min(a1, a2) * 100, max(a1, a2) * 100
    rows.append(dict(variable="area_inundada_FEN2023", valor="", valor_min=lo, valor_max=hi, unidad="ha", zona=z, zonas_aplicables=za,
                     lugar=f"Provincia {prov} (parte analizada sin nubes: {s1:,} km² el 22-mar y {s2:,} km² el 1-abr)".replace(",", " "),
                     fecha_o_periodo="2023-03-22 y 2023-04-01", fuente="UNITAR/UNOSAT, 'Satellite detected water extents over Lambayeque and Piura provinces' (abr-2023), tabla por provincia",
                     url_o_doi="https://unosat.org/products/ (copia local suelos/fuentes/fen/unosat_2023_lambayeque_piura.pdf)",
                     metodo="Agua detectada en Sentinel-1/2 en dos fechas; km² × 100 = ha; rango = las dos fechas",
                     tipo_evidencia="regional", estado="observado",
                     notas=(f"Publicado {a1} km² (22-mar) y {'<1' if prov == 'Morropon' and a2 == 1 else a2} km² (1-abr). Incluye toda el agua superficial detectada (lagunas, "
                            "esteros y la laguna La Niña/Ramón en Sechura), no solo cultivo inundado; parte del área no se pudo analizar por nubes, así que es cota inferior del área inundada. "
                            + ("Provincia de Piura abarca Medio Piura, Bajo Piura (Catacaos, Cura Mori, El Tallán, La Arena, La Unión) y San Lorenzo (Tambogrande, Las Lomas): no se puede repartir. " if prov == "Piura" else "")
                            + ("Morropón: 1-abr publicado como '<1'; se usa 1 como techo. " if prov == "Morropon" else "")),
                     resolucion="provincia (Sentinel ~10-20 m)", representatividad="zona" if z else "regional"))

# INGEMMET: flujos por zona
ig = pd.read_csv(os.path.join(B, "fuentes", "ingemmet", "peligros_geologicos_bbox_piura.csv"), dtype=str)
ig = ig[ig.NM_DPTO == "Piura"].copy()
ig["zona"] = ig.UBIGEO.map(dict(zip(DZ.ubigeo, DZ.zona)))
ig["anio"] = pd.to_datetime(pd.to_numeric(ig.FECHA, errors="coerce"), unit="ms", errors="coerce").dt.year
fl = ig[ig.TIP_PELIGRO == "1000|1500"]
tab = pd.DataFrame({"peligros_total": ig.groupby("zona").size(), "flujos_huaicos": fl.groupby("zona").size(),
                    "flujos_fechados_2017": fl[fl.anio == 2017].groupby("zona").size(), "flujos_fechados_2023": fl[fl.anio == 2023].groupby("zona").size()}).fillna(0).astype(int)
tab["anio_min_inventario"] = ig.groupby("zona").anio.min(); tab["anio_max_inventario"] = ig.groupby("zona").anio.max()
tab["sin_ubigeo_en_mapa"] = ig.zona.isna().sum()
tab.to_csv(os.path.join(D, "fen", "ingemmet_flujos_por_zona.csv"))
print(tab)
for z, r in tab.iterrows():
    rows.append(dict(variable="huaicos_inventariados_INGEMMET", valor="sí" if r.flujos_huaicos > 0 else "no", valor_min="", valor_max="", unidad="categoría", zona=z,
                     lugar=f"Distritos de la zona {z}", fecha_o_periodo=f"inventario {int(r.anio_min_inventario)}-{int(r.anio_max_inventario)} (fecha de registro)",
                     fuente="INGEMMET, GEOCATMIN, inventario de peligros geológicos (capa de peligros), filtrado a Piura",
                     url_o_doi="https://geocatmin.ingemmet.gob.pe/ (copia local suelos/fuentes/ingemmet/peligros_geologicos_bbox_piura.csv)",
                     metodo="Conteo de registros TIP_PELIGRO 1000|1500 (movimientos en masa tipo flujo: huaicos, flujos de detritos) por UBIGEO de distrito",
                     tipo_evidencia="regional", estado="observado",
                     notas=(f"Categorías permitidas: sí/no (hay al menos un flujo inventariado en la zona). Conteo: {r.flujos_huaicos} flujos de {r.peligros_total} peligros inventariados; "
                            f"fechados en 2017: {r.flujos_fechados_2017}; en 2023: {r.flujos_fechados_2023}. La fecha es de registro en el inventario, no del evento; por autor, la mayoría son estudios INGEMMET 2003-2004 y no es un registro por evento, "
                            "así que no sirve para ha de cultivo perdidas por huaico en 2017 o 2023; indica dónde hay quebradas activas. Detalle en datos/fen/ingemmet_flujos_por_zona.csv."),
                     resolucion="punto de inventario agregado a zona", representatividad="zona"))

# Consistencia con ICEN y totales departamentales
icen = pd.read_csv(os.path.join(D, "clima", "clasificacion_campanias_icen.csv")).set_index("anio_lluvias")
dep = {yr: (round(det[i].afectado.sum(), 1), round(det[i].perdido.sum(), 1)) for i, yr in enumerate((2017, 2023))}
cons = (f"ICEN: 2016-2017 = {icen.loc[2017, 'magnitud_evento']} (máx dic-abr {icen.loc[2017, 'icen_max_dic_abr']}); 2022-2023 = {icen.loc[2023, 'magnitud_evento']} "
        f"(máx dic-abr {icen.loc[2023, 'icen_max_dic_abr']}). Suma INDECI por distrito: 2017 {dep[2017][0]} ha afectadas / {dep[2017][1]} perdidas (sin la provincia de Piura, reportada en 0, "
        f"y con VICE 10 000/5 000); 2023 {dep[2023][0]} / {dep[2023][1]}. Otras cifras departamentales de 2017: INDECI boletín ago-2017 15 342/8 733; "
        "DRA Piura 28 000 afectadas/2 800 perdidas (América TV); CIE-PerúCámaras con datos MINAGRI 22 915/4 591. "
        "Lectura: 2017 tuvo más ha afectadas en la región pese a ICEN 'moderada', porque el daño de 2017 vino de lluvias locales extremas y del desborde del río Piura "
        "(3 800 m³/s el 27-mar); 2023 'fuerte' tuvo más ha perdidas. El ICEN (Niño 1+2) no ordena por sí solo el daño agrícola en Piura: no usarlo como único proxy de pérdidas.")
rows.append(dict(variable="consistencia_FEN_ICEN", valor="parcial", valor_min="", valor_max="", unidad="categoría", zona="piura_region", lugar="Departamento de Piura",
                 fecha_o_periodo="2016-2017 y 2022-2023", fuente="Este análisis: INDECI IE 607/2017 e IE 2186/2023; datos/clima/clasificacion_campanias_icen.csv (IGP ICEN); INDECI boletín 2017; CIE-PerúCámaras 2017",
                 url_o_doi="http://met.igp.gob.pe/datos/ICEN.txt ; https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201708091706381.pdf ; https://diariocorreo.pe/economia/nino-costero-provoco-perdida-de-mas-de-29-mil-hectareas-de-cultivos-744400/",
                 metodo="Comparación cualitativa de magnitud ICEN con ha afectadas/perdidas", tipo_evidencia="regional", estado="estimado",
                 notas="Categorías permitidas: sí/no/parcial (¿el orden de daño coincide con el orden de magnitud ICEN?). " + cons,
                 resolucion="departamento", representatividad="regional"))
for yr, (lo, hi, src) in {2017: ((13960, 28000), (2800, 8733), "IE 607 (suma distrital), INDECI boletín ago-2017, DRA Piura, CIE-PerúCámaras/MINAGRI")}.items():
    rows.append(dict(variable="cultivo_afectado_FEN2017", valor="", valor_min=13960, valor_max=28000, unidad="ha", zona="piura_region", lugar="Departamento de Piura",
                     fecha_o_periodo="2016-12/2017-04", fuente="INDECI IE 607 (05/06/2017); INDECI boletín estadístico ago-2017; DRA Piura (América TV 2017); CIE-PerúCámaras 2017 (datos MINAGRI)",
                     url_o_doi="https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201708091706381.pdf ; https://www.americatv.com.pe/noticias/actualidad/piura-lluvias-y-desbordes-ocasionaron-perdida-s-220-millones-cultivos-n271771 ; https://diariocorreo.pe/economia/nino-costero-provoco-perdida-de-mas-de-29-mil-hectareas-de-cultivos-744400/",
                     metodo="Rango entre cuatro cifras oficiales o de prensa con fuente oficial", tipo_evidencia="regional", estado="observado",
                     notas="13 960 (IE 607, suma distrital sin provincia de Piura), 15 342 (INDECI ago-2017), 22 915 (CIE/MINAGRI), 28 000 (DRA Piura). Las fuentes no concuerdan; usar el rango.",
                     resolucion="departamento", representatividad="regional"))
    rows.append(dict(variable="cultivo_perdido_FEN2017", valor="", valor_min=2800, valor_max=8733, unidad="ha", zona="piura_region", lugar="Departamento de Piura",
                     fecha_o_periodo="2016-12/2017-04", fuente="INDECI IE 607 (05/06/2017); INDECI boletín estadístico ago-2017; DRA Piura (América TV 2017); CIE-PerúCámaras 2017 (datos MINAGRI)",
                     url_o_doi="https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201708091706381.pdf ; https://www.americatv.com.pe/noticias/actualidad/piura-lluvias-y-desbordes-ocasionaron-perdida-s-220-millones-cultivos-n271771 ; https://diariocorreo.pe/economia/nino-costero-provoco-perdida-de-mas-de-29-mil-hectareas-de-cultivos-744400/",
                     metodo="Rango entre cuatro cifras", tipo_evidencia="regional", estado="observado",
                     notas="2 800 (DRA Piura), 4 591 (CIE/MINAGRI; 2 823 de arroz), 7 822 (IE 607 suma distrital, con VICE 5 000), 8 733 (INDECI ago-2017).",
                     resolucion="departamento", representatividad="regional"))
out = pd.DataFrame(rows)
cols = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi",
        "metodo", "tipo_evidencia", "estado", "notas", "zonas_aplicables", "resolucion", "representatividad"]
for c in cols:
    if c not in out: out[c] = ""
out[cols].to_csv(os.path.join(D, "fen_por_zona.csv"), index=False)
pd.concat(det).to_csv(os.path.join(D, "fen", "indeci_cultivos_distrito_zona.csv"), index=False)
print(out[["variable", "zona", "valor", "valor_min", "valor_max", "estado"]].to_string())
print(cons)
