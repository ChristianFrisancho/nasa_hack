"""Ronda 6: columna zona del CONTRATO en todos los CSV (cultivos/ y para_motor/), zonas_aplicables, filas C (fuentes de Territorio, ECe/Kc). Idempotente."""
import os, glob, re, pandas as pd
from fuentes import F
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")
ZV = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura", "medio_bajo_piura", "piura_region", ""}
COSTA = "chira;san_lorenzo;medio_piura;bajo_piura;alto_piura"
def load(n): return pd.read_csv(os.path.join(D, n), dtype=str, keep_default_na=False)
def tag(t): return t if t.startswith("[R6]") else "[R6] " + t
def note(df, ids, t):
    m = df.id.isin([ids] if isinstance(ids, str) else ids) if not callable(ids) else ids(df)
    t = tag(t); df.loc[m, "notas"] = df.loc[m, "notas"].apply(lambda s: s if t in s else (s + "; " + t if s else t))
def add(df, rows):
    df = df[~df.id.str.startswith("R6")]
    for c in {k for r in rows for k in r} - set(df.columns): df[c] = ""
    return pd.concat([df, pd.DataFrame(rows).reindex(columns=df.columns, fill_value="")], ignore_index=True)
def row(i, var, val, u, cult, etapa, key, tipo, est, nota, conf, vmin="", vmax="", **k):
    s, url = F[key]; x = dict(id=i, variable=var, valor=str(val), valor_min=str(vmin), valor_max=str(vmax), unidad=u, cultivo=cult, etapa=etapa,
        fuente=s, url_o_doi=url, tipo_evidencia=tipo, estado=est, notas=tag(nota), confianza=str(conf), metodo="transcripción de texto publicado")
    x.update({a: str(b) for a, b in k.items()}); return x
# ---------------- C: recuperación de suelos con fuentes que dejó Territorio ----------------
S = load("recuperacion_suelo.csv")
FU = "OCR de segunda mano sin página (buscador web), no cotejado con el PDF; extracto de Territorio en suelos/fuentes/"
BP = dict(lugar="Bajo Piura (valle, ~40 000 ha)", fecha_o_periodo="informe 1990", zona="bajo_piura")
MB = dict(lugar="Valle Medio y Bajo Piura (pozos IRHS y SEV)", fecha_o_periodo="2004-2015 (informe oct 2015)", zona="medio_bajo_piura")
S = add(S, [
 row("R6S001", "ece_clase_afectacion_dominante", "", "dS/m", "", "", "FAO_UNALM90", "regional", "observado",
     "'los valores más altos de área son dos niveles de afectación de la salinidad del suelo: < 4 mmhos/cm y entre 4-12 mmhos/cm'; usar 4-12 dS/m solo como ESCENARIO de clase para bajo_piura, no como ECe de parcela; no da % de área por clase; " + FU, 0.3,
     vmin=4, vmax=12, propiedad="ECe (clase de afectación)", manejo="diagnóstico (sin manejo)", **BP),
 row("R6S002", "fraccion_area_napa_menor_2m_pre_poechos", "", "%", "", "", "FAO_UNALM90", "regional", "observado",
     "'en el periodo previo a la construcción y funcionamiento del reservorio [Poechos], entre el 50% y 80% de la superficie total del Bajo Piura tenía el nivel freático a menos de 2 m de profundidad, variación que dependía de la época del año'; " + FU, 0.3,
     vmin=50, vmax=80, propiedad="profundidad de napa", manejo="diagnóstico (sin manejo)", **BP),
 row("R6S003", "longitud_drenes_abiertos", 450, "km", "", "", "FAO_UNALM90", "regional", "observado",
     "sistema principal de drenaje terminado en 1977: 164 km de colectores rehabilitados + 97 km nuevos + 195 km de drenes secundarios; sin drenes parcelarios (condiciona el lavado: sin dren parcelario funcional los análogos de lavado no aplican); " + FU, 0.3,
     propiedad="drenaje", manejo="infraestructura de drenaje", **BP),
 row("R6S004", "ce_agua_subterranea", "", "dS/m", "", "", "ANA_ERH15", "regional", "observado",
     "'La conductividad eléctrica en el área de estudio fluctúa entre 0,04 (IRHS-46 – Piura) y 16.83 mmhos/cm (IRHS-68 – Catacaos)' (pág. 102 y 118); es CE del AGUA de pozos (ECw), NO ECe del suelo; aguas de riego C3S1 a C3S4", 0.5,
     vmin=0.04, vmax=16.83, metodo="CE de agua de pozo (inventario IRHS); transcripción", propiedad="ECw de agua subterránea", manejo="diagnóstico (sin manejo)", **MB),
 row("R6S005", "nivel_estatico_pozos", "", "m", "", "", "ANA_ERH15", "regional", "observado",
     "'valores de profundidad mayores a los 30 metros en pozos de los Distritos de Piura, Castilla y Catacaos. Para el resto de zonas investigadas ... entre los 15 hasta los 30 metros' (pág. 110); acuífero explotado por bombeo, NO la napa colgada bajo parcelas regadas (ver R6S006)", 0.45,
     vmin=15, vmax=30, propiedad="nivel estático de pozos", manejo="diagnóstico (sin manejo)", **MB),
 row("R6S006", "napa_freatica_sev_mediana", 2.3, "m", "", "", "ANA_ERH15", "regional", "estimado",
     "mediana de 41 SEV con dato (Cuadros 7.6-7.18, secciones 1-7, 12 y 13), p25-p75 0.6-6.0 m; 20 de 41 bajo 2 m y 11 bajo 1 m; cálculo de Territorio que no rehíce; geofísica indirecta, sin estación del año ni ubicación por SEV (no separa Medio de Bajo Piura); excluye secciones 8-11 (114-285 m, bordes desérticos)", 0.4,
     vmin=0.6, vmax=6.0, metodo="mediana y p25-p75 calculados por Territorio sobre tablas publicadas", propiedad="profundidad de napa", manejo="diagnóstico (sin manejo)", **MB),
])
S.to_csv(os.path.join(D, "recuperacion_suelo.csv"), index=False)
# ---------------- C: perennes (mango ECe y Kc; banano Kc) ----------------
P = load("perennes.csv")
KENT = dict(variedad="Kent", lugar="Submedio São Francisco (Petrolina-Juazeiro, Brasil), semiárido con riego", fecha_o_periodo="Silva 2019 (citado en 2022)", fuente_primaria="Silva 2019 (según Cavalcante 2022)")
KN = "Kc medido en mango 'Kent' (variedad principal de Piura) en clima semiárido con riego; COMPARABILIDAD: latitud ~9 S y ETo alta como Piura, pero otro manejo de floración; sin duraciones de etapa en días"
P = add(P, [
 row("R6P001", "ece_inicio_problemas", 1.4, "dS/m", "mango", "ciclo", "DZ_SJAR03", "analogo_externo", "observado",
     "Durán Zuazo 2003 p. 72 cita a Embleton y Jones 1966: problemas desde ECe ~1.4 dS/m; COMPARABILIDAD: dato antiguo de otra región (EE.UU.), depende del portainjerto; es inicio de síntomas, no umbral de rendimiento; el defecto S 1.3 queda coherente", 0.35, fuente_primaria="Embleton y Jones 1966 (según Durán Zuazo 2003)", lugar="no indicado (cita)"),
 row("R6P002", "ecw_umbral_rendimiento", "", "dS/m", "mango", "ciclo", "DZ_EJA04", "analogo_externo", "observado",
     "umbral 0.88 dS/m (1996-97) y 1.81 dS/m (1998-99) en agua de riego, cv. Osteen sobre Gomera-1/3; COMPARABILIDAD: Almuñécar (España), terraza a 140 m; probablemente ECw, no ECe; resumen citado por Territorio, Agente 1 no abrió el artículo (cerrado)", 0.3,
     vmin=0.88, vmax=1.81, variedad="Osteen", lugar="Almuñécar (Granada, España)", fecha_o_periodo="1996-1999"),
 row("R6P003", "pendiente_rendimiento_ecw", "", "%/(dS/m)", "mango", "ciclo", "DZ_EJA04", "analogo_externo", "observado",
     "pendiente b 17.1 %/(dS/m) en 1996-97 y 12.5 en 1998-99; mismas salvedades que R6P002 (ECw probable, España, resumen de segunda mano)", 0.3,
     vmin=12.5, vmax=17.1, variedad="Osteen", lugar="Almuñécar (Granada, España)", fecha_o_periodo="1996-1999"),
 row("R6P004", "kc", 0.88, "adimensional", "mango", "vegetativo", "CAVALCANTE22", "analogo_externo", "observado", KN + "; Tabla 9", 0.4, **KENT),
 row("R6P005", "kc", 0.84, "adimensional", "mango", "floracion", "CAVALCANTE22", "analogo_externo", "observado", KN + "; Tabla 9", 0.4, **KENT),
 row("R6P006", "kc", 0.81, "adimensional", "mango", "caida_de_frutos", "CAVALCANTE22", "analogo_externo", "observado", KN + "; Tabla 9", 0.4, **KENT),
 row("R6P007", "kc", 0.73, "adimensional", "mango", "formacion_y_maduracion_fruto", "CAVALCANTE22", "analogo_externo", "observado", KN + "; Tabla 9", 0.4, **KENT),
 row("R6P008", "kc", 1.12, "adimensional", "banano", "periodo_critico_ago_dic", "MONGE22_BAN", "analogo_externo", "observado",
     "Kc 1.12 en la época crítica (agosto-diciembre) medido con lisímetros de drenaje, banano Williams; COMPARABILIDAD: trópico húmedo (Quevedo, Ecuador), etapa fenológica no indicada en el resumen; mayor que FAO-56 media 1.1 del año 1", 0.35,
     variedad="Williams", lugar="Quevedo (Los Ríos, Ecuador)", metodo="lisímetro de drenaje (según resumen)"),
])
note(P, lambda d: (d.cultivo == "mango") & d.variable.str.startswith("ece_umbral"), "R6: única ECe de mango con fuente citada es 1.4 dS/m (Embleton y Jones 1966 vía Durán Zuazo 2003, R6P001); umbral de rendimiento solo en agua (R6P002/3); se mantiene el defecto S")
P.to_csv(os.path.join(D, "perennes.csv"), index=False)
# ---------------- C: anuales (frijol de palo ECe; caupí FBN UNITRU) ----------------
A = load("fichas_anuales.csv")
PK = "COMPARABILIDAD: ensayo en macetas en Pakistán, variedades locales; leído solo en el extracto del buscador (PDF con timeout); sugiere más sensibilidad que el defecto S 1.3/(pendiente CPIC)"
A = add(A, [
 row("R6A001", "ece_muerte_antes_madurez", "", "dS/m", "frijol de palo", "ciclo", "PAKBOT16_CAJ", "analogo_externo", "observado",
     "las plantas murieron antes de madurar a ECe 3.8-4.3 dS/m; " + PK, 0.25, vmin=3.8, vmax=4.3, lugar="Pakistán (macetas)", metodo="transcripción de extracto de buscador"),
 row("R6A002", "reduccion_peso_semilla_pct_a_ece_3_5", 88, "%", "frijol de palo", "cosecha", "PAKBOT16_CAJ", "analogo_externo", "observado",
     "a ECe 3.5 dS/m: flores -72 %, vainas -70 %, número de semillas -80 %, peso de semillas -88 %; " + PK, 0.25, lugar="Pakistán (macetas)", metodo="transcripción de extracto de buscador"),
 row("R6A003", "efectividad_simbiotica_cepas_nativas", "", "categoría", "frijol caupi", "ciclo", "UNITRU13", "regional", "observado",
     "resumen de tesis UNT: ensayo de campo oct-dic 2012 (26-30 °C); las cepas Rc 455-02 y Rc 391-01 fueron las más efectivas; el resumen NO dice el lugar (Territorio lo citó como Piura: sin confirmar) ni da kg N/ha; cualitativo", 0.2,
     lugar="no indicado en el resumen", fecha_o_periodo="oct-dic 2012", metodo="lectura del resumen (ALICIA)"),
])
note(A, lambda d: (d.variable == "fbn_medicion_piura"), "R6 (r3 L22): resumen de la tesis UNT leído (R6A003): cepas efectivas, sin kg N/ha ni lugar declarado; sigue desconocido")
note(A, lambda d: d.cultivo.isin(["frijol de palo", "zarandaja"]) & d.variable.isin(["kc", "duracion_etapa"]), "R6: 2 búsquedas más (Kc lisimétrico de frijol de palo; Kc de Lablab purpureus) sin cifras; sigue desconocido")
A.to_csv(os.path.join(D, "fichas_anuales.csv"), index=False)
# ---------------- R5R001b: id estable para la fila de Lambayeque ----------------
R = load("reglas_rotacion.csv"); m = (R.id == "R5R004") & (R.lugar == "Lambayeque"); R.loc[m, ["id", "regla_id"]] = "R5R001b"; R.to_csv(os.path.join(D, "reglas_rotacion.csv"), index=False)
# ---------------- A: columna zona en todos los CSV de datos ----------------
OVR = {"PE0015": ("chira", ""), "PE0031": ("chira", ""), "R5P001": ("piura_region", "chira;medio_piura;san_lorenzo"), "PE0053": ("piura_region", "chira;medio_piura;san_lorenzo"),
       "R5P003": ("", "chira;san_lorenzo;medio_piura"), "R5P004": ("", "chira;san_lorenzo;medio_piura"),
       "R5R002": ("alto_piura", ""), "R5R003": ("alto_piura", ""), "R5R001": ("piura_region", ""), "R5R001b": ("", COSTA)}
REG = [(r"medio y bajo piura", "medio_bajo_piura", ""), (r"mochum", "bajo_piura", "bajo_piura;chira"), (r"olmos", "", "chira;san_lorenzo;medio_piura"),
       (r"chira|sullana|paita", "chira", ""), (r"alto piura|chulucanas|morrop|huápalas|huapalas", "alto_piura", ""), (r"san lorenzo|tambogrande|las lomas", "san_lorenzo", ""),
       (r"medio piura", "medio_piura", ""), (r"bajo piura|sechura|catacaos", "bajo_piura", ""), (r"sierra|ayabaca|huancabamba", "sierra_piura", ""),
       (r"costa norte \(lambayeque\)|^lambayeque", "", COSTA), (r"piura|costa norte", "piura_region", "")]
def zona_de(r):
    if r.get("id", "") in OVR: return OVR[r["id"]]
    l = r["lugar"].lower()
    for pat, z, za in REG:
        if re.search(pat, l): return z, za
    if l == "" and r["tipo_evidencia"] in ("regional", "medicion_local"): return "piura_region", ""
    return "", ""
cnt = {}
for f in sorted(glob.glob(os.path.join(D, "*.csv"))):
    nm = os.path.basename(f)
    if nm.startswith("respuesta_revision_"): continue
    d = pd.read_csv(f, dtype=str, keep_default_na=False)
    if nm != "calendario_drap_piura.csv":
        zz = d.apply(zona_de, axis=1); z = [a for a, _ in zz]; za = [b for _, b in zz]
        d = d.drop(columns=[c for c in ("zona", "zonas_aplicables") if c in d]); d.insert(list(d.columns).index("etapa") + 1, "zona", z)
        d["zonas_aplicables"] = za
    elif "zonas_aplicables" not in d: d["zonas_aplicables"] = ""
    d = d[[c for c in d.columns if c != "zonas_aplicables"] + ["zonas_aplicables"]]
    assert set(d.zona) <= ZV, (nm, set(d.zona) - ZV)
    d.to_csv(f, index=False); cnt[nm] = d.zona.replace("", "(vacío)").value_counts().to_dict()
# ---------------- A: para_motor ----------------
PMZ = {"fao56_kc_propuesta.csv": "", "nutrientes_cultivo_propuesta.csv": "", "parametros_cultivo_v2_propuesta.csv": "",
       "umbrales_salinidad_defecto_clase.csv": "", "umbrales_salinidad_propuesta.csv": ""}
for nm, z in PMZ.items():
    f = os.path.join(PM, nm); d = pd.read_csv(f, dtype=str, keep_default_na=False)
    k = "crop" if "crop" in d else "cultivo"
    if "zona" not in d: d.insert(list(d.columns).index(k) + 1, "zona", z)
    else: d["zona"] = z
    d.to_csv(f, index=False); cnt["para_motor/" + nm] = d.zona.replace("", "(vacío: genérico, vale para toda la región)").value_counts().to_dict()
for k, v in cnt.items(): print(k, v)
