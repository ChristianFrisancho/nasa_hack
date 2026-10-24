"""Ronda 4 (Agente 1): respuesta a la revisión cruzada de Piura Territorio (suelos/revision_agronomia_r1.*).
Parchea filas de Ronda 1 por id (valores absolutos; notas con marcador [R4] sin duplicar), añade filas R4A/R4R/R4S,
parchea motor_integracion.csv y las notas de para_motor/umbrales_salinidad_*. Idempotente: borra ids R4* antes de añadir.
Orden: build_fichas.py -> build_reglas.py -> build_ronda3.py -> build_ronda4.py. El motor NO se modifica."""
import os, pandas as pd
from fuentes import F
from build_fichas import COLS
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")
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
    txt = "[R4] " + txt
    for i in ids if isinstance(ids, (list, tuple)) else [ids]:
        j = ix(df, i); n = df.loc[j, "notas"]
        if txt not in n: df.loc[j, "notas"] = (n + "; " + txt) if n else txt
def rng(a, b, p="AN"): return [f"{p}{k:04d}" if p in ("AN", "PE") else f"{p}{k:03d}" for k in range(a, b + 1)]
def new(rows, prefix, extra=None):
    def r(variable, valor, unidad, cultivo, etapa, src, tipo, estado, notas, conf, vmin="", vmax="", variedad="", lugar="",
          fecha="", metodo="transcripción de documento publicado", **x):
        cita, u = F[src] if src else ("", "")
        if estado == "desconocido": valor = ""
        d = dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo, variedad=variedad,
                 etapa=etapa, lugar=lugar, lat="", lon="", fecha_o_periodo=fecha, fuente=cita, url_o_doi=u, metodo=metodo,
                 tipo_evidencia=tipo, estado=estado, notas=notas, confianza=conf)
        d.update(x); d["id"] = f"{prefix}{len(rows)+1:03d}"
        if "regla_id" in d: d["regla_id"] = d["id"]
        rows.append(d)
    return r
def save(df, n, rows, pref="R4"):
    df = df[~df.id.str.startswith(pref)]
    out = pd.concat([df, pd.DataFrame(rows, columns=df.columns).fillna("")], ignore_index=True) if rows else df
    out.to_csv(os.path.join(D, n), index=False); print(n, len(df), "+", len(rows), "=", len(out))

LUGAR_ND = "Bajo Piura: Territorio cita CE de napa hasta 16.83 dS/m (ANA, cifra no verificada por Agronomía: ana.gob.pe no descargó)"
# ============ fichas_anuales ============
A = load("fichas_anuales.csv"); A = A[~A.id.str.startswith("R4")].copy(); NA = []; ra = new(NA, "R4A")
ece = A[A.variable.str.startswith("ece_") & A.fuente.str.contains("FAO-29 rev.1, Tabla 4|FAO-56, Tabla 23")].id.tolist()
note(A, ece, "válido para ECe MEDIDA en extracto saturado; FAO-29 deriva ECe=1.5·ECw suponiendo fracción de lavado 15-20 % y sin aporte de napa; "
     "con napa <2 m salina no derivar ECe de ECw; la tolerancia baja en periodos cálidos y secos (FAO-29 cap. 2); " + LUGAR_ND)
# H14 arroz
setv(A, "AN0018", valor="MS", src="F29T5", confianza=0.5)
note(A, "AN0018", "FAO-29 T5 (Maas 1984) pone 'Rice, paddy' en MS (verificado en el texto); FAO-56 T23 da S; misma línea Maas; umbral 3.0 dS/m en el límite MS/MT")
# H17 algodón G. hirsutum
alg = [i for i in rng(87, 91) if i in set(A.id)]
setv(A, alg, confianza=0.5)
note(A, alg, "umbral de G. hirsutum (upland, Maas 1984); en Piura domina Pima (G. barbadense) sin umbral propio en FAO-29/56; aplicar con cautela")
ra("ece_50pct_emergencia", 15.5, "dS/m", "algodon", "germinacion", "F29T7", "bibliografico", "estimado",
   "FAO-29 T7: ECe que reduce 50 % la emergencia; G. hirsutum; la germinación es más sensible que el rendimiento; Pima sin dato", 0.5, variedad="G. hirsutum")
# H13 páprika
setv(A, rng(410, 413), confianza=0.35)
note(A, rng(410, 413), "la suma de etapas (175 d) no cubre la cosecha completa: MIDAGRI da cosecha desde 120 d del trasplante + 45-60 d de cosecha; usar AN0414")
setv(A, "AN0414", valor=202, valor_min=187, valor_max=202, src="MIDAGRI_PAP2", confianza=0.5, metodo="transcripción (extracto de búsqueda del PDF)")
note(A, "AN0414", "periodo vegetativo 202 d (testigo) y 187 d (con Ethrel) en ensayo de Barranca (costa de Lima, no Piura); la fuente no aclara si cuenta desde siembra o trasplante; "
     "reemplaza el total 175 d de Ronda 1. Territorio sugiere 165-210 d desde siembra (folleto no verificado por Agronomía)")
setv(A, rng(446, 448), confianza=0.3)
note(A, rng(446, 448), "base de conteo no confirmada: la fuente cuenta la cosecha desde el trasplante; no sumar como 'desde siembra'")
setv(A, "AN0449", notas="", variable="dias_desde_trasplante_a_fase", src="MIDAGRI_PAP2", confianza=0.45)
note(A, "AN0449", "cosecha 'a partir de los 120 días del trasplante' (verificado en extracto); corrige la lectura 'desde siembra' de Ronda 1")
# H15 caupí INIA 432
setv(A, "AN0422", notas="", valor="mejor comportamiento que variedades locales en suelos en proceso de salinización (cualitativo)", src="SEMPIU432", confianza=0.35)
note(A, "AN0422", "la fuente no dice 'resistente' ni da ECe; usar el umbral FAO-29 de caupí (especie) para cálculos")
setv(A, ["AN0420", "AN0421"], notas="", src="SEMPIU432", confianza=0.55)
note(A, ["AN0420", "AN0421"], "confirmado en la ficha del tríptico (80-100 d; 2000-2500 kg/ha comercial, 3000 potencial; floración 40-45 d); variedad liberada para Piura")
# H16 pH caupí
setv(A, ["AN0431", "AN0432"], confianza=0.3)
note(A, ["AN0431", "AN0432"], "manual de Loreto (trópico ácido): no usar como límite duro en la costa norte, donde el caupí se cultiva en suelos neutros a alcalinos; sin pH máximo verificado para Piura")
# H20
note(A, ["AN0436", "AN0438"], "desconocido explícito: el motor no debe leer la ausencia de umbral como tolerancia; yuca tiene solo clase MS (FAO-61, fila R3)")
# L27 / L28 arroz
setv(A, "AN0423", notas="", src="INIA510_WB", tipo_evidencia="regional", confianza=0.7)
note(A, "AN0423", "'ciclo intermedio, en promedio madura en 148 días, igual que IR 43' (PDF primario leído completo, confirmado por Territorio); 15.5 t/ha experimental en Sullana (Piura); "
     "excepción al tope 0.6 de fuente única por ser documento primario del obtentor, local y verificado por dos agentes")
setv(A, "AN0424", notas="", src="INIA502_WB", tipo_evidencia="regional", confianza=0.6)
note(A, "AN0424", "150-155 d (PDF primario leído completo); evaluado en Lambayeque, La Libertad y Arequipa, no en Piura; siembra oct-ene")
# L30
note(A, ["AN0440", "AN0441"], "PDF no verificado en la revisión cruzada; evaluado en Lambayeque, no en Piura")
# H12 + M11 algodón ventanas
setv(A, "AN0452", variedad="híbridos", lugar="Medio y Bajo Piura")
note(A, "AN0452", "coincide con la ventana de híbridos de RJ 041-2002-AG para Medio y Bajo Piura; Pima siembra 1 ene-28 feb (fila R4A)")
NORMA = "norma de campaña (RM 0251-94-AG y modificatorias); vigencia posterior a 2002 no verificada; fechas transcritas"
for zona, pima, hib, mat, cl, norma in [
    ("Medio y Bajo Piura", "1 ene - 28 feb", "15 mar - 30 abr", "1 set - 15 oct", "16 oct - 31 dic", "RJ 041-2002-AG"),
    ("Alto Piura", "1 mar - 15 abr", "30 abr - 30 may", "1 nov - 15 dic", "16 dic - 28 feb", "RJ 041-2002-AG"),
    ("Valle del Chira", "20 dic - 30 ene", "15 feb - 20 mar", "20 ago - 30 set", "1 oct - 19 dic", "RM 1118-2001-AG"),
    ("San Lorenzo", "1 feb - 15 mar", "1 abr - 15 may", "1 oct - 15 nov", "16 nov - 31 ene", "RM 1118-2001-AG")]:
    for var, v, val in [("ventana_siembra", "Pima", pima), ("ventana_siembra", "híbridos", hib),
                        ("ventana_matado_y_quema", "todas", mat), ("ventana_campo_limpio", "todas", cl)]:
        ra(var, val, "fecha", "algodon", "siembra" if "siembra" in var else "poscosecha", "RM0251", "regional", "observado",
           f"{NORMA}; {norma}", 0.6, variedad=v, lugar=zona)
note(A, "AN0450", "en FEN fuerte las lluvias de ene-abr coinciden con esta ventana (ver R4A FEN)") if "AN0450" in set(A.id) else None
# L33
note(A, "AN0453", "tolerancia a lámina controlada; no aplica a sumersión total prolongada ni a inundación FEN con sedimento o corriente")
# H05 anegamiento
setv(A, rng(454, 459), confianza=0.4)
note(A, rng(454, 459), "válido solo dentro del rango del metaanálisis (anegamiento <=15 d, ensayos controlados); no extrapolar a inundación FEN: en 2017 el agua quedó estancada sin duración publicada (INDECI)")
for c in ["maiz amarillo duro", "algodon", "trigo"]:
    ra("perdida_rendimiento_anegamiento_mas_15d", "", "%", c, "ciclo", "", "bibliografico", "desconocido",
       "fuera del rango de Tian 2021 (<=15 d); sin dato; el motor puede asumir pérdida total como escenario conservador, pero no es una cifra medida", 0)
# H04 FEN
setv(A, ["AN0460", "AN0461"], confianza=0.4)
note(A, ["AN0460", "AN0461"], "criterio de diseño de drenaje superficial, no tolerancia de campo ante FEN (que dejó agua estancada días o semanas)")
ra("area_cultivo_perdida_FEN", 8733, "ha", "todos", "ciclo", "INDECI17", "medicion_local", "observado",
   "Niño Costero 2017, departamento de Piura, registro SINPAD/COEN; cifra única, sin rango", 0.6, lugar="Piura (departamento)", fecha="2017", metodo="transcripción de tabla oficial")
ra("area_cultivo_afectada_FEN", 15342, "ha", "todos", "ciclo", "INDECI17", "medicion_local", "observado",
   "Niño Costero 2017, Piura; afectada = con daño parcial (distinta de perdida); SINPAD/COEN", 0.6, lugar="Piura (departamento)", fecha="2017", metodo="transcripción de tabla oficial")
ra("caudal_maximo_rio_Piura_FEN", 3800, "m3/s", "todos", "ciclo", "INDECI17", "medicion_local", "observado",
   "pico del 27 mar 2017; desborde afectó todo el Bajo Piura; lluvias desde el 29 ene", 0.55, lugar="río Piura", fecha="2017-03-27", metodo="transcripción de crónica oficial")
ra("duracion_anegamiento_FEN", "", "días", "todos", "ciclo", "INDECI17", "medicion_local", "desconocido",
   "INDECI no publica cuántos días quedó el agua estancada en 2017; no se rellena", 0, lugar="Bajo Piura", fecha="2017")
ra("pronostico_FEN", "Niño costero extraordinario hasta ene 2027, fuerte hasta inicio de otoño 2027; lluvias sobre lo normal en verano 2027 y caudales sobre lo normal desde noviembre en Chira y Piura",
   "categoría", "todos", "ciclo", "ENFEN18_26", "prediccion", "estimado", "pronóstico oficial vigente al 16 oct 2026; actualizar con cada comunicado", 0.5, lugar="costa norte", fecha="2026-10-16")
# H03 napa
setv(A, "AN0463", variable="napa_freatica_profundidad_diseno_aireacion"); setv(A, "AN0464", variable="napa_freatica_media_critica_aireacion")
note(A, ["AN0463", "AN0464"], "criterio de AIREACIÓN de raíces (vía FAO-62), no de control de salinidad; en zona árida con napa salina FAO-29 pide normalmente >=2 m (fila R4A)")
ra("napa_freatica_profundidad_minima_control_salinidad", 2, "m", "todos", "ciclo", "F29_TXT", "bibliografico", "estimado",
   "FAO-29: en zonas áridas la napa debe mantenerse 'usually at least two metres'; napa no controlada a 1-2 m causa salinización; criterio general, no por cultivo", 0.5, lugar="zona árida con napa salina")
save(A, "fichas_anuales.csv", NA)

# ============ perennes ============
P = load("perennes.csv"); P = P[~P.id.str.startswith("R4")].copy()
setv(P, ["PE0011", "PE0027"], confianza=0.4)
note(P, ["PE0011", "PE0027"], "banano no figura en FAO-29 T5 (verificado); clase solo de FAO-56 T23; en frutales la tolerancia depende del patrón y de la variedad")
t11 = P[P.fuente.str.contains("Tabla 11")].id.tolist()
note(P, t11, "duración de FAO-56 T11 (análogo, ya en 0.4); sin ficha MIDAGRI/INIA verificada para Piura que la reemplace")
save(P, "perennes.csv", [])

# ============ reglas_rotacion ============
R = load("reglas_rotacion.csv"); R = R[~R.id.str.startswith("R4")].copy(); NR = []; rr = new(NR, "R4R")
z = rng(1, 25, "RR"); setv(R, z, valor=7, valor_min=0, valor_max=20, src="ZHAO22_TXT", confianza=0.35)
for i in z:
    j = ix(R, i); R.loc[j, "condicion"] = "cereal de riego con N alto (arroz costa norte ~270 kg N/ha según INIA 502)"
note(R, z, "Zhao 2022: el beneficio cae al subir el N; 7 % en ambientes de alto rendimiento (valor), 'negligible' sobre el rendimiento medio (min 0), ~20 % solo con poco N (max). "
     "N: 11 bolsas urea×50 kg×46 % + 2 DAP×50 kg×18 % ≈ 271 kg N/ha (INIA 502). Sin cifra peruana")
setv(R, [i for i in z if R.loc[ix(R, i), "cultivo_siguiente"] == "arroz"], confianza=0.3)
fr = rng(26, 37, "RR"); setv(R, fr, confianza=0.2)
note(R, fr, "NO APLICABLE a Piura: Franke mide cereal de secano en África subsahariana sin N o con 60-120 kg N/ha; Piura riega con N alto; no usar cuantitativamente")
note(R, "RR038", "magnitud sigue desconocida, pero la norma fija restricciones: campo limpio, socas prohibidas y >=1 campaña sin algodón si la infestación es fuerte (R4R)")
note(R, rng(58, 61, "RR"), "sin evidencia peruana; sin uso cuantitativo; falta el efecto de piso de arado por fangueo")
note(R, rng(62, 64, "RR"), "sin evidencia peruana; sin uso cuantitativo")
mh = rng(65, 80, "RR"); setv(R, mh, confianza=0.5)
for i in mh:
    j = ix(R, i); a = R.loc[j, "condicion"].split(">")[1].split("dS/m")[0].strip() if ">" in R.loc[j, "condicion"] else "a"
    R.loc[j, "condicion"] = f"ECe MEDIDA (extracto saturado) > {a} dS/m Y napa >=2 m o drenaje funcional; con napa <2 m salina usar ECe medida o escenario de suelos, nunca ECe=1.5·ECw"
note(R, mh, "FAO-29 deriva ECe=1.5·ECw con fracción de lavado 15-20 % sin aporte de napa; en Bajo Piura la ECe puede subir durante la campaña por ascenso capilar: la regla da la pérdida para una ECe dada, no predice la ECe; " + LUGAR_ND)
note(R, "RR074", "FAO-29/56 dan 1.5 dS/m; FAO-61 (Cerda 1982) da 3.4 dS/m y b=10.6, valor principal desde Ronda 3; FAO-29 rev.1 T4 deriva ECe=1.5·ECw con FL 15-20 % sin napa; con napa <2 m salina usar ECe medida")
X = dict(cultivo_previo="", cultivo_siguiente="", tipo_efecto="", condicion="", efecto="", regla_id="")
def regla(prev, sig, tipo, cond, efecto, *a, **k): rr(*a, cultivo_previo=prev, cultivo_siguiente=sig, tipo_efecto=tipo, condicion=cond, efecto=efecto, regla_id="", **k)
regla("arroz", "cualquiera (secano o vecino)", "sales_napa", "drenaje deficiente o napa <2 m",
      "sube la napa y la ECe superficial (salinización secundaria por ascenso capilar)",
      "cambio_ECe_suelo", "", "dS/m", "arroz", "poscosecha", "F29_TXT", "bibliografico", "desconocido",
      "dirección por FAO-29 (napa no controlada a 1-2 m causa salinización); magnitud desconocida; diagnósticos locales atribuyen la salinización del Bajo Piura al exceso de arroz (fuente secundaria, no citada)", 0.35)
regla("arroz", "cualquiera", "sales_napa", "drenaje funcional (napa >=2 m) y lámina continua o intermitente",
      "lava sales del perfil: ECe baja (el arroz es cultivo de recuperación)",
      "cambio_ECe_suelo", "", "dS/m", "arroz", "ciclo", "F29_TXT", "bibliografico", "desconocido",
      "FAO-29: 'Barley and rice are common reclamation crops'; sin drenaje el lavado no sale del perfil; magnitud desconocida", 0.35)
regla("cualquiera", "cultivo en campo ene-abr en parcela inundable", "evento_FEN",
      "alerta ENFEN de Niño costero fuerte o extraordinario (vigente: Comunicado 18-2026) y parcela inundable (Bajo Piura)",
      "riesgo alto de pérdida del cultivo; en 2017 Piura perdió 8733 ha y tuvo 15342 ha afectadas",
      "riesgo_perdida_cultivo", "", "categoría", "todos", "ciclo", "INDECI17", "medicion_local", "desconocido",
      "probabilidad por parcela desconocida; la siembra de Pima en Medio y Bajo Piura (1 ene-28 feb) y la ventana de arroz caen en la temporada de lluvias FEN; ver R4A FEN", 0.45, fecha="ene-abr")
regla("algodon", "algodon", "fitosanitario_legal", "obligatorio por norma",
      "campo limpio sin plantas de algodón", "plazo_campo_limpio", 77, "días", "algodon", "poscosecha", "RM0251", "regional", "observado",
      "Medio y Bajo Piura 16 oct-31 dic (77 d); Alto Piura 16 dic-28 feb (75 d); Chira 1 oct-19 dic (80 d); San Lorenzo 16 nov-31 ene (77 d); vigencia posterior a 2002 no verificada", 0.6,
      vmin=75, vmax=80, metodo="conteo de días entre fechas de la norma", lugar="Medio y Bajo Piura")
regla("algodon", "algodon", "fitosanitario_legal", "campo fuertemente infestado por gorgojo de la chupadera (Eutinobothrus gossypii)",
      "no sembrar algodón al menos una campaña", "campanas_sin_algodon", "", "campañas", "algodon", "siembra", "RM0251", "regional", "observado",
      "RM 0251-94-AG Art. 11; mínimo 1 campaña; vigencia posterior a 2002 no verificada", 0.6, vmin=1)
regla("algodon", "algodon", "fitosanitario_legal", "siempre (valles de la costa)", "socas (rebrote de la campaña anterior) prohibidas",
      "socas_algodon", "prohibido", "categoría", "algodon", "poscosecha", "RM0251", "regional", "observado",
      "RM 0251-94-AG Art. 13; vigencia posterior a 2002 no verificada", 0.6)
regla("cualquiera", "pimiento/paprika", "salinidad", "ECe MEDIDA > 1.5 dS/m Y napa >=2 m o drenaje funcional (misma condición que RR065-080)",
      "pérdida de rendimiento = b·(ECe − 1.5) %", "pendiente_salinidad_b", 14.1, "%/(dS/m)", "pimiento/paprika", "ciclo", "F29T4", "bibliografico", "estimado",
      "b=100/(ECe_0−a) con a=1.5 y ECe_0=8.6 dS/m de FAO-29 T4 (filas AN0191 y AN0195); pimiento (Capsicum annuum), no ensayo de páprika; sin rango", 0.5,
      metodo="cálculo Maas-Hoffman desde tabla publicada")
regla("barbecho", "cualquiera", "sales_napa", "barbecho en verano cálido con napa <2 m salina (en Piura dic-mar: interpretación nuestra)",
      "salinización secundaria rápida de la capa superficial", "cambio_ECe_suelo", "", "dS/m", "barbecho", "poscosecha", "F29_TXT", "bibliografico", "desconocido",
      "FAO-29: 'avoid fallow periods particularly during hot summers' y la salinización desde la napa 'can be rapid' con tierra en barbecho; magnitud desconocida", 0.4)
save(R, "reglas_rotacion.csv", NR)

# ============ recuperacion_suelo ============
S = load("recuperacion_suelo.csv"); S = S[~S.id.str.startswith("R4")].copy(); NS = []; rs = new(NS, "R4S")
note(S, rng(1, 6, "RS"), "NO APLICA a algodón: RM 0251-94-AG Art. 12 prohíbe incorporar al suelo rastrojos de algodonero en los valles de la costa (ver R4S001)")
setv(S, ["RS007", "RS008"], confianza=0.2)
note(S, ["RS007", "RS008"], "análogo templado-húmedo; en la costa árida la cobertura exige riego extra; sin dato de Piura")
note(S, rng(9, 11, "RS"), "solo si la napa se mantiene >=2 m o hay drenaje (FAO-29); con napa somera salina el lavado no evacúa las sales")
rs("restriccion_legal_incorporacion_rastrojo", "prohibido", "categoría", "algodon", "poscosecha", "RM0251", "regional", "observado",
   "Art. 12: prohibido incorporar rastrojos de algodón al suelo en valles de la costa; Art. 14 restringe usar tocones o broza; vigencia posterior a 2002 no verificada", 0.6,
   manejo="incorporación de rastrojo de algodón", propiedad="cumplimiento normativo", direccion="prohibido", plazo="desconocido")
save(S, "recuperacion_suelo.csv", NS)

# ============ motor_integracion ============
M = load("motor_integracion.csv")
setv(M, "R3M0001", src="INIA510_WB", tipo_evidencia="regional", confianza=0.6,
     notas="148 d (INIA 510, maduración media; PDF leído, probado en Sullana) y 150-155 d (INIA 502, PDF leído vía Wayback: https://web.archive.org/web/20240520000233id_/https://www.inia.gob.pe/wp-content/uploads/investigacion/programa/sistProductivo/variedad/arroz/INIA_502.pdf); R4 sube de 0.45 a 0.6")
setv(M, "R3M0002", src="SEMPIU432", confianza=0.55,
     notas="periodo vegetativo 80-100 d de INIA 432 (variedad liberada para Piura), ficha del tríptico leída; R4 sube de 0.5 a 0.55")
M.to_csv(os.path.join(D, "motor_integracion.csv"), index=False); print("motor_integracion.csv", len(M))

# ============ para_motor: notas de salinidad ============
CAV = "[R4] ECw=ECe/1.5 supone fracción de lavado 15-20 % sin aporte de napa (FAO-29); con napa <2 m salina (Bajo Piura) usar solo ECe medida, no las columnas ECw"
for n in ["umbrales_salinidad_propuesta.csv", "umbrales_salinidad_defecto_clase.csv"]:
    p = os.path.join(PM, n); d = pd.read_csv(p, dtype=str, keep_default_na=False)
    d["notas"] = d.notas.apply(lambda s: (s[:s.index("[R4]")].rstrip(" ;") if "[R4]" in s else s)).apply(lambda s: f"{s}; {CAV}" if s else CAV)
    d.to_csv(p, index=False); print(n, len(d))

# =====================================================================================
# Ronda 4b: respuesta a la revisión de Ronda 3 (suelos/revision_agronomia_r3.*)
# =====================================================================================
A = load("fichas_anuales.csv"); NB = []; rb = new(NB, "R4N")
P = load("perennes.csv"); NQ = []; rq = new(NQ, "R4Q")
def defecto_tipo(df):
    m = df.variable.str.contains("defecto_clase")
    df.loc[m, "tipo_evidencia"] = "analogo_externo"
defecto_tipo(A); defecto_tipo(P)
# r3-1 papaya MS
setv(P, "R3P0008", valor=3.0, src="CPIC07", confianza=0.3, notas="")
setv(P, "R3P0009", valor=7.7, src="CPIC07", confianza=0.3, notas="")
note(P, ["R3P0008", "R3P0009"], "defecto de clase MS (CPIC: 3.0/7.7), coherente con FAO-61 (MS; criterio crecimiento de plántula y daño foliar, no rendimiento). "
     "Validación gruesa: Subhas Chander 2007, ECw 4 dS/m por 6 meses → -10 % (Tainan) y -24 % (Red Lady); con ECe≈1.5·ECw≈6 (supuesto FL 15-20 %) MS predice -23 %, MT 0 %. "
     "MT 6.0/5.6 (fila Papaya de CPIC y FAO-29) queda solo como cota alta de sensibilidad")
note(P, "R3P0007", "MS confirmado en FAO-61 Anexo 1 (Kottenmeier 1983; Makhija y Jindal 1983) y respaldado por Subhas Chander 2007; se usa MS")
rq("ece_umbral_cota_alta_sensibilidad", 6.0, "dS/m", "papaya", "ciclo", "CPIC07", "analogo_externo", "estimado",
   "fila Papaya de CPIC (MT) y FAO-29; sobrestima la tolerancia frente al ensayo de Subhas Chander 2007; solo para análisis de sensibilidad; pendiente 5.6", 0.2)
# r3-8 banano: defecto S coherente (CPIC no lista banano)
note(P, ["R3P0004", "PE0011", "PE0027"], "clase principal S (FAO-61, rendimiento de fruto, Israeli et al. 1986, verificado); FAO-56 T23 (MS) no trae referencia")
note(P, ["R3P0005", "R3P0006"], "sin umbral medido; para coherencia con mango y frijol de palo se añade el defecto genérico de clase S (fila R4Q)")
for v, val, u in [("ece_umbral_defecto_clase", 1.3, "dS/m"), ("pendiente_salinidad_defecto_clase", 17.5, "%/(dS/m)")]:
    rq(v, val, u, "banano", "ciclo", "CPIC07", "analogo_externo", "estimado",
       "defecto genérico de clase S aplicado por Agente 1 (CPIC no lista banano; el valor es el que CPIC asigna a S en mango y frijol de palo); no medición; sin rango", 0.25)
# r3-7 mango
note(P, ["R3P0002", "R3P0003"], "Territorio cita Durán Zuazo et al. 2003 (Osteen sobre Gomera-1/3, 4 años: 0.88-1.81 dS/m y 12.5-17.1 %/(dS/m), probablemente ECw) — no verificado por Agronomía (ScienceDirect no descargó); "
     "la tolerancia depende del portainjerto y no se sabe cuáles se usan en Piura; FAO-61 da S por daño foliar (Cooper 1952)")
# r3-12 frijol de palo
note(A, ["R3A0010", "R3A0011"], "FAO-61 da S con criterio biomasa aérea (Keating y Fisher 1985; Subbarao et al. 1991), no rendimiento de grano")
# r3-9 yuca
setv(A, "R3A0008", notas="CPIC Appendix I sí lista 'Casava' 3.0/7.7 (valor de clase MS; corrige la nota de Ronda 3); FAO-29/56/61 no dan umbral medido; ver defecto R4N")
for v, val, u in [("ece_umbral_defecto_clase", 3.0, "dS/m"), ("pendiente_salinidad_defecto_clase", 7.7, "%/(dS/m)")]:
    rb(v, val, u, "yuca", "ciclo", "CPIC_CAS", "analogo_externo", "estimado",
       "defecto de clase MS de CPIC (fila Casava), coherente con FAO-61 (MS, rendimiento de raíz); no medición; sin rango", 0.3)
# r3-11 / r3-26 café y cacao
note(P, ["R3P0014", "R3P0015"], "solo ADVERTENCIA, nunca filtro duro: almácigo/plántula, no café adulto; el café de Piura es de sierra con lluvia")
setv(P, "R3P0012", confianza=0.2); note(P, "R3P0012", "solo ADVERTENCIA, nunca filtro duro")
# r3-2 / r3-24 FBN
fbn = ["R3A0155", "R3A0156", "R3A0157", "R3A0158", "R3A0159"]
setv(A, fbn, variable="fbn_total_fijado_kg_N_ha", unidad="kg N/ha/campaña")
note(A, fbn, "N fijado TOTAL (parte aérea + raíz: Herridge multiplica el N aéreo por 1.4, 1.5 en soya) por ha cosechada y CAMPAÑA (no por año); NO es N que queda en el suelo ni crédito para el cultivo siguiente")
setv(A, "R3A0159", src="HERRIDGE08_M")
note(A, "R3A0159", "a ~0.5 t/ha de grano (promedio global); rango por método 25-58 kg N/ha (con 30-40 kg N/t MS aérea de Peoples 2009 × 1.45 t/ha de MS de Herridge T4)")
note(A, ["R3A0161", "R3A0162", "R3A0163"], "unidad: kg N fijado (aéreo + raíz) por t de MS AÉREA")
# r3-3 balance neto caupí
rb("balance_N_neto_suelo_rastrojo_retenido", 31, "kg N/ha/campaña", "frijol caupi", "ciclo", "EMB_BAL", "analogo_externo", "estimado",
   "a 1 t/ha de grano: FBN aérea 0.63×101.8=64 kg N menos 33 kg N exportados en grano; sin N radical; coeficientes de Piauí (Brasil); escenario rotulado, no medición; sin rango", 0.3,
   metodo="cálculo de balance con coeficientes publicados")
rb("balance_N_neto_suelo_parte_aerea_retirada", -38, "kg N/ha/campaña", "frijol caupi", "ciclo", "EMB_BAL", "analogo_externo", "estimado",
   "a 1 t/ha de grano retirando toda la parte aérea (heno/forraje): 64 − 101.8 kg N; escenario rotulado, no medición; sin rango", 0.3,
   metodo="cálculo de balance con coeficientes publicados")
rb("credito_N_cultivo_siguiente", "", "kg N/ha", "frijol caupi", "ciclo", "", "bibliografico", "desconocido",
   "sin medición en Piura; el signo depende del rendimiento y del manejo del rastrojo; Territorio cita ensayos de campo +1.4 (Namibia) y +3 a +18 kg N/ha (Sokoto), no verificados por Agronomía (PDF no descargó); el motor debería usar 0 como valor central conservador", 0)
# r3-13 heno
for i, n in zip(["R3A0137", "R3A0138", "R3A0139"], ["N", "P2O5", "K2O"]):
    setv(A, i, variable=f"exportacion_heno_{n}", unidad="kg/t heno")
note(A, ["R3A0137", "R3A0138", "R3A0139"], "HENO de caupí (PNB16 T28), no grano: no usar en el balance de grano (usar R3A0131-0133)")
# r3-16/17 Kc perennes
kcr = P[P.id.str.startswith("R3P") & P.variable.isin(["kc", "kcb"])].id.tolist()
setv(P, kcr, confianza=0.4)
note(P, kcr, "Kc de Paredes et al. 2024 (método FAO-56), NO de FAO-56 T12 (que no trae mango ni papaya); faltan duraciones de etapa y el ajuste climático (ec. 62) requiere HRmin y u2 que el clima del repo no trae; no suponer que Piura aumenta el Kc")
# r3-27 ventanas
note(A, "R3A0122", "única ventana fuera de algodón; las de algodón por zona se añadieron en R4A desde la norma; el resto sigue pendiente")
save(A, "fichas_anuales.csv", NB, "R4N"); save(P, "perennes.csv", NQ, "R4Q")

# ---------- para_motor (r3) ----------
pp = os.path.join(PM, "parametros_cultivo_v2_propuesta.csv"); pr = pd.read_csv(pp, dtype=str, keep_default_na=False)
pr = pr[~pr.parameter_key.str.endswith("|R4D")]
PHN = ("PHMIN–PHMAX de EcoCrop = límite ABSOLUTO de la especie (no de variedad ni de Piura). R4: pasa de filtro duro (pH_suelo_adaptacion) a advertencia, "
       "porque suelos aluviales de la costa de Piura tienen pH ~7.5-8.3 (HWSD2 según Territorio) y cultivos que ya se producen aquí (p. ej. piquillo, máx 7.0) quedarían descartados. "
       "Rampa recomendada al dueño del motor: aptitud 1 dentro del óptimo, lineal hasta 0 en el límite absoluto, fuera del absoluto advertencia fuerte; descarte duro solo con pH medido y evidencia local")
m = pr.parameter == "pH_suelo_adaptacion"
pr.loc[m, "parameter"] = "pH_suelo_absoluto_ecocrop"
pr.loc[m, "parameter_key"] = pr.loc[m, "parameter_key"].str.replace("pH_suelo_adaptacion", "pH_suelo_absoluto_ecocrop", regex=False)
pr.loc[m, "applicability_note"] = PHN
pr.loc[pr.parameter == "pH_suelo_optimo", "applicability_note"] = "PHOPMN–PHOPMX de EcoCrop (especie); usar solo como penalización suave de peso bajo: con pH costero 7.3-8.3 casi toda la costa queda fuera del óptimo y no discrimina; prioridad a medir pH en parcela"
pr.loc[pr.parameter.str.startswith("temperatura"), "applicability_note"] = "EcoCrop grueso; temperatura_adaptacion son límites absolutos: compararlos con Tmax y Tmin mensuales, no con T media (con T media nunca descartan)"
DEPN = ("DEPR (mínimo absoluto) de EcoCrop; comparar en INTERVALO con la profundidad efectiva de Territorio = mín(profundidad física, napa estacional − franja capilar): "
        "< DEPR descarta; entre DEPR y DEP rampa de aptitud; >= DEP apto")
pr.loc[pr.parameter == "profundidad_suelo_apta_minima", "applicability_note"] = DEPN
eco = pd.read_csv("/tmp/ecocrop.csv", encoding="latin1") if os.path.exists("/tmp/ecocrop.csv") else pd.read_csv(F["ECOCROP"][1], encoding="latin1")
LOW = {"very": 0, "shallow": 20, "medium": 50, "deep": 150}
dep = []
for _, x in pr[pr.parameter == "profundidad_suelo_apta_minima"].iterrows():
    e = eco[eco.ScientificName == x.cultivar]
    if not len(e) or str(e.iloc[0].DEP).split(" ")[0] not in LOW: continue
    d = e.iloc[0].DEP; y = x.copy()
    y["parameter"] = "profundidad_suelo_favorable_minima"; y["min_value"] = str(LOW[d.split(" ")[0]] / 100); y["max_value"] = ""
    y["parameter_key"] = f"{x.crop}|{x.cultivar}|{x.harvest_use}|profundidad_suelo_favorable_minima|ciclo|R4D"
    y["applicability_note"] = f"DEP (óptimo) de EcoCrop = '{d}': límite inferior de la clase; NO descarta (el motor lo lee como favorable/advertencia); par de la fila DEPR para la rampa DEPR→DEP"
    dep.append(y)
pr = pd.concat([pr, pd.DataFrame(dep)], ignore_index=True); pr.to_csv(pp, index=False); print("parametros:", len(pr), "| DEP añadidas:", len(dep), "| pH absolutos a advertencia:", int(m.sum()))

def sal(c, prox, a, b, src, tipo, notas):
    e = {f"ECe_{y}": round(a + (100 - y) / b, 2) for y in (100, 90, 75, 50, 0)}
    w = {f"ECw_{y}": round(v / 1.5, 2) for y, v in zip((100, 90, 75, 50, 0), e.values())}
    return dict(cultivo=c, cultivo_fao29=prox, **e, **w, unidad="dS/m", fuente=F[src][0], url_o_doi=F[src][1], tipo_evidencia=tipo, estado="estimado",
                notas=notas + "; ECe_90..0 por Maas-Hoffman; " + CAV)
S2 = [sal("frijol de palo", "Pigeon pea, CPIC Appendix I", 1.3, 17.5, "CPIC07", "analogo_externo", "es_defecto_clase=true; DEFECTO DE CLASE S, no medición; FAO-61 S por biomasa aérea, no grano"),
      sal("mango", "Mango, CPIC Appendix I", 1.3, 17.5, "CPIC07", "analogo_externo", "es_defecto_clase=true; DEFECTO DE CLASE S, no medición; depende del portainjerto (Durán Zuazo 2003 citado por Territorio, no verificado)"),
      sal("papaya", "Papaya, clase MS (FAO-61); defecto CPIC MS", 3.0, 7.7, "CPIC07", "analogo_externo", "es_defecto_clase=true; R4: MS en vez de MT 6.0/5.6 (cota alta); Subhas Chander 2007 mide -10/-24 % a ECw 4"),
      sal("yuca", "Casava, CPIC Appendix I", 3.0, 7.7, "CPIC_CAS", "analogo_externo", "es_defecto_clase=true; DEFECTO DE CLASE MS, no medición"),
      sal("banano", "Banana, clase S (FAO-61, Israeli 1986); CPIC no lo lista", 1.3, 17.5, "CPIC07", "analogo_externo", "es_defecto_clase=true; defecto genérico S aplicado por Agente 1; conf 0.25")]
pd.DataFrame(S2).to_csv(os.path.join(PM, "umbrales_salinidad_defecto_clase.csv"), index=False)
s1 = pd.read_csv(os.path.join(PM, "umbrales_salinidad_propuesta.csv"), dtype=str, keep_default_na=False)
s1["notas"] = s1.notas.apply(lambda s: s if "R4 r3" in s else s + "; R4 r3: arveja 3.4/10.6 (FAO-61, Cerda 1982) se mantiene como principal")
s1.to_csv(os.path.join(PM, "umbrales_salinidad_propuesta.csv"), index=False)
pn = os.path.join(PM, "nutrientes_cultivo_propuesta.csv"); nu = pd.read_csv(pn, dtype=str, keep_default_na=False)
nu = nu[nu.crop != "papa"]
nu.loc[nu.crop == "zapallo", "note"] = "análogo; lb/acre convertido a kg/t; se eligió winter squash porque el zapallo de Piura (C. moschata/C. maxima, de guarda) se le parece; summer squash (1.6/0.6/2.8) descartado; falta absorción total"
nu.loc[(nu.crop == "caupi") & nu.measurement_type.str.startswith("absorción"), "note"] = "una sola localidad; balance neto derivado en fichas R4N (+31 con rastrojo, -38 sin parte aérea, a 1 t/ha); el crédito de N al siguiente cultivo es desconocido (usar 0)"
nu = pd.concat([nu, pd.DataFrame([dict(crop="papa", main_product_or_part="tubérculo", measurement_type="exportación potencial del producto retirado", N_kg_per_t=3.0,
     P2O5_kg_per_t=1.6, K2O_kg_per_t=5.3, base_unit="kg nutriente/t parte retirada", residue_management="multiplicar solo por masa realmente retirada",
     source_region="Carolina del Norte, EE.UU. (Zublena)", source_year=2006, source_url=F["PNB16T28"][1], source_table="FAO FPNB 16 Tabla 28 (filas AN0222-0224)",
     Piura_calibration="pendiente", note="análogo; para dimensionar fertilización usar absorción total FPNB 16 T29 (3.3/0.9/6.2 kg/t, filas AN0219-0221)")])], ignore_index=True)
nu.to_csv(pn, index=False)
pk = os.path.join(PM, "fao56_kc_propuesta.csv"); kc = pd.read_csv(pk, dtype=str, keep_default_na=False)
kc["source_table"] = "Paredes et al. 2024 Tabla 6 (método FAO-56; NO es Kc de FAO-56 T12)"
kc["applicability_note"] = kc.applicability_note.apply(lambda s: s.split("; R4")[0] + "; R4: faltan duraciones de etapa (usar calendario fenológico anual); sin ajuste ec. 62 por falta de HRmin/u2 en el clima del repo; Paredes da valores 'previamente tabulados' más bajos para mango (cota baja; no transcritos)")
kc.to_csv(pk, index=False); print("para_motor r3: salinidad", len(S2), "defectos; nutrientes", len(nu), "; Kc", len(kc))
