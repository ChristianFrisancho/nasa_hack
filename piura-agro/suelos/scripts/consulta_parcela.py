"""Ficha de territorio para una parcela de Piura: clima por escenario ENSO costero, suelo, pendiente y peligros.

Uso:
  .venv/bin/python scripts/consulta_parcela.py --lat -5.27 --lon -80.67 --nombre catacaos
  .venv/bin/python scripts/consulta_parcela.py --poligono ejemplos/parcela_catacaos.geojson --nombre parcela_catacaos
Salida: ejemplos/<nombre>.csv (formato CONTRATO.md + modulo, resolucion, advertencia_escala) y ejemplos/<nombre>.json.

Fuentes (todas publicas, sin clave):
  clima     NASA POWER mensual (PRECTOTCORR_SUM, T2M) en la celda de la parcela; campañas ago-jul clasificadas
            con el ICEN oficial (datos/clima/clasificacion_campanias_icen.csv, NT ENFEN 01-2024).
  suelo     SoilGrids 2.0 (250 m) Q05 / media / Q95, 0-30 cm ponderado por espesor; HWSD v2 (1 km) para drenaje y ECe solo como contexto (contradice CE medida en chacra);
            contexto por zona de datos/zonas_ece_drenaje_fen.csv (fuentes locales mandan sobre HWSD en el Bajo Piura).
  pendiente Copernicus DEM GLO-30 (COG en AWS); punto: pixel y anillo de 150 m; poligono: media, p90 y % sobre 2/5/15 %.
  peligros  INGEMMET GEOCATMIN (susceptibilidad a inundacion fluvial 50 m, a movimientos en masa 200 m, peligros
            geologicos inventariados a <1 km) y CENEPRED (riesgo por inundacion por distrito, tabla en datos/peligros).
Cada fila lleva estado observado/estimado/desconocido; si un servicio falla, la fila queda 'desconocido' con el error.
"""
import argparse, json, math, os, time, urllib.parse
import numpy as np, pandas as pd, rasterio, requests, urllib3
from rasterio.windows import from_bounds
from rasterio.merge import merge
from rasterio.features import geometry_mask
from shapely.geometry import shape, Point, mapping

urllib3.disable_warnings()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "datos")
GEO = "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services"
ICEN_NT = "https://enfen.imarpe.gob.pe/download/nota-tecnica-enfen-01-2024-definicion-operacional-de-los-eventos-el-nino-costero-y-la-nina-costera-en-el-peru/?wpdmdl=1905"
ZONAS = {  # mismas cajas que ece_drenaje_hwsd.py
    "Valle del Chira": (-81.0, -5.0, -80.5, -4.75), "San Lorenzo": (-80.55, -5.05, -80.2, -4.75),
    "Medio Piura": (-80.7, -5.2, -80.45, -5.0), "Bajo Piura": (-80.85, -5.55, -80.55, -5.2),
    "Alto Piura": (-80.25, -5.45, -79.85, -5.0), "Sierra Ayabaca": (-79.9, -4.8, -79.5, -4.45),
    "Sierra Huancabamba": (-79.6, -5.45, -79.3, -5.05)}
ZONA_COD = {"Valle del Chira": "chira", "San Lorenzo": "san_lorenzo", "Medio Piura": "medio_piura", "Bajo Piura": "bajo_piura",
            "Alto Piura": "alto_piura", "Sierra Ayabaca": "sierra_piura", "Sierra Huancabamba": "sierra_piura"}
# orden de CONTRATO.md; columnas extra al final
COLS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
        "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas",
        "modulo", "subzona", "resolucion", "advertencia_escala"]
S = requests.Session(); S.headers["User-Agent"] = "piura-agro-hackathon/1.0"


class Ficha:
    def __init__(self, lugar, lat, lon, zona="", subzona=""):
        self.rows, self.lugar, self.lat, self.lon = [], lugar, lat, lon
        self.zona, self.subzona = zona, subzona

    def add(self, modulo, variable, valor="", vmin="", vmax="", unidad="", resolucion="", fecha="", fuente="", url="",
            metodo="", tipo="", estado="estimado", escala="", notas=""):
        self.rows.append(dict(modulo=modulo, variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad,
                              cultivo="", variedad="", etapa="", zona=self.zona, subzona=self.subzona, lugar=self.lugar, lat=round(self.lat, 5), lon=round(self.lon, 5),
                              resolucion=resolucion, fecha_o_periodo=fecha, fuente=fuente, url_o_doi=url, metodo=metodo,
                              tipo_evidencia=tipo, estado=estado, advertencia_escala=escala, notas=notas))

    def fallo(self, modulo, variable, fuente, url, err):
        self.add(modulo, variable, fuente=fuente, url=url, tipo="prediccion" if modulo == "clima" else "regional",
                 estado="desconocido", notas=f"FALLO al consultar el servicio: {str(err)[:200]}")


def get(url, tries=3, **kw):
    for i in range(tries):
        try:
            r = S.get(url, timeout=60, **kw); r.raise_for_status(); return r
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(5 * (i + 1))


LIMITES = os.path.join(D, "limites", "distritos_piura_inei.geojson")
LIMITES_URL = f"{GEO}/SERV_CARTOGRAFIA_DEMARCACION_WGS84/MapServer/2"
_DIST = None


def _distritos():
    """Polígonos de distrito de Piura (INEI 2024 vía GEOCATMIN), en caché local; se bajan si faltan."""
    global _DIST
    if _DIST is None:
        if not os.path.exists(LIMITES):
            os.makedirs(os.path.dirname(LIMITES), exist_ok=True)
            r = get(LIMITES_URL + "/query", params={"where": "CD_DEPA='20'", "outFields": "CD_DIST,NM_DIST,NM_PROV,FUENTE,FEC_ING",
                                                    "outSR": 4326, "f": "geojson", "maxAllowableOffset": 0.0005}, verify=False)
            open(LIMITES, "w").write(r.text)
        gj = json.load(open(LIMITES))
        _DIST = [(shape(ft["geometry"]), ft["properties"]) for ft in gj["features"]]
    return _DIST


def _subzona(cod, lon, lat):
    """Caja de datos por zona (subzona) para un código: la que contiene el punto, o la más cercana con ese código."""
    cajas = {z: b for z, b in ZONAS.items() if ZONA_COD[z] == cod}
    if not cajas: return ""
    for z, (w, s, e, n) in cajas.items():
        if w <= lon <= e and s <= lat <= n: return z
    return min(cajas, key=lambda z: math.hypot(lon - (cajas[z][0] + cajas[z][2]) / 2, lat - (cajas[z][1] + cajas[z][3]) / 2))


def zona_de(lon, lat):
    """Zona del CONTRATO por polígono de distrito (INEI) cruzado con datos/distrito_zona.csv.
    Devuelve dict: zona (código), subzona (caja de datos), distrito, ubigeo, ambiguo, zona_alternativa, metodo."""
    pt = Point(lon, lat)
    try:
        hit = next((p for g, p in _distritos() if g.covers(pt)), None)
    except Exception as e:
        hit, err = None, e
    else:
        err = None
    if hit is not None:
        dz = pd.read_csv(os.path.join(D, "distrito_zona.csv"), dtype={"ubigeo": str})
        r = dz[dz.ubigeo == str(hit["CD_DIST"])]
        if not r.empty:
            r = r.iloc[0]
            alt = "" if pd.isna(r.zona_alternativa) else str(r.zona_alternativa)
            amb = str(r.ambiguo)
            return dict(zona=r.zona, subzona=_subzona(r.zona, lon, lat), distrito=hit["NM_DIST"], provincia=hit["NM_PROV"], ubigeo=hit["CD_DIST"],
                        ambiguo=amb, zona_alternativa=alt if amb != "no" else "", criterio=str(r.criterio),
                        metodo="Polígono de distrito INEI (GEOCATMIN) + datos/distrito_zona.csv", dentro=True)
    # respaldo: cajas (fuera de Piura o sin límites)
    for z, (w, s, e, n) in ZONAS.items():
        if w <= lon <= e and s <= lat <= n:
            return dict(zona=ZONA_COD[z], subzona=z, distrito="", provincia="", ubigeo="", ambiguo="", zona_alternativa="", criterio="",
                        metodo="Respaldo: caja de zona que contiene el punto" + (f" (límites no disponibles: {str(err)[:80]})" if err else " (punto fuera de los distritos de Piura)"), dentro=True)
    d = {z: math.hypot(lon - (b[0] + b[2]) / 2, lat - (b[1] + b[3]) / 2) for z, b in ZONAS.items()}
    z = min(d, key=d.get)
    return dict(zona=ZONA_COD[z], subzona=z, distrito="", provincia="", ubigeo="", ambiguo="", zona_alternativa="", criterio="",
                metodo="Respaldo: caja más cercana; el punto no cae en ningún distrito de Piura ni en ninguna caja", dentro=False)


# ---------------- clima ----------------
def clima(f, lat, lon, area):
    url = ("https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=PRECTOTCORR_SUM,T2M&community=AG"
           f"&longitude={lon:.4f}&latitude={lat:.4f}&start=1981&end=2025&format=JSON")
    try:
        p = get(url).json()["properties"]["parameter"]
    except Exception as e:
        return f.fallo("clima", "lluvia_dic_abr", "NASA POWER", url, e)
    m = pd.DataFrame({"ym": list(p["PRECTOTCORR_SUM"].keys()), "pp": list(p["PRECTOTCORR_SUM"].values()), "t": list(p["T2M"].values())})
    m = m[~m.ym.str.endswith("13")]
    m["y"], m["mo"] = m.ym.str[:4].astype(int), m.ym.str[4:].astype(int)
    m = m[(m.pp >= 0)]
    m["camp"] = np.where(m.mo >= 8, m.y + 1, m.y)
    g = m.groupby("camp")
    c = pd.DataFrame({"n": g.size(), "pp_camp": g.pp.sum(), "t_camp": g.t.mean(),
                      "pp_da": m[m.mo.isin([12, 1, 2, 3, 4])].groupby("camp").pp.sum()}).reset_index()
    c = c[c.n == 12].rename(columns={"camp": "anio_lluvias"})
    k = pd.read_csv(os.path.join(D, "clima", "clasificacion_campanias_icen.csv"))
    c = c.merge(k[["anio_lluvias", "campania", "enso_costero", "magnitud_en_campania"]], on="anio_lluvias")
    p20 = c.pp_da.quantile(0.2)
    c["esc"] = np.select([c.enso_costero == "el_nino", c.pp_da <= p20], ["el_nino", "seco"],
                         default=np.where(c.enso_costero == "la_nina", "la_nina", "normal"))
    extra = c[(c.esc == "el_nino") & (c.magnitud_en_campania == "calida_extraordinaria")].assign(esc="el_nino_extraordinario")
    per = f"campañas {c.campania.min()} a {c.campania.max()}"
    adv = "Celda POWER ~0.5x0.625 grados (~55x70 km): una sola celda para toda la parcela" + (" y alrededores" if area else "")
    for esc, s in pd.concat([c, extra]).groupby("esc"):
        x = s.pp_da
        nota = f"n={len(s)} campañas ({', '.join(s.campania)}). " if len(s) <= 6 else f"n={len(s)} campañas. "
        nota += "Rango = p10-p90. " if len(s) >= 5 else "Rango = min-max (n<5, poco robusto). "
        nota += "Lluvia de reanálisis (MERRA-2 corregida), no de estación: en la costa POWER supera a CHIRPS por ~10x en años FEN (1997-98: 1394 vs 155 mm en Bajo Piura) y ninguno está validado con estaciones SENAMHI aquí."
        lo, hi = (x.quantile(.1), x.quantile(.9)) if len(s) >= 5 else (x.min(), x.max())
        f.add("clima", f"lluvia_dic_abr_{esc}", round(x.median(), 1), round(lo, 1), round(hi, 1), "mm", "0.5x0.625 grados", per,
              "NASA POWER mensual + ICEN oficial (ENFEN NT 01-2024)", url + " ; " + ICEN_NT,
              "Suma dic-abr por campaña ago-jul; escenario por ICEN (El Niño/La Niña si >=2 meses dic-abr en evento) o seco (<= p20 local, sin El Niño)",
              "prediccion", "estimado", adv, nota)
        f.add("clima", f"temperatura_media_campania_{esc}", round(s.t_camp.median(), 1), round(s.t_camp.min(), 1), round(s.t_camp.max(), 1),
              "°C", "0.5x0.625 grados", per, "NASA POWER T2M", url, "Media ago-jul; rango min-max entre campañas", "prediccion", "estimado", adv,
              f"n={len(s)}. En sierra la celda promedia altitudes muy distintas: corregir por gradiente (~-0.6 °C/100 m) con la cota del DEM")
    f.add("clima", "alerta_el_nino_costero_2026_27", "evento cálido en curso; ICEN ago-2026 = 3.98 (rango extraordinario >3.5)", "", "", "",
          "región Niño 1+2", "2026-03 a 2026-08 (evento abierto)", "IGP ICEN oficial; ENFEN comunicado oficial 18-2026",
          "http://met.igp.gob.pe/datos/ICEN.txt ; https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-18-2026/?wpdmdl=2165",
          "Umbrales NT ENFEN 01-2024", "regional", "observado", "Índice oceánico regional, no lluvia local",
          "Para la campaña 2026-27 usar el escenario el_nino_extraordinario como caso de diseño (n=2 históricos: 1982-83 y 1997-98). La magnitud final depende de los meses dic-abr")
    return c


# ---------------- suelo ----------------
SG_PROPS = {"clay": ("arcilla", "%"), "sand": ("arena", "%"), "silt": ("limo", "%"), "soc": ("carbono_organico", "g/kg"),
            "phh2o": ("pH_agua", "pH"), "cec": ("CIC", "cmol/kg"), "bdod": ("densidad_aparente", "g/cm3"), "nitrogen": ("nitrogeno_total", "g/kg")}
SG_DIV = {"clay": 10, "sand": 10, "silt": 10, "soc": 10, "phh2o": 10, "cec": 10, "bdod": 100, "nitrogen": 100}


HW_URL = "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip"
PROF_CLASE = {1: (1.0, None), 2: (0.5, 1.0), 3: (0.1, 0.5), 4: (0.0, 0.1)}  # D_ROOT_DEPTH de HWSD v2, en m
GRUESA = {"arena", "arena franca", "franco arenoso"}  # franja capilar 0.25-0.43 m (arena media-fina; Lohman 1972, USGS PP 708, Tabla 1)
FINA = {"arcilla", "arcillo limoso", "franco arcillo limoso", "limo", "franco limoso"}  # ~1.06 m (limo 0.1-0.05 mm; Lohman 1972); en limo más fino >2 m


def clima_zona(f, sub):
    """Clima de referencia SENAMHI (PISCO) por zona y sesgo de NASA POWER (datos/clima_por_zona.csv)."""
    p = os.path.join(D, "clima_por_zona.csv")
    if not sub or not os.path.exists(p): return
    z = pd.read_csv(p); z = z[(z.subzona == sub) & (z.estado == "estimado")]
    keep = {"lluvia_dic_abr_normal", "lluvia_dic_abr_nino_1998", "lluvia_dic_abr_nino_2017", "tmedia_ago_jul_normal",
            "sesgo_lluvia_dic_abr_POWER_normal", "sesgo_tmedia_ago_jul_POWER_normal", "sesgo_lluvia_dic_abr_POWER_vs_CHIRPS_nino_2023"}
    g = lambda r, k: "" if pd.isna(getattr(r, k)) else getattr(r, k)
    for r in z[z.variable.isin(keep) & ~z.fuente.str.startswith("CHIRPS")].itertuples():
        f.add("clima", "zona:" + r.variable, r.valor, g(r, "valor_min"), g(r, "valor_max"), r.unidad, r.resolucion, r.fecha_o_periodo, r.fuente,
              r.url_o_doi, r.metodo, r.tipo_evidencia, r.estado, f"Valor de la zona {sub}, no de la parcela", g(r, "notas"))


def cew_zona(f, zona_cod):
    """CEw por zona y fuente de agua (datos/cew_por_zona.csv, scripts/cew_por_zona.py): filas resumen y sin_dato de la zona."""
    p = os.path.join(D, "cew_por_zona.csv")
    if not zona_cod or not os.path.exists(p): return
    z = pd.read_csv(p); z = z[(z.zona == zona_cod) & z.nivel.isin(["resumen", "sin_dato"])]
    g = lambda r, k: "" if pd.isna(getattr(r, k)) else getattr(r, k)
    for r in z.itertuples():
        # en cew_por_zona.csv todas las filas son ce_agua_riego; aquí el sufijo fuente_agua evita filas homónimas en la ficha
        sufijo = f"_{r.fuente_agua}" + ("_tablazo_sur" if str(g(r, "lugar")).startswith("Tablazo") else "")
        f.add("agua", "zona:" + r.variable + sufijo, g(r, "valor"), g(r, "valor_min"), g(r, "valor_max"), r.unidad, g(r, "resolucion"), g(r, "fecha_o_periodo"),
              r.fuente, g(r, "url_o_doi"), r.metodo, r.tipo_evidencia, r.estado,
              f"Valor de la zona {zona_cod} (puntos de muestreo: {g(r, 'lugar')}), no del agua que llega a la parcela", g(r, "notas"))


def textura_usda(sand, clay):
    silt = 100 - sand - clay
    if silt + 1.5 * clay < 15: return "arena"
    if silt + 1.5 * clay < 30: return "arena franca"
    if (7 <= clay < 20 and sand > 52) or (clay < 7 and silt < 50): return "franco arenoso"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52: return "franco"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12): return "franco limoso"
    if silt >= 80 and clay < 12: return "limo"
    if 20 <= clay < 35 and silt < 28 and sand > 45: return "franco arcillo arenoso"
    if 27 <= clay < 40 and 20 < sand <= 45: return "franco arcilloso"
    if 27 <= clay < 40 and sand <= 20: return "franco arcillo limoso"
    if clay >= 35 and sand > 45: return "arcillo arenoso"
    if clay >= 40 and silt >= 40: return "arcillo limoso"
    return "arcilla"


def sg_valido_cercano(lon, lat, radio_m=2000):
    """Píxel SoilGrids (pH 0-5 cm) con dato más cercano al punto, dentro de radio_m. Devuelve (lon, lat, distancia_m) o None."""
    from rasterio.vrt import WarpedVRT
    from rasterio.windows import from_bounds as fb
    d = radio_m / 111320
    with rasterio.open("/vsicurl/https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean.vrt") as s0, WarpedVRT(s0, crs="EPSG:4326") as v:
        w = fb(lon - d, lat - d, lon + d, lat + d, v.transform).round_offsets().round_lengths()
        a = v.read(1, window=w); t = v.window_transform(w)
    rr, cc = np.nonzero(a > 0)
    if not len(rr): return None
    xs, ys = rasterio.transform.xy(t, rr, cc)
    xs, ys = np.array(xs), np.array(ys)
    dist = np.hypot((xs - lon) * 111320 * np.cos(np.radians(lat)), (ys - lat) * 111320)
    i = int(np.argmin(dist))
    return (float(xs[i]), float(ys[i]), float(dist[i])) if dist[i] <= radio_m else None


def suelo(f, lat, lon, zona, area):
    url = ("https://rest.isric.org/soilgrids/v2.0/properties/query?" +
           urllib.parse.urlencode([("lon", f"{lon:.5f}"), ("lat", f"{lat:.5f}")] + [("property", p) for p in SG_PROPS] +
                                  [("depth", d) for d in ["0-5cm", "5-15cm", "15-30cm"]] + [("value", v) for v in ["Q0.05", "mean", "Q0.95"]]))
    adv = "Celda de 250 m; mapa predicho por aprendizaje automático con pocos perfiles en la costa peruana" + ("; consultado solo en el centroide del polígono" if area else "")
    out = {}
    try:
        lay = get(url).json()["properties"]["layers"]
        if all(d["values"]["mean"] is None for L in lay for d in L["depths"]):
            alt = sg_valido_cercano(lon, lat)
            if alt:
                lon2, lat2, dist = alt
                url = url.replace(f"lon={lon:.5f}", f"lon={lon2:.5f}").replace(f"lat={lat:.5f}", f"lat={lat2:.5f}")
                lay = get(url).json()["properties"]["layers"]
                adv += f"; el punto cae en celda enmascarada (urbano/agua): se usó el píxel válido más cercano a {dist:.0f} m ({lat2:.5f}, {lon2:.5f})"
        for L in lay:
            n = L["name"]; vals = {}
            for q in ["Q0.05", "mean", "Q0.95"]:
                xs = [(d["values"][q], d["range"]["bottom_depth"] - d["range"]["top_depth"]) for d in L["depths"]]
                if any(v is None for v, _ in xs): vals[q] = None; continue
                vals[q] = sum(v * w for v, w in xs) / sum(w for _, w in xs) / SG_DIV[n]
            out[n] = vals
            nom, u = SG_PROPS[n]
            if vals["mean"] is None:
                f.add("suelo", f"{nom}_0_30cm", unidad=u, resolucion="250 m", fecha="perfiles 1950-2017, mapa 2020",
                      fuente="ISRIC SoilGrids 2.0", url=url, tipo="prediccion", estado="desconocido", escala=adv,
                      notas="SoilGrids sin dato (celda enmascarada: urbano, agua o arena desnuda)")
                continue
            f.add("suelo", f"{nom}_0_30cm", round(vals["mean"], 2), round(vals["Q0.05"], 2), round(vals["Q0.95"], 2), u, "250 m",
                  "perfiles 1950-2017, mapa 2020", "ISRIC SoilGrids 2.0", url,
                  "Media ponderada por espesor de 0-5, 5-15 y 15-30 cm; rango = Q05-Q95 ponderados (aproximación: no es el cuantil exacto de 0-30 cm)",
                  "prediccion", "estimado", adv, "Modelo QRF de ISRIC; validar con análisis de suelo de la parcela" +
                  (". BAJA CONFIANZA en costa árida (revisión Agronomía H07): el intervalo Q05-Q95 es muy ancho y el único contraste local en el repo "
                   "es MO 1.2 % en Sullana (Atoche 2025, ~7 g/kg de C con factor 1.724, restricciones/evidencia_observada.csv); no derivar N "
                   "disponible de este valor sin análisis de laboratorio" if n in ("soc", "nitrogen") and zona not in ("Sierra Ayabaca", "Sierra Huancabamba") else ""))
    except Exception as e:
        f.fallo("suelo", "SoilGrids_0_30cm", "ISRIC SoilGrids 2.0", url, e)
    if out.get("sand", {}).get("mean") is not None and out.get("clay", {}).get("mean") is not None:
        tx = textura_usda(out["sand"]["mean"], out["clay"]["mean"])
        f.add("suelo", "textura_usda_0_30cm", tx, textura_usda(out["sand"]["Q0.95"], out["clay"]["Q0.05"]),
              textura_usda(out["sand"]["Q0.05"], out["clay"]["Q0.95"]), "clase", "250 m", "mapa 2020", "ISRIC SoilGrids 2.0 (derivado)", url,
              "Triángulo USDA con arena y arcilla medias; min = más arenoso (arena Q95, arcilla Q05), max = más arcilloso", "prediccion", "estimado", adv,
              "Contraste con el repo (SIAR 584 / ZEE Montero) en la fila suelo_repo_unidades")
    # HWSD en el punto
    prof = {}
    try:
        lay = pd.read_csv(os.path.join(D, "hwsd2", "HWSD2_LAYERS.csv"), low_memory=False)
        with rasterio.open(os.path.join(D, "hwsd2", "HWSD2.bil")) as hs:
            smu = int(next(hs.sample([(lon, lat)]))[0])
        l1 = lay[(lay.HWSD2_SMU_ID == smu) & (lay.LAYER == "D1") & (lay.ELEC_COND >= 0)]
        if len(l1):
            w = l1.SHARE.astype(float)
            ec = float(np.average(l1.ELEC_COND, weights=w)); pmal = float(w[l1.DRAINAGE.str.strip().isin(["I", "P", "VP"])].sum() / w.sum())
            comp = "; ".join(f"{r.WRB4} {int(r.SHARE)}% dren {str(r.DRAINAGE).strip()} EC {r.ELEC_COND:g}" for r in l1.itertuples())
            baja = zona == "Bajo Piura"
            nota = ("HWSD contradice CE medida en chacra (fuente: Piura Datos, ver su carpeta en /workspace/piura-agro/restricciones/: "
                    "Bajo Piura 3.44-8.2 frente a 1.51; Chira 0.10 frente a 1.36; Medio 0.95 frente a 2.74; Alto 0.46-0.6 frente a 1.15 dS/m). "
                    "Solo contexto: no usar como ECe; ver zona:ECe_medida_local. ") + ("BAJA REPRESENTATIVIDAD en el Bajo Piura: no usar como valor central (FAO/UNALM 1990 ubica buena parte del área en 4-12 dS/m; SIAR 584 describe Aquisalids). " if baja else "") + f"SMU {smu}: {comp}"
            f.add("suelo", "ECe_0_20cm_HWSD2_contexto", round(ec, 2), round(l1.ELEC_COND.min(), 2), round(l1.ELEC_COND.max(), 2), "dS/m", "30 arcseg (~0.9 km)",
                  "HWSD v2.0 (2023), perfiles tipo antiguos", "FAO/IIASA HWSD v2.0",
                  "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip",
                  "Media ponderada por SHARE de los componentes de la unidad; rango = min-max entre componentes", "regional", "estimado",
                  "Unidad cartográfica de ~1 km con varios suelos; el componente de la parcela no se conoce", nota)
            f.add("suelo", "fraccion_drenaje_imperfecto_o_pobre_HWSD", round(pmal, 2), "", "", "fraccion", "30 arcseg (~0.9 km)", "HWSD v2.0 (2023)",
                  "FAO/IIASA HWSD v2.0", "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip",
                  "Suma de SHARE de componentes con drenaje I, P o VP", "regional", "estimado",
                  "Unidad de ~1 km", ("BAJA REPRESENTATIVIDAD en el Bajo Piura; ver clase_drenaje_local. " if baja else "") + "Sin rango: es una proporción de la unidad, no una medición")
        else:  # H11 (Agronomía): unidad sin EC en D1 (p. ej. Sechura, SMU con suelos sin perfil): declarar el hueco
            f.add("suelo", "ECe_0_20cm_HWSD2_contexto", "", "", "", "dS/m", "30 arcseg (~0.9 km)", "HWSD v2.0 (2023)", "FAO/IIASA HWSD v2.0",
                  "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip",
                  "Capa D1 con ELEC_COND >= 0 en la unidad del punto", "regional", "desconocido", "",
                  f"SMU {smu} sin componentes con CE en HWSD (frecuente en Sechura/desierto costero). Usar zona:ECe_medida_local y zona:ECe_clase_salina_FAO_UNALM_1990")
        # pH y clase de profundidad HWSD en el punto (todos los componentes D1, aunque no tengan EC)
        la = lay[(lay.HWSD2_SMU_ID == smu) & (lay.LAYER == "D1")]
        lp = la[la.PH_WATER > 0]
        if len(lp):
            comp = "; ".join(f"{r.WRB4} {int(r.SHARE)}% pH {r.PH_WATER:g}" for r in lp.itertuples())
            f.add("suelo", "pH_agua_0_20cm_HWSD", round(float(np.average(lp.PH_WATER, weights=lp.SHARE.astype(float))), 2),
                  round(float(lp.PH_WATER.min()), 2), round(float(lp.PH_WATER.max()), 2), "pH", "30 arcseg (~0.9 km)", "HWSD v2.0 (2023)",
                  "FAO/IIASA HWSD v2.0", HW_URL, "Media ponderada por SHARE; rango = min-max entre componentes", "regional", "estimado",
                  "Unidad de ~1 km; el componente de la parcela no se conoce", f"SMU {smu}: {comp}. Contrastar con pH_0_30cm (SoilGrids) y zona:pH_rango_zona")
        lr = la[la.ROOT_DEPTH.isin([1, 2, 3, 4])]
        if len(lr):
            lo_ = min(PROF_CLASE[int(k)][0] for k in lr.ROOT_DEPTH); his = [PROF_CLASE[int(k)][1] for k in lr.ROOT_DEPTH]
            hi_ = None if None in his else max(his)
            prof["fisica"] = (lo_, hi_)
            f.add("suelo", "profundidad_fisica_suelo_HWSD", "", lo_, "" if hi_ is None else hi_, "m", "30 arcseg (~0.9 km)", "HWSD v2.0 (2023)",
                  "FAO/IIASA HWSD v2.0, ROOT_DEPTH", HW_URL, "Unión de las clases ROOT_DEPTH de los componentes (1 >1 m, 2 0.5-1, 3 0.1-0.5, 4 <0.1 m)",
                  "regional", "estimado", "Clase por tipo de suelo en una unidad de ~1 km; no es una medida",
                  "Máximo vacío = >1 m sin cota superior. " + "; ".join(f"{r.WRB4} {int(r.SHARE)}% clase {int(r.ROOT_DEPTH)}" for r in lr.itertuples()))
    except Exception as e:
        f.fallo("suelo", "ECe_0_20cm_HWSD2_contexto", "FAO/IIASA HWSD v2.0", "", e)
    # contexto de zona (ECe local, drenaje, napa, FEN)
    z = pd.read_csv(os.path.join(D, "zonas_ece_drenaje_fen.csv"))
    keep = ["ECe_0_20cm", "CE_agua_riego", "CE_agua_napa", "ECe_suelo_superficial_rango_local", "ECe_clase_salina_FAO_UNALM_1990", "clase_drenaje_local",
            "profundidad_napa_minima_recomendada_salinidad", "ECe_medida_local", "area_inundada_FEN2017",
            "cultivo_inundado_FEN2017", "infraestructura_riego_rehabilitada_FEN2023"]
    for r in z[(z.subzona == zona) & z.variable.isin(keep)].itertuples():
        f.add("suelo" if "FEN" not in r.variable else "peligros", "zona:" + r.variable, "" if pd.isna(r.valor) else r.valor,
              "" if pd.isna(r.valor_min) else r.valor_min, "" if pd.isna(r.valor_max) else r.valor_max, r.unidad, r.resolucion,
              r.fecha_o_periodo, r.fuente, r.url_o_doi, r.metodo, r.tipo_evidencia, r.estado,
              f"Valor de la zona {zona}, no de la parcela", "" if pd.isna(r.notas) else r.notas)
    m = pd.read_csv("/workspace/piura-agro/consolidado/motor/datos_repo/matriz_cultivo_suelo_regional_v2.csv")
    scope = {"Bajo Piura": "Bajo Piura", "Medio Piura": "Bajo Piura", "Sierra Ayabaca": "Montero-Ayabaca"}.get(zona)
    if scope:
        u = m[m.soil_scope == scope].drop_duplicates("soil_map_unit_or_CUM")
        txt = " | ".join(f"{r.soil_map_unit_or_CUM}: {r.soil_information}" for r in u.itertuples())
        f.add("suelo", "suelo_repo_unidades", f"{len(u)} unidades", "", "", "", "1:50 000 a 1:100 000 (estudio)", "estudios SIAR / ZEE",
              "repo nasa_hack: matriz_cultivo_suelo_regional_v2.csv", u.source_soil.iloc[0], "Unidades de suelo del ámbito, sin ubicación de la parcela",
              "regional", "estimado", "El repo no georreferencia unidades: la parcela puede caer en cualquiera",
              "Contraste con SoilGrids: comparar textura_usda_0_30cm con estas texturas. " + txt)
    else:
        f.add("suelo", "suelo_repo_unidades", unidad="", fuente="repo nasa_hack", tipo="regional", estado="desconocido",
              notas=f"El repo no tiene unidades de suelo para la zona {zona}; SoilGrids queda sin contraste local")
    # pH y profundidad por zona (scripts/profundidad_ph_zona.py) + profundidad efectiva en la parcela
    zp = pd.read_csv(os.path.join(D, "profundidad_ph_por_zona.csv"))
    zp = zp[zp.subzona == zona].set_index("variable")
    for v in ["pH_rango_zona", "pH_agua_0_20cm_HWSD2", "pH_agua_0_30cm_SoilGrids", "profundidad_napa_estacional", "profundidad_napa_sector_somero_FAO1990", "profundidad_napa_SEV_ANA2015",
              "nivel_estatico_pozos_ANA2014", "fraccion_area_napa_menor_2m", "cumple_napa_2m_FAO29", "fraccion_puntos_cumple_napa_2m_FAO29", "profundidad_efectiva_enraizamiento"]:
        if v in zp.index:
            r = zp.loc[v]
            g = lambda k: "" if pd.isna(r[k]) else r[k]
            f.add("suelo", "zona:" + v, g("valor"), g("valor_min"), g("valor_max"), r.unidad, g("resolucion"), g("fecha_o_periodo"), r.fuente,
                  g("url_o_doi"), g("metodo"), r.tipo_evidencia, r.estado, f"Valor de la zona {zona}, no de la parcela", g("notas"))
    tx = textura_usda(out["sand"]["mean"], out["clay"]["mean"]) if out.get("sand", {}).get("mean") is not None and out.get("clay", {}).get("mean") is not None else None
    fr = (0.25, 0.43) if tx in GRUESA else (1.06, 1.06) if tx in FINA else (0.43, 1.06)  # Lohman 1972, USGS PP 708, Tabla 1
    fis = prof.get("fisica")
    napa = zp.loc["profundidad_napa_estacional"] if "profundidad_napa_estacional" in zp.index else None
    nmin = None if napa is None or pd.isna(napa.valor_min) else float(napa.valor_min)
    nmax = None if napa is None or pd.isna(napa.valor_max) else float(napa.valor_max)
    base = (f"min(profundidad física HWSD en el punto, napa estacional de la zona - franja capilar {fr[0]}-{fr[1]} m por textura SoilGrids "
            f"'{tx or 'sin dato'}'; franja según Lohman 1972, USGS PP 708, Tabla 1, doi 10.3133/pp708)")
    if fis is None:
        f.add("suelo", "profundidad_efectiva_enraizamiento", unidad="m", fuente="HWSD v2.0 + napa de zona", tipo="regional", estado="desconocido",
              metodo=base, notas="Sin clase de profundidad HWSD en el punto")
    else:
        lo_, hi_ = fis
        if nmin is not None and nmax is not None and nmin < 2:
            e_lo = max(0.0, min(lo_, nmin - fr[1])); e_hi = nmax - fr[0] if hi_ is None else min(hi_, nmax - fr[0])
            nota = (f"Napa de zona {nmin:g}-{nmax:g} m ({napa.metodo}; {napa.fuente}). El límite inferior 0 significa napa en superficie en la época húmeda o en "
                    "años FEN; la napa real de la parcela no se conoce: medirla con un pozo de observación (barreno a 2 m) antes de decidir.")
            f.add("suelo", "profundidad_efectiva_enraizamiento", "", round(e_lo, 2), round(e_hi, 2), "m", "mezcla: HWSD ~0.9 km y napa de valle",
                  "HWSD 2023; napa: " + str(napa.fecha_o_periodo), "HWSD v2.0 + " + str(napa.fuente), HW_URL + " ; " + str(napa.url_o_doi), base,
                  "regional", "estimado", "Intervalo de zona aplicado a la parcela; no es una medida de la parcela", nota)
        else:
            nota = ("Napa conocida profunda en la zona (pozos 15-38 m); manda la profundidad física. " if nmin is not None else
                    "Napa desconocida en la zona: el intervalo es solo la profundidad física y es una cota superior. ")
            f.add("suelo", "profundidad_efectiva_enraizamiento", "", lo_, "" if hi_ is None else hi_, "m", "30 arcseg (~0.9 km)", "HWSD 2023",
                  "FAO/IIASA HWSD v2.0, ROOT_DEPTH", HW_URL, base, "regional", "estimado", "Clase de profundidad por tipo de suelo, no medida",
                  nota + "Máximo vacío = >1 m sin cota superior. En ladera, la erosión puede dejar suelos más someros que la clase HWSD.")
    return out


# ---------------- pendiente ----------------
def dem_tiles(w, s, e, n):
    out = []
    for la in range(math.floor(s), math.floor(n) + 1):
        for lo in range(math.floor(w), math.floor(e) + 1):
            name = f"Copernicus_DSM_COG_10_{'S' if la < 0 else 'N'}{abs(la):02d}_00_{'W' if lo < 0 else 'E'}{abs(lo):03d}_00_DEM"
            out.append(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif")
    return out


def pendiente(f, lat, lon, geom):
    buf = 0.004
    b = geom.bounds if geom is not None else (lon, lat, lon, lat)
    bb = (b[0] - buf, b[1] - buf, b[2] + buf, b[3] + buf)
    url = dem_tiles(*bb)
    try:
        srcs = [rasterio.open(u) for u in url]
        z, tr = merge(srcs, bounds=bb); z = z[0].astype(float)
        for s_ in srcs: s_.close()
    except Exception as e:
        return f.fallo("pendiente", "pendiente", "Copernicus DEM GLO-30", ";".join(u.replace('/vsicurl/', '') for u in url), e)
    dy = abs(tr.e) * 111320; dx = tr.a * 111320 * math.cos(math.radians(lat))
    gy, gx = np.gradient(z, dy, dx)
    sl = np.hypot(gx, gy) * 100
    rows, cols = z.shape
    src = "Copernicus DEM GLO-30 (ESA/Airbus), COG en AWS"
    u0 = url[0].replace("/vsicurl/", "")
    adv = "DEM de 30 m (modelo de superficie: incluye árboles y edificios); no resuelve bordos, surcos ni nivelación de la parcela"
    if geom is None:
        r, c = rasterio.transform.rowcol(tr, lon, lat)
        yy, xx = np.ogrid[:rows, :cols]
        ring = ((yy - r) * dy) ** 2 + ((xx - c) * dx) ** 2 <= 150 ** 2
        v = sl[ring]
        s0 = float(sl[r, c])
        f.add("pendiente", "pendiente_punto", round(s0, 1), round(min(s0, float(np.percentile(v, 10))), 1), round(max(s0, float(np.percentile(v, 90))), 1),
              "%", "1 arcseg (~30 m)", "adquisición 2011-2015", src, u0,
              "Gradiente por diferencias centrales; rango = p10-p90 en un radio de 150 m, ampliado para incluir el píxel central", "prediccion", "estimado", adv,
              "Error vertical del DEM ~2-4 m: pendientes <1 % no se distinguen de cero")
        z0 = float(z[r, c])
        f.add("pendiente", "cota", round(z0, 0), round(min(z0, float(np.percentile(z[ring], 10))), 0), round(max(z0, float(np.percentile(z[ring], 90))), 0),
              "m s.n.m.", "1 arcseg (~30 m)", "adquisición 2011-2015", src, u0, "Valor del píxel; rango p10-p90 a 150 m", "prediccion", "estimado", adv, "")
    else:
        mask = ~geometry_mask([mapping(geom)], out_shape=z.shape, transform=tr, all_touched=False)
        v = sl[mask]
        if v.size == 0:
            return f.add("pendiente", "pendiente_poligono", estado="desconocido", fuente=src, url=u0, notas="El polígono no contiene centros de píxel de 30 m")
        common = dict(resolucion="1 arcseg (~30 m)", fecha="adquisición 2011-2015", fuente=src, url=u0, tipo="prediccion", estado="estimado", escala=adv)
        f.add("pendiente", "pendiente_media", round(float(v.mean()), 1), round(float(np.percentile(v, 10)), 1), round(float(np.percentile(v, 90)), 1), "%",
              metodo=f"Media de {v.size} píxeles dentro del polígono; rango p10-p90", notas="Error vertical ~2-4 m", **common)
        f.add("pendiente", "pendiente_p90", round(float(np.percentile(v, 90)), 1), unidad="%", metodo="Percentil 90 dentro del polígono",
              notas="Sin rango: es un estadístico del polígono", **common)
        for t in (2, 5, 15):
            f.add("pendiente", f"porcentaje_area_pendiente_mayor_{t}pct", round(float((v > t).mean() * 100), 1), unidad="%",
                  metodo=f"Fracción de píxeles con pendiente > {t} % (2: límite riego por gravedad/inundación; 5: surcos con control de erosión; 15: laderas)",
                  notas="Sin rango; con pocos píxeles (<20) el porcentaje es muy inestable" if v.size < 20 else "Sin rango: es un conteo de píxeles", **common)
        f.add("pendiente", "cota_media", round(float(z[mask].mean()), 0), round(float(z[mask].min()), 0), round(float(z[mask].max()), 0), "m s.n.m.",
              metodo="Media, min y max dentro del polígono", notas="", **common)


# ---------------- peligros ----------------
SUS = [("SERV_IMG_SUSCEP_INUN_FLUVIAL", "susceptibilidad_inundacion_fluvial", "50 m", 4),
       ("SERV_IMG_SUSCEP_MOV_MASA", "susceptibilidad_movimientos_masa", "200 m", 5)]


def peligros(f, lat, lon, geom):
    pts = [(lon, lat)]
    if geom is not None:
        w, s, e, n = geom.bounds
        g = [(x, y) for x in np.linspace(w, e, 6) for y in np.linspace(s, n, 6) if geom.contains(Point(x, y))]
        pts = g or [(geom.centroid.x, geom.centroid.y)]
    for svc, var, res, nmax in SUS:
        url = f"{GEO}/{svc}/ImageServer/identify"
        try:
            vals = []
            for x, y in pts:
                q = {"f": "json", "geometry": json.dumps({"x": x, "y": y, "spatialReference": {"wkid": 4326}}), "geometryType": "esriGeometryPoint",
                     "returnGeometry": "false", "returnCatalogItems": "false"}
                v = get(url, params=q, verify=False).json().get("value")
                if v not in (None, "NoData"): vals.append(int(v))
            if not vals: raise ValueError("sin dato (NoData) en el punto")
            leyenda = ("clases 1-5 (muy baja a muy alta según la descripción del servicio; la leyenda REST solo da números)" if nmax == 5
                       else "clases 1-4; la leyenda REST solo da números: sentido ascendente inferido (llanura del río en Catacaos = 4)")
            f.add("peligros", var, max(vals), min(vals), max(vals), f"clase 1-{nmax}", res, "mapa nacional INGEMMET (fecha de edición no indicada en el servicio)",
                  "INGEMMET GEOCATMIN", f"{GEO}/{svc}/ImageServer",
                  f"identify en {len(vals)} punto(s); valor = máximo" + (" de una grilla 6x6 dentro del polígono" if geom is not None else ""),
                  "regional", "estimado", f"Mapa nacional a {res} de píxel, hecho a escala regional: no delimita el riesgo de la parcela", leyenda)
        except Exception as e:
            f.fallo("peligros", var, "INGEMMET GEOCATMIN", url, e)
    url = f"{GEO}/SERV_PELIGROS_GEOLOGICOS/MapServer/0/query"
    try:
        q = {"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326, "distance": 1000,
             "units": "esriSRUnit_Meter", "outFields": "*", "returnGeometry": "false"}
        feats = get(url, params=q, verify=False).json()["features"]
        tipos = sorted({str(next((v for k, v in ft["attributes"].items() if "TIPO" in k.upper() or "PELIGRO" in k.upper()), "?")) for ft in feats})
        f.add("peligros", "peligros_geologicos_inventariados_1km", len(feats), "", "", "número", "inventario puntual", "inventario INGEMMET",
              "INGEMMET GEOCATMIN (SERV_PELIGROS_GEOLOGICOS capa 0)", url, "Consulta por distancia de 1 km al punto/centroide", "regional", "observado",
              "Inventario incompleto: 0 significa 'nada inventariado', no 'sin peligro'", "Tipos: " + ", ".join(tipos) if tipos else "Sin registros a 1 km")
    except Exception as e:
        f.fallo("peligros", "peligros_geologicos_inventariados_1km", "INGEMMET GEOCATMIN", url, e)
    url = f"{GEO}/SERV_CARTOGRAFIA_DEMARCACION_WGS84/MapServer/2/query"
    try:
        a = get(url, params={"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                             "spatialRel": "esriSpatialRelIntersects", "outFields": "CD_DIST,NM_DIST,NM_PROV", "returnGeometry": "false"},
                verify=False).json()["features"][0]["attributes"]
        c = pd.read_csv(os.path.join(D, "peligros", "cenepred_riesgo_inundacion_piura.csv"), dtype={"ubigeo": str})
        r = c[c.ubigeo == a["CD_DIST"]]
        if r.empty: raise ValueError(f"distrito {a['CD_DIST']} sin fila CENEPRED")
        r = r.iloc[0]
        frac = r.sagr_inu / r.sagr_tot if r.sagr_tot else float("nan")
        f.add("peligros", "riesgo_inundacion_distrito_CENEPRED", r.nriesgo_in, "", "", "nivel", f"distrito {a['NM_DIST']} ({a['CD_DIST']})",
              "escenario de riesgo por lluvias intensas (consultado 24-oct-2026)", "CENEPRED SIGRID, capa 3020604",
              "https://sig.cenepred.gob.pe/sigrid/rest/services/sigrid/Informacion_CENEPRED/MapServer/3020604",
              "Distrito por GEOCATMIN (límites INEI 2024) y nivel de la tabla CENEPRED", "regional", "observado",
              "Un nivel para todo el distrito: no distingue parcelas altas de bajas",
              f"Superficie agrícola susceptible a inundación / total del distrito = {frac:.2f} (unidad de sagr no documentada). Tabla bajada con WebFetch: el servidor rechaza TLS desde esta caja")
    except Exception as e:
        f.fallo("peligros", "riesgo_inundacion_distrito_CENEPRED", "CENEPRED SIGRID", url, e)
    f.add("peligros", "faja_marginal_o_zona_inundable_ANA", fuente="ANA", url="https://www.ana.gob.pe", tipo="regional", estado="desconocido",
          notas="Sin servicio ANA consultable: los dominios de ANA rechazan TLS desde esta caja. Verificar a mano si la parcela está en faja marginal del Piura o el Chira")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float); ap.add_argument("--lon", type=float)
    ap.add_argument("--poligono"); ap.add_argument("--nombre", required=True)
    ap.add_argument("--salida", default=os.path.join(BASE, "ejemplos"))
    a = ap.parse_args()
    geom = None
    if a.poligono:
        gj = json.load(open(a.poligono))
        geom = shape(gj["features"][0]["geometry"] if gj.get("type") == "FeatureCollection" else gj.get("geometry", gj))
        lat, lon = geom.centroid.y, geom.centroid.x
    else:
        lat, lon = a.lat, a.lon
    zi = zona_de(lon, lat)
    zona = zi["subzona"]
    f = Ficha(a.nombre, lat, lon, zi["zona"], zona)
    area_ha = None
    if geom is not None:
        area_ha = geom.area * (111320 ** 2) * math.cos(math.radians(lat)) / 1e4
        f.add("parcela", "area_poligono", round(area_ha, 2), unidad="ha", resolucion="geometría de entrada", fuente="GeoJSON del usuario",
              metodo="Área planar aproximada en grados escalados", tipo="medicion_local", estado="observado", notas="Error <1 % para parcelas pequeñas")
    nota = []
    if zi["distrito"]: nota.append(f"Distrito {zi['distrito']} ({zi['provincia']}, ubigeo {zi['ubigeo']}). Criterio: {zi['criterio']}")
    if zi["zona_alternativa"]: nota.append(f"Distrito ambiguo ({zi['ambiguo']}): zona alternativa = {zi['zona_alternativa']}")
    nota.append(f"Datos por zona tomados de la caja '{zona}'" if zona else "Zona sin caja de datos (piura_region): no hay filas zona:*; usar valores de punto")
    if not zi["dentro"]: nota.append("AVISO: el punto no cae en ninguna zona definida; los datos por zona son solo orientativos")
    f.add("parcela", "zona_territorial", zi["zona"], resolucion="polígono de distrito (INEI 2024)" if zi["distrito"] else "cajas de zona del proyecto",
          fuente="INEI límites distritales vía INGEMMET GEOCATMIN + suelos/datos/distrito_zona.csv" if zi["distrito"] else "suelos/scripts (ZONAS)",
          url=LIMITES_URL if zi["distrito"] else "", metodo=zi["metodo"], tipo="regional", estado="estimado", notas=". ".join(nota))
    if zi["zona_alternativa"]:
        f.add("parcela", "zona_alternativa", zi["zona_alternativa"], resolucion="polígono de distrito (INEI 2024)", fuente="suelos/datos/distrito_zona.csv",
              metodo="Columna zona_alternativa del distrito", tipo="regional", estado="estimado", notas=f"ambiguo: {zi['ambiguo']}")
    clima(f, lat, lon, geom is not None)
    clima_zona(f, zona)
    suelo(f, lat, lon, zona, geom is not None)
    cew_zona(f, zi["zona"])
    pendiente(f, lat, lon, geom)
    peligros(f, lat, lon, geom)
    os.makedirs(a.salida, exist_ok=True)
    df = pd.DataFrame(f.rows, columns=COLS)
    df.to_csv(os.path.join(a.salida, f"{a.nombre}.csv"), index=False)
    json.dump({"lugar": a.nombre, "lat": lat, "lon": lon, "zona": zi["zona"], "zona_alternativa": zi["zona_alternativa"], "distrito": zi["distrito"], "ubigeo": zi["ubigeo"], "subzona": zona, "area_ha": area_ha, "variables": f.rows},
              open(os.path.join(a.salida, f"{a.nombre}.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(f"{a.nombre}: {len(df)} filas -> {a.salida}/{a.nombre}.csv | " + ", ".join(f"{k}={v}" for k, v in df.estado.value_counts().items()))


if __name__ == "__main__":
    main()
