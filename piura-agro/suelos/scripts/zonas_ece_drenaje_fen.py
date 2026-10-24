"""CSV por zona de ECe, drenaje y eventos FEN 2017/2023 (prioridad 05:36 UTC).
Junta salidas ya calculadas (HWSD v2, EMSR199) con cifras verificadas a mano en fuentes citadas.
Columnas del CONTRATO.md más zona y resolucion; 'notas' lleva la advertencia.
Salida: datos/zonas_ece_drenaje_fen.csv
"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contrato import a_contrato  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "datos")
ZONAS = {  # misma definicion que ece_drenaje_hwsd.py y fen2017_emsr199.py (lon_min, lat_min, lon_max, lat_max)
    "Valle del Chira": (-81.0, -5.0, -80.5, -4.75), "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
    "Medio Piura": (-80.7, -5.2, -80.45, -5.0), "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
    "Alto Piura": (-80.25, -5.45, -79.85, -5.0), "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
    "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05)}

HWSD = "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip"
WC = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
EMS = "https://mapping.emergency.copernicus.eu/activations/EMSR199/"
INDECI = "https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201802271714541.pdf"
AGRO = "https://agropress.pe/noticias/lluvias-en-piura-generaron-perdidas-de-mas-de-230-millones-de-soles-en-sector-agrario/"
FRONT = "https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2025.1672107/full"
SECH = "https://doi.org/10.70747/cr.v5i2.1147"
SIAR = "https://siar.regionpiura.gob.pe/documentos/normativa/584.pdf"
ANA75 = "https://hdl.handle.net/20.500.12543/1510"
ANA90 = "https://hdl.handle.net/20.500.12543/1535"
EVENTOS = "datos/clima/eventos_enso_costero_icen_oficial.csv (ICEN oficial http://met.igp.gob.pe/datos/ICEN.txt)"

rows = []
def add(zona, variable, valor, vmin, vmax, unidad, resolucion, periodo, fuente, url, metodo, tipo, estado, notas, lat="", lon=""):
    if zona in ZONAS and lat == "":
        b = ZONAS[zona]; lon = round((b[0] + b[2]) / 2, 3); lat = round((b[1] + b[3]) / 2, 3)
    if valor != "" and vmin == "" and vmax == "":
        notas += ". Sin rango: la fuente da una cifra unica"
    rows.append(dict(zona=zona, variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo="", variedad="", etapa="",
                     lugar=zona, lat=lat, lon=lon, resolucion=resolucion, fecha_o_periodo=periodo, fuente=fuente, url_o_doi=url,
                     metodo=metodo, tipo_evidencia=tipo, estado=estado, notas=notas))

h = pd.read_csv(os.path.join(D, "ece_drenaje_hwsd_por_zona.csv"))
f17 = pd.read_csv(os.path.join(D, "fen", "fen2017_emsr199_por_zona.csv")).set_index("zona")
for _, r in h.iterrows():
    z = r.zona; caja = "caja " + str(ZONAS[z])
    baja = "BAJA REPRESENTATIVIDAD, NO USAR COMO VALOR CENTRAL: contradice FAO/UNALM 1990, SIAR 584 y ANA (ver filas locales). " if z == "Bajo Piura" else ("Representatividad dudosa: el Medio Piura comparte napa somera con el Bajo Piura (estudio ANA de napa Bajo y Medio Piura). " if z == "Medio Piura" else "")
    met = f"HWSD v2 SMU x componente (SHARE), ponderado por ha de cultivo WorldCover 2021 dentro de {caja}; rango = Q05-Q95 entre pixeles de cultivo"
    add(z, "ECe_0_20cm", r.ec_d1_media, r.ec_d1_q05, r.ec_d1_q95, "dS/m", "~1 km (30 arcsec), unidad cartografica 1:5 000 000", "HWSD v2 2023 (datos de perfiles de decadas previas)",
        "FAO/IIASA HWSD v2.0, capa D1", HWSD, met, "regional", "estimado",
        baja + "Valor por transferencia taxonomica, no medicion. No resuelve parcelas ni bolsones salinos; " + ("subestima con claridad: el repo (SIAR 584, 1:50 000) documenta Aquisalids/Haplosalids y Sechura mide CE ~10 dS/m. " if z == "Bajo Piura" else "") + "Q95 de 4.3 viene de SMU 18789 (Solonchak 30 %). SMU: " + r.smu_principales[:200])
    add(z, "ECe_40_60cm", r.ec_d3_media, r.ec_d3_q05, r.ec_d3_q95, "dS/m", "~1 km, 1:5 000 000", "HWSD v2 2023", "FAO/IIASA HWSD v2.0, capa D3", HWSD, met, "regional", "estimado",
        baja + "Por transferencia taxonomica. Subsuelo; no refleja napa salina actual.")
    add(z, "fraccion_suelo_salino_EC_ge_4", r.p_sal_media, r.p_sal_q05, r.p_sal_q95, "fraccion 0-1", "~1 km, 1:5 000 000", "HWSD v2 2023", "FAO/IIASA HWSD v2.0", HWSD,
        met + "; fraccion de componentes con EC D1 >= 4 dS/m", "regional", "estimado", baja + "Indicador de presencia de suelos salinos en la unidad, no de area salina medida.")
    add(z, "ECe_medida_local", "", "", "", "dS/m", "", "", "", "", "", "medicion_local", "desconocido",
        "No se encontro medicion publica de ECe por pasta saturada en esta zona. Pistas sin verificar: " + ("ANA 1975 Chira, 7 394 ha con salinidad o mal drenaje (" + ANA75 + ")" if z == "Valle del Chira" else ("FAO/ANA 1990 SIG drenaje y salinidad Bajo Piura (" + ANA90 + "); 75 % del area agricola del Bajo Piura con sales segun Santayana 2012 (slideshare, sin verificar en fuente primaria)" if z == "Bajo Piura" else "ninguna")))
    add(z, "fraccion_drenaje_imperfecto_o_pobre", r.p_mal_media, r.p_mal_q05, r.p_mal_q95, "fraccion 0-1", "~1 km, 1:5 000 000", "HWSD v2 2023", "FAO/IIASA HWSD v2.0, DRAINAGE", HWSD,
        met + "; fraccion de componentes con clase I, P o VP", "regional", "estimado",
        baja + "Clase de drenaje del perfil tipo (deriva de la clasificacion del suelo y textura), no de la napa. Bajo y Medio Piura salen 0 y eso contradice el mal drenaje documentado (drenes D-1000 a D-7000); no usar como ausencia de riesgo.")
    add(z, "profundidad_napa_freatica", "", "", "", "m", "", "", "", ANA90 if z in ("Bajo Piura", "Medio Piura") else (ANA75 if z == "Valle del Chira" else ""), "", "medicion_local", "desconocido",
        ("Sin dato accesible: repositorio ANA no respondio (curl, WebFetch y Tavily). Criterio ANA 1975: normal >1.5 m, imperfecto 0.8-1.5 m, pobre 0.3-0.8 m (sin verificar en el PDF)." if z in ("Valle del Chira", "Bajo Piura", "Medio Piura") else "Sin dato.")
        + (" ACTUALIZADO: rango de napa en datos/profundidad_ph_por_zona.csv (profundidad_napa_estacional)." if z in ("Bajo Piura", "Medio Piura") else ""))
    # FEN 2017 EMSR199
    g = f17.loc[z]
    if g.cobertura_aoi_pct < 5:  # cobertura despreciable: no se reporta cifra
        add(z, "area_inundada_FEN2017", "", "", "", "ha", "", "2017-03-23/30", "Copernicus EMS EMSR199", EMS, "AOI de EMSR199 cubre <5 % de la caja", "regional", "desconocido",
            f"EMSR199 cubre {g.cobertura_aoi_pct} % de la caja. Desconocido no significa cero" + ("; en sierra el peligro principal fue huaico y deslizamiento, no inundacion de llanura" if z.startswith("Sierra") else "") + ".")
        add(z, "cultivo_inundado_FEN2017", "", "", "", "ha", "", "2017-03", "Copernicus EMS EMSR199", EMS, "Sin AOI", "regional", "desconocido", "Sin mapeo.")
    else:
        cota = "" if g.cobertura_aoi_pct >= 99 else f"; solo {g.cobertura_aoi_pct} % de la caja cubierto por los AOI: cota inferior"
        add(z, "area_inundada_FEN2017", g.inundado_ha, g.inundado_ha, "", "ha", "radar COSMO-SkyMed, Radarsat-2, Sentinel-1; mapas 1:25 000-1:100 000", "2017-03-23/30",
            "Copernicus EMS EMSR199 (crisis_information Flooded Area)", EMS, "Union de poligonos de inundacion de todos los productos, interseccion con la caja", "regional", "observado",
            "Instantanea de las fechas de imagen, no area maxima del evento" + cota)
        add(z, "cultivo_inundado_FEN2017", g.cultivo_inundado_ha, g.cultivo_inundado_ha, "", "ha", "~30 m (WorldCover remuestreado) x poligonos EMS", "2017-03",
            "EMSR199 x ESA WorldCover 2021 clase 40", EMS + " ; " + WC, "Interseccion area inundada con cultivo WorldCover", "regional", "estimado",
            f"{g.cultivo_inundado_pct} % del cultivo de la caja. WorldCover es de 2021, posterior al evento" + cota)
for zona, km in [("Sechura", 10), ("Bajo Piura", 19.3), ("San Lorenzo", 40), ("Valle del Chira", 31)]:
    add(zona, "infraestructura_riego_rehabilitada_FEN2023", km, "", "", "km", "Junta de Usuarios", "2023 (temporada de lluvias, ciclon Yaku y El Nino costero)",
        "DRA Piura via Agropress", AGRO, "Declaracion del director regional de Agricultura", "regional", "observado",
        ("Junta Medio y Bajo Piura (cubre ambas zonas). " if zona == "Bajo Piura" else "") + ("Sechura dice 'mas de 10 km'. " if zona == "Sechura" else "") + "Proxy de dano, no area afectada; nota de prensa sin documento tecnico")
for z in ZONAS:
    add(z, "cultivo_perdido_FEN2023", "", "", "", "ha", "", "2023", "", "", "", "regional", "desconocido",
        "No hay activacion Copernicus EMS para Peru en 2023 (verificado en la API) ni desagregado publico por zona; solo cifra departamental")
dep = dict(lat=-5.2, lon=-80.6)
add("Departamento Piura", "cultivo_afectado_FEN2017", 15342, "", "", "ha", "departamento", "2017 (El Nino costero moderado, ene-abr 2017)", "INDECI Compendio Estadistico 2017, p.15", INDECI, "Registro EDAN", "regional", "observado", "Nacional: 91 906 ha afectadas", **dep)
add("Departamento Piura", "cultivo_perdido_FEN2017", 8733, "", "", "ha", "departamento", "2017", "INDECI Compendio Estadistico 2017, p.15", INDECI, "Registro EDAN", "regional", "observado", "Nacional: 39 705 ha perdidas", **dep)
add("Departamento Piura", "caudal_pico_rio_Piura_FEN2017", 3800, "", "", "m3/s", "estacion", "2017-03-27", "INDECI Compendio 2017, p.28", INDECI, "Reporte", "regional", "observado", "Afecto todo el Bajo Piura. Una cifra de 2 325 m3/s en redes sociales no coincide; se usa INDECI", **dep)
add("Departamento Piura", "area_inundada_FEN2017", 163720, "", "", "ha", "satelital", "2017", "Frontiers in Environmental Science 2025", FRONT, "Mapeo satelital del articulo (1 637.2 km2)", "bibliografico", "estimado", "Distinto de EMSR199 (59 705 ha dentro de los AOI): otro metodo y cobertura", **dep)
add("Departamento Piura", "cultivo_afectado_FEN2023", 14973, "", "", "ha", "departamento", "2023 (El Nino costero fuerte mar-2023 a feb-2024 + ciclon Yaku)", "DRA Piura via Agropress", AGRO, "Declaracion oficial", "regional", "observado", "Nota de prensa; cifra preliminar", **dep)
add("Departamento Piura", "cultivo_perdido_FEN2023", 13651, "", "", "ha", "departamento", "2023", "DRA Piura via Agropress", AGRO, "Declaracion oficial", "regional", "observado", "Nota de prensa; cifra preliminar", **dep)
add("Sechura", "CE_suelo_0_30cm", 9.98, 9.86, 10.10, "dS/m", "1 calicata", "2024-08", "Ciencia y Reflexion v5 n2 (2024)", SECH, "Extracto 1:2.5, no pasta saturada; rango = +-1 DE", "medicion_local", "observado",
    "Zona agraria Sol Sol; un solo perfil. Con extracto diluido la ECe real seria mayor. pH 4.87-5.14", lat=-5.558, lon=-80.821)
add("Sechura", "CE_suelo_70_100cm", 8.37, 8.28, 8.46, "dS/m", "1 calicata", "2024-08", "Ciencia y Reflexion v5 n2 (2024)", SECH, "Extracto 1:2.5", "medicion_local", "observado", "Mismo perfil", lat=-5.558, lon=-80.821)
add("Bajo Piura", "ECe_unidades_suelo_repo", "", "", "", "dS/m", "1:50 000", "circa 2005", "SIAR 584 (via repo suelos_bajo_piura_unidades_v2.csv)", SIAR, "", "regional", "desconocido",
    "El repo tiene las unidades (Pajarito Aquisalids, Ramon Haplosalids...) pero el campo ECe esta vacio; falta leer las tablas del PDF")
# Fuentes locales del Bajo Piura (revision cruzada de agronomia r1, 05:57 UTC): mandan sobre HWSD
ERH = "https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf"
add("Bajo Piura", "ECe_suelo_superficial_rango_local", "", 1.2, 12, "dS/m", "valle (mosaico de unidades 1:50 000)", "1990-2024",
    "FAO/UNALM 1990 (SIG drenaje y salinidad Bajo Piura); SIAR 584; Sechura 2024", ANA90 + " ; " + SIAR + " ; " + SECH,
    "Rango armado con fuentes locales: minimo = unidades no salinas (Palo Verde, Piura; HWSD Q05 1.2); maximo = clase 4-12 mmhos/cm de FAO/UNALM 1990; Sechura 9.98 (1:2.5) cae dentro", "regional", "estimado",
    "VALOR CENTRAL DE ESTA ZONA. Sin valor central: la ECe varia por unidad y la fraccion de area por clase no esta disponible (solo se leyo un extracto de FAO/UNALM 1990). Para una parcela, pedir ECe por pasta saturada. Puede superar 12 en Aquisalids (Pajarito) y Haplosalids (Ramon)")
add("Bajo Piura", "ECe_clase_salina_FAO_UNALM_1990", "", 4, 12, "dS/m", "SIG del estudio (escala no verificada)", "1990",
    "FAO/UNALM 1990, estudio de drenaje y salinidad del Bajo Piura", ANA90, "Clases de salinidad del suelo en mmhos/cm (= dS/m)", "regional", "observado",
    "Segun la revision cruzada (extracto): 'buena parte del area' en esta clase; hectareas por clase no leidas. Yo no pude abrir el handle (timeout); dato de segunda mano, no verificado por este agente")
add("Bajo Piura", "clase_drenaje_local", "imperfecto a pobre (napa somera y salina)", "", "", "clase", "valle", "1990-2025",
    "FAO/UNALM 1990; SIAR 584 (Aquisalids); ANA ERH Piura", ANA90 + " ; " + ERH, "Descripcion cualitativa de fuentes locales", "regional", "estimado",
    "Reemplaza a la clase HWSD (bien drenado) como valor de trabajo. Falta la fraccion de area por clase y la profundidad de napa medida")
add("Bajo Piura", "CE_agua_subterranea", "", 0.04, 16.83, "dS/m", "pozos IRHS", "estudio ERH ANA (fecha no verificada)",
    "ANA, Evaluacion de recursos hidricos Piura, tomos I-II", ERH, "Inventario de pozos; publicado en mmhos/cm", "medicion_local", "observado",
    "Abarca Medio y Bajo Piura (maximo IRHS-68 Catacaos). Es agua de napa, no suelo; indica aporte de sales por ascenso capilar. Cifra tomada por el agente de restricciones de un fragmento Tavily; el PDF no abre desde la caja (TLS). 0.04 es inusualmente bajo")
for zz in ["Bajo Piura", "Medio Piura", "Valle del Chira", "San Lorenzo", "Alto Piura"]:
    add(zz, "profundidad_napa_minima_recomendada_salinidad", 2.0, "", "", "m", "criterio general", "FAO-29 (1985)",
        "FAO Irrigation and Drainage Paper 29 rev.1 (Ayers y Westcot)", "https://www.fao.org/4/t0234e/t0234e00.htm",
        "Criterio de manejo: en zona arida con napa salina mantener la napa a >= 2 m", "bibliografico", "estimado",
        "Criterio citado por la revision cruzada de agronomia; no lo verifique en el texto de FAO-29. Umbral para evitar salinizacion por ascenso capilar; distinto del umbral de aireacion de 0.8-0.9 m (FAO-62). No es un dato medido de la zona")
out = pd.DataFrame(rows)
a_contrato(out).to_csv(os.path.join(D, "zonas_ece_drenaje_fen.csv"), index=False)
print(out.groupby(["estado"]).size()); print(len(out))
