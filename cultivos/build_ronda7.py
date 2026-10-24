"""Ronda 7: respuesta a revision_agronomia_r6 (Territorio), arveja (salinidad 3.4 FAO-61 vs 1.5 FAO-56; temperatura de floración;
viabilidad tras arroz en Bajo Piura), zonas_aplicables en filas no genéricas. Corre DESPUÉS de build_ronda6.py. Idempotente."""
import os, pandas as pd
from fuentes import F
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")
COSTA = "chira;san_lorenzo;medio_piura;bajo_piura;alto_piura"
SEIS = "alto_piura;medio_piura;bajo_piura;chira;san_lorenzo;sierra_piura"
def load(n): return pd.read_csv(os.path.join(D, n), dtype=str, keep_default_na=False)
def save(df, n): df.to_csv(os.path.join(D, n), index=False)
def tag(t): return t if t.startswith("[R7]") else "[R7] " + t
def note(df, ids, t, col="notas", key="id"):
    m = df[key].isin([ids] if isinstance(ids, str) else ids) if not callable(ids) else ids(df)
    t = tag(t); df.loc[m, col] = df.loc[m, col].apply(lambda s: s if t in s else (s + "; " + t if s else t))
def setv(df, i, **kv):
    m = df.id == i; assert m.sum() == 1, i
    for k, v in kv.items(): df.loc[m, k] = str(v)
def add(df, rows):
    df = df[~df.id.str.startswith("R7")]
    for c in {k for r in rows for k in r} - set(df.columns): df[c] = ""
    return pd.concat([df, pd.DataFrame(rows).reindex(columns=df.columns, fill_value="")], ignore_index=True)
def row(i, var, val, u, cult, etapa, key, tipo, est, nota, conf, vmin="", vmax="", **k):
    s, url = F[key]; x = dict(id=i, variable=var, valor=str(val), valor_min=str(vmin), valor_max=str(vmax), unidad=u, cultivo=cult, etapa=etapa,
        fuente=s, url_o_doi=url, tipo_evidencia=tipo, estado=est, notas=tag(nota), confianza=str(conf), metodo="transcripción de texto publicado")
    x.update({a: str(b) for a, b in k.items()}); return x
CAL = load("calendario_drap_piura.csv")
def drap(c): return ";".join(z for z in SEIS.split(";") if z in set(CAL[CAL.cultivo == c].zona))
DZ = F["DZ_EJA04"]

# ============ recuperacion_suelo (r6 #1-6, #14) ============
S = load("recuperacion_suelo.csv")
NV = "NO VERIFICADO en el original: el repositorio ANA (hdl 20.500.12543/1535) rechaza la conexión y no hay copia en Wayback; fragmentos OCR sin página"
setv(S, "R6S001", variable="ece_clases_mayor_area", valor_min="", valor_max=12, confianza=0.3, estado="estimado",
     notas=tag("'los valores más altos de área son dos niveles de afectación de la salinidad del suelo: < 4 mmhos/cm y entre 4-12 mmhos/cm': DOS clases (<4 y 4-12 dS/m), proporción de área de cada una desconocida; no usar 4-12 como clase dominante ni como ECe de parcela (Territorio r6 #2); " + NV))
setv(S, "R6S002", confianza=0.3, estado="estimado", notas=tag("'entre el 50% y 80% de la superficie total del Bajo Piura tenía el nivel freático a menos de 2 m de profundidad' antes de Poechos (variaba con la época del año); " + NV))
setv(S, "R6S003", confianza=0.3, estado="estimado", fecha_o_periodo="1977-1990",
     notas=tag("sistema principal de drenaje terminado en 1977: 164 km de colectores rehabilitados + 97 km nuevos + 195 km de drenes secundarios; 'sin drenes parcelarios' describe SOLO la red de 1977-1990; una presentación secundaria (SlideShare, no FAO, sin fecha) menciona una II etapa con 1 605 km de drenes terciarios/parcelarios y 1 368 km entubados: estado actual de drenes parcelarios DESCONOCIDO; " + NV))
note(S, "R6S004", "cita en p. 102 del informe ANA 2015 (verificada por Territorio r6)")
note(S, "R6S005", "cita en p. 110, §10.3.4 del informe ANA 2015 (verificada por Territorio r6)")
note(S, "R6S006", "recalculado por Territorio r6 sobre Cuadros 7.6-7.18: coincide (n=41, mediana 2.3 m, p25-p75 0.6-6.0, 20/41 bajo 2 m, 11/41 bajo 1 m); ambigüedad OCR en SEV 15 (nivel 0.078 con capa 1 de 0-0.60 m)")
setv(S, "R5S009", valor=6.8, valor_min=6.4, valor_max=7.1, metodo="cálculo propio con ecuación publicada (coeficientes verificados por Territorio r6 en el original)",
     notas=tag("CE 1:1 final 3.36-3.71 (R5S002) con Sonmez arcilla 2.03x-0.41 -> ECe 6.4-7.1 (valor central 6.8); textura SUPUESTA arcillosa/franco-arcillosa (no reportada en la fila); envolvente de las 9 ecuaciones de Spiteri y Sacco 2024 Tabla 4: 5.9 (Ozcan 2006, 1.93x-0.57) a 11.1 (USDA 3.0x); las 3 de menor error en esa validación dan 5.9-7.1 (Kargas, Sonmez arcilla, Ozcan); el 5.9 de Territorio en r5 era correcto (Ozcan; nuestra tabla r5 lo omitía); COMPARABILIDAD: Mochumí (Lambayeque) es análogo solo de bajo_piura/bajo Chira con drenaje operativo previo al lavado; un solo ensayo"))
for i in ["R5S001", "R5S002", "R5S003", "R5S004", "R5S005", "R5S006", "R5S008", "R5S009"]:
    setv(S, i, zona="", zonas_aplicables="bajo_piura;chira")
    note(S, i, "zona vacía: el dato se midió en Mochumí (Lambayeque), no en Piura; se aplica a bajo_piura;chira vía zonas_aplicables (Territorio r6 #14)")
save(S, "recuperacion_suelo.csv")

# ============ perennes (r6 #7-10, Durán Zuazo 2004, zonas) ============
P = load("perennes.csv")
OLD = "[R4] Territorio cita Durán Zuazo et al. 2003 (Osteen sobre Gomera-1/3, 4 años: 0.88-1.81 dS/m y 12.5-17.1 %/(dS/m), probablemente ECw) — no verificado por Agronomía (ScienceDirect no descargó)"
NEW = "[R4→R7] Durán Zuazo, Martínez Raya y Aguilar Ruiz 2004, Eur. J. Agron. 21(3):323-334 (doi 10.1016/j.eja.2003.10.004; fuente primaria, en línea 2003): Osteen sobre Gomera-1/3, umbrales 0.88-1.81 dS/m y pendientes 12.5-17.1 %/(dS/m) en base ECw (tratamientos por CE del agua de riego 1.02-2.50 dS/m); 0.88 extrapolado bajo el tratamiento mínimo; ver R6P002-R6P003"
P["notas"] = P.notas.str.replace(OLD, NEW, regex=False)
P["notas"] = P.notas.str.replace("Embleton y Jones 1966 vía Durán Zuazo 2003, R6P001", "Embleton y Jones 1966 vía Durán Zuazo et al. 2003, Span. J. Agric. Res. 1(1), R6P001 (artículo distinto del de Eur. J. Agron. 2004)", regex=False)
ECW = ("umbral 0.88 dS/m (1996-97) y 1.81 dS/m (1998-99), cv. Osteen sobre Gomera-1/3; base ECw CONFIRMADA (los tratamientos son CE del agua de riego 1.02, 1.50, 2.00 y 2.50 dS/m, según el resumen del artículo, fuente primaria); "
       "0.88 está por debajo del tratamiento mínimo (1.02): es extrapolación de la recta; con ECe≈1.5·ECw (FAO-29, FL 15-20 %, sin napa) equivale a ECe ≈1.3-2.7 dS/m, coherente con R6P001 (ECe 1.4); "
       "COMPARABILIDAD: Almuñécar (España), terraza a 140 m, portainjerto distinto de los de Piura")
setv(P, "R6P002", fuente=DZ[0], url_o_doi=DZ[1], metodo="transcripción del resumen publicado (ScienceDirect)", notas=tag(ECW))
setv(P, "R6P003", fuente=DZ[0], url_o_doi=DZ[1], metodo="transcripción del resumen publicado (ScienceDirect)",
     notas=tag("pendiente b 17.1 %/(dS/m ECw) en 1996-97 y 12.5 en 1998-99; en base ECe (÷1.5) ≈ 8.3-11.4 %/(dS/m); mismas salvedades que R6P002 (España, recta extrapolada en el extremo bajo)"))
for i, e in [("R6P004", "vegetativo"), ("R6P005", "floracion"), ("R6P006", ""), ("R6P007", "")]:
    note(P, i, "FAO-56 Tabla 12 no tabula mango: la comparación válida es Paredes et al. 2024 (R3P0059-R3P0076: Kc mid 0.85 densidad baja-media, 0.95 alta); Kent 0.73-0.88 es coherente; en la misma Tabla 9, 4.27/4.98 = 0.86 (no 0.88; quizá promedio de razones diarias); no hay etapa de estrés para la inducción floral")
setv(P, "R6P008", confianza=0.3)
note(P, "R6P008", "corrección r6: el banano de Piura (Chira) es plantación perenne de soca, cubierta por FAO-56 año 2 (PE0017-PE0019, Kc mid 1.20); frente a esa fila, 1.12 es MENOR; viene de trópico húmedo (Quevedo), donde Kc mid es más bajo que en clima árido; no reemplaza PE0017-PE0019; además el resumen no cuadra (227.78 mm al 100 % ETc vs 79.81 mm al 80 %)")
for i in ["R6P001", "R6P002", "R6P003", "R6P004", "R6P005", "R6P006", "R6P007", "R6P008"]:
    setv(P, i, zona="", zonas_aplicables=COSTA)
save(P, "perennes.csv")
f = os.path.join(PM, "umbrales_salinidad_defecto_clase.csv"); u = pd.read_csv(f, dtype=str, keep_default_na=False)
u["notas"] = u.notas.str.replace("(Durán Zuazo 2003 citado por Territorio, no verificado)", "(Durán Zuazo et al. 2004, Eur. J. Agron. 21(3):323-334, doi 10.1016/j.eja.2003.10.004, fuente primaria: 0.88-1.81 dS/m en ECw, ≈1.3-2.7 en ECe)", regex=False)
u.to_csv(f, index=False)

# ============ fichas_anuales: r6 #11-12 + arveja ============
A = load("fichas_anuales.csv")
setv(A, "R6A003", lugar="EEA Vista Florida (INIA), Chiclayo, Lambayeque", zona="", zonas_aplicables=COSTA, fuente=F["UNITRU13"][0], url_o_doi=F["UNITRU13"][1],
     notas=tag("ensayo en la EEA Vista Florida (INIA), km 8 carretera Chiclayo-Ferreñafe, Lambayeque (tesis pp. 21, 25 §3.2.7 y 96 Anexo 37), NO en Piura; dato regional de costa norte; SOLO CUALITATIVO (efectividad de cepas nativas); los rendimientos de la tesis ('71753.29 y 79.335.72 Kg/ha', p. 47) son inverosímiles y no se usan"))
for i in ["R6A001", "R6A002"]:
    setv(A, i, fuente=F["TAYYAB16"][0], url_o_doi=F["TAYYAB16"][1], metodo="transcripción del texto publicado, p. 1354", lugar="Karachi, Pakistán (lisímetros de tambor de 200 kg)", confianza=0.3, zona="", zonas_aplicables=drap("frijol de palo"))
    note(A, i, "PDF completo leído por Territorio r6: a 3.8 y 4.3 dS/m ECe las plantas murieron antes de la madurez reproductiva; a 3.5 dS/m flores -72 %, vainas -70 %, n.º de semillas -80 %, peso -88 %; suelo franco arenoso con sal marina")
# arveja: salinidad
note(A, ["AN0263", "AN0264", "AN0265"], "ALTERNATIVA ROTULADA, NO RECOMENDADA: 1.5/14/S de FAO-56 T23 parece un corrimiento de fila heredado de FAO-48 Tabla 13 ('after Maas 1986', p. 30): Pea muestra 1.5/14.0 'S*' (= valores de Pepper en Maas) y Pepper 1.7/12.0 (= Potato); nota 4 de FAO-48: 'Ratings with an * are estimates'; valor principal 3.4/10.6 MS (R3A0001-R3A0003)")
for i in ["AN0263", "AN0264", "AN0265"]: setv(A, i, confianza=0.2)
note(A, "AN0437", "FAO-61 Anexo 1 sí permite el 50 %: ECe 8.12 dS/m (R3A0004, con 3.4/10.6)")
setv(A, "R3A0001", valor_min=2.5, valor_max=4.5)
note(A, "R3A0001", "VALOR PRINCIPAL (decisión R7): 3.4 dS/m, b 10.6, MS; Grieve, Grattan y Maas 2012 (ASCE Manual 71, Tabla 13-1) lo atribuyen a Cerda, Caro y Fernández 1982 (Agron. J. 74:796-798): lisímetros en Murcia, suelo calcáreo, agua 1.8/4/6/10 dS/m, rendimiento de vaina verde; SP-290 umbral 2.5 (MS) y Durana 4.5 (MT) con igual pendiente (R7A001-R7A002); rango por cultivar 2.5-4.5; variante prudente para cultivar desconocido: 2.5; alternativa FAO-56 1.5 rotulada en AN0263")
A = add(A, [
 row("R7A001", "ece_umbral", 2.5, "dS/m", "arveja", "ciclo", "CERDA82", "analogo_externo", "observado",
     "cv. SP-290, clase MS; misma pendiente que Durana; rendimiento de vaina verde; COMPARABILIDAD: lisímetros con suelo calcáreo en clima mediterráneo; la tolerancia a sales es propiedad del cultivar, aplicable a cualquier zona con riego", 0.5,
     variedad="SP-290", lugar="Murcia, España (lisímetros, suelo calcáreo)", zona="", zonas_aplicables=SEIS, metodo="transcripción del resumen publicado"),
 row("R7A002", "ece_umbral", 4.5, "dS/m", "arveja", "ciclo", "CERDA82", "analogo_externo", "observado",
     "cv. Durana, clase MT; ver R7A001", 0.5, variedad="Durana", lugar="Murcia, España (lisímetros, suelo calcáreo)", zona="", zonas_aplicables=SEIS, metodo="transcripción del resumen publicado"),
 row("R7A003", "temperatura_umbral_estres_reproductivo", "", "°C", "arveja", "floracion", "OSORIO23", "bibliografico", "observado",
     "'>25 °C can harm' el rendimiento; '>27 °C during reproductive development triggers severe abortion' (Lambert y Linck 1958; Guilioni et al. 2003); en campo 'stress-threshold of 28-32 °C'; Jeuffroy et al. 1990: 31 °C; Guilioni et al. 1997: 33/30 °C día/noche; temperatura del aire durante floración-llenado; rango de umbrales de varios estudios, no un valor único", 0.45, vmin=27, vmax=32),
 row("R7A004", "temperatura_optima", "", "°C", "arveja", "ciclo", "SENASA20_ARV", "regional", "observado",
     "'las temperaturas óptimas oscilan entre los 15 y 18 °C' (§3.2); guía nacional, sin zona", 0.45, vmin=15, vmax=18, lugar="Perú (guía nacional SENASA)", zona="", zonas_aplicables=SEIS),
 row("R7A005", "temperatura_max_calidad", 30, "°C", "arveja", "cosecha", "SENASA20_ARV", "regional", "observado",
     "'Temperaturas por encima de los 30°C afectan de manera negativa la calidad del producto cosechado' (§3.2)", 0.45, lugar="Perú (guía nacional SENASA)", zona="", zonas_aplicables=SEIS),
 row("R7A006", "epoca_siembra_costa_sur_chico", "may-jun", "mes", "arveja", "siembra", "SENASA20_ARV", "analogo_externo", "observado",
     "'para las zonas de los valles comprendidos en el sur chico los mejores meses para sembrar son los comprendidos entre mayo a junio' (INIA citado por SENASA, §3.7); sierra: oct-ene grano verde, jul-nov grano seco; COMPARABILIDAD: sur chico (Lima-Ica, ~13 S) es más fresco en invierno que Piura (~5 S); no trasladar los meses a Piura", 0.4,
     lugar="valles del sur chico (costa central-sur, Perú)", zona="", zonas_aplicables=COSTA),
 row("R7A007", "epoca_siembra", "", "mes", "arveja", "siembra", "DRAP_GRP", "regional", "desconocido",
     "DESCONOCIDO: ninguna fuente consultada da época de siembra de arveja para el llano costero de Piura; la estadística DRAP 2016-2024 no registra arveja en bajo_piura ni medio_piura (solo san_lorenzo: Paimas y Suyo, siembra mar-may/jul; y sierra_piura)", 0,
     lugar="Bajo Piura (llano costero)", zona="bajo_piura", zonas_aplicables=""),
 row("R7A008", "tmax_media_normal_jun_nov", "", "°C", "", "", "SENAMHI_PIURA", "regional", "observado",
     "Tmáx media normal SENAMHI 'PIURA': may 30.3, jun 28.3, jul 27.5, ago 27.9, set 28.8, oct 29.5, nov 30.3; Tmín jul-set 17.1; estación y periodo no indicados en la página; contexto: SENAMHI informó que julio de 2026 fue el más cálido registrado en el Perú (las normales subestiman años cálidos)", 0.5,
     vmin=27.5, vmax=30.3, lugar="Piura (normal SENAMHI)", zona="piura_region", zonas_aplicables=""),
 row("R7A009", "tmax_maxima_absoluta_mensual_jun_sep", "", "°C", "", "", "POWER_REPO", "regional", "estimado",
     "máxima ABSOLUTA mensual de NASA POWER (no Tmáx media diaria): medianas 1981-2025 jun 33.6, jul 33.4, ago 33.4, set 33.1; p5-p95 de los 180 meses jun-sep: 31.5-37.0 (extremos 30.2-40.8); los '32-37.5 °C' del brief son estos picos; reanálisis de celda ~0.5x0.625°, sin validar contra estación", 0.4,
     vmin=31.5, vmax=37.0, lugar="Bajo Piura (celda NASA POWER)", zona="bajo_piura", zonas_aplicables="", metodo="medianas y percentiles calculados por Agente 1 sobre el CSV del repo"),
 row("R7A010", "viabilidad_tras_arroz", "marginal", "categoría", "arveja", "ciclo", "SENAMHI_PIURA", "prediccion", "estimado",
     "MARGINAL (inferencia de Agente 1, no fuente directa): arroz de bajo_piura se cosecha jun-jul (calendario DRAP, R5C0229-R5C0230) -> siembra de arveja jul-ago; con FAO-56 (inicial 20 + desarrollo 30 d) la floración cae ~ago-oct, con Tmáx media 27.9-29.5 °C (R7A008), en o sobre el umbral de aborto de 27-28 °C (R7A003) y picos absolutos ~33 °C (R7A009); además ECe frecuente >3.4 dS/m en bajo_piura, suelo de poza de arroz compactado y napa somera; la DRAP no registra arveja en el llano costero; sin ensayo local", 0.3,
     lugar="Bajo Piura (rotación arroz -> arveja)", zona="bajo_piura", zonas_aplicables="", metodo="inferencia de Agente 1 combinando R7A003, R7A008, R7A009, calendario DRAP y FAO-56"),
 row("R7A011", "ventana_siembra_propuesta", "jul", "mes", "arveja", "siembra", "SENAMHI_PIURA", "prediccion", "estimado",
     "siembra inmediata tras la cosecha de arroz de julio, para que la floración (día ~50) caiga en ago-set, los meses de Tmáx media más baja (27.5-28.8 °C); derivada, NO observada ni recomendada por fuente; sembrar en agosto o después lleva la floración a oct (29.5 °C)", 0.3,
     lugar="Bajo Piura (rotación arroz -> arveja)", zona="bajo_piura", zonas_aplicables="", metodo="inferencia de Agente 1 (FAO-56 duraciones + normales SENAMHI)"),
])
# zonas_aplicables en filas no genéricas con zona vacía (regla nueva de validar.py)
ZA = {}
for i in ["AN0410", "AN0411", "AN0412", "AN0413", "AN0414", "AN0415", "AN0416", "AN0417", "AN0418", "AN0446", "AN0447", "AN0448", "AN0449"]: ZA[i] = drap("pimiento/paprika")
for i, c in [("AN0425", "arroz"), ("AN0426", "maiz amilaceo"), ("AN0427", "maiz amarillo duro"), ("AN0428", "trigo"), ("AN0429", "yuca"), ("AN0430", "haba"), ("AN0444", "arroz"), ("AN0445", "arroz")]: ZA[i] = drap(c)
ZA["R3A0160"] = drap("frijol castilla/grano seco"); ZA["R3A0167"] = COSTA
for i in ["R5A001", "R5A002", "R5A003", "R5A004", "R5A005"]: ZA[i] = drap("frijol de palo")
for i in ["R5A006", "R5A007"]: ZA[i] = drap("yuca")
ZN = "zonas_aplicables = zonas donde la DRAP 2016-2024 registra el cultivo (calendario_drap_piura.csv), salvo análogos costeros (solo costa)"
for i, z in ZA.items():
    setv(A, i, zonas_aplicables=z); note(A, i, ZN)
save(A, "fichas_anuales.csv")
P = load("perennes.csv"); ZP = {"PE0094": drap("cacao"), "R5P002": drap("cacao"), "R3P0012": drap("cacao"), "PE0104": drap("cafe"), "R3P0014": drap("cafe"), "R3P0015": drap("cafe"), "PE0129": COSTA}
for i, z in ZP.items():
    setv(P, i, zonas_aplicables=z); note(P, i, ZN if i != "PE0129" else "zonas_aplicables provisional: costa regada; la piña no figura en la estadística DRAP Piura")
save(P, "perennes.csv")

# ============ reglas_rotacion: RR074 a FAO-61 ============
R = load("reglas_rotacion.csv")
s61, u61 = F["F61A1"]
setv(R, "RR074", valor=10.6, valor_min="", valor_max="", fuente=s61, url_o_doi=u61,
     condicion="ECe MEDIDA (extracto saturado) > 3.4 dS/m (cultivar desconocido; 2.5 si SP-290 o variante prudente, 4.5 si Durana) Y napa >=2 m o drenaje funcional; con napa <2 m salina usar ECe medida o escenario de suelos, nunca ECe=1.5·ECw")
note(R, "RR074", "R7: umbral a=3.4 dS/m y b=10.6 %/(dS/m) (FAO-61 Anexo 1; Grieve, Grattan y Maas 2012 Tabla 13-1; Cerda et al. 1982, R3A0001-R3A0002); ALTERNATIVA ROTULADA no recomendada: FAO-56 T23 1.5/14 (AN0263-AN0264), probable corrimiento de fila de FAO-48 Tabla 13")
save(R, "reglas_rotacion.csv")

# ============ para_motor ============
f = os.path.join(PM, "umbrales_salinidad_propuesta.csv"); u = pd.read_csv(f, dtype=str, keep_default_na=False)
m = u.cultivo == "arveja"
t = "[R7] decisión: 3.4/10.6 MS es el principal (Cerda 1982 vía Grieve et al. 2012 Tabla 13-1); por cultivar 2.5 (SP-290) a 4.5 (Durana); FAO-56 1.5/14 queda como alternativa rotulada (probable corrimiento de fila en FAO-48 Tabla 13, p. 30)"
u.loc[m, "notas"] = u.loc[m, "notas"].apply(lambda s: s if t in s else s + "; " + t); u.to_csv(f, index=False)
f = os.path.join(PM, "parametros_cultivo_v2_propuesta.csv"); p = pd.read_csv(f, dtype=str, keep_default_na=False)
p = p[~p.parameter_key.str.endswith("|R7")]
base = p[p.parameter_key == "arveja|Pisum sativum|cosecha|temperatura_adaptacion|ciclo|R32"].iloc[0].to_dict()
t32 = "[R7] la Tmáx media de Piura en jun-oct (27.5-29.5 °C, SENAMHI) no supera 30, pero la floración sufre desde 27-28 °C (ver temperatura_umbral_estres_reproductivo); este límite EcoCrop no basta para juzgar viabilidad"
p.loc[p.parameter_key == base["parameter_key"], "applicability_note"] = p.loc[p.parameter_key == base["parameter_key"], "applicability_note"].apply(lambda s: s if t32 in s else s + "; " + t32)
new = dict(base); new.update(parameter_key="arveja|Pisum sativum|cosecha|temperatura_umbral_estres_reproductivo|floracion|R7", parameter="temperatura_umbral_estres_reproductivo",
    min_value="27.0", max_value="32.0", stage="floracion", geographic_scope="Global; revisión de literatura (Osorio et al. 2023)", source_url=F["OSORIO23"][1],
    applicability_note="[R7] Tmáx del aire en floración-llenado sobre la que hay aborto de óvulos/vainas (>27 °C severo; 28-32 °C umbral de campo); comparar con Tmáx media mensual del mes de floración. En bajo_piura tras arroz (siembra jul-ago, floración ago-oct, Tmáx media 27.9-29.5 °C) la arveja resulta MARGINAL (confianza 0.3); época de siembra en el llano de Piura desconocida; la DRAP solo registra arveja en san_lorenzo y sierra_piura")
p = pd.concat([p, pd.DataFrame([new])], ignore_index=True); p.to_csv(f, index=False)
f = os.path.join(PM, "calendario_siembra_cosecha_piura.csv"); c = pd.read_csv(f, dtype=str, keep_default_na=False)
m = c.applicability_note.str.contains("MARGINAL") & (pd.to_numeric(c.confianza) > 0.4)
c.loc[m, "confianza"] = "0.4"; c.to_csv(f, index=False)
m = CAL.notas.str.contains("MARGINAL") & (pd.to_numeric(CAL.confianza, errors="coerce") > 0.4)
if "confianza" in CAL: CAL.loc[m, "confianza"] = "0.4"; save(CAL, "calendario_drap_piura.csv")
print("R7 ok; MARGINAL ajustadas:", int(m.sum()))

# ============ respuestas previas (r6 #1, #16) ============
def resp(n, hid, accion=None, pre=""):
    d = load(n); m = d.id_hallazgo == hid; assert m.sum() == 1, (n, hid)
    if accion: d.loc[m, "accion"] = accion
    d.loc[m, "justificacion"] = d.loc[m, "justificacion"].apply(lambda s: s if s.startswith(pre) else pre + s); save(d, n)
resp("respuesta_revision_r1.csv", "H02", "pendiente", "[R7] PARCIAL: la parte ANA 2015 está verificada con página (pp. 102 y 110); la parte FAO/UNALM 1990 (R6S001-R6S003) queda pendiente de que alguien con acceso lea el PDF (repositorio ANA cerrado desde nuestra red); R6S001-R6S003 pasan a estimado, conf 0.3. Texto previo: ")
resp("respuesta_revision_r5.csv", "H15", None, "[R7] El aviso ya no aplica: consolidado/motor/motor_rotacion/calendario_obs.py (zonas_de) lee códigos y zonas_aplicables desde la ronda 6. Texto previo: ")

# ============ respuesta_revision_r6.csv ============
SP = "Spiteri y Sacco 2024, doi 10.1080/00103624.2024.2304636, Tabla 4"
R6 = [
 ("H01", "media", "respuesta_revision_r1.csv H02; R6S001-R6S003", "corregido", "H02 pasa a 'pendiente' con la marca PARCIAL: la parte ANA está verificada y la FAO/UNALM queda pendiente de leer el PDF", "hdl 20.500.12543/1535 (inaccesible); revision_agronomia_r6 #1"),
 ("H02", "media", "recuperacion_suelo.csv R6S001", "corregido", "La variable pasa a ece_clases_mayor_area: valor_min vacío y valor_max 12. La nota indica que son DOS clases (<4 y 4-12) con proporción de área desconocida", "cita OCR FAO/UNALM 1990 (suelos/fuentes/FAO_UNALM_1990_BajoPiura_drenaje_salinidad_extracto.md)"),
 ("H03", "media", "recuperacion_suelo.csv R6S001-R6S003", "corregido", "Pasan a estado 'estimado' con conf 0.3 y la nota 'NO VERIFICADO en el original'. Se mantienen como regional (Bajo Piura), pero no se suben de nivel hasta leer el PDF", "revision_agronomia_r6 #3"),
 ("H04", "baja", "recuperacion_suelo.csv R6S003", "corregido", "fecha_o_periodo pasa a 1977-1990. La nota dice que 'sin drenes parcelarios' solo vale para esa red y que el estado actual de los drenes parcelarios es desconocido. Se menciona la II etapa (1 605 km y 1 368 km) que da la fuente secundaria", "https://es.slideshare.net/slideshow/salinidad-y-degradacion-en-el-valle-bajo-piuraptx/275664890 (secundaria)"),
 ("H05", "baja", "recuperacion_suelo.csv R6S006", "corregido", "Nota: 'recalculado por Territorio r6: coincide', con n=41, mediana 2.3 m, p25-p75 0.6-6.0 y la ambigüedad OCR de la SEV 15. También se añaden las páginas de ANA 2015: p. 102 (R6S004) y p. 110 §10.3.4 (R6S005)", "ANA 2015, Cuadros 7.6-7.18, pp. 102 y 110"),
 ("H06", "media", "recuperacion_suelo.csv R5S009", "corregido", "valor 6.8 con rango 6.4-7.1 (Sonmez arcilla 2.03x-0.41 sobre CE 1:1 de 3.36-3.71). La textura arcillosa se supone. La nota da la envolvente de las 9 ecuaciones (5.9-11.1) y reconoce que el 5.9 (Ozcan) era correcto. Lleva doi y método con coeficientes verificados", SP),
 ("H07", "media", "perennes.csv R6P002, R6P003, R4 de mango (Osteen); para_motor/umbrales_salinidad_defecto_clase.csv; fuentes.py DZ_EJA04", "corregido", "Durán Zuazo, Martínez Raya y Aguilar Ruiz 2004, Eur. J. Agron. 21(3):323-334, es fuente primaria y se corrigió en todas las filas (el texto '2003, no verificado' se reemplazó). La base ECw queda confirmada (tratamientos de 1.02 a 2.50 dS/m en el agua). 0.88 es una extrapolación bajo el tratamiento mínimo. En la nota: ECe ≈1.3-2.7 y pendiente ECe ≈8.3-11.4. R6P001 sigue con Durán Zuazo 2003, SJAR, que es otro artículo", "doi 10.1016/j.eja.2003.10.004"),
 ("H08", "media", "perennes.csv R6P001-R6P008", "corregido", "zona vacía y zonas_aplicables chira;san_lorenzo;medio_piura;bajo_piura;alto_piura, sin sierra_piura", "CONTRATO.md; criterio de H04 en respuesta_revision_r5"),
 ("H09", "media", "perennes.csv R6P008", "corregido", "conf 0.3. Nota: es MENOR que FAO-56 año 2 (Kc mid 1.20, PE0017-19), viene de clima húmedo, no reemplaza PE0017-19, y las cifras del resumen no cuadran (227.78 vs 79.81 mm)", "FAO-56 Tabla 12 (https://www.fao.org/4/x0490e/x0490e0b.htm); Monge-Freile 2022"),
 ("H10", "baja", "perennes.csv R6P004-R6P007", "corregido", "Nota: FAO-56 no tabula el mango. La comparación se hace con Paredes 2024 (R3P0059-76; mid 0.85/0.95). Se anota que 4.27/4.98 = 0.86 y que no hay etapa de estrés para la inducción floral", "Paredes et al. 2024 Tabla 6; Cavalcante 2022 Tabla 9"),
 ("H11", "media", "fichas_anuales.csv R6A003; fuentes.py UNITRU13", "corregido", "lugar: EEA Vista Florida (INIA), Chiclayo, Lambayeque (pp. 21, 25, 96); zona vacía; zonas_aplicables de costa. Queda SOLO CUALITATIVO: los rendimientos de 71 753 kg/ha no se usan", "suelos/fuentes/PenaSerrano_2013_UNT_caupi_extracto.md; hdl 20.500.14414/3647"),
 ("H12", "baja", "fichas_anuales.csv R6A001, R6A002; fuentes.py TAYYAB16", "corregido", "Fuente: Tayyab et al. 2016, Pak. J. Bot. 48(4):1353-1360. Método: transcripción de la p. 1354. Lugar: Karachi (lisímetros de tambor de 200 kg). conf 0.3; zonas_aplicables según la DRAP para frijol de palo (alto_piura;chira;sierra_piura)", "https://www.pakbs.org/pjbot/PDFs/48(4)/05.pdf"),
 ("H13", "media", "CONTRATO.md (no editable por Agronomía); validar.py", "corregido", "validar.py ya exige zonas_aplicables cuando la zona está vacía y el dato no es genérico, y prohíbe piura_region y medio_bajo_piura en zonas_aplicables. Texto propuesto para CONTRATO.md (lo integra el coordinador): 'zonas_aplicables (opcional): códigos de zona separados por ;, sin piura_region ni medio_bajo_piura; obligatoria con zona vacía si el dato no es genérico (lugar concreto o tipo regional/medicion_local); un análogo de costa nunca incluye sierra_piura'. Se rellenaron 48 filas (33 en fichas y 15 en perennes) con las zonas de la DRAP para el cultivo", "CONTRATO.md línea 11; consolidado/motor/motor_rotacion/calendario_obs.py"),
 ("H14", "baja", "recuperacion_suelo.csv R5S001-R5S006, R5S008, R5S009", "corregido", "zona vacía, zonas_aplicables bajo_piura;chira, lugar Mochumí (Lambayeque); queda igual que Olmos (R5P003/004). R5S007 (Sechura) sigue en bajo_piura", "CONTRATO.md; R5P003/R5P004"),
 ("H15", "baja", "para_motor/calendario_siembra_cosecha_piura.csv y calendario_drap_piura.csv (filas MARGINAL)", "corregido", "Toda fila con nota MARGINAL y confianza >0.4 baja a 0.4 (arroz sierra_piura, algodón Pima alto_piura y otras)", "applicability_note de cada fila"),
 ("H16", "baja", "respuesta_revision_r5.csv H15", "corregido", "La justificación se reescribe así: el motor consolidado ya lee códigos y zonas_aplicables (calendario_obs.zonas_de)", "consolidado/motor/motor_rotacion/calendario_obs.py"),
 ("H17", "baja", "suelos/revision_agronomia_r3.md (archivo de Territorio, no se reescribe)", "corregido", "Se acepta la autocorrección: la tesis UNT tiene el ensayo en Chiclayo (Lambayeque). En cultivos/ ya quedó corregido (R6A003 y UNITRU13)", "tesis UNT pp. 21 y 25"),
 ("H18", "baja", "suelos/fuentes/DuranZuazo_2003_extracto.md (archivo de Territorio); fuentes.py DZ_EJA04", "corregido", "Se acepta. En cultivos/ la cita es 2004 (en línea 2003), vol. 21(3):323-334, en todas las filas", "doi 10.1016/j.eja.2003.10.004"),
]
pd.DataFrame(R6, columns=["id_hallazgo", "severidad", "filas_afectadas", "accion", "justificacion", "fuente"]).to_csv(os.path.join(D, "respuesta_revision_r6.csv"), index=False)
print("respuesta_revision_r6:", len(R6))
