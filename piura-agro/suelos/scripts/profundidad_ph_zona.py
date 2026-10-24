"""pH por zona (rango) y profundidad efectiva de enraizamiento por zona (intervalo).

profundidad_efectiva = min(profundidad física del suelo, napa estacional - franja capilar)
  - profundidad física: clase ROOT_DEPTH de HWSD v2 (1 >100 cm, 2 50-100, 3 10-50, 4 <10 cm),
    ponderada por SHARE del componente y por ha de cultivo WorldCover 2021. No hay medida local
    numérica (SIAR 584, matriz regional y ZEE Montero no la traen; ver revision_agronomia_r3.md §4).
    SoilGrids 2.0 no publica profundidad de suelo.
  - napa estacional: solo documentada para el Bajo Piura (0-2.0 m en 355 km2; FAO/UNALM 1990 clases
    <1, 1-2, >2 m) y, en pozos, en Castilla (Medio Piura: nivel estático 15-38 m). Resto: desconocida.
  - franja capilar: 0.3 m (textura gruesa) a 0.5 m (fina), rango dado por el revisor agronómico.
pH: HWSD v2 D1 (0-20 cm) ponderado como arriba; SoilGrids 2.0 phh2o media 0-30 cm (250 m) sobre
píxeles con >=30 % de cultivo, rango p05-p95 espacial.
Salida: datos/profundidad_ph_por_zona.csv (columnas del contrato + zona, resolucion).
Uso: .venv/bin/python scripts/profundidad_ph_zona.py
"""
import os
import numpy as np, pandas as pd, rasterio
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds
from rasterio.enums import Resampling

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(BASE, "datos", "hwsd2")
WC = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S06W081_Map.tif"
SG = "/vsicurl/https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_{}_mean.vrt"
HW_URL = "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip"
from ece_drenaje_hwsd_zonas import ZONAS  # noqa: E402  (módulo ligero con las cajas)
from contrato import a_contrato  # noqa: E402

CLASE = {1: (1.0, None), 2: (0.5, 1.0), 3: (0.1, 0.5), 4: (0.0, 0.1)}  # m
FRANJA = (0.25, 1.06)  # Lohman 1972, USGS PP 708, Tabla 1 (Atterberg): arena media 24.6 cm, arena fina 42.8 cm, limo 0.1-0.05 mm 105.5 cm
NAPA = {  # zona: (min, max, fuente, url, tipo, estado, nota)
    # R8 (revisión Agronomía H04 + coordinador): el Bajo Piura ya no lleva el tope 0-2.0 m (era el sector somero de 355 km2 de
    # FAO/UNALM 1990, no toda la zona). Ahora: distribución de los 41 SEV ANA 2015, rango = p25-p75; el sector somero va en otra fila.
    "Bajo Piura": (0.6, 6.0,
        "ANA/AAA Jequetepeque-Zarumilla 2015, ERH Piura Tomo I, Cuadros 7.6-7.18 (41 SEV con nivel freático)",
        "https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf",
        "regional", "estimado",
        "Distribución de 41 SEV del Valle Medio y Bajo Piura (sin ubicar: el Anexo 4 de mapas no está disponible, así que se asignan al Bajo "
        "Piura como zona con más SEV someros, sin poder probarlo). p25 0.6 m, mediana 2.3 m, p75 6.0 m; min-max 0.0-159.5 m. "
        "20 de 41 (48.8 %, IC 95 % Wilson 34-64 %) con napa < 2 m; 11 de 41 con < 1 m. Contraste por área (1977-1978, Castillo Albines c. 2001 "
        "vía restricciones/evidencia_observada.csv): napa alta permanente 21.2 % + temporal 32.2 % = 53.4 % de 34 721 ha. "
        "FAO/UNALM 1990: 0-2.0 m en 355 km2 (sector somero) y 50-80 % del área con napa < 2 m antes de Poechos. Geofísica, no piezómetro; "
        "estación del SEV no indicada. La napa sube en años FEN y con riego de arroz."),
    "Medio Piura": (15.08, 37.60,
        "Tesis UNP, sector Punta Arena (Castilla), niveles estáticos en pozos", "http://repositorio.unp.edu.pe/handle/UNP/2010",
        "medicion_local", "observado",
        "Solo un sector (Punta Arena, Castilla) y en pozos; no representa las partes bajas del Medio Piura que lindan con el Bajo Piura, "
        "donde la revisión cruzada supone napa somera compartida. Fuera de Punta Arena la napa es desconocida."),
}
ANA15 = "ANA/AAA Jequetepeque-Zarumilla 2015, Evaluación de Recursos Hídricos Superficiales en la Cuenca del Río Piura, Tomo I"
ANA15_URL = "https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf"
SEV = {"mediana": 2.3, "p25": 0.6, "p75": 6.0, "min": 0.0, "max": 159.5, "n": 41, "n_menor2": 20, "n_menor1": 11}  # 41 SEV de las secciones 1-7 y 12-13 (ver extracto)
CUMPLE = {"Bajo Piura": (48.8, 34.3, 63.5, "estimado", "Valor = 20 de 41 SEV ANA 2015 con napa < 2 m (fracción de PUNTOS, usada como aproximación de "
                         "área); rango = IC 95 % de Wilson para n = 41. Contraste por área: 53.4 % con napa alta (1977-1978) y 50-80 % según la época "
                         "(FAO/UNALM 1990, 1975-1982, segunda mano). Las tres fuentes caben en ~35-80 %. Sin serie reciente."),
          "Medio Piura": ("", "", 49, "estimado", "Cota superior: 49 % es la cifra conjunta Medio+Bajo de los SEV; en el Medio Piura debe ser menor "
                          "(pozos >30 m en Piura y Castilla) pero no la puedo separar. Mínimo vacío: desconocido.")}
# valor categórico: si / no / parcial (corrección del coordinador, ronda 7)
FAO29 = {"Bajo Piura": ("parcial", "estimado", "Cumple (napa >= 2 m) en 21 de 41 SEV ANA 2015 = 51.2 % (IC 95 % 36-66 %); no cumple en 48.8 % "
                        "(p25 0.6 m, mediana 2.3 m, p75 6.0 m). Consecuencia: los umbrales de ECe de FAO-29 sirven solo como APROXIMACIÓN a escala de zona; "
                        "en la parcela son exactos solo si se mide napa >= 2 m (barreno o pozo de observación). Ver fraccion_area_napa_menor_2m."),
         "Medio Piura": ("parcial", "estimado", "Texto original: sí en la mayor parte, no verificado en partes bajas. Pozos 15-38 m (Punta Arena) y >30 m (Piura, Castilla); "
                         "algunos SEV del estudio Medio+Bajo dan napa somera sin ubicación."),
         "Valle del Chira": ("", "desconocido", "Problemas de drenaje conocidos (ANA 1975: 7 394 ha con sales o mal drenaje, sin verificar) pero sin cifras de napa."),
         "San Lorenzo": ("", "desconocido", "Sin datos de napa."),
         "Alto Piura": ("", "desconocido", "Sin datos de napa."),
         "Sierra Ayabaca": ("si", "estimado", "Texto original: probablemente sí (ladera). Ladera sin napa somera esperable salvo fondos de valle; sin dato."),
         "Sierra Huancabamba": ("si", "estimado", "Texto original: probablemente sí (ladera). Ladera sin napa somera esperable salvo fondos de valle; sin dato.")}
CONTRATO = ["zona", "variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "lugar", "lat", "lon",
            "resolucion", "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]
LOCAL_PH = {
    "San Lorenzo": "INGEMMET 2025 'Geología del limón, valle San Lorenzo' (https://hdl.handle.net/20.500.12544/5244) caracteriza 53 suelos y "
                   "los describe con 'pH alcalino'; no leí los valores numéricos del libro (pendiente).",
    "Alto Piura": "INGEMMET 2025 (Geología del limón) cubre también Chulucanas: 'pH alcalino', sin valor numérico leído.",
}

def wq(x, w, q):
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w) / w.sum()
    return float(np.interp(q, c, x))

lay = pd.read_csv(os.path.join(H, "HWSD2_LAYERS.csv"), low_memory=False)
d1 = lay[(lay.LAYER == "D1")].copy()
d1["ph"] = d1.PH_WATER.where(d1.PH_WATER > 0)
d1["rd"] = d1.ROOT_DEPTH.where(d1.ROOT_DEPTH.isin([1, 2, 3, 4]))

def smu_stats(g):
    w = g.SHARE.astype(float)
    ok = g.ph.notna()
    r = dict(ph=np.average(g.ph[ok], weights=w[ok]) if ok.any() else np.nan,
             ph_min=g.ph.min(), ph_max=g.ph.max())
    for k in CLASE:
        r[f"rd{k}"] = w[g.rd == k].sum() / w.sum()
    return pd.Series(r)
smu = d1.groupby("HWSD2_SMU_ID").apply(smu_stats, include_groups=False)

filas = []
def add(zona, b, variable, valor="", vmin="", vmax="", unidad="", resolucion="", fecha="", fuente="", url="", metodo="", tipo="", estado="", notas=""):
    filas.append(dict(zona=zona, variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, lugar=zona,
                      lat=round((b[1] + b[3]) / 2, 3), lon=round((b[0] + b[2]) / 2, 3), resolucion=resolucion, fecha_o_periodo=fecha,
                      fuente=fuente, url_o_doi=url, metodo=metodo, tipo_evidencia=tipo, estado=estado, notas=notas))

hs = rasterio.open(os.path.join(H, "HWSD2.bil")); wc = rasterio.open(WC)
sg = [WarpedVRT(rasterio.open(SG.format(d)), crs="EPSG:4326") for d in ("0-5cm", "5-15cm", "15-30cm")]
for zona, b in ZONAS.items():
    # --- HWSD ponderado por cultivo
    win = from_bounds(*b, hs.transform).round_offsets().round_lengths()
    ids = hs.read(1, window=win); tr = hs.window_transform(win); ny, nx = ids.shape
    w2 = from_bounds(*rasterio.transform.array_bounds(ny, nx, tr), wc.transform)
    frac = (wc.read(1, window=w2, out_shape=(ny * 18, nx * 18)) == 40).reshape(ny, 18, nx, 18).mean(axis=(1, 3))
    df = pd.DataFrame({"smu": ids.ravel(), "w": frac.ravel()}).join(smu, on="smu")
    df = df[(df.w > 0)]
    met = f"HWSD v2 capa D1, SMU x componente (SHARE), ponderado por ha de cultivo WorldCover 2021 en caja {b}"
    # pH a nivel de componente: peso = ha de cultivo de la SMU x SHARE del componente (no se promedia dentro de la celda,
    # para no esconder CMca 8.2 detrás de Arenosoles 6.7)
    wsmu = df.groupby("smu").w.sum()
    cp = d1[d1.HWSD2_SMU_ID.isin(wsmu.index) & d1.ph.notna()].copy()
    cp["peso"] = cp.HWSD2_SMU_ID.map(wsmu) * cp.SHARE.astype(float)
    cp = cp[cp.peso > 0]
    if len(cp):
        x, w = cp.ph.values.astype(float), cp.peso.values
        top = cp.groupby(["WRB4", "ph"]).peso.sum().sort_values(ascending=False)
        top = ", ".join(f"{k[0]} {k[1]:g} ({100*v/top.sum():.0f} %)" for k, v in top.head(5).items())
        add(zona, b, "pH_agua_0_20cm_HWSD2", round(np.average(x, weights=w), 2), round(wq(x, w, .05), 2), round(wq(x, w, .95), 2), "pH",
            "~1 km (30 arcsec), unidad 1:5 000 000", "HWSD v2 2023 (perfiles de décadas previas)", "FAO/IIASA HWSD v2.0, capa D1", HW_URL,
            met + "; rango = Q05-Q95 entre componentes de suelo (peso = ha de cultivo x SHARE)", "regional", "estimado",
            f"Transferencia taxonómica, no medición. Componentes con más peso: {top}. El mapa no dice dónde está cada componente dentro de la celda.")
    # clases de profundidad
    cls = {k: float(np.average(df[f"rd{k}"].fillna(0), weights=df.w)) for k in CLASE}
    presentes = [k for k in CLASE if cls[k] >= 0.05]
    lo = min(CLASE[k][0] for k in presentes); his = [CLASE[k][1] for k in presentes]
    hi = None if None in his else max(his)
    reparto = ", ".join(f"clase {k} {100*cls[k]:.0f} %" for k in CLASE if cls[k] > 0)
    # valor típico (H08 Agronomía): límite inferior de la clase que contiene la mediana del área de cultivo (de más profunda a más somera)
    acc, tip = 0.0, None
    for k in (1, 2, 3, 4):
        acc += cls[k] / max(sum(cls.values()), 1e-9)
        if acc >= 0.5: tip = CLASE[k][0]; break
    add(zona, b, "profundidad_fisica_suelo_HWSD2", tip if tip is not None else "", lo, "" if hi is None else hi, "m", "~1 km, 1:5 000 000",
        "HWSD v2 2023", "FAO/IIASA HWSD v2.0, ROOT_DEPTH (D_ROOT_DEPTH: 1 >100 cm, 2 50-100, 3 10-50, 4 <10)", HW_URL,
        met + "; intervalo = unión de las clases con >=5 % del área de cultivo; valor = límite inferior de la clase mediana (típico), el mínimo es el limitante",
        "regional", "estimado",
        f"Reparto en cultivo: {reparto}. El mínimo del intervalo es la clase más somera con >= 5 % del área: limitante local, no valor típico. Es una clase por tipo de suelo, no una medida; >100 cm queda sin cota superior. "
        "No considera napa ni capas endurecidas locales. No hay profundidad numérica local en el repo (SIAR 584 / matriz / ZEE Montero).")
    # napa
    if zona in NAPA:
        nmin, nmax, fu, url, tipo, est, nota = NAPA[zona]
        if zona == "Bajo Piura":
            add(zona, b, "profundidad_napa_estacional", SEV["mediana"], nmin, nmax, "m", "41 SEV sin ubicar (valle Medio+Bajo Piura)",
                "estudio 2015 (estación del SEV no indicada)", fu, url, "valor = mediana; rango = p25-p75 (IQR) de 41 SEV, NO min-max ni tope", tipo, est, nota)
            add(zona, b, "profundidad_napa_sector_somero_FAO1990", "", 0.0, 2.0, "m", "sector de 355 km2 del Bajo Piura", "1975-1982",
                "Tesis UNP (repositorio.unp.edu.pe/handle/UNP/2010) que cita FAO/UNALM 1990", "http://repositorio.unp.edu.pe/handle/UNP/2010 ; https://hdl.handle.net/20.500.12543/1535",
                "Rango reportado por la fuente para el sector con napa somera", "regional", "observado",
                "Era la fila de zona hasta la ronda 7; describe solo el sector somero, no toda la zona (H04 de Agronomía). Dato de segunda mano.")
        else:
            add(zona, b, "profundidad_napa_estacional", "", nmin, nmax, "m", "sector del valle (estudio)", "estudio UNP (fecha no leída)",
                fu, url, "Rango reportado por la fuente", tipo, est, nota)
    else:
        nmin = nmax = None
        add(zona, b, "profundidad_napa_estacional", unidad="m", resolucion="", fuente="sin fuente encontrada", tipo="regional",
            estado="desconocido", notas="No encontré datos de napa para esta zona. " +
            ("En el Chira hay problemas de drenaje conocidos, pero no tengo cifras." if zona == "Valle del Chira" else ""))
    # napa: evidencia ANA 2015 (Medio y Bajo Piura sin separar) y cumplimiento de la condición FAO-29 (napa >= 2 m)
    if zona in ("Bajo Piura", "Medio Piura"):
        add(zona, b, "profundidad_napa_SEV_ANA2015", SEV["mediana"], SEV["p25"], SEV["p75"], "m", "41 SEV en el Valle Medio y Bajo Piura",
            "estudio 2015 (campaña SEV/TDEM, estación no indicada)", ANA15, ANA15_URL,
            "Nivel freático interpretado de sondeos eléctricos verticales (Cuadros 7.6-7.18, págs. 75-83); valor = mediana; rango = p25-p75 (IQR), NO min-max",
            "regional", "estimado",
            "Rango rotulado como IQR (p25-p75); min-max = 0.0-159.5 m. Medición indirecta (geofísica), no piezómetro. 20 de 41 SEV con napa <2 m y 11 con <1 m. La ubicación de cada SEV está en el Anexo 4 "
            "(mapas digitales) que no pude abrir, así que no separo Medio de Bajo Piura. Excluí las secciones 8-11 (31 SEV con nivel 114-285 m, "
            "probablemente bordes desérticos). Extracto: suelos/fuentes/ANA_2015_ERH_Piura_extracto.md")
        add(zona, b, "nivel_estatico_pozos_ANA2014", "", 30.0 if zona == "Medio Piura" else 15.0, "", "m", "inventario de pozos 2014 (Fig. 27)",
            "2014", ANA15, ANA15_URL, "Zonificación del nivel estático en pozos (sección 10.3.4, pág. 110)", "regional", "observado",
            (">30 m en pozos de Piura y Castilla; " if zona == "Medio Piura" else ">30 m en Catacaos y 15-30 m en el resto; ")
            + "máximo vacío = sin cota superior. Son pozos de bombeo, a menudo dentro de conos de descenso (Cura Mori, oeste de Piura): "
            "no miden la napa colgada bajo parcelas regadas. No contradice los SEV someros; describe otra parte del sistema.")
    if zona in CUMPLE:
        v, lo_, hi_, est, nota = CUMPLE[zona]
        add(zona, b, "fraccion_area_napa_menor_2m", v, lo_, hi_, "%", "valle", "1975-1982 y 2014-2015",
            "FAO/UNALM 1990 (vía página del repositorio) + ANA 2015 (SEV)", "https://hdl.handle.net/20.500.12543/1535 ; " + ANA15_URL,
            ("Fracción de SEV ANA 2015 con napa < 2 m; rango = IC 95 % de Wilson (n = 41)" if zona == "Bajo Piura" else "Cota superior: fracción conjunta Medio+Bajo de los SEV 2015"),
            "regional", est, nota)
    add(zona, b, "cumple_napa_2m_FAO29", FAO29.get(zona, ("", "desconocido", "Sin datos de napa en la zona."))[0], "", "", "categoría",
        "zona", "", "regla: suelos/datos/zonas_ece_drenaje_fen.csv (profundidad_napa_minima_recomendada_salinidad)", "",
        "Compara la napa de la zona con 2 m (FAO-29: umbrales de ECe válidos solo con napa >= 2 m). Valor categórico si/no/parcial; vacío si desconocido", "regional",
        FAO29.get(zona, ("", "desconocido", ""))[1], FAO29.get(zona, ("", "", "Sin datos de napa en la zona."))[2])
    if zona == "Bajo Piura":
        add(zona, b, "fraccion_puntos_cumple_napa_2m_FAO29", 51.2, 36.5, 65.7, "%", "41 SEV sin ubicar", "estudio 2015", ANA15, ANA15_URL,
            "21 de 41 SEV con napa >= 2 m; rango = IC 95 % de Wilson", "regional", "estimado",
            "Cuantifica 'parcial' en cumple_napa_2m_FAO29: FAO-29 exacto en ~la mitad de los puntos, aproximación en el resto. Fracción de puntos, no de área; "
            "por área (1977-1978) cumplía ~47 % (100 - 53.4 % con napa alta).")
    add(zona, b, "franja_capilar", "", FRANJA[0], FRANJA[1], "m", "", "", "Lohman, S.W. (1972). Ground-Water Hydraulics. USGS Professional Paper 708, Tabla 1 (Atterberg, citado en Terzaghi 1942), p. 3",
        "https://doi.org/10.3133/pp708",
        "Ascenso capilar medido en columnas de porosidad 41 % tras 72 días; mínimo = arena media (0.5-0.2 mm) 0.246 m, máximo = limo (0.1-0.05 mm) 1.055 m",
        "bibliografico", "estimado",
        "Ronda 8: sustituye el 0.3-0.5 m de la revisión agronómica (06:08), que no tenía fuente primaria. Valores de laboratorio por tamaño de grano, no medidos en Piura: "
        "arena fina 0.43 m; en limo más fino (0.05-0.02 mm) el ascenso seguía subiendo a los 72 días (>2 m), así que en suelos limosos del Bajo Piura el máximo puede ser mayor. "
        "Elegir el extremo según la textura de la parcela.")
    # profundidad efectiva
    if zona == "Bajo Piura":
        e_lo = max(0.0, min(lo, nmin - FRANJA[1]))
        add(zona, b, "profundidad_efectiva_enraizamiento", "", round(e_lo, 2), "" if hi is None else hi, "m", "zona (SEV sin ubicar + HWSD 1 km)",
            "SEV ANA 2015; HWSD 2023", "HWSD v2 + " + NAPA[zona][2], HW_URL + " ; " + NAPA[zona][3],
            "lo = napa p25 (0.6 m) - franja 0.5 m; hi = profundidad física HWSD (con napa p75 6.0 m la napa no limita)", "regional", "estimado",
            "En ~49 % de los puntos (napa < 2 m) la profundidad útil es napa - franja capilar (0.1-1.7 m); en el resto manda la profundidad física "
            f"(HWSD >= {lo} m). Máximo vacío = >1 m sin cota superior. Medir la napa en la parcela antes de decidir cultivos sensibles.")
    elif nmin is not None and nmax is not None and nmax < (lo if hi is None else hi) + 2:
        e_lo = max(0.0, min(lo, nmin - FRANJA[1]))
        e_hi = nmax - FRANJA[0] if hi is None else min(hi, nmax - FRANJA[0])
        add(zona, b, "profundidad_efectiva_enraizamiento", "", round(e_lo, 2), round(e_hi, 2), "m", "zona (mezcla de 1 km y estudio de valle)",
            "napa 1975-1982 y estudio UNP; HWSD 2023", "HWSD v2 + " + NAPA[zona][2], HW_URL + " ; " + NAPA[zona][3],
            "min(profundidad física HWSD, napa estacional - franja capilar 0.3-0.5 m); lo = napa mínima - 0.5, hi = napa máxima - 0.3",
            "regional", "estimado",
            "Vale para el sector con napa somera (la mayor parte del valle según la fuente). Donde la napa supera 2 m manda la profundidad física "
            f"(HWSD >= {lo} m). Una napa a 0 m (lo = 0) significa anegamiento: no hay zona radical útil. La napa sube en años FEN.")
    else:
        nota = ("La napa conocida (pozos de Punta Arena, 15-38 m) no limita; manda la profundidad física. En las partes bajas que lindan con el "
                "Bajo Piura puede haber napa somera y la profundidad efectiva sería menor." if zona == "Medio Piura" else
                "Napa desconocida: el intervalo es solo la profundidad física y es una cota superior.")
        add(zona, b, "profundidad_efectiva_enraizamiento", "", lo, "" if hi is None else hi, "m", "~1 km, 1:5 000 000", "HWSD 2023",
            "FAO/IIASA HWSD v2.0, ROOT_DEPTH", HW_URL, "min(profundidad física, napa - franja); sin napa limitante o conocida = profundidad física",
            "regional", "estimado", nota + " Valor máximo vacío = >1 m sin cota superior.")
    # --- SoilGrids pH 0-30 cm
    try:
        arrs = []
        for v in sg:
            wv = from_bounds(*b, v.transform).round_offsets().round_lengths()
            arrs.append(v.read(1, window=wv).astype(float))
        sh = min(a.shape[0] for a in arrs), min(a.shape[1] for a in arrs)
        a = [x[:sh[0], :sh[1]] for x in arrs]
        valid = (a[0] > 0) & (a[1] > 0) & (a[2] > 0)
        ph = (a[0] * 5 + a[1] * 10 + a[2] * 15) / 30 / 10
        tv = v.window_transform(wv)
        wb = rasterio.transform.array_bounds(sh[0], sh[1], tv)
        cf = wc.read(1, window=from_bounds(*wb, wc.transform), out_shape=(sh[0] * 5, sh[1] * 5), resampling=Resampling.nearest)
        cf = (cf == 40).reshape(sh[0], 5, sh[1], 5).mean(axis=(1, 3))
        m = valid & (cf >= 0.3)
        x = ph[m]
        add(zona, b, "pH_agua_0_30cm_SoilGrids", round(float(np.median(x)), 2), round(float(np.percentile(x, 5)), 2),
            round(float(np.percentile(x, 95)), 2), "pH", "250 m", "perfiles 1950-2017, mapa 2020", "ISRIC SoilGrids 2.0, phh2o media",
            "https://files.isric.org/soilgrids/latest/data/phh2o/", f"media ponderada 0-5/5-15/15-30 cm; mediana y p05-p95 espacial sobre "
            f"{int(m.sum())} píxeles con >=30 % de cultivo WorldCover", "prediccion", "estimado",
            "Rango espacial de la media predicha; la incertidumbre por píxel (Q05-Q95) es más ancha (en Catacaos 6.5-9.2).")
        sgr = (round(float(np.percentile(x, 5)), 2), round(float(np.percentile(x, 95)), 2))
    except Exception as e:
        add(zona, b, "pH_agua_0_30cm_SoilGrids", unidad="pH", fuente="ISRIC SoilGrids 2.0", tipo="prediccion", estado="desconocido",
            notas=f"Falló la lectura: {e}")
        sgr = None
    # rango combinado
    hw = [r for r in filas if r["zona"] == zona and r["variable"] == "pH_agua_0_20cm_HWSD2"]
    mins = [r["valor_min"] for r in hw] + ([sgr[0]] if sgr else []); maxs = [r["valor_max"] for r in hw] + ([sgr[1]] if sgr else [])
    if mins:
        add(zona, b, "pH_rango_zona", "", min(mins), max(maxs), "pH", "zona", "HWSD 2023 y SoilGrids 2020",
            "envolvente de HWSD v2 (D1) y SoilGrids 2.0 (0-30 cm)" + ("; referencia local cualitativa INGEMMET 2025" if zona in LOCAL_PH else ""),
            HW_URL + " ; https://files.isric.org/soilgrids/latest/data/phh2o/",
            "min y max de los rangos Q05-Q95 de ambas fuentes", "regional", "estimado",
            "Sin centro: las fuentes no concuerdan en el valor medio. " + LOCAL_PH.get(zona, "No encontré pH medido local para esta zona."))
out = pd.DataFrame(filas).reindex(columns=CONTRATO)
a_contrato(out).to_csv(os.path.join(BASE, "datos", "profundidad_ph_por_zona.csv"), index=False)
pd.set_option("display.width", 250)
print(out[["zona", "variable", "valor", "valor_min", "valor_max", "estado"]].to_string(index=False))
