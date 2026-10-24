#!/usr/bin/env python3
"""CEw (conductividad eléctrica del agua de riego y de la napa) por zona y por fuente de agua.

Salida: datos/cew_por_zona.csv, en formato CONTRATO más columnas extra:
  fuente_agua (rio, quebrada, reservorio, toma, canal, pozo, dren), estacion (estiaje may-nov | avenida dic-abr | mixta | desconocida), nivel (punto | resumen | sin_dato), punto, subzona, resolucion.
- Filas "punto": una medición por estación (ANA 2024, ANA 2015, ANA ERH 2014, Piura Datos).
- Filas "resumen": CE_agua_riego_<fuente> o CE_agua_napa_pozo por zona; el rango es mín-máx de los puntos de esa zona.
- Filas "sin_dato": combinaciones zona x fuente buscadas sin cifra (estado desconocido, valor vacío).
La zona de cada punto sale de consulta_parcela.zona_de (polígono de distrito INEI + distrito_zona.csv).
Unidades: 1 dS/m = 1 mS/cm = 1000 µS/cm.
"""
import math, os, sys
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "datos")
sys.path.insert(0, os.path.dirname(__file__))
from consulta_parcela import zona_de  # noqa: E402

COLS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona", "lugar", "lat", "lon",
        "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas",
        "fuente_agua", "estacion", "nivel", "punto", "subzona", "resolucion"]

ANA24P = ("ANA-AAA Jequetepeque-Zarumilla, Informe Técnico N.° 0076-2024-ANA-AAA.JZ/KFDB, I Monitoreo participativo de calidad "
          "de recursos hídricos superficiales UH 1378 Piura (21-25 oct 2024), Anexo 01 y Cuadros 6.1-6.3 (copia SIAR Piura)")
ANA24P_URL = "https://siar.regionpiura.gob.pe/documentos/repositorio/php2IO9KS.PDF"
ANA24C = ("ANA-AAA Jequetepeque-Zarumilla, Informe Técnico N.° 0074-2024-ANA-AAA.JZ/KFDB, I Monitoreo de calidad de recursos "
          "hídricos superficiales UH 138 Chira (9-17 oct 2024, estiaje), Anexo 01 y cuadros de resultados (copia SIAR Piura)")
ANA24C_URL = "https://siar.regionpiura.gob.pe/documentos/repositorio/phpyrdxHS.PDF"
ANA15 = ("ANA, Informe técnico del segundo monitoreo participativo de calidad de agua superficial en la cuenca Piura "
         "(24-27 nov 2015), Cuadro 05")
ANA15_URL = "https://hdl.handle.net/20.500.12543/2890"
ERH = "ANA, Evaluación de Recursos Hídricos de la cuenca Piura (Valle Medio y Bajo Piura), tomos I-II, cap. 9 (pp. 95-102; año de publicación no verificado)"
ERH_URL = "https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf"
PD = "Piura Datos: /workspace/piura-agro/restricciones/evidencia_observada.csv"

M_CAMPO = "Conductividad medida in situ con multiparámetro (protocolo nacional ANA de monitoreo de calidad de agua superficial), una muestra puntual"


def utm17s_a_geo(e, n):
    """UTM zona 17 Sur (WGS84) a lat/lon (fórmulas de Snyder, error < 1 m)."""
    a, f = 6378137.0, 1 / 298.257223563
    e2 = f * (2 - f); ep2 = e2 / (1 - e2); k0 = 0.9996
    x, y = e - 500000.0, n - 10000000.0
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu) \
        + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu)
    c1 = ep2 * math.cos(p1) ** 2; t1 = math.tan(p1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(p1) ** 2); r1 = a * (1 - e2) / (1 - e2 * math.sin(p1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = p1 - (n1 * math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                          + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(p1)
    return round(math.degrees(lat), 5), round(-81 + math.degrees(lon), 5)


# (punto, descripción, fuente_agua, este, norte, CE en µS/cm, fecha, fuente, url, nota)
# Ronda 8: corrección tras la revisión de Piura Datos (PDF originales, restricciones/fuentes_r4/) y de Agronomía (H01-H03).
# Las tablas ANA 2024 imprimen la CE en µS/cm. En QCarn1, QSFran1, RPiur4 y RPiur5 la cifra (QCarn1 retirada; 5, 9.03, 9.92) es imposible
# Cierre del coordinador 08:04 + precisión de Piura Datos 08:12: cifra de Datos por punto (COORD), estimado, metodo balance_ionico.
# Iones mayores del Cuadro 6.3 del IT 0076-2024 (pp. 20-21 del PDF), mg/L.
IONES = {  # Ca, Mg, Na, K, HCO3, SO4, Cl
    "QCarn1": (96.745, 52.188, 235.300, 0.54, 1137, 546, 0.11),
    "QSFran1": (318.241, 96.819, 676.753, 3.45, 959, 1151, 0.21),
    "RPiur4": (484.728, 163.356, 1198.125, 11.39, 2377, 797, 0.09),
    "RPiur5": (505.794, 175.611, 1321.393, 6.72, 218, 1290, 3288),
    "RPiur13": (290.616, 106.780, 845.146, 4.62, 237, 685, 1595),
    "RPiur6": (55.920, 16.460, 65.991, 2.21, 166, 69, 81)}
# Tolerancia de electroneutralidad: APHA/AWWA/WEF Standard Methods 1030E (±5 % si la suma de aniones > 10 meq/L; ±2 % entre 3 y 10).
def balance(cod):
    ca, mg, na, k, h, so4, cl = IONES[cod]
    cat = ca / 20.04 + mg / 12.153 + na / 22.99 + k / 39.10
    an = h / 61.02 + so4 / 48.03 + cl / 35.45
    cbe = 100 * (cat - an) / (cat + an)
    tol = 5 if an > 10 else 2
    return cat, an, cbe, abs(cbe) <= tol, tol
# Valores de los otros dos agentes (para dejar las tres versiones en la nota).
AGRO = {"QCarn1": "3.0-3.3", "QSFran1": "4.0-4.6", "RPiur4": "5.1-5.8", "RPiur5": "11-12"}
PDATOS = "valor vacío, estado desconocido (restricciones/evidencia_observada.csv)"
def nota_iones(cod, ce_pub):
    cat, an, cbe, cierra, tol = balance(cod)
    t = (f"Balance iónico (Cuadro 6.3, pp. 20-21): cationes {cat:.1f} meq/L, aniones {an:.1f} meq/L, error {cbe:+.1f} % "
         f"(tolerancia ±{tol} %, Standard Methods 1030E): {'cierra' if cierra else 'NO cierra'}. "
         f"CE ≈ suma de iones/10 (USDA Handbook 60, Richards 1954, fig. 4): {an / 10:.2f} dS/m por aniones y {cat / 10:.2f} por cationes. ")
    if cod in AGRO:
        t = (f"Cifra impresa: {ce_pub} µs/cm (p. 20); leída como µS/cm es imposible con estos iones. " + t +
             f"Tres versiones: Territorio {min(an, cat) / 10:.1f}-{max(an, cat) / 10:.1f} dS/m (aniones y cationes); "
             f"Agronomía {AGRO[cod]} dS/m (revisión r1); Piura Datos {PDATOS}. Se adopta 'desconocido' porque el balance no cierra "
             "y la regla del coordinador lo exige; el intervalo de Territorio queda solo como cota, no como valor. "
             + ("Los cloruros impresos (0.09-0.21 mg/L con Na de 235-1198 mg/L) también parecen mal transcritos. " if IONES[cod][6] < 1 else "")
             + "Lo seguro: agua salina (> 1.9 dS/m con cualquiera de las dos sumas). ")
    else:
        ce = {"RPiur13": 5.98, "RPiur6": 0.74}[cod]
        t += (f"La CE impresa en µS/cm ({ce} dS/m) cae a menos de 15 % de las dos sumas: la unidad µS/cm es coherente y este punto sirve "
              "de control del método" + ("" if cierra else " aunque su electroneutralidad excede la tolerancia estricta para < 10 meq/L") + ". ")
    return t

# Ronda 8 (07:55): la decisión de los 4 ambiguos sale del balance explícito (scripts/balance_ionico_ana2024.py -> datos/balance_ionico_ana2024.csv):
# suma con y sin cloruro, credibilidad del Cl impreso y cifra fijada. Sustituye a la regla anterior (todo 'desconocido').
BI = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos", "balance_ionico_ana2024.csv")).set_index("punto")
def nota_bi(cod):
    b = BI.loc[cod]
    return (f"Cifra impresa {b.ce_impresa} 'µs/cm' (p. 20); como µS/cm sería {b.ce_impresa_como_uS_dS_m} dS/m, imposible con {b.cationes_meq} meq/L de cationes. "
            f"Balance (Cuadro 6.3): cationes {b.cationes_detalle} → Σ {b.cationes_meq} meq/L; aniones {b.aniones_detalle} → Σ {b.aniones_con_cl_meq} meq/L "
            f"(sin Cl {b.aniones_sin_cl_meq}). CE ≈ Σ/10: cationes {b.ce_cationes_dS_m}, aniones con Cl {b.ce_aniones_con_cl_dS_m}, sin Cl {b.ce_aniones_sin_cl_dS_m} dS/m; "
            f"error de balance {b.error_balance_con_cl_pct:+} %. ¿Cl impreso creíble? {b.cl_impreso_creible}. Decisión: {b.decision} "
            f"Versiones previas: Agronomía {AGRO[cod]} dS/m (suma de aniones); Piura Datos (aviso_territorio_cew.md) 5 / 9.03 / 9.92 / desconocido. "
            "Detalle en datos/balance_ionico_ana2024.csv. ")

# Página del PDF donde está la cifra de CE de cada punto (verificada en restricciones/fuentes_r4/*.txt).
PAG = {**{c: 14 for c in ("QPfie1", "RPusm2", "RHuar3", "QSing1")},
       **{c: 17 for c in ("QSing2", "RBigo2", "RPiur2", "RPiur11", "RCmed1")},
       **{c: 20 for c in ("QCarn1", "QSFran1", "RPiur4", "RPiur5", "RPiur13", "RPiur6")},
       **{c: 37 for c in ("RPbla1", "RSpab1", "RMaca1", "RQuir1", "RMaca4", "RQuir3", "RQuir2", "RChir2", "RChir3", "RChir4", "RChir11", "RChir6", "RChir7")},
       **{c: 47 for c in ("QTimb1", "RChip1", "RChip2", "RChip4", "RChir12")}}
AMBIG = {"QCarn1", "QSFran1", "RPiur4", "RPiur5"}
# Cierre del coordinador (24-oct 08:04): una cifra por punto, la de Piura Datos. Sustituye a la decisión de Territorio por balance.
COORD = {"RPiur4": (7.86, 5.56, 9.03), "QCarn1": (3.23, 1.94, 3.23), "QSFran1": (5.0, 3.97, 5.34), "RPiur5": (9.92, 9.73, 12.32)}  # precisión de Piura Datos 08:12
M_COORD = "balance_ionico"
ERR = {"QSFran1": "+14,7 %", "RPiur5": "−11,7 %", "RPiur4": "+24 %", "QCarn1": "≈ −22 %"}
def nota_coord(cod):
    b = BI.loc[cod]; v, lo, hi = COORD[cod]
    extra = (" La cifra impresa no tiene respaldo: haría falta ~104 meq/L de cationes y el cuadro da 19,4; se retira." if cod == "QCarn1" else "")
    return (f"Cifra de Piura Datos: {v} dS/m [{lo}–{hi}], estimado por balance iónico; error de balance {ERR[cod]}.{extra} "
            "El Gráfico 6.7 del informe ANA está en µS/cm y no sostiene el cambio de unidad; lo sostiene el balance iónico (Piura Datos, restricciones/aviso_territorio_cew.md). "
            f"Balance explícito (Cuadro 6.3, p. 20): cationes {b.cationes_detalle} → Σ {b.cationes_meq} meq/L; aniones {b.aniones_detalle} → Σ {b.aniones_con_cl_meq} meq/L. "
            "Detalle en datos/balance_ionico_ana2024.csv (evidencia; la cifra adoptada es la de Datos). ")

PTS = [
    # Piura 2024 (estiaje, octubre)
    ("QPfie1", "Quebrada Puente Fierro, captación agua potable Palambla", "quebrada", 657444, 9406483, 172, "2024-10-22", "P24", ""),
    ("RPusm2", "Río Pusmalca, 100 m aguas arriba del puente La Afiladera", "rio", 652250, 9402784, 197, "2024-10-22", "P24", ""),
    ("RHuar3", "Río Huarmaca, 350 m aguas abajo del badén Serrán", "rio", 636451, 9399512, 510, "2024-10-21", "P24", ""),
    ("QSing1", "Quebrada Singucate parte alta, puente Coyona", "quebrada", 653179, 9413398, 61, "2024-10-22", "P24", ""),
    ("QSing2", "Quebrada Singucate parte baja, puente Pajonal", "quebrada", 646531, 9416317, 348, "2024-10-23", "P24", ""),
    ("RBigo2", "Río Bigote, estación hidrométrica Barrios", "rio", 644100, 9415178, 483, "2024-10-23", "P24", ""),
    ("RPiur2", "Río Piura, 400 m aguas arriba del puente Salitral", "rio", 629121, 9408634, 741, "2024-10-23", "P24", ""),
    ("RPiur11", "Río Piura, 500 m aguas arriba del río Bigote", "rio", 626667, 9410751, 621, "2024-10-23", "P24", ""),
    ("RCmed1", "Río Corral del Medio, caserío Polvazal (Morropón)", "rio", 612830, 9423306, 345, "2024-10-23", "P24", ""),
    ("QCarn1", "Quebrada Los Carneros, 50 m aguas abajo del puente Bonanpira (Tambogrande)", "quebrada", 573598, 9454937, 10400, "2024-10-24", "P24", ""),
    ("QSFran1", "Quebrada San Francisco, 1.8 km antes de su desembocadura en el río Piura", "quebrada", 576255, 9452643, 5000, "2024-10-24", "P24", ""),
    ("RPiur4", "Río Piura frente a Ocoto Bajo", "rio", 565142, 9455752, 9030, "2024-10-24", "P24", ""),
    ("RPiur5", "Río Piura a la altura del caserío El Papayo", "rio", 542529, 9442583, 9920, "2024-10-25", "P24", ""),
    ("RPiur13", "Río Piura, 150 m aguas arriba de la captación de la empresa Rapel", "rio", 541870, 9440015, 5980, "2024-10-25", "P24",
     "Supera ECA cat. 3 D1 y D2; el informe lo atribuye a drenaje agrícola y evaporación. Cloruros 1 595 mg/L. "),
    ("RPiur6", "Río Piura frente a la caseta de bombeo del penal, caserío Río Seco", "rio", 542488, 9431711, 740, "2024-10-25", "P24",
     "Aguas abajo de RPiur13 (5.98 dS/m) pero con 0.74 dS/m: el tramo cambia mucho en pocos km (aportes y bombeos); no interpolar. "),
    # Chira 2024 (estiaje, octubre)
    ("RPbla1", "Río Palo Blanco, 30 m aguas arriba del puente Aranza", "rio", 656882, 9463717, 90.3, "2024-10-10", "C24", ""),
    ("RSpab1", "Río San Pablo frente a Frejolito", "rio", 649659, 9465931, 227, "2024-10-10", "C24", ""),
    ("RMaca1", "Río Macará, bocatoma del canal de irrigación Macará", "rio", 628955, 9505967, 334, "2024-10-11", "C24", ""),
    ("RMaca4", "Río Macará, 500 m aguas abajo del puente internacional", "rio", 614682, 9514664, 436, "2024-10-11", "C24", ""),
    ("RQuir1", "Río Quiroz, 200 m aguas arriba del puente Jambur", "rio", 616565, 9489053, 449, "2024-10-14", "C24", ""),
    ("RQuir3", "Río Quiroz (punto 3 de la red)", "rio", 621652, 9485339, 445, "2024-10-11", "C24", ""),
    ("RChip1", "Río Chipillico, 5.5 km antes del reservorio San Lorenzo", "rio", 597696, 9478877, 417, "2024-10-14", "C24", ""),
    ("QTimb1", "Quebrada Timbes de Guabal, 80 m aguas arriba del puente peatonal", "quebrada", 605313, 9474827, 347, "2024-10-14", "C24", ""),
    ("RChip2", "Río Chipillico, 300 m del acueducto del canal de derivación Daniel Escobar", "rio", 557049, 9477847, 1877, "2024-10-14", "C24",
     "Tramo bajo del Chipillico (retornos de riego); no es el agua del canal Daniel Escobar. "),
    ("RChip4", "Río Chipillico, 690 m aguas abajo de la descarga de American Quality Aquaculture", "rio", 554272, 9478889, 888, "2024-10-14", "C24", ""),
    ("RQuir2", "Río Quiroz, 1 km antes de unirse al Chira", "rio", 582013, 9509610, 591, "2024-10-15", "C24", ""),
    ("RChir2", "Río Chira, 150 m antes de la unión con el río Alamor", "rio", 568175, 9504140, 514, "2024-10-15", "C24", ""),
    ("RChir3", "Río Chira, sector Huaypira, 250 m aguas abajo de la salida del reservorio Poechos", "rio", 552481, 9481894, 590, "2024-10-16", "C24",
     "Mejor aproximación disponible al agua que entrega Poechos (canales Miguel Checa, Daniel Escobar y, vía río Piura, Biaggio Arbulú). "
     "El informe anota bajo caudal en este punto. Es agua en la salida, no en la cabecera de parcela. "),
    ("RChir4", "Río Chira en La Peña, 200 m antes de la captación de agua potable", "rio", 549666, 9471211, 665, "2024-10-16", "C24", ""),
    ("RChir11", "Río Chira, puente Nuevo Sullana", "rio", 533512, 9458951, 848, "2024-10-17", "C24",
     "El cuadro de ubicación da Este 553512 y el anexo invierte Este/Norte; se usa 533512 (Sullana), coherente con RChir5 (533846). "),
    ("RChir6", "Río Chira, puente Sojo", "rio", 519329, 9459052, 1707, "2024-10-17", "C24", "Supera ECA cat. 1 A2 (1 600 µS/cm). "),
    ("RChir7", "Río Chira, captación de la planta de tratamiento El Arenal", "rio", 497288, 9459638, 4980, "2024-10-17", "C24",
     "Anexo de campo dice '4.98 uS/cm'; el cuadro de resultados da 4980 µS/cm, que es el valor usado. El informe lo atribuye al retorno de riego o a la geología. "),
    ("RChir12", "Río Chira, 300 m de la localidad Miramar (frente al pase a Pueblo Nuevo)", "rio", 488905, 9460601, 4110, "2024-10 (fecha impresa '14/14/24')", "C24",
     "Supera ECA cat. 3. "),
    # Piura nov-2015 (mismos códigos de estación de la red ANA; coordenadas tomadas del informe 2024)
    ("QSFran1", "Quebrada San Francisco, 750 m antes de la desembocadura en el río Piura", "quebrada", 576255, 9452643, 1945, "2015-11 (24-27)", "P15", ""),
    ("RPiur4", "Río Piura frente a Ocoto Bajo", "rio", 565142, 9455752, 2320, "2015-11 (24-27)", "P15", ""),
    ("RPiur5", "Río Piura, caseta de bombeo de riego de parcelas", "rio", 542529, 9442583, 3320, "2015-11 (24-27)", "P15", ""),
    ("RPiur6", "Río Piura, caseta de bombeo de agua para el penal (Río Seco)", "rio", 542488, 9431711, 1979, "2015-11 (24-27)", "P15", ""),
]
SRC = {"P24": (ANA24P, ANA24P_URL, "regional"), "C24": (ANA24C, ANA24C_URL, "regional"), "P15": (ANA15, ANA15_URL, "regional")}
NOTA15 = ("Cifras leídas del extracto indexado del Cuadro 05 (solo lista los puntos que superan el ECA 1-A2); el PDF del repositorio ANA "
          "no se pudo descargar (error TLS). Coordenadas: las de la misma estación en el informe 2024. ")


def zona_pt(lat, lon):
    z = zona_de(lon, lat)
    return z["zona"], z["subzona"], z.get("distrito", "")


def estacion_de(fecha):
    """estiaje = may-nov, avenida = dic-abr (régimen del río Piura/Chira). 'desconocida' si no hay mes."""
    import re
    m = re.findall(r"\d{4}-(\d{2})", str(fecha))
    if not m: return "desconocida"
    e = {"avenida" if int(x) in (12, 1, 2, 3, 4) else "estiaje" for x in m}
    return e.pop() if len(e) == 1 else "mixta"


def main():
    rows = []
    for cod, desc, fa, e, n, ce, fecha, src, nota in PTS:
        lat, lon = utm17s_a_geo(e, n)
        zona, sub, dist = zona_pt(lat, lon)
        fuente, url, _ = SRC[src]
        ambiguo = src == "P24" and cod in AMBIG
        pub = {"QSFran1": "5", "RPiur4": "9.03", "RPiur5": "9.92"}.get(cod, "")
        if src == "P24" and cod in IONES: nota = nota + (nota_coord(cod) if ambiguo else nota_iones(cod, pub))
        bi = BI.loc[cod] if ambiguo else None
        bi_val = COORD[cod][0] if ambiguo else ""
        pag = f" (p. {PAG[cod]} del PDF)" if src in ("P24", "C24") else ""
        if not ambiguo: assert ce / 1000 <= 20, f"{cod}: CE de agua superficial > 20 dS/m, revisar unidad"
        cifra = "" if ambiguo else f"Cifra impresa {ce:g} µs/cm{pag}; µS/cm ÷ 1000 = dS/m. "
        rows.append(dict(variable="CE_agua_punto", valor=bi_val if ambiguo else round(ce / 1000, 4),
                         valor_min=(COORD[cod][1] if ambiguo else ""), valor_max=(COORD[cod][2] if ambiguo else ""), unidad="dS/m", zona=zona,
                         lugar=f"{desc} ({dist})" if dist else desc, lat=lat, lon=lon, fecha_o_periodo=fecha, fuente=fuente + pag, url_o_doi=url,
                         metodo=(M_COORD if ambiguo else M_CAMPO) + f"; UTM 17S {e} E, {n} N convertido a WGS84", tipo_evidencia="medicion_local",
                         estado="estimado" if ambiguo else "observado",
                         notas=(cifra + nota + (NOTA15 if src == "P15" else "") +
                                "Muestra puntual de un cuerpo de agua superficial en estiaje (oct-nov): no es CE en cabecera de parcela ni un promedio anual. "
                                + ("" if ambiguo else "Sin rango porque es una sola lectura.")).strip(),
                         fuente_agua=fa, nivel="punto", punto=cod, subzona=sub, resolucion="punto (estación)"))
    # Piura Datos: río Chira en Sullana (Coronel 2021)
    rows.append(dict(variable="CE_agua_punto", valor="", valor_min=0.373, valor_max=1.167, unidad="dS/m", zona="chira",
                     lugar="Río Chira, tramo urbano de Sullana (puente viejo)", lat="", lon="", fecha_o_periodo="c. 2019-2021",
                     fuente="Coronel Chávez (2021), tesis doctoral UNP, vía " + PD + " (id f5bb78566d2c)",
                     url_o_doi="https://alicia.concytec.gob.pe/vufind/Record/RUMP_d09e47b2e18ce642f9b68f9a40aad3fe",
                     metodo="Conductividad en puntos de muestreo de la tesis (resumen)", tipo_evidencia="medicion_local", estado="observado",
                     notas="Publicado 373-1167 µS/cm. Sin valor central en el resumen. Coincide con ANA oct-2024 en Sullana (0.85 dS/m, RChir11).",
                     fuente_agua="rio", nivel="punto", punto="Coronel2021", subzona="Valle del Chira", resolucion="tramo de río"))
    # pozos ERH (UDEP/EQUAS, 19-sep-2014): solo rango publicado en el texto
    for zona, sub in [("medio_piura", "Medio Piura"), ("bajo_piura", "Bajo Piura")]:
        rows.append(dict(variable="CE_agua_napa_pozo", valor="", valor_min=0.04, valor_max=16.83, unidad="dS/m", zona=zona,
                         lugar="Pozos IRHS del valle Medio y Bajo Piura (18 pozos con análisis; incluye La Unión, Bellavista, Sechura, Catacaos, Castilla)",
                         lat="", lon="", fecha_o_periodo="2014-09 (muestreo 19-sep-2014 en Cuadros 9.7-9.8)",
                         fuente=ERH + "; también en " + PD + " (id 421935e783db)", url_o_doi=ERH_URL,
                         metodo="Análisis de laboratorio UDEP y EQUAS de 18 pozos; diagrama de Wilcox (AquaChem)", tipo_evidencia="medicion_local",
                         estado="observado",
                         notas=("Rango conjunto Medio + Bajo Piura: el estudio no lo separa por zona y las tablas pozo por pozo (Cuadros 9.5-9.9) "
                                "son imágenes que no salen en el texto. Mínimo IRHS-46 (Piura), máximo IRHS-68 (Catacaos). Solo IRHS-01 (Castilla) "
                                "es apto para riego por salinidad; la mayoría cae en C3S1-C3S4 (C3 = 0.75-2.25 dS/m) y IRHS-06 es el peor. "
                                "El acuífero somero (influencia marina) es más salino que el profundo; familia clorurada sódica. Boro 0.24-2.68 ppm. "
                                "Para Tablazo Sur no hay cifra de pozo separada."),
                         fuente_agua="pozo", nivel="punto", punto="ERH_IRHS", subzona=sub, resolucion="18 pozos, valle"))
    # Reservorio San Lorenzo: análisis de agua de riego, laboratorio de suelos UNP, en perfil PSI (nov-2011)
    rows.append(dict(variable="CE_agua_punto", valor=0.47, valor_min="", valor_max="", unidad="dS/m", zona="san_lorenzo",
                     lugar="Agua del reservorio San Lorenzo que llega por el canal Yuscay / canal Tablazo / lateral L-3 T2+520 (sector Cerro Hermoso, CR Algarrobo-Valle Hermoso, Tambogrande)",
                     lat="", lon="", fecha_o_periodo="c. 2011 (perfil fechado nov-2011; fecha de muestreo no indicada)",
                     fuente="PSI-MINAG, Perfil 'Instalación de un sistema de riego tecnificado por goteo - GGE Jesús es mi Salvador - Sector Cerro Hermoso - Tambogrande' (nov-2011), Cuadro 13; análisis del Laboratorio de Suelos, Facultad de Agronomía UNP",
                     url_o_doi="https://dokumen.site/download/proyecto-de-riego-tecnifiacado-tambo-grande-piura-a5b39f03bcba0a",
                     metodo="Análisis de agua de riego en laboratorio (CE, pH, cationes, aniones, RAS; clasificación Riverside)",
                     tipo_evidencia="medicion_local", estado="observado",
                     notas=("Publicado 0.47 mmhos/cm (470 micromhos/cm), pH 6.95, Na 2.10 meq/L, RAS 1.90, C2S1, sales totales 0.21 g/L. "
                            "Control por aniones: Cl 1.92 + SO4 0.65 + HCO3 2.15 = 4.72 meq/L, que da ~0.47 dS/m: unidad coherente. "
                            "El texto dice 'aguas del reservorio de San Lorenzo'; el proyecto capta del lateral L-3 del canal Tablazo, alimentado por el reservorio vía canal Yuscay. "
                            "Es el agua que entra a la red de canales de San Lorenzo, no una muestra tomada dentro de un canal. Una sola muestra, sin rango. "
                            "Leído en una copia de terceros (dokumen.site) del perfil PSI; no se encontró el original en sitio oficial. "
                            "Estación desconocida: el Cuadro 13 y el texto (sección B.4) no dan fecha ni mes de muestreo (revisado de nuevo el 24-oct-2026)."),
                     fuente_agua="reservorio", nivel="punto", punto="PSI2011_SanLorenzo", subzona="Valle San Lorenzo", resolucion="una muestra, sistema de riego"))
    # pozos en tesis UNP (solo resumen del repositorio, vía buscador; el repositorio UNP no respondió el 24-oct-2026)
    rows.append(dict(variable="CE_agua_napa_pozo", valor="", valor_min=0.13, valor_max=1.12, unidad="dS/m", zona="bajo_piura",
                     lugar="Pozos del AA.HH. Nuevo Santa Rosa y alrededores (Cura Mori)", lat="", lon="", fecha_o_periodo="c. 2019",
                     fuente="Flores Huancas, D. L. (2019). Exploración hidrogeológica para aprovechamiento de agua subterránea en el AA.HH. Nuevo Santa Rosa, distrito de Cura Mori. Tesis UNP",
                     url_o_doi="http://repositorio.unp.edu.pe/handle/UNP/2009",
                     metodo="CE de pozos inventariados (5 pozos) a 25 °C; dato tomado del resumen", tipo_evidencia="medicion_local", estado="observado",
                     notas=("Publicado 0.13-1.12 mmhos/cm a 25 °C; clasificación C3S1 en el resumen. Acuífero confinado de la Formación Zapallal. "
                            "Leído solo el resumen vía buscador: el repositorio UNP no respondió (timeout) y ALICIA devolvió 403 el 24-oct-2026. Rango entre pozos."),
                     fuente_agua="pozo", nivel="punto", punto="UNP2019_CuraMori", subzona="Bajo Piura", resolucion="5 pozos, distrito"))
    rows.append(dict(variable="CE_agua_napa_pozo", valor="", valor_min=0.16, valor_max=3.83, unidad="dS/m", zona="medio_piura",
                     lugar="Pozos del predio Progreso Bajo y alrededores (Castilla); pozo Santa Clara 1.80 dS/m", lat="", lon="", fecha_o_periodo="c. 2018",
                     fuente="Tesis UNP (2018). Exploración hidrogeológica para la ejecución de una obra de captación de agua subterránea en el predio Progreso Bajo, distrito de Castilla",
                     url_o_doi="http://repositorio.unp.edu.pe/handle/UNP/1806",
                     metodo="CE de 7 pozos; dato tomado del resumen", tipo_evidencia="medicion_local", estado="observado",
                     notas=("Publicado 0.16-3.83 mS/cm en 7 pozos; pozo Santa Clara 1.80 dS/m, RAS 5.5, C3S2. "
                            "Leído solo el resumen vía buscador: el repositorio UNP no respondió (timeout) el 24-oct-2026. Rango entre pozos."),
                     fuente_agua="pozo", nivel="punto", punto="UNP2018_Castilla", subzona="Medio Piura", resolucion="7 pozos, predio"))
    pts = pd.DataFrame(rows)
    pts["estacion"] = pts.fecha_o_periodo.map(estacion_de)

    # resúmenes por zona y fuente de agua
    res = []
    for (zona, fa), g in pts[pts.zona.isin(["chira", "san_lorenzo", "medio_piura", "bajo_piura", "alto_piura", "sierra_piura"])].groupby(["zona", "fuente_agua"]):
        excl = sorted(set(g[g.estado == "desconocido"].punto))
        g = g[g.estado != "desconocido"]
        # Alineado con restricciones/anexos/cew_resumen_zona.csv (Piura Datos, 08:12): en agua superficial el resumen usa solo la
        # campaña ANA oct-2024 (misma fecha, mismo método); 2015, la tesis de 2021 y el perfil de 2011 quedan como filas nivel=punto.
        otros = []
        if fa != "pozo":
            otros = sorted(set(f"{a} {str(b)[:7]}" for a, b, v in zip(g.punto, g.fecha_o_periodo, g.valor) if not str(b).startswith("2024")))
            g2 = g[g.fecha_o_periodo.astype(str).str.startswith("2024")]
            if not g2.empty: g = g2
        if g.empty: continue
        # rango entre puntos: cifra del punto si la tiene; su rango solo si no hay cifra (el rango del balance iónico no ensancha la zona)
        v_ = pd.to_numeric(g.valor, errors="coerce")
        lo = v_.fillna(pd.to_numeric(g.valor_min, errors="coerce")).min()
        hi = v_.fillna(pd.to_numeric(g.valor_max, errors="coerce")).max()
        med = pd.to_numeric(g.valor, errors="coerce").dropna()
        var = "CE_agua_napa_pozo" if fa == "pozo" else f"CE_agua_riego_{fa}"
        est = "estimado" if (g.estado == "estimado").any() else "observado"
        res.append(dict(variable=var, valor=round(med.median(), 3) if len(med) >= 2 else "", valor_min=round(lo, 4), valor_max=round(hi, 4),
                        unidad="dS/m", zona=zona, lugar="; ".join(sorted(set(f"{a} ({str(b)[:7]})" for a, b in zip(g.punto, g.fecha_o_periodo)))), lat="", lon="",
                        fecha_o_periodo="; ".join(sorted(set(str(x)[:7] for x in g.fecha_o_periodo))),
                        fuente="; ".join(sorted(set(g.fuente.str.split(",").str[0]))) + " (detalle en filas nivel=punto)",
                        url_o_doi="; ".join(sorted(set(g.url_o_doi))),
                        metodo="Mín-máx de las mediciones de la zona (filas nivel=punto); valor = mediana si hay ≥ 2 puntos; agua superficial: solo campaña ANA oct-2024",
                        tipo_evidencia="medicion_local", estado=est,
                        notas=((f"{len(g)} mediciones. " + ("Incluye lecturas con unidad corregida (estado estimado). " if est == "estimado" else "") +
                               "Rango entre puntos y fechas distintos, no incertidumbre de un punto. " +
                               ("Superficial en estiaje (oct-nov); en avenida baja por dilución. " if set(g.estacion) == {"estiaje"} else
                                "Estación: " + ", ".join(sorted(set(g.estacion))) + ". ") +
                               "La zona sale del polígono de distrito del punto de muestreo, no de dónde se usa el agua. " +
                               (f"Excluidos por CE desconocida (balance iónico no cierra): {', '.join(excl)}. " if excl else "") +
                               (f"Fuera del resumen por ser de otra campaña (ver filas nivel=punto): {', '.join(otros)}. " if otros and len(g) and str(g.fecha_o_periodo.iloc[0]).startswith("2024") else "") +
                               "Alineado con restricciones/anexos/cew_resumen_zona.csv (Piura Datos). ") if fa != "pozo" else
                               " | ".join(f"{p}: {n}" for p, n in zip(g.punto, g.notas))),
                        fuente_agua=fa, estacion="; ".join(sorted(set(g.estacion))), nivel="resumen", punto="", subzona="", resolucion="zona"))
    res = pd.DataFrame(res)

    # combinaciones buscadas sin cifra
    SIN = [
        ("canal", "bajo_piura", "Canal Biaggio Arbulú y canales del Bajo Piura (incl. Sechura)", PD + " (id e4fdd29e73aa)",
         "https://alicia.concytec.gob.pe/vufind/Record/RUMP_2d9b598e96d96609a3bec74516783a5a",
         "Tesis García Ramos (2022) midió CE en 27 muestras del canal Biaggio Arbulú pero el resumen no da cifras y el PDF UNP no responde; "
         "Scribd cita un máximo de 1948 µS/cm sin autor verificable (no se carga). Búsqueda web 24-oct-2026 sin otra cifra. "
         "Aproximación: agua de Poechos en la salida 0.59 dS/m (RChir3, oct-2024) más lo que gane en el trayecto."),
        ("canal", "medio_piura", "Canal Biaggio Arbulú (Castilla) y canal de derivación Daniel Escobar", PD + " (id e4fdd29e73aa)", "",
         "Igual que el Bajo Piura: no hay cifra verificada del canal. RChip2 (1.88 dS/m) es el río Chipillico junto al acueducto, no el canal."),
        ("canal", "chira", "Canales Miguel Checa, Norte y Sur del Chira", "Búsqueda web 24-oct-2026 (ANA, Junta de Usuarios Chira, PECHP)", "",
         "Sin cifra de canal. El río Chira entre Poechos y Sullana da 0.59-0.85 dS/m (oct-2024)."),
        ("canal", "san_lorenzo", "Canales Yuscay, Tablazo y laterales de San Lorenzo", PD + " (id 5e50e1ec77bf); IMARPE 2007 sin CE; búsqueda web 24-oct-2026", "",
         "Sin muestra tomada dentro de un canal. Lo más cercano: agua del reservorio San Lorenzo 0.47 dS/m (PSI-UNP c. 2011, fila PSI2011_SanLorenzo) "
         "y afluentes en oct-2024: Chipillico antes del reservorio 0.42 dS/m, Quiroz 0.45-0.59 dS/m."),
        ("dren", "bajo_piura", "Drenes Sechura y 13.08 (DS 13.04) y red secundaria", "Búsqueda web 24-oct-2026; World Bank (proyecto Bajo Piura); tesis UPCH bahía de Sechura", "",
         "Ninguna fuente con CE del agua de dren. ANA (nota 7-feb-2024) dice que la quebrada Sofía supera el ECA (> 2.5 dS/m) por drenaje agrícola, sin cifra."),
        ("rio", "bajo_piura", "Río Piura aguas abajo de Piura (Catacaos, Cura Mori, La Arena, El Tallán, Sechura)",
         "Informes ANA 0076-2024 y monitoreo nov-2015; nota ANA 7-feb-2024 (" + PD + ", id ea10256add7c)", ANA24P_URL,
         "Ninguna estación de la red ANA cae en distritos del Bajo Piura (la más baja, RPiur6 Río Seco, está en Medio Piura). "
         "Aguas arriba, en Medio Piura: 0.74-9.92 dS/m en oct-2024 (RPiur6 0.74 y RPiur13 5.98 medidos; RPiur5 El Papayo 9.92 [9.73-12.32] estimado por balance iónico, Piura Datos) y 1.98-3.32 dS/m en nov-2015 (filas nivel=punto). No se transfiere al Bajo Piura."),
        ("dren", "medio_piura", "Drenes del Medio Piura", "Búsqueda web 24-oct-2026", "", "Sin cifra."),
        ("pozo", "chira", "Pozos del valle del Chira", "Búsqueda web 24-oct-2026", "", "Sin cifra de CE de pozos."),
        ("pozo", "san_lorenzo", "Pozos de San Lorenzo", "Búsqueda web 24-oct-2026", "", "Sin cifra de CE de pozos."),
        ("pozo", "alto_piura", "Pozos del Alto Piura", "Búsqueda web 24-oct-2026", "",
         "Sin cifra. La tesis UNP de Cura Mori (0.13-1.12 dS/m) es Bajo Piura y va en esa zona."),
        ("pozo", "bajo_piura", "Tablazo Sur (La Unión-Sechura), acuífero Sechura-Parachique, pozo por pozo", PD + " (id 0a5bfd09ce64)",
         "https://core.ac.uk/download/pdf/270312601.pdf",
         "CORE devuelve un desafío Cloudflare (24-oct-2026). Los pozos IRHS-21 y IRHS-32 (La Unión, Tablazo) están dentro del rango ERH 0.04-16.83 dS/m, "
         "pero sus valores individuales no salen del texto."),
    ]
    sin = pd.DataFrame([dict(variable=("CE_agua_napa_pozo" if fa == "pozo" else f"CE_agua_riego_{fa}") + ("_tablazo_sur" if lug.startswith("Tablazo") else ""), valor="", valor_min="", valor_max="",
                             unidad="dS/m", zona=z, lugar=lug, lat="", lon="", fecha_o_periodo="", fuente=fu, url_o_doi=u,
                             metodo="Búsqueda documentada (WebSearch, curl, archivos de Piura Datos)", tipo_evidencia="regional",
                             estado="desconocido", notas=nt + " Sin rango porque no hay dato.", fuente_agua=fa, estacion="", nivel="sin_dato", punto="",
                             subzona="", resolucion="zona") for fa, z, lug, fu, u, nt in SIN])
    out = pd.concat([res, pts, sin], ignore_index=True)
    for c in COLS:
        if c not in out: out[c] = ""
    out = out[COLS]
    v = pd.to_numeric(pd.concat([out.valor, out.valor_min, out.valor_max]), errors="coerce")
    assert (v.dropna() <= 20).all() or False, "CE de agua > 20 dS/m: probable µS/cm sin convertir"
    # H05 + coordinador 07:55: una sola variable del contrato, ce_agua_riego; el origen va en fuente_agua y el nivel (punto/resumen/sin_dato) en nivel.
    out["variable"] = "ce_agua_riego"
    out.to_csv(os.path.join(D, "cew_por_zona.csv"), index=False)
    print(out.groupby(["nivel", "estado"]).size())
    print(res[["variable", "zona", "valor", "valor_min", "valor_max", "estado", "lugar"]].to_string())
    print(pts[["punto", "zona", "subzona", "lat", "lon", "valor"]].to_string())


if __name__ == "__main__":
    main()
