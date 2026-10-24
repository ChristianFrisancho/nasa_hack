"""Ronda 5: calendario observado de siembra/cosecha por zona (DRAP/SIEA) y profundización. Idempotente."""
import os, numpy as np, pandas as pd
from fuentes import F
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")
COLS = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon","fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","confianza","id"]
MES = ["ene","feb","mar","abr","may","jun","jul","ago","set","oct","nov","dic"]
# ---- zonas: fuente única = suelos/datos/distrito_zona.csv (Territorio), unión por UBIGEO (Ronda 6) ----
DZ = pd.read_csv(os.path.join(D, "..", "suelos", "datos", "distrito_zona.csv"), dtype=str, keep_default_na=False).set_index("ubigeo")
ZLAB = {"alto_piura": "Alto Piura", "medio_piura": "Medio Piura", "bajo_piura": "Bajo Piura", "chira": "Chira", "san_lorenzo": "San Lorenzo",
        "sierra_piura": "Sierra de Piura", "piura_region": "Piura (región)"}
C = {"ARROZ": "arroz", "MAIZ AMARILLO DURO": "maiz amarillo duro", "FRIJOL GRANO SECO": "frijol castilla/grano seco",
     "FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO SECO": "frijol caupi", "FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO VERDE": "frijol caupi (vaina verde)",
     "ARVEJA GRANO SECO": "arveja", "ARVEJA GRANO VERDE": "arveja (grano verde)", "FRIJOL DE PALO GRANO SECO (T.)": "frijol de palo",
     "ZARANDAJA GRANO SECO": "zarandaja", "PAPA (agrupa mejoradas y nativas)": "papa", "YUCA": "yuca", "CAMOTE": "camote", "ALGODON PIMA": "algodon (Pima)",
     "ALGODON": "algodon (no Pima)", "PAPRIKA": "pimiento/paprika", "PIQUILLO (T.)": "piquillo", "MANI  PARA FRUTA": "mani", "SOYA": "soya",
     "CEBOLLA": "cebolla", "ZAPALLO": "zapallo", "SANDIA": "sandia", "MAIZ AMILACEO": "maiz amilaceo", "TRIGO BLANDO": "trigo", "HABA GRANO SECO": "haba",
     "SORGO ESCOBERO": "sorgo escobero", "MELON": "melon", "MAIZ CHOCLO": "maiz choclo", "TOMATE": "tomate",
     "MANGO": "mango", "LIMON SUTIL": "limon", "PLATANOS Y BANANAS PARA COCCI N (M X paradisiaca)": "platano/banano", "VID": "uva",
     "CACAO": "cacao", "CAFETO": "cafe", "PALTO": "palta", "MARACUYA": "maracuya", "NARANJO": "naranja", "PAPAYA": "papaya"}
PEREN = {"mango", "limon", "platano/banano", "uva", "cacao", "cafe", "palta", "maracuya", "naranja", "papaya"}
d = pd.read_csv(os.path.join(D, "raw", "drap_dataset.csv"), dtype={"UBIGEO": str})
d = d[(d.ANO >= 2016) & d.CULTIVO.isin(C)].copy()
assert d.UBIGEO.isin(DZ.index).all(), set(d.UBIGEO) - set(DZ.index)
d["zona"] = d.UBIGEO.map(DZ.zona); d["zalt"] = d.UBIGEO.map(DZ.zona_alternativa); d["dist"] = d.UBIGEO.map(DZ.distrito).str.title(); d["cultivo"] = d.CULTIVO.map(C); d["m"] = d.MES % 100
src, url = F["DRAP_GRP"]; PER = "2016-2024 (9 campañas calendario)"
rows = []; n = [0]
def r(**k):
    n[0] += 1; x = {c: "" for c in COLS}; x.update(fuente=src, url_o_doi=url, tipo_evidencia="regional", estado="observado", fecha_o_periodo=PER, id=f"R5C{n[0]:04d}"); x.update(k); rows.append(x)
def runs(mask):
    idx = [i for i in range(12) if mask[i]]
    if not idx: return []
    if all(mask): return [(0, 11)]
    start = next(i for i in range(12) if mask[i] and not mask[i - 1]); out = []; i = start; k = 0
    while k < 12:
        if mask[i % 12] and not mask[(i - 1) % 12]: a = i % 12
        if mask[i % 12] and not mask[(i + 1) % 12]: out.append((a, i % 12))
        i += 1; k += 1
    return out
lag_rows = []
TOTC = {cc: gg["PRODUCCION" if cc in PEREN else "SIEMBRA"].sum() for cc, gg in d.groupby("cultivo")}
CTX = {}
def contexto(c, z, g):
    col = "PRODUCCION" if c in PEREN else "SIEMBRA"; uu = "t" if c in PEREN else "ha"
    by = g.groupby(["dist", "zalt"])[col].sum(); by = by[by > 0].sort_values(ascending=False); tz = by.sum()
    lug = f"{ZLAB[z]} (distritos con datos: {', '.join(x for x, _ in by.index)})" if len(by) else ZLAB[z]
    alt = [(x, a, 100 * v / tz) for (x, a), v in by.items() if a]
    nt = "zona por distrito según suelos/datos/distrito_zona.csv (Territorio, unión por UBIGEO)"
    if alt: nt += "; distritos ambiguos (zona_alternativa): " + ", ".join(f"{x}->{a} {p:.0f} % de las {uu}" for x, a, p in alt)
    sh = 100 * tz / TOTC[c] if TOTC[c] else 0
    if sh < 5: nt += f"; MARGINAL: esta zona aporta {sh:.1f} % de las {uu} del cultivo en el departamento"
    if sh < 5 and z == "sierra_piura": nt += " (probablemente valles bajos interandinos; no tomar como ventana típica de la sierra)"
    CTX[(c, z)] = (lug, nt); return lug, nt
for (c, z), g in d.groupby(["cultivo", "zona"]):
    lug, ctx = contexto(c, z, g)
    for var, col in (("siembra", "SIEMBRA"), ("cosecha", "PRODUCCION" if c in PEREN else "COSECHA")):
        prof = g.groupby("m")[col].sum().reindex(range(1, 13), fill_value=0).values.astype(float); tot = prof.sum()
        if c in PEREN and var == "siembra": continue
        if tot < 50: continue
        yrs = int((g.groupby("ANO")[col].sum() > 0).sum()); pct = 100 * prof / tot
        win = runs(pct >= 10); txt = "; ".join(MES[a] if a == b else f"{MES[a]}-{MES[b]}" for a, b in win)
        if not win: txt = "todo el año (ningún mes >=10 %)"
        cov = sum(pct[i] for a, b in win for i in ([*range(a, b + 1)] if a <= b else [*range(a, 12), *range(0, b + 1)]))
        conf = 0.6 if yrs >= 6 and tot >= 500 else 0.5 if yrs >= 4 else 0.35
        base = dict(cultivo=c, zona=z, lugar=lug, etapa=var, metodo="agregación propia de hectáreas mensuales del dataset (suma 2016-2024 por zona, % por mes)")
        uu = "t" if col == "PRODUCCION" else "ha"
        extra = "; en perennes se usa PRODUCCION mensual (t) porque el dataset registra la superficie cosechada anual en diciembre" if uu == "t" else ""
        r(variable=f"ventana_{var}_observada", valor=txt, unidad="meses", confianza=conf,
          notas=f"meses con >=10 % de las {uu} de {var} acumuladas{extra}; cubren {cov:.0f} % de {tot:.0f} {uu}; {yrs} de 9 años con {var}>0; {ctx}; incluye años FEN 2017 y 2023", **base)
        r(variable=f"mes_pico_{var}", valor=MES[int(pct.argmax())], unidad="mes", confianza=conf, notas=f"{pct.max():.0f} % de las {uu} de {var} del periodo", **base)
        for i in range(12):
            r(variable=f"{var}_pct_mes", valor=round(pct[i], 1), unidad=f"% de {uu} del periodo", fecha_o_periodo=f"{PER}; mes={MES[i]}", confianza=conf,
              notas=f"total {tot:.0f} {uu}; perfil medio del periodo, no de un año", **base)
    # desfase siembra->cosecha (anuales): retardo que maximiza la correlación circular
    if c not in PEREN:
        s = g.groupby("m").SIEMBRA.sum().reindex(range(1, 13), fill_value=0).values.astype(float)
        h = g.groupby("m").COSECHA.sum().reindex(range(1, 13), fill_value=0).values.astype(float)
        if s.sum() >= 200 and h.sum() >= 200:
            cc = np.array([np.dot(s, np.roll(h, -L)) for L in range(12)]); cc[0] = -1
            ties = [L for L in range(1, 12) if cc[L] >= 0.95 * cc.max()]; L = min(ties)
            amb = f"; AMBIGUO: retardos casi empatados {ties} (perfil bimodal); se reporta el menor" if len(ties) > 1 else ""
            r(variable="desfase_siembra_cosecha_observado", valor=L, unidad="meses", cultivo=c, zona=z, lugar=lug, etapa="ciclo_total", confianza=0.3 if amb else 0.4,
              valor_min=min(ties) if amb else "", valor_max=max(ties) if amb else "",
              metodo="cálculo propio: retardo (0-11 meses) que maximiza la correlación circular entre perfiles mensuales de siembra y cosecha",
              notas="aproxima la duración siembra-cosecha en meses (±1); no es medición de ciclo" + amb)
cal = pd.DataFrame(rows, columns=COLS); cal.to_csv(os.path.join(D, "calendario_drap_piura.csv"), index=False)
print("calendario:", len(cal), "filas;", cal[cal.variable.str.startswith("ventana")].shape[0], "ventanas;", (cal.variable == "desfase_siembra_cosecha_observado").sum(), "desfases")

# ---- para_motor: calendario compacto por cultivo y zona ----
v = cal[cal.variable.isin(["ventana_siembra_observada", "ventana_cosecha_observada", "mes_pico_siembra", "mes_pico_cosecha", "desfase_siembra_cosecha_observado"])]
w = v.pivot_table(index=["cultivo", "zona"], columns="variable", values="valor", aggfunc="first").reset_index().fillna("")
cf = v[v.variable.str.startswith("ventana")].groupby(["cultivo", "zona"]).confianza.max().reset_index()
w = w.merge(cf, on=["cultivo", "zona"])
w["applicability_note"] = [f"{CTX[(c, z)][0]}; {CTX[(c, z)][1]}; meses con >=10 % de ha (anuales) o de t (perennes); desfase en meses ±1 por correlación circular; no distingue variedades" for c, z in zip(w.cultivo, w.zona)]
w = w.rename(columns={"cultivo": "crop"})
w["source_url"] = url; w["periodo"] = PER; w["validation_status"] = "observado_estadistica_oficial_agregada_por_agente1"
w = w[[c for c in w.columns if c != "applicability_note"] + ["applicability_note"]]
w.to_csv(os.path.join(PM, "calendario_siembra_cosecha_piura.csv"), index=False); print("para_motor calendario:", len(w))

# =====================================================================================
# Ronda 5b: perennes (P2), frijol de palo / yuca (P3), revisiones M24-L32-L22-M27 (P4), rotación (P5)
# Parches por id con valores absolutos; notas con marcador [R5] sin duplicar; filas nuevas R5P/R5A/R5S/R5R
# (save() borra ese prefijo antes de añadir, así que el script es idempotente).
# =====================================================================================
def load(n): return pd.read_csv(os.path.join(D, n), dtype=str, keep_default_na=False)
def ix(df, i):
    m = df.index[df.id == i]; assert len(m) == 1, i; return m[0]
def setv(df, ids, **k):
    for i in ids if isinstance(ids, (list, tuple)) else [ids]:
        j = ix(df, i)
        for c, v in k.items():
            if c == "src": df.loc[j, "fuente"], df.loc[j, "url_o_doi"] = F[v]
            else: df.loc[j, c] = str(v)
def note(df, ids, txt):
    txt = "[R5] " + txt
    for i in ids if isinstance(ids, (list, tuple)) else [ids]:
        j = ix(df, i); nn = df.loc[j, "notas"]
        if txt not in nn: df.loc[j, "notas"] = (nn + "; " + txt) if nn else txt
def new(rows, prefix):
    def rr(variable, valor, unidad, cultivo, etapa, srck, tipo, estado, notas, conf, vmin="", vmax="", variedad="", lugar="",
           fecha="", metodo="transcripción de documento publicado", **x):
        cita, u = F[srck]
        if estado == "desconocido": valor = ""
        dd = dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo, variedad=variedad,
                  etapa=etapa, lugar=lugar, lat="", lon="", fecha_o_periodo=fecha, fuente=cita, url_o_doi=u, metodo=metodo,
                  tipo_evidencia=tipo, estado=estado, notas=notas, confianza=conf)
        dd.update(x); dd["id"] = f"{prefix}{len(rows)+1:03d}"
        if "regla_id" in dd: dd["regla_id"] = dd["id"]
        rows.append(dd)
    return rr
def save(df, nm, rows, pref):
    df = df[~df.id.str.startswith(pref)]
    out = pd.concat([df, pd.DataFrame(rows, columns=df.columns).fillna("")], ignore_index=True) if rows else df
    out.to_csv(os.path.join(D, nm), index=False); print(nm, len(df), "+", len(rows), "=", len(out))
M2A = "transcripción; meses convertidos a años (÷12)"

# ============ P2 perennes ============
P = load("perennes.csv"); NP = []; rp = new(NP, "R5P")
setv(P, "PE0053", valor="", valor_min=1.0, valor_max=1.08, src="REDAGRI_UVA21", tipo_evidencia="regional", estado="estimado", confianza=0.35,
     metodo=M2A, lugar="Piura", fecha_o_periodo="2021")
note(P, "PE0053", "'En Piura, desde que se planta hasta la primera cosecha podrían pasar 12 a 13 meses' (asesor técnico, una sola fuente; no ensayo); dos podas, una de producción")
rp("rendimiento_primera_cosecha", "", "t/ha", "uva de mesa", "primera cosecha", "REDAGRI_UVA21", "regional", "estimado",
   "'para sacar entre 20 y 25 t/ha, aunque hay variedades nuevas con las cuales están sacando entre 25 y 30 t/ha'; opinión de un asesor (fuente única), no ensayo ni estadística", 0.35,
   vmin=20, vmax=25, lugar="Piura", fecha="2021")
note(P, "PE0054", "búsqueda R5 sin vida útil de parrón para Piura; Redagrícola 2021 menciona patrones Harmony y MGT muertos 'en poco tiempo' por nematodos (cualitativo); sigue desconocido")
for i in ("PE0015", "PE0031"):
    setv(P, i, valor=1.0, valor_min=0.85, valor_max=1.2, src="SWISS_BAN12", tipo_evidencia="regional", estado="estimado", confianza=0.45,
         metodo="lectura de un gráfico de fenología (semana aproximada); semanas convertidas a años (÷52)", lugar="Valle del Chira", fecha_o_periodo="2012")
note(P, "PE0015", "r5 alto: Swisscontact 2012 p. 23 (gráfico §2.11) ubica la 'Cosecha para exportación' hacia la semana ~48-53 y la 'Segunda cosecha' hacia la semana ~72; "
     "el texto da ciclo vegetativo de 8.5 meses (plantas bien expuestas a la luz) hasta 14 meses (penumbra): rango 0.85-1.2 años. Los 9-11 meses de Cooperación Suiza (Cuadro 8) eran la edad promedio de las parcelas, no la edad a la primera cosecha")
note(P, "PE0031", "misma plantación que PE0015 (Swisscontact 2012 p. 23): la primera cosecha llega hacia 1.0 año (0.85-1.2); en el año 2 la planta ya produce y la segunda cosecha cae hacia la semana ~72 (~1.4 años)")
for i in ("PE0016", "PE0032"):
    setv(P, i, valor="", valor_min=10, valor_max=15, src="HUAMAN05", tipo_evidencia="regional", estado="estimado", confianza=0.45, lugar="Valle del Chira", fecha_o_periodo="2005")
note(P, ["PE0016", "PE0032"], "'Su ciclo de vida es de 10 a 15 años, dependiendo del manejo técnico' (diagnóstico de cadena de valor, CRS 2005; no es ensayo; vida de la plantación, no de la planta madre)")
setv(P, "PE0094", valor=3, src="CAT_TOCACHE21", tipo_evidencia="analogo_externo", estado="estimado", confianza=0.45, lugar="Tocache (San Martín, selva)")
note(P, "PE0094", "'generalmente, la primera cosecha comercial de un cacaotal sale a los 3 años de sembrado'; análogo de selva alta, el cacao de Piura (Alto Piura/Morropón) puede diferir")
rp("vida_economica_max", "", "años", "cacao", "ciclo", "CAT_TOCACHE21", "analogo_externo", "estimado",
   "'el ciclo de vida biológico del cacao dura más de 100 años, pero su vida económica normalmente no pasa de 40 años'; cota superior; MIDAGRI (PE0095) da 20 años promedio; COMPARABILIDAD: análogo de selva alta húmeda (Tocache), no de Alto Piura/Morropón seco con riego; usar solo como cota", 0.35,
   vmax=40, lugar="Tocache (San Martín, selva)")
note(P, "PE0095", "CAT Tocache 2021 da vida económica <=40 años (R5P): 20 queda como promedio MIDAGRI, 40 como cota superior")
setv(P, "PE0104", valor="", valor_min=2, valor_max=3, src="MIDAGRI_CAFE_VRAEM", tipo_evidencia="analogo_externo", estado="estimado", confianza=0.35,
     metodo="inferencia de Agente 1 desde texto publicado (extracto de búsqueda)", lugar="VRAEM (selva)")
note(P, "PE0104", "INFERENCIA: el manual dice 'Al cuarto año de producción (6 años de edad) ... realizar la poda de renovación'; si el 4.º año productivo es a los 6 años, "
     "la primera producción cae a los 2-3 años según se cuente; no es cifra textual; extracto de búsqueda, PDF no descargó")
note(P, "PE0105", "una cifra de declive >15 años se vio solo en un extracto sin URL conservada: no se transcribe; sigue desconocido")
setv(P, "PE0129", valor="", valor_min=1.0, valor_max=1.25, src="UNALM_PINA", tipo_evidencia="analogo_externo", estado="estimado", confianza=0.4,
     metodo=M2A + "; extracto de búsqueda", lugar="selva central")
note(P, "PE0129", "'El tratamiento de inducción floral (TIF) ... permite cosechar a los 12-15 meses de instalado el cultivo'; selva central, cv. Golden; sin dato de Piura")
note(P, "PE0130", "búsqueda R5 sin vida útil (n.º de socas) con fuente; sigue desconocido")
note(P, ["PE0138", "PE0139"], "búsqueda R5 (SENASA BPA naranja leída, sin plazos; solo posts de redes sociales): sigue desconocido")
note(P, "PE0069", "búsqueda R5: ficha MIDAGRI 14 limonero no descargó (repositorio caído) y la guía SENASA BPA limón no da plazo de injerto; Morton 3-6 años es para planta de semilla, el injertado sigue sin cifra")
note(P, "PE0070", "búsqueda R5 sin cifra con fuente; sigue desconocido")
setv(P, ["PE0083", "PE0084"], confianza=0.45)
note(P, ["PE0083", "PE0084"], "L32 verificado en parte: GORE La Libertad 2025 (OCR, p. 8) dice que la primera cosecha 'se ensayan entre el segundo y tercer año'; "
     "Redagrícola Olmos (Lambayeque, Hass) reporta primera cosecha a los 18 meses en un fundo récord (R5P003): es un MÍNIMO empresarial, NO coincide con los 2-3 años típicos; ninguna es de Piura")
rp("anos_a_primera_cosecha_observada", 1.5, "años", "palta", "primera cosecha", "REDAGRI_OLMOS17", "regional", "observado",
   "Olmos (Lambayeque): primera cosecha de Hass a los 18 meses del trasplante en un fundo récord (arena, 40 t/ha de compost, riego tecnificado); MÍNIMO observado, no típico (GORE La Libertad: 2-3 años); solo costa con riego empresarial (chira, san_lorenzo, medio_piura), nunca sierra_piura", 0.3,
   variedad="Hass", lugar="Olmos (Lambayeque)", metodo=M2A)
rp("rendimiento_primera_cosecha", 8, "t/ha", "palta", "primera cosecha", "REDAGRI_OLMOS17", "regional", "estimado",
   "techo empresarial Olmos: el fundo récord (Cholocal) dio 12 t/ha promedio con lotes de 8 t/ha a los 18 meses; otra empresa del mismo artículo (Pampa Baja) proyecta 4-8 t/ha; "
   "valor central 8 = lote más bajo del récord y techo de la proyección (elección de Agente 1 siguiendo a Territorio r5); solo costa con riego empresarial, nunca sierra_piura", 0.3,
   vmin=4, vmax=12, variedad="Hass", lugar="Olmos (Lambayeque)")
setv(P, "PE0085", confianza=0.5)
note(P, "PE0085", "GORE La Libertad 2025 (OCR, p. 12): 'periodo vegetativo mayor a 20 años'; dos fuentes regionales coinciden en >20-25 años")
save(P, "perennes.csv", NP, "R5")

# ============ P3 / P4 fichas anuales ============
A = load("fichas_anuales.csv"); NA = []; ra = new(NA, "R5A")
SIP = dict(variedad="INIA-Sipán (selección de EEA Vista Florida, Lambayeque)", lugar="Pucallpa (Ucayali), suelos de altura", fecha="1998")
ra("dias_a_floracion", 130, "días", "frijol de palo", "floracion", "IIAP_SIPAN", "analogo_externo", "observado",
   "ficha técnica INIA Pucallpa: 'Días a la floración 130 días'; variedad de origen costeño (Vista Florida) evaluada en selva; sin dato de Piura; selva baja, secano: usar solo como orden de magnitud", 0.3, **SIP)
ra("periodo_vegetativo", 15, "meses", "frijol de palo", "ciclo_total", "IIAP_SIPAN", "analogo_externo", "observado",
   "'Período vegetativo 15 meses' (cultivo semiperenne, cosecha escalonada); en selva; el calendario DRAP de Piura da desfases de 1-6 meses porque mide cosechas sucesivas; selva baja, secano: usar solo como orden de magnitud", 0.3, **SIP)
ra("inicio_cosecha", "", "meses", "frijol de palo", "cosecha", "IIAP_SIPAN", "analogo_externo", "observado",
   "'A los 6-7 meses se inicia la cosecha escalonada, según la maduración de las vainas'; selva; selva baja, secano: usar solo como orden de magnitud", 0.3, vmin=6, vmax=7, **SIP)
ra("rendimiento_grano_seco", 2.5, "t/ha", "frijol de palo", "cosecha", "IIAP_SIPAN", "analogo_externo", "observado",
   "'Rendimiento. 2,5 t/ha de grano seco y de 5 a 7 t/ha de grano verde'; paquete tecnológico (no promedio de campo); otro ensayo del mismo documento dio 1.2 t/ha a 1x1 m; selva baja, secano: usar solo como orden de magnitud", 0.3, vmin=1.2, vmax=2.5, **SIP)
ra("rendimiento_grano_verde", "", "t/ha", "frijol de palo", "cosecha", "IIAP_SIPAN", "analogo_externo", "observado",
   "'de 5 a 7 t/ha de grano verde'; paquete tecnológico en selva; selva baja, secano: usar solo como orden de magnitud", 0.3, vmin=5, vmax=7, **SIP)
note(A, "R3A0121", "INIA-Sipán (análogo de selva, R5A): floración 130 d, cosecha escalonada desde 6-7 meses, período vegetativo 15 meses; no da etapas FAO, por eso duracion_etapa sigue desconocida")
note(A, "R3A0120", "3 búsquedas R5 (Tavily) sin Kc medido de frijol de palo fuera del lisímetro de Vidarbha ya citado; sigue desconocido")
note(A, ["AN0434", "AN0435"], "búsquedas R5 sin etapas ni Kc de zarandaja (Lablab purpureus) con fuente primaria; sigue desconocido")
note(A, "R3A0168", "búsqueda R5 (FBN costa norte) sin kg N/ha medidos en Perú; sigue desconocido")
note(A, "R3A0169", "L22: búsqueda R5 sin medición de FBN de caupí en Piura; la tesis UNITRU citada por Territorio sigue sin poder leerse; sigue desconocido")
ra("ece_sin_sintomas_genotipos_seleccionados", 3, "dS/m", "yuca", "ciclo", "SG99", "analogo_externo", "observado",
   "Shannon y Grieve 1999 (Indira y Ramanujam 1982): 6 selecciones con K:Na foliar >15 se establecieron en campo a ECe 3 dS/m (pH 8.65) sin quemadura ni necrosis; "
   "dice 'sin síntomas', no 'sin pérdida de rendimiento'; India; no es umbral", 0.35, lugar="India (campo)", metodo="transcripción de revisión bibliográfica")
ra("ece_rend_50pct_campo", 0.7, "dS/m", "yuca", "ciclo", "SG99", "analogo_externo", "observado",
   "Shannon y Grieve 1999 citan ensayos de campo de largo plazo en Colombia (Anon. 1976 vía Hawker y Smith 1982): incluso cultivares 'putativamente tolerantes' perdieron ~50 % del rendimiento a ECe 0.7 dS/m; "
   "cita de tercera mano ('Anon. 1976' no figura en la bibliografía de SG99; no se sabe si es ECe o ECw; Hawker y Smith en invernadero dan -50 % a 30-50 mM NaCl); contradice el umbral CPIC 3.0 dS/m (MS), que sigue siendo el central (3.0/7.7); NO usar como umbral ni pendiente, solo como alerta", 0.2,
   fecha="1976", lugar="Colombia (campo)", metodo="transcripción de revisión bibliográfica")
w5 = pd.read_csv(os.path.join(PM, "calendario_siembra_cosecha_piura.csv"), dtype=str, keep_default_na=False)
for i in [f"R3A{k:04d}" for k in range(122, 131)]:
    c = A.loc[ix(A, i), "cultivo"]; s = w5[w5.crop == c]
    txt = "; ".join(f"{z}: {v}" for z, v in zip(s.zona, s.ventana_siembra_observada) if v) or "sin filas en el calendario DRAP para este cultivo"
    note(A, i, f"M27: ventanas de siembra OBSERVADAS por zona en calendario_drap_piura.csv y para_motor/calendario_siembra_cosecha_piura.csv (DRAP 2016-2024): {txt}; "
         "son meses con >=10 % de las ha sembradas, no fechas recomendadas; esta fila sigue como estaba (sin fecha normativa)")
save(A, "fichas_anuales.csv", NA, "R5")

# ============ P4 recuperación de suelos (M24) ============
S = load("recuperacion_suelo.csv"); NS = []; rs = new(NS, "R5S")
MOCH = "; COMPARABILIDAD: Mochumí es análogo solo de bajo_piura (quizá bajo Chira) con drenaje operativo previo al lavado; 18 000 m3/ha supone un dren funcional; un solo ensayo con agua de Tinajones; no vale para medio/alto Piura ni sierra"
PAS = dict(lugar="Mochumí, parte baja del valle Chancay (Lambayeque)", fecha="abr 2018-ene 2019", metodo="ensayo de campo, BCA; transcripción de tesis")
rs("ce_1_1_inicial", "", "dS/m", "", "", "PASACHE21", "regional", "observado",
   "CE en extracto suelo:agua 1:1 (NO es ECe de pasta saturada; no convertir sin calibración); evaluación 1 (24 abr 2018) antes de enmiendas: 26.22-41.86 dS/m según tratamiento (Figura 8 y texto); suelo 'fuertemente salino'; fuera del rango calibrado de las ecuaciones CE1:1->ECe: solo orden de magnitud, no comparable" + MOCH, 0.5,
   vmin=26.22, vmax=41.86, manejo="diagnóstico inicial", propiedad="CE 1:1", direccion="", plazo="", **PAS)
rs("ce_1_1_final_tras_lavado", 3.36, "dS/m", "", "", "PASACHE21", "regional", "observado",
   "CE 1:1 más baja al final (eval. 5, 28 dic 2018): 3.36 dS/m (yeso 12 t/ha) y 3.71 (yeso 8 t/ha); el primer lavado (1500 m3/ha) bajó la CE en TODOS los tratamientos, con o sin enmienda: "
   "el efecto es del lavado con drenaje, no del mejorador; el estiércol no influyó en la CE; equivale a ECe ~6.4-11.1 dS/m según textura (fila ece_final_estimada): el suelo 'recuperado' SIGUE salino para maíz" + MOCH, 0.5,
   vmin=3.36, vmax=3.71, manejo="lavado 12 riegos x 1500 m3/ha + yeso o azufre + estiércol 20 t/ha", propiedad="CE 1:1", direccion="reduce", plazo="8 meses", **PAS)
rs("lamina_lavado_total", 18000, "m3/ha", "", "", "PASACHE21", "regional", "observado",
   "12 lavados de 1500 m3/ha (150 mm) cada 22-25 días = 18 000 m3/ha (1800 mm) en ~8 meses; con drenaje funcional; agua de riego del valle" + MOCH, 0.55,
   manejo="lavado con drenaje", propiedad="volumen de agua", direccion="", plazo="8 meses", **PAS)
rs("psi_final", 10.57, "%", "", "", "PASACHE21", "regional", "observado",
   "PSI final más bajo 10.57 con azufre 6 t/ha + estiércol 20 t/ha; el testigo (solo estiércol) terminó en PSI 22.44 (fila psi_final_testigo; no es un rango); yeso 12 t/ha bajó el PSI y los demás lo mantuvieron; suelo muy variable (bloques 13.6-28.4)" + MOCH, 0.5, manejo="azufre 6 t/ha + estiércol 20 t/ha + lavado", propiedad="PSI", direccion="reduce", plazo="8 meses", **PAS)
rs("dosis_yeso_ensayada", "", "t/ha", "", "", "PASACHE21", "regional", "observado",
   "dosis calculadas por requerimiento de yeso según el PSI de cada parcela: 8, 12 y 22 t/ha (azufre 4 y 6 t/ha por bibliografía); son dosis de diseño, no óptimos" + MOCH, 0.5,
   vmin=8, vmax=22, manejo="yeso agrícola + lavado", propiedad="dosis", direccion="", plazo="", **PAS)
rs("germinacion_maiz_indicador", 64.92, "%", "maiz amarillo duro", "germinacion", "PASACHE21", "regional", "observado",
   "test biológico tras la recuperación: germinación promedio de maíz 64.92 %; indicador de recuperación parcial, no rendimiento" + MOCH, 0.5,
   manejo="siembra de maíz indicador tras recuperación", propiedad="germinación", direccion="", plazo="tras 8 meses", **PAS)
rs("reduccion_CE_laboratorio", 78.86, "%", "", "", "SECHURA26", "medicion_local", "observado",
   "LABORATORIO, no campo: estiércol de conejo a 50-100 g por 50 g de suelo (dosis irreal a escala de campo) bajó la CE de 9.98 a 2.11 mS/cm (capa Ap, -78.86 %) y de 8.37 a 2.24 (capa Cg, -73.24 %) en 14 días; "
   "estiércol de chivo y compost: -14 a -21 %; revista con arbitraje no verificado y referencias que no pude comprobar; laboratorio; no extrapolar a campo", 0.2,
   vmin=73.24, vmax=78.86, lugar="Zona agraria Sol, Sechura (Bajo Piura)", fecha="2026", metodo="ensayo de laboratorio; transcripción del resumen",
   manejo="enmienda orgánica (estiércol de conejo)", propiedad="CE", direccion="reduce", plazo="14 días")
rs("psi_final_testigo", 22.44, "%", "", "", "PASACHE21", "regional", "observado",
   "PSI final del testigo (solo estiércol 20 t/ha + lavado), sin enmienda química; referencia para comparar con R5S004" + MOCH, 0.5,
   manejo="estiércol 20 t/ha + lavado (testigo)", propiedad="PSI", direccion="", plazo="8 meses", **PAS)
rs("ece_final_estimada", "", "dS/m", "", "", "SPITERI24", "bibliografico", "estimado",
   "CE 1:1 final 3.36-3.71 (R5S002) convertida con las 5 ecuaciones de la Tabla 4 citadas por Territorio: Sonmez arcilla 2.03x-0.41 -> 6.4; franco 2.15x-0.44 -> 6.8; Zhang 1.79x+1.46 -> 7.5-8.1; arena 2.72x-1.27 -> 7.9-8.8; USDA 3.0x -> 10.1-11.1; "
   "textura no reportada en la fila; Territorio escribió 5.9 como mínimo pero mi recálculo da 6.4; coeficientes no verificados por Agente 1 en el original (Zhang 2005: solo vi el resumen)" + MOCH, 0.25,
   vmin=6.4, vmax=11.1, metodo="cálculo propio con ecuaciones publicadas (no verificadas en el original)", lugar=PAS["lugar"], fecha=PAS["fecha"],
   manejo="lavado 12 x 1500 m3/ha + enmiendas", propiedad="ECe equivalente", direccion="", plazo="8 meses")
note(S, ["RS009", "RS010", "RS011"], "dato peruano de campo (R5S, Pasache 2021, Mochumí-Lambayeque): con drenaje, 1 lavado de 150 mm bajó la CE 1:1 de 26-42 a <8 dS/m y 1800 mm en 8 meses la dejaron en 3.4-3.7")
note(S, "RS013", "dato peruano (R5S): en Mochumí se ensayaron 8-22 t/ha de yeso calculadas por PSI; yeso 12 t/ha y azufre 6 t/ha bajaron el PSI en 8 meses, pero no por debajo de 10")
note(S, "RS014", "dato peruano (R5S): en 8 meses con azufre 6 t/ha el PSI llegó a 10.57 (testigo 22.44): la recuperación sódica no se completó en una campaña")
save(S, "recuperacion_suelo.csv", NS, "R5")

# ============ P5 reglas de rotación ============
R = load("reglas_rotacion.csv"); NR = []; r5 = new(NR, "R5R")
def regla(prev, sig, tipo, cond, efecto, *a, **k): r5(*a, cultivo_previo=prev, cultivo_siguiente=sig, tipo_efecto=tipo, condicion=cond, efecto=efecto, regla_id="", **k)
regla("pimiento/paprika", "pimiento/paprika; piquillo; otros hospedantes de Meloidogyne", "nematodo",
      "parcela previa con capsicum en Piura", "riesgo de inóculo de M. incognita y M. arenaria para el siguiente hospedante; magnitud desconocida",
      "presencia_Meloidogyne_documentada", "sí", "categoría", "pimiento/paprika", "ciclo", "COSSIO18", "regional", "observado",
      "tesis UNP: en capsicums de Piura y Lambayeque se identificaron M. incognita y M. arenaria; M. arenaria (A2) es la especie más frecuente en la costa norte; sin daño cuantificado", 0.45, lugar="Piura")
regla("melon", "cucurbitáceas u hortalizas hospedantes", "nematodo", "parcela previa con melón en Chulucanas (Alto Piura)",
      "riesgo de inóculo de M. ethiopica y M. arenaria; magnitud desconocida",
      "presencia_Meloidogyne_documentada", "sí", "categoría", "melon", "ciclo", "COSSIO18", "regional", "observado",
      "tesis UNP: en melón de Chulucanas se identificaron M. ethiopica (E3) y M. arenaria; melón no está en el catálogo de anuales de Agente 1", 0.45, lugar="Chulucanas (Alto Piura)")
regla("uva de mesa", "replante de vid o cultivo hospedante intercalado/siguiente", "nematodo", "parcela con parrón en Piura",
      "inóculo de Meloidogyne diverso; patrones sensibles (Harmony, MGT) murieron por nematodos según un asesor; magnitud desconocida",
      "presencia_Meloidogyne_documentada", "sí", "categoría", "uva de mesa", "ciclo", "ALBAN18", "regional", "observado",
      "tesis UNP: en uva de Piura predomina M. morocciensis, luego M. arenaria y M. incognita; M. ethiopica solo en Huápalas (Alto Piura); Redagrícola 2021 (cualitativo): hoy se planta con Salt Creek o Ramsey", 0.45, lugar="Piura")
regla("pimiento/paprika", "pimiento/paprika; piquillo; otros hospedantes de Meloidogyne", "nematodo",
      "parcela previa con capsicum en Lambayeque", "riesgo de inóculo de M. incognita y M. arenaria para el siguiente hospedante; magnitud desconocida",
      "presencia_Meloidogyne_documentada", "sí", "categoría", "pimiento/paprika", "ciclo", "COSSIO18", "regional", "observado",
      "tesis UNP: en capsicums de Piura y Lambayeque se identificaron M. incognita y M. arenaria; M. arenaria (A2) es la especie más frecuente en la costa norte; sin daño cuantificado; Lambayeque no es Piura: análogo regional costa norte", 0.45, lugar="Lambayeque")
note(R, ["RR058", "RR059", "RR060"], "búsqueda R5 (tesis UNP/UNALM, INIA, CGIAR): sin cuantificación peruana de arroz-leguminosa ni arroz-maíz; solo práctica cualitativa (R5R)")
note(R, ["RR058", "RR059", "RR060"], "práctica local (MIDAGRI, catálogo de leguminosas, extracto): el frijol bayo se siembra en rotación con arroz, maíz o algodón en la costa norte; efecto en rendimiento no publicado; no encontré ensayo peruano con testigo en monocultivo (r5: la fila vacía R5R004 se eliminó)")
note(R, ["RR038"], "R5: DRAP solo da siembras por distrito, no por parcela: no permite medir rotaciones reales")
save(R, "reglas_rotacion.csv", NR, "R5")
