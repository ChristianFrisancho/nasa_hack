"""Ronda 3 (Agente 1): añade filas R3 a fichas_anuales.csv y perennes.csv y genera
motor_integracion.csv + para_motor/ (propuestas en esquemas del motor; el motor NO se modifica).
Idempotente: borra filas con id R3* antes de añadir. Correr después de build_fichas.py."""
import csv, os, pandas as pd
from fuentes import F
from build_fichas import COLS
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")
AN, PE = [], []

def mk(rows, prefix):
    def r(variable, valor, unidad, cultivo, etapa, src, tipo, estado, notas, conf, vmin="", vmax="",
          variedad="", lugar="", fecha="", metodo="transcripción de tabla publicada"):
        cita, u = F[src] if src else ("", "")
        if estado == "desconocido": valor = ""
        rows.append(dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad, cultivo=cultivo,
            variedad=variedad, etapa=etapa, lugar=lugar, lat="", lon="", fecha_o_periodo=fecha, fuente=cita, url_o_doi=u,
            metodo=metodo, tipo_evidencia=tipo, estado=estado, notas=notas, confianza=conf, id=f"{prefix}{len(rows)+1:04d}"))
    return r
ra, rp = mk(AN, "R3A"), mk(PE, "R3P")
PER = {"mango", "banano", "papaya", "cacao", "cafe", "limon", "uva de mesa"}
def R(c): return rp if c in PER else ra
MH = "cálculo Maas-Hoffman Y=100−b(ECe−a) a partir de umbral y pendiente publicados"

# ---------- 1. Salinidad ----------
r = ra
r("ece_umbral", 3.4, "dS/m", "arveja", "ciclo", "FAO61", "bibliografico", "estimado",
  "Pisum sativum, rendimiento de semilla fresca (Cerda et al. 1982); CONFLICTO con FAO-56 T23 (1.5 dS/m, S) ya en el archivo; ambas son línea Maas, no independientes; FAO-61 cita el ensayo original y por eso queda como valor principal", 0.5)
r("pendiente_salinidad_b", 10.6, "%/(dS/m)", "arveja", "ciclo", "FAO61", "bibliografico", "estimado", "Cerda et al. 1982; sin rango: la fuente da un solo valor", 0.5)
r("clase_tolerancia_salinidad", "MS", "categoría", "arveja", "ciclo", "FAO61", "bibliografico", "estimado", "FAO-61 da MS; FAO-56 da S: conflicto entre tablas de la misma línea", 0.45)
r("ece_rend_50pct", round(3.4 + 50 / 10.6, 2), "dS/m", "arveja", "ciclo", "FAO61", "bibliografico", "estimado", "derivado de 3.4 y 10.6; sin rango", 0.45, metodo=MH)
r("ece_umbral_defecto_clase", 1.3, "dS/m", "arveja", "ciclo", "CPIC07", "bibliografico", "estimado",
  "valor por defecto de la clase S, no medición; pendiente por defecto 17.5 %/(dS/m); solo de respaldo si se descarta FAO-61", 0.3)
for c, cl, conf, nota in [
    ("yuca", "MS", 0.45, "Manihot esculenta; FAO-61 da solo la clase, sin umbral ni pendiente"),
    ("frijol de palo", "S", 0.45, "Cajanus cajan; FAO-61 da solo la clase (criterio peso seco de parte aérea, no rendimiento de grano)")]:
    r("clase_tolerancia_salinidad", cl, "categoría", c, "ciclo", "FAO61", "bibliografico", "estimado", nota, conf)
r("ece_umbral", "", "dS/m", "yuca", "ciclo", "", "bibliografico", "desconocido", "FAO-29, FAO-56, FAO-61 y CPIC no publican umbral numérico de yuca; no se rellena con el valor por defecto de clase", 0)
r("pendiente_salinidad_b", "", "%/(dS/m)", "yuca", "ciclo", "", "bibliografico", "desconocido", "sin fuente con pendiente medida", 0)
r("ece_umbral_defecto_clase", 1.3, "dS/m", "frijol de palo", "ciclo", "CPIC07", "bibliografico", "estimado",
  "valor por defecto de la clase S (pigeon pea), no medición; pendiente por defecto 17.5 %/(dS/m)", 0.3)
r("pendiente_salinidad_defecto_clase", 17.5, "%/(dS/m)", "frijol de palo", "ciclo", "CPIC07", "bibliografico", "estimado", "valor por defecto de clase S, no medición; sin rango", 0.3)
r = rp
r("clase_tolerancia_salinidad", "S", "categoría", "mango", "ciclo", "FAO61", "bibliografico", "estimado", "FAO-61: criterio daño foliar; coincide con FAO-29 (S)", 0.5)
r("ece_umbral_defecto_clase", 1.3, "dS/m", "mango", "ciclo", "CPIC07", "bibliografico", "estimado", "valor por defecto de clase S, no medición; pendiente por defecto 17.5", 0.3)
r("pendiente_salinidad_defecto_clase", 17.5, "%/(dS/m)", "mango", "ciclo", "CPIC07", "bibliografico", "estimado", "valor por defecto de clase S, no medición; sin rango", 0.3)
r("clase_tolerancia_salinidad", "S", "categoría", "banano", "ciclo", "FAO61", "bibliografico", "estimado", "FAO-61 (Israeli 1986, rendimiento de fruta) da S; CONFLICTO con FAO-56 T23 (MS)", 0.4)
r("ece_umbral", "", "dS/m", "banano", "ciclo", "", "bibliografico", "desconocido", "ninguna tabla consultada da umbral numérico; clase en conflicto S/MS", 0)
r("pendiente_salinidad_b", "", "%/(dS/m)", "banano", "ciclo", "", "bibliografico", "desconocido", "sin pendiente publicada en FAO-29/56/61", 0)
r("clase_tolerancia_salinidad", "MS", "categoría", "papaya", "ciclo", "FAO61", "bibliografico", "estimado", "FAO-61 da MS; CONFLICTO con FAO-29 (MT)", 0.4)
r("ece_umbral_defecto_clase", 6.0, "dS/m", "papaya", "ciclo", "CPIC07", "bibliografico", "estimado", "valor de Appendix I, consistente con clase MT por defecto, no medición; pendiente 5.6; contradice la clase MS de FAO-61", 0.3)
r("pendiente_salinidad_defecto_clase", 5.6, "%/(dS/m)", "papaya", "ciclo", "CPIC07", "bibliografico", "estimado", "valor por defecto de clase, no medición; sin rango", 0.3)
r("ece_umbral", "", "dS/m", "cacao", "ciclo", "", "bibliografico", "desconocido", "ausente en FAO-29, FAO-56, FAO-61 y CPIC", 0)
r("pendiente_salinidad_b", "", "%/(dS/m)", "cacao", "ciclo", "", "bibliografico", "desconocido", "ausente en todas las tablas consultadas", 0)
r("ece_aptitud_tierras_max", "", "dS/m", "cacao", "ciclo", "CACAO_IOP", "analogo_externo", "estimado",
  "criterio de aptitud de tierras (clase S1) de Indonesia, no umbral de rendimiento; solo sirve como alerta", 0.3, vmax=1.0, lugar="Sulawesi, Indonesia")
r("ece_umbral", "", "dS/m", "cafe", "ciclo", "", "bibliografico", "desconocido", "no hay umbral de rendimiento en campo publicado en las tablas FAO/CPIC", 0)
r("ece_crecimiento_90pct_almacigo", 1.1, "dS/m", "cafe", "almacigo", "CAFE_UDENAR", "analogo_externo", "estimado",
  "CE crítica para 90 % de crecimiento relativo en almácigo de Caturra (Colombia); crecimiento de plántula, no rendimiento de planta adulta; sin rango", 0.35, variedad="Caturra", lugar="Colombia")
r("ecw_dano_plantula", 1.2, "dS/m", "cafe", "almacigo", "CAFE_UFLA", "analogo_externo", "estimado",
  "agua de riego con CEw ≥1.2 dS/m ya redujo el crecimiento de plántulas (Brasil); es CEw, no CEe; sin rango", 0.35, lugar="Minas Gerais, Brasil")
r("pendiente_salinidad_b", "", "%/(dS/m)", "cafe", "ciclo", "", "bibliografico", "desconocido", "sin pendiente publicada", 0)

# ---------- 2. EcoCrop: T, pH, profundidad ----------
eco = pd.read_csv("/tmp/ecocrop.csv", encoding="latin1") if os.path.exists("/tmp/ecocrop.csv") else pd.read_csv(F["ECOCROP"][1], encoding="latin1")
ESP = {"arroz": "Oryza sativa", "maiz amarillo duro": "Zea mays", "frijol castilla/grano seco": "Phaseolus vulgaris",
       "frijol caupi": "Vigna unguiculata", "arveja": "Pisum sativum", "frijol de palo": "Cajanus cajan",
       "algodon": "Gossypium barbadense", "papa": "Solanum tuberosum", "yuca": "Manihot esculenta",
       "zapallo": "Cucurbita moschata", "cebolla": "Allium cepa", "piquillo": "Capsicum annuum",
       "pimiento/paprika": "Capsicum annuum", "camote": "Ipomoea batatas", "mani": "Arachis hypogaea",
       "sorgo": "Sorghum bicolor", "soya": "Glycine max", "zarandaja": "Lablab purpureus",
       "mango": "Mangifera indica", "papaya": "Carica papaya", "cafe": "Coffea arabica", "cacao": "Theobroma cacao",
       "banano": "Musa acuminata", "limon": "Citrus aurantifolia", "uva de mesa": "Vitis vinifera"}
NOTE = {"algodon": "G. barbadense (Pima/Tangüis de Piura); G. hirsutum da T 22–36/15–42 y pH 6.0–7.5/5.0–9.5",
        "zapallo": "C. moschata (zapallo loche/macre); C. maxima da T 20–30/9–38 y pH 5.5–7.5/5.0–8.5",
        "banano": "M. acuminata (Cavendish AAA)", "frijol castilla/grano seco": "P. vulgaris"}
DEPC = {"shallow": (20, 50), "medium": (50, 150), "deep": (150, "")}
ECON = "EcoCrop: rango global de la especie, no de variedad ni de Piura; resolución gruesa"
for c, sp in ESP.items():
    x = eco[eco.ScientificName == sp].iloc[0]; f = R(c); n = ECON + ("; " + NOTE[c] if c in NOTE else "")
    f("temperatura_optima", "", "°C", c, "ciclo", "ECOCROP", "bibliografico", "estimado", n + "; TOPMN–TOPMX", 0.5, vmin=x.TOPMN, vmax=x.TOPMX, variedad=sp)
    f("temperatura_absoluta", "", "°C", c, "ciclo", "ECOCROP", "bibliografico", "estimado", n + "; TMIN–TMAX (límites absolutos de supervivencia/producción)", 0.5, vmin=x.TMIN, vmax=x.TMAX, variedad=sp)
    f("ph_optimo", "", "pH", c, "ciclo", "ECOCROP", "bibliografico", "estimado", n + "; PHOPMN–PHOPMX", 0.5, vmin=x.PHOPMN, vmax=x.PHOPMX, variedad=sp)
    f("ph_absoluto", "", "pH", c, "ciclo", "ECOCROP", "bibliografico", "estimado", n + "; PHMIN–PHMAX", 0.5, vmin=x.PHMIN, vmax=x.PHMAX, variedad=sp)
    for var, col, nn in (("profundidad_suelo_optima", "DEP", "clase óptima"), ("profundidad_suelo_minima", "DEPR", "clase del rango absoluto; su límite inferior es el mínimo tolerado")):
        k = str(x[col]).split()[0]; lo, hi = DEPC[k]
        f(var, "", "cm", c, "ciclo", "ECOCROP", "bibliografico", "estimado", f"{n}; {col}='{x[col]}' ({nn}); profundidad efectiva de suelo, no de raíz", 0.4, vmin=lo, vmax=hi, variedad=sp)

# ---------- 3. Kc perennes (Paredes 2024 T6) y duraciones ----------
P24 = "Kc estándar propuesto (subhúmedo, HRmin 45 %, u2 2 m/s; ajustar en Piura árida); Paredes et al. revisan ensayos de campo, misma escuela de FAO-56"
for c, dens, vals, nota in [
    ("mango", "baja-media 100–250 pl/ha (fc 0.25–0.40, h 2–3 m)", [(0.60, 0.45), (0.85, 0.70), (0.75, 0.60)], "valores de campo citados: Kc ini 0.60–0.75, mid 0.85–1.12, end 0.60–0.70; densidad típica de huertos de Piura (supuesto)"),
    ("mango", "alta 400–600 pl/ha (fc 0.40–0.50, h 2.5–4 m)", [(0.75, 0.65), (0.95, 0.85), (0.85, 0.75)], "valores de campo citados: Kc ini 0.35–0.75, mid 0.75–1.10, end 0.20–0.93"),
    ("mango", "joven <4 años (fc <0.25, h <2 m)", [(0.45, 0.25), (0.60, 0.40), (0.65, 0.35)], ""),
    ("papaya", "media, hilera simple 1330–4500 pl/ha (fc 0.40–0.70, h 1.5–3 m)", [(0.65, 0.55), (0.95, 0.85), (0.70, 0.60)], "valores de campo citados: Kc ini 0.31–0.38, mid 0.84–1.02"),
    ("papaya", "alta <7000 pl/ha (fc 0.70–0.85, h >2.5 m)", [(0.80, 0.75), (1.05, 1.00), (0.85, 0.80)], "valores de campo citados: Kc 0.90/1.10/0.90, Kcb 0.15/1.00/0.60"),
    ("papaya", "joven <1 año (fc <0.40, h <1.5 m)", [(0.50, 0.35), (0.75, 0.60), (0.55, 0.55)], "")]:
    for et, (kc, kcb) in zip(("inicial", "media", "final"), vals):
        rp("kc", kc, "adimensional", c, et, "PAREDES24", "bibliografico", "estimado", f"{P24}; {nota}; sin rango", 0.5, variedad=dens)
        rp("kcb", kcb, "adimensional", c, et, "PAREDES24", "bibliografico", "estimado", f"{P24}; coeficiente basal; sin rango", 0.5, variedad=dens)
for c in ("mango", "papaya"):
    rp("duracion_etapa", "", "días", c, "inicial/desarrollo/media/final", "", "bibliografico", "desconocido",
       "Paredes et al. 2024 no da longitud de etapas en días; la fenología anual de Piura (floración, cosecha) no se encontró con plazos citables", 0)
rp("meses_a_primera_cosecha", 9, "meses", "papaya", "establecimiento", "PAREDES24", "bibliografico", "estimado", "texto de Paredes et al.: ~9 meses a la primera cosecha; huertos de 3 a 10 años; sin rango", 0.4)
ra("kc", "", "adimensional", "frijol de palo", "inicial/media/final", "PIGEON_LYS", "bibliografico", "desconocido",
   "no figura en FAO-56 ni en Pereira et al. 2021; el estudio lisimétrico de Vidarbha 2025 solo da el resumen, sin cifras (PDF bloqueado)", 0)
ra("duracion_etapa", "", "días", "frijol de palo", "inicial/desarrollo/media/final", "", "bibliografico", "desconocido",
   "sin etapas FAO publicadas; las fases fenológicas de Anand (India) no equivalen a etapas Kc", 0)
ra("ventana_siembra", "setiembre", "mes", "frijol caupi", "siembra", "UNP_CAUPI", "regional", "estimado",
   "siembra en setiembre y cosecha en diciembre en el Medio Piura según tesis UNP leída solo en extracto; sin rango numérico", 0.3, lugar="Medio Piura")
for c in ("maiz amarillo duro", "frijol castilla/grano seco", "zapallo", "cebolla", "piquillo", "yuca", "camote", "frijol de palo"):
    ra("ventana_siembra", "", "fecha", c, "siembra", "INIA_CAL", "regional", "desconocido",
       "calendario agrícola de costa de INIA y DRA Piura no accesible desde el box (gob.pe e inia.gob.pe bloqueados); el comité PCR 2025-26 solo oficializó arroz y algodón", 0, lugar="Piura")

# ---------- 4. Nutrientes ----------
P2, K2 = 2.2914, 1.2046
EMB = "BRS Guariba en secano, 2000 kg/ha grano y 4000 kg/ha MS; una sola localidad de Piauí (Brasil); conversión P→P2O5 ×2.2914, K→K2O ×1.2046"
for n, v in (("N", 66.0 / 2), ("P2O5", 7.8 / 2 * P2), ("K2O", 31.8 / 2 * K2)):
    ra(f"exportacion_{n}", round(v, 1), "kg/t", "frijol caupi", "cosecha", "EMBRAPA_CAUPI", "analogo_externo", "estimado",
       f"tipo_coeficiente=exportacion_cosecha (grano); {EMB}; sin rango", 0.45, metodo="transcripción de texto publicado y conversión por t de grano")
for n, v in (("N", 203.6 / 2), ("P2O5", 16.6 / 2 * P2), ("K2O", 142.2 / 2 * K2)):
    ra(f"absorcion_total_{n}", round(v, 1), "kg/t", "frijol caupi", "ciclo", "EMBRAPA_CAUPI", "analogo_externo", "estimado",
       f"tipo_coeficiente=absorcion_total por t de grano (planta entera); {EMB}; sin rango", 0.45, metodo="transcripción de texto publicado y conversión por t de grano")
for n, v in (("N", 26.8), ("P2O5", 5.6), ("K2O", 17.9)):
    ra(f"exportacion_{n}", v, "kg/t", "frijol caupi", "forraje", "PNB16T28", "analogo_externo", "estimado",
       "tipo_coeficiente=exportacion_cosecha; fila 'Cowpea' de PNB16 T28 = heno, no grano; Carolina del Norte; sin rango", 0.4)
for n, v in (("N", 1.2), ("P2O5", 1.0), ("K2O", 5.8)):
    ra(f"exportacion_{n}", v, "kg/t", "zapallo", "cosecha", "NCSU_REMOVAL", "analogo_externo", "estimado",
       "tipo_coeficiente=exportacion_cosecha (fruto); 'squash, winter' a 5 t/acre: 12/10/58 lb/acre → kg/t (lb/t corta ×0.5); análogo de Carolina del Norte para zapallo macre/loche; sin rango", 0.4,
       metodo="transcripción de tabla publicada y conversión de unidades")
for n, v in (("N", 1.6), ("P2O5", 0.6), ("K2O", 2.8)):
    ra(f"exportacion_{n}", v, "kg/t", "zapallo", "cosecha", "NCSU_REMOVAL", "analogo_externo", "estimado",
       "tipo_coeficiente=exportacion_cosecha; 'squash, summer' (zapallito italiano) a 10 t/acre: 32/12/56 lb/acre; solo referencia de calabacín, no zapallo; sin rango", 0.35,
       variedad="zapallito (summer squash)", metodo="transcripción de tabla publicada y conversión de unidades")
for n in ("N", "P2O5", "K2O"):
    ra(f"absorcion_total_{n}", "", "kg/t", "zapallo", "ciclo", "", "bibliografico", "desconocido", "tipo_coeficiente=absorcion_total; PNB16 no tiene zapallo; el dato MSU de pumpkin no se pudo verificar (PDF no descargó)", 0)

# ---------- 5. Fijación biológica de N ----------
H = "HERRIDGE08"
for c, mean, lo, hi, farm, grp in [("frijol castilla/grano seco", 40, 0, 73, 36, "common bean"),
                                   ("frijol caupi", 63, 8, 97, 65, "grupo garbanzo/arveja/caupí/mungo/frijol de palo"),
                                   ("arveja", 63, 8, 97, 65, "grupo garbanzo/arveja/caupí/mungo/frijol de palo"),
                                   ("frijol de palo", 63, 8, 97, 65, "grupo garbanzo/arveja/caupí/mungo/frijol de palo"),
                                   ("soya", 68, 0, 95, 58, "grupo soya/maní"), ("mani", 68, 0, 95, 58, "grupo soya/maní")]:
    ra("fbn_pct_Ndfa", mean, "% N de la atmósfera", c, "ciclo", H, "bibliografico", "estimado",
       f"Tabla 2, {grp}: media de ensayos {mean} % (rango {lo}–{hi}); en campos de agricultores {farm} %; global, no Piura", 0.5, vmin=lo, vmax=hi)
for c, v, nota in [("frijol castilla/grano seco", 23, "Tabla 5 (calculado de FAOSTAT 2005); Smil da 30–50"),
                   ("arveja", 86, "Tabla 5; Smil da 30–50"), ("mani", 88, "Tabla 5; Smil da 60–100"), ("soya", 176, "Tabla 5; Smil da 60–100")]:
    ra("fbn_kg_N_ha", v, "kg N/ha/año", c, "ciclo", H, "bibliografico", "estimado", f"promedio global {nota}; sin rango propio", 0.45, metodo="transcripción de tabla publicada (estimación global)")
ra("fbn_kg_N_ha", 25, "kg N/ha/año", "frijol caupi", "ciclo", H, "bibliografico", "estimado",
   "derivado por Agente 1 de la Tabla 4: 0.23 Tg N ÷ 9.2 Mha ≈ 25 kg N/ha (promedio global, mayormente África de secano); sin rango", 0.4, metodo="cálculo propio desde tabla publicada")
ra("fbn_kg_N_ha", "", "kg N/ha", "frijol castilla/grano seco", "ciclo", "MANRIQUE93", "regional", "observado",
   "costa de Lima (La Molina), 20 cultivares, 15N, verano 1986 e invierno 1988: los peores <30 % Ndfa y <20 kg N/ha; cv. Caballero >50 % Ndfa y 60–80 kg N/ha; el mínimo del rango es cota superior aproximada de los peores", 0.5,
   vmin=20, vmax=80, lugar="La Molina, Lima (costa peruana)", fecha="1986-1988", metodo="dilución isotópica 15N en campo")
for c in ("frijol caupi", "arveja", "frijol de palo"):
    ra("fbn_kg_N_por_t_ms_aerea", "", "kg N/t MS aérea", c, "ciclo", "PEOPLES09", "bibliografico", "estimado",
       "regla general: ~30–40 kg N fijado por t de MS aérea (planta entera, incluye raíces); multiplicar por la biomasa local, que es desconocida", 0.45, vmin=30, vmax=40)
ra("fbn_kg_N_por_t_ms_aerea", 15, "kg N/t MS aérea", "frijol castilla/grano seco", "ciclo", H, "bibliografico", "estimado", "valor de Herridge 2008 para frijol común; sin rango", 0.45)
ra("fbn_kg_N_por_t_ms_aerea", 40, "kg N/t MS aérea", "soya", "ciclo", H, "bibliografico", "estimado", "valor de Herridge 2008 para soya y garbanzo; sin rango", 0.45)
ra("n_aportado_abono_verde", 60, "kg N/ha", "frijol caupi", "abono_verde", "PNB16T22", "bibliografico", "estimado",
   "Tabla 22, abono verde de 45–60 días en condiciones óptimas (suelo bien drenado, 10–38 °C); N total incorporado, no solo fijado; sin rango", 0.4)
ra("fbn_kg_N_ha", "", "kg N/ha", "frijol caupi", "ciclo", "BR_CAUPI_FBN", "analogo_externo", "estimado",
   "semiárido brasileño: hasta 45 kg N/ha en monocultivo, ~30 en asocio con maíz; solo extracto de búsqueda", 0.35, vmax=45, lugar="semiárido de Brasil")
ra("fbn_kg_N_ha", "", "kg N/ha", "frijol de palo", "ciclo", "", "bibliografico", "desconocido", "sin dato verificable; usar %Ndfa del grupo (63 %) por biomasa local", 0)
ra("fbn_medicion_piura", "", "kg N/ha", "frijol caupi", "ciclo", "", "medicion_local", "desconocido", "no se encontró ninguna medición de FBN en Piura para ninguna leguminosa", 0, lugar="Piura")

# ---------- escribir CSV de contrato ----------
def merge(name, new):
    p = os.path.join(D, name); d = pd.read_csv(p, dtype=str, keep_default_na=False)
    d = d[~d.id.str.startswith("R3")]
    if name == "fichas_anuales.csv":  # rótulo de tipo de coeficiente en papa (decisión R3)
        for pref, tag in (("absorcion_total", "[tipo_coeficiente=absorcion_total: solo para dimensionar fertilización]"),
                          ("exportacion", "[tipo_coeficiente=exportacion_cosecha: usar en balance de suelo]")):
            m = (d.cultivo == "papa") & d.variable.str.startswith(pref) & ~d.notas.str.contains("tipo_coeficiente", regex=False)
            d.loc[m, "notas"] = tag + " " + d.loc[m, "notas"]
    out = pd.concat([d, pd.DataFrame(new, columns=COLS).astype(str).replace({"nan": ""})], ignore_index=True)
    out.to_csv(p, index=False); print(name, len(d), "+", len(new), "=", len(out))
merge("fichas_anuales.csv", AN); merge("perennes.csv", PE)

# ---------- motor_integracion.csv (variables que acepta --integrar) ----------
def row(**k): return {c: k.get(c, "") for c in COLS}
MI = [row(variable="duracion_ciclo", valor="", valor_min=148, valor_max=155, unidad="días", cultivo="arroz", variedad="INIA 510 Mallares / INIA 502 Pitipo",
          etapa="ciclo_total", lugar="Piura", fuente=F["INIA510"][0] + "; " + F["INIA502"][0], url_o_doi=F["INIA510"][1], metodo="transcripción de texto publicado",
          tipo_evidencia="regional", estado="estimado", notas="148 d (INIA 510, Chira) y 150–155 d (INIA 502); leído en extractos de búsqueda", confianza=0.45, id="R3M0001"),
      row(variable="duracion_ciclo", valor="", valor_min=80, valor_max=100, unidad="días", cultivo="caupi", variedad="INIA 432 Vaina Verde", etapa="ciclo_total",
          lugar="costa norte del Perú", fuente=F["INIA432"][0], url_o_doi=F["INIA432"][1], metodo="transcripción de texto publicado", tipo_evidencia="regional",
          estado="estimado", notas="periodo vegetativo de la variedad liberada para Piura; leído en extracto", confianza=0.5, id="R3M0002")]
pd.DataFrame(MI, columns=COLS).to_csv(os.path.join(D, "motor_integracion.csv"), index=False)

# ---------- para_motor/: propuestas en esquemas del motor ----------
MOT = {"frijol castilla/grano seco": "frijol grano", "frijol caupi": "caupi", "uva de mesa": "uva"}
MOTOR_OK = {"arroz", "maiz amarillo duro", "frijol grano", "caupi", "arveja", "frijol de palo", "algodon", "papa", "yuca", "zapallo",
            "cebolla", "piquillo", "banano", "cacao", "cafe", "uva", "limon", "mango", "papaya", "camote", "mani", "sorgo", "soya"}
USE = {"mango": "fruta", "papaya": "fruta", "banano": "fruta", "limon": "fruta", "uva": "fruta", "cacao": "grano", "cafe": "grano"}
pr = []
for c, sp in ESP.items():
    m = MOT.get(c, c)
    if m not in MOTOR_OK or c == "pimiento/paprika": continue
    x = eco[eco.ScientificName == sp].iloc[0]; u = USE.get(m, "cosecha")
    dmin = DEPC[str(x.DEPR).split()[0]][0] / 100
    for i, (p, lo, hi, unit) in enumerate([("pH_suelo_adaptacion", x.PHMIN, x.PHMAX, "pH"), ("pH_suelo_optimo", x.PHOPMN, x.PHOPMX, "pH"),
                                           ("temperatura_adaptacion", x.TMIN, x.TMAX, "°C"), ("temperatura_optima", x.TOPMN, x.TOPMX, "°C"),
                                           ("profundidad_suelo_apta_minima", dmin, "", "m")]):
        pr.append(dict(parameter_key=f"{m}|{sp}|{u}|{p}|ciclo|R3{i}", crop=m, cultivar=sp, harvest_use=u, parameter=p, min_value=lo, max_value=hi,
                       unit=unit, stage="ciclo", parameter_kind="direct_source", geographic_scope="Global; FAO EcoCrop (rango de especie)",
                       source_url=F["ECOCROP"][1], validation_status="propuesta_agente1_no_calibrada",
                       applicability_note="EcoCrop grueso; temperatura_adaptacion son límites absolutos, el motor la compara con T media mensual" if "temp" in p else "EcoCrop grueso; límite inferior de la clase DEPR" if "prof" in p else "EcoCrop grueso"))
pd.DataFrame(pr).to_csv(os.path.join(PM, "parametros_cultivo_v2_propuesta.csv"), index=False)

def sal(c, prox, a, b, src, tipo, notas):
    e = {f"ECe_{y}": round(a + (100 - y) / b, 2) for y in (100, 90, 75, 50, 0)}
    w = {f"ECw_{y}": round(v / 1.5, 2) for y, v in zip((100, 90, 75, 50, 0), e.values())}
    return dict(cultivo=c, cultivo_fao29=prox, **e, **w, unidad="dS/m", fuente=F[src][0], url_o_doi=F[src][1], tipo_evidencia=tipo, estado="estimado",
                notas=notas + "; ECe_90..0 calculados por Maas-Hoffman; ECw=ECe/1.5")
S1 = [sal("arveja", "Pea (Pisum sativum), FAO-61 Anexo 1", 3.4, 10.6, "FAO61", "bibliografico", "Cerda et al. 1982; conflicto con FAO-56 (1.5, S)")]
S2 = [sal("frijol de palo", "Pigeon pea, CPIC Appendix I", 1.3, 17.5, "CPIC07", "bibliografico", "VALOR POR DEFECTO DE CLASE S, no medición"),
      sal("mango", "Mango, CPIC Appendix I", 1.3, 17.5, "CPIC07", "bibliografico", "VALOR POR DEFECTO DE CLASE S, no medición"),
      sal("papaya", "Papaya, CPIC Appendix I", 6.0, 5.6, "CPIC07", "bibliografico", "VALOR POR DEFECTO DE CLASE MT, no medición; FAO-61 la pone en MS")]
pd.DataFrame(S1).to_csv(os.path.join(PM, "umbrales_salinidad_propuesta.csv"), index=False)
pd.DataFrame(S2).to_csv(os.path.join(PM, "umbrales_salinidad_defecto_clase.csv"), index=False)

NC = ["crop", "main_product_or_part", "measurement_type", "N_kg_per_t", "P2O5_kg_per_t", "K2O_kg_per_t", "base_unit", "residue_management", "source_region",
      "source_year", "source_url", "source_table", "Piura_calibration", "note"]
nu = [["caupi", "grano", "exportación potencial del producto retirado", 33.0, round(3.9 * P2, 1), round(15.9 * K2, 1), "kg nutriente/t parte retirada",
       "multiplicar solo por masa realmente retirada", "Piauí, Brasil", 2017, F["EMBRAPA_CAUPI"][1], "Embrapa 2017 cap. 6", "pendiente", "una sola localidad, BRS Guariba en secano"],
      ["caupi", "grano", "absorción total por biomasa por t de producto principal", 101.8, round(8.3 * P2, 1), round(71.1 * K2, 1), "kg nutriente/t producto",
       "incluye parte aérea", "Piauí, Brasil", 2017, F["EMBRAPA_CAUPI"][1], "Embrapa 2017 cap. 6", "pendiente", "una sola localidad"],
      ["zapallo", "fruto", "exportación potencial del producto retirado", 1.2, 1.0, 5.8, "kg nutriente/t parte retirada", "multiplicar solo por masa realmente retirada",
       "Carolina del Norte, EE.UU.", "", F["NCSU_REMOVAL"][1], "NCSU Tabla 1, squash winter", "pendiente", "análogo; lb/acre convertido a kg/t"]]
pd.DataFrame(nu, columns=NC).to_csv(os.path.join(PM, "nutrientes_cultivo_propuesta.csv"), index=False)

KC = ["crop", "fao_crop_subtype", "Kc_initial", "Kc_mid_min", "Kc_mid_max", "Kc_end_min", "Kc_end_max", "locality_match", "soil_match", "stage_match",
      "water_requirement_mm", "source_url", "source_table", "source_scope", "applicability_note"]
kc = [["mango", "mango 100–600 pl/ha (baja-media a alta)", 0.60, 0.85, 0.95, 0.75, 0.85, "sin comprobar", "sin comprobar", "tipo general", "", F["PAREDES24"][1],
       "Paredes et al. 2024 Tabla 6", "Kc estándar propuesto por cobertura", "Kc_initial = clase baja-media (alta da 0.75)"],
      ["papaya", "papaya 1330–7000 pl/ha (media a alta)", 0.65, 0.95, 1.05, 0.70, 0.85, "sin comprobar", "sin comprobar", "tipo general", "", F["PAREDES24"][1],
       "Paredes et al. 2024 Tabla 6", "Kc estándar propuesto por cobertura", "Kc_initial = clase media (alta da 0.80)"]]
pd.DataFrame(kc, columns=KC).to_csv(os.path.join(PM, "fao56_kc_propuesta.csv"), index=False)
print("motor_integracion.csv", len(MI), "| para_motor:", len(pr), "parámetros,", len(S1) + len(S2), "salinidad,", len(nu), "nutrientes,", len(kc), "Kc")
