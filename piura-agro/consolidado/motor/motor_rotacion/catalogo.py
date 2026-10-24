"""Catálogo de fichas de cultivo armado desde CSV.

Fuentes por defecto:
- ../datos_repo/   copias del repo nasa_hack (Kc, duraciones, NPK, Ky, umbrales de suelo, plagas, clima)
- ../datos_motor/  tablas del motor (salinidad FAO-29, DRAP, costos, reglas, escenarios, zonas)
- ../datos_agronomia/  copia fechada de lo que entrega Piura Agronomía (EcoCrop pH/profundidad/temperatura,
  salinidad de arveja y por defecto de clase, nutrientes, Kc de mango y papaya, reglas). Cada fila se valida
  antes de entrar (validacion.py) y queda en `Catalogo.registro` (aceptada | rechazada | ignorada + motivo).

Punto de integración para los otros bots: `Catalogo.integrar_csv_contrato(ruta)` acepta cualquier CSV con las
columnas de CONTRATO.md (incluida `zona`). Las variables reconocidas están en VARIABLES_CONTRATO; una fila reemplaza
al dato actual solo si cumple el contrato y su tipo_evidencia tiene igual o mayor prioridad. Una fila con zona
se guarda para esa zona y solo se usa en parcelas de esa zona (`Catalogo.ficha(nombre, zona)`).
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from .cifra import Cifra, TIPOS_EVIDENCIA
from .validacion import (ACEPTADA, IGNORADA, RECHAZADA, Registro, faltan_columnas, validar_fila_contrato, validar_kc,
                         validar_nutriente, validar_parametro, validar_salinidad, METODO_CE_NO_DECLARADO,
                         METODO_DOTACION, VARIABLES_CE_SUELO, ZONAS_AGREGADAS, validar_zona_columna, zonas_de_fila)

BASE = Path(__file__).resolve().parents[1]
DIR_REPO = BASE / "datos_repo"
# Escenarios climáticos por clasificación ICEN (ENFEN/IGP) de la campaña, los de Piura Datos (lluvia_zona_pisco.csv)
ESCENARIOS_ICEN = ("sin_el_nino", "el_nino_moderado", "el_nino_fuerte_extraordinario")
ESCENARIOS_NINO = ESCENARIOS_ICEN[1:]
DIR_MOTOR = BASE / "datos_motor"
DIR_AGRONOMIA = BASE / "datos_agronomia"
ETAPAS = ("inicial", "desarrollo", "media", "final")
FAO56_URL = "https://www.fao.org/4/x0490e/x0490e0b.htm"


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x) -> float | None:
    if x is None:
        return None
    x = str(x).strip().replace(",", ".")
    if x in ("", "nan", "NaN", "None"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def _dias(txt: str) -> tuple[float, float] | None:
    vals = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", str(txt))]
    return (min(vals), max(vals)) if vals else None


def anios_del_mes(campanias: list[int], mes: int) -> list[int]:
    """Años calendario de un mes dentro de campañas ICEN ago(Y-1)-jul(Y) rotuladas por Y."""
    return list(campanias) if mes <= 7 else [y - 1 for y in campanias]


@dataclass
class Umbral:
    """Rango de aptitud de suelo/clima. `duro=True` descarta; `duro=False` solo advierte."""
    variable: str
    minimo: float | None
    maximo: float | None
    unidad: str
    duro: bool
    fuente: str
    url: str
    tipo_evidencia: str = "bibliografico"
    nivel: str = ""  # "" = según duro; "nota" = solo se anota (óptimo EcoCrop, sin peso en la decisión)
    etiqueta: str = ""  # texto corto para el mensaje


@dataclass
class Rampa:
    """Aptitud continua (FAO EcoCrop): 1 dentro de [apto_min, apto_max], lineal hasta 0 en el límite absoluto.

    pH: apto = óptimo EcoCrop, absoluto = PHMIN–PHMAX. Profundidad (m): apto_min = DEP (favorable), abs_min = DEPR
    (mínima apta). Un límite absoluto desconocido (None) deja la aptitud fuera del rango apto como desconocida."""
    variable: str  # "ph" | "profundidad_m"
    unidad: str
    apto_min: float | None
    apto_max: float | None
    abs_min: float | None
    abs_max: float | None
    fuente: str
    url: str
    tipo_evidencia: str = "bibliografico"
    notas: str = ""

    def aptitud(self, x: float) -> float | None:
        if self.apto_min is not None and x < self.apto_min:
            if self.abs_min is None:
                return None
            if x <= self.abs_min or self.apto_min <= self.abs_min:
                return 0.0
            return (x - self.abs_min) / (self.apto_min - self.abs_min)
        if self.apto_max is not None and x > self.apto_max:
            if self.abs_max is None:
                return None
            if x >= self.abs_max or self.apto_max >= self.abs_max:
                return 0.0
            return (self.abs_max - x) / (self.abs_max - self.apto_max)
        return 1.0

    def aptitud_intervalo(self, lo: float, hi: float) -> tuple[float | None, float | None]:
        """(mínima, máxima) aptitud posible si el valor real está en [lo, hi]. La función es una meseta, así que el
        mínimo está en un extremo y el máximo es 1 si el intervalo toca el rango apto."""
        a_lo, a_hi = self.aptitud(lo), self.aptitud(hi)
        minimo = None if None in (a_lo, a_hi) else min(a_lo, a_hi)
        toca = (self.apto_min is None or hi >= self.apto_min) and (self.apto_max is None or lo <= self.apto_max)
        if toca:
            maximo = 1.0
        else:
            conocidos = [a for a in (a_lo, a_hi) if a is not None]
            maximo = max(conocidos) if len(conocidos) == 2 else None
        return minimo, maximo

    def describir(self) -> str:
        f = lambda a, b: f"{'' if a is None else a}–{'' if b is None else b}"
        if self.variable == "profundidad_m":
            return (f"mínima apta {self.abs_min if self.abs_min is not None else 'desconocida'} m, "
                    f"favorable ≥ {self.apto_min if self.apto_min is not None else 'desconocida'} m")
        return f"óptimo {f(self.apto_min, self.apto_max)}, absoluto {f(self.abs_min, self.abs_max)}"


@dataclass
class Ficha:
    cultivo: str
    familia: str
    modulo: str  # anual | perenne
    leguminosa: bool
    notas: str = ""
    kc: dict | None = None  # ini, mid_lo, mid_hi, end_lo, end_hi, fuente
    etapas: dict | None = None  # etapa -> (dias_lo, dias_hi)
    duracion: Cifra | None = None
    salinidad: dict | None = None  # ECe_100..ECe_0, ECw_100..ECw_0, fuente, estado, notas
    umbrales: list[Umbral] = field(default_factory=list)
    ky: Cifra | None = None
    absorcion: dict = field(default_factory=dict)  # 'N'|'P2O5'|'K2O' -> Cifra kg/t
    exportacion: dict = field(default_factory=dict)  # producto retirado, kg/t
    exportacion_residuo: dict = field(default_factory=dict)
    rendimiento: dict = field(default_factory=dict)  # lugar -> Cifra t/ha
    precio: dict = field(default_factory=dict)  # lugar -> Cifra PEN/kg
    costo: Cifra | None = None
    rampas: dict = field(default_factory=dict)  # "ph" | "profundidad_m" -> Rampa
    por_zona: dict = field(default_factory=dict)  # (destino, zona) -> Cifra (destino: rendimiento|precio|costo|duracion)
    calendario: dict = field(default_factory=dict)  # zona -> VentanaObservada (siembra/cosecha observadas DRAP)
    primera_produccion: dict = field(default_factory=dict)  # zona ('' = sin zona) -> Cifra años a la 1.ª producción
    anegamiento: list = field(default_factory=list)  # textos con fuente: pérdida o tolerancia al anegamiento
    umbral_floracion: Umbral | None = None  # Tmáx del aire en floración-llenado (aborto); se compara con PISCOt

    def tiene_registro_en(self, provincia: str) -> bool:
        return clave_provincia(provincia) in self.rendimiento

    def por_lugar(self, tabla: dict, provincia: str | None, unidad: str, variable: str, zona: str | None = None) -> Cifra:
        if zona and f"zona:{zona}" in tabla:
            return tabla[f"zona:{zona}"]
        if provincia:
            c = tabla.get(clave_provincia(provincia))
            if c is not None:
                return c
        return tabla.get("Piura (departamento)") or Cifra.desconocido(unidad, variable, f"sin dato de {variable}")


def clave_provincia(provincia: str) -> str:
    """'Morropón' -> 'Piura/Morropon' (clave de las tablas DRAP)."""
    import unicodedata
    p = unicodedata.normalize("NFKD", provincia.strip()).encode("ascii", "ignore").decode()
    return f"Piura/{p.title()}"


VARIABLES_CONTRATO = {
    "rendimiento": "rendimiento",
    "precio_chacra": "precio",
    "costo_produccion_ha": "costo",
    "costo_produccion": "costo",  # nombre usado en evidencia_observada.csv (Piura Datos); solo si la unidad es PEN/ha
    "duracion_ciclo": "duracion",
}
# nombres de otros equipos -> cultivo del catálogo (solo equivalencias exactas de especie/producto)
ALIAS_CULTIVO = {"frijol caupí": "caupi", "frijol caupi": "caupi", "maíz amarillo duro": "maiz amarillo duro",
                 "algodón": "algodon"}
UNIDAD_DESTINO = {"costo": ("PEN/ha",), "rendimiento": ("t/ha",), "precio": ("PEN/kg",), "duracion": ("días",)}
# Variables de zona (no de cultivo) que el motor usa como contexto cuando la parcela no trae el dato.
VARIABLES_ZONA = {
    "ce_agua_riego": "ecw",
    "pendiente_p50_cultivo": "pendiente_p50",
    "pendiente_p90_cultivo": "pendiente_p90",
    "pendiente_media_cultivo": "pendiente_media",
}
# Ampliación convencional de un costo análogo externo sin rango propio (supuesto del motor, no dato): [v/2, 2v].
FACTOR_ANALOGO_COSTO = 2.0  # supuesto del motor: costo análogo externo se amplía a [v/2, 2v]


def ampliar_costo_analogo(c: Cifra) -> Cifra:
    """Un costo de otra región/especie (analogo_externo) se usa con incertidumbre ampliada: el rango final es la
    envolvente de su propio rango (si lo trae) y [v/FACTOR, v·FACTOR]. Se marca en notas para que el reporte avise."""
    lo = min(x for x in (c.lo, c.valor / FACTOR_ANALOGO_COSTO) if x is not None)
    hi = max(x for x in (c.hi, c.valor * FACTOR_ANALOGO_COSTO) if x is not None)
    return c.con(valor_min=lo, valor_max=hi, notas=f"{c.notas} [COSTO ANÁLOGO EXTERNO: rango = envolvente del rango de la "
                                     f"fuente (si lo trae) y ×1/{FACTOR_ANALOGO_COSTO:g}–×{FACTOR_ANALOGO_COSTO:g} del valor "
                                     "(supuesto del motor, no dato)]".strip())


# CE del agua (ce_agua_riego). Solo el agua que llega a los canales (canal, reservorio, toma; columna fuente_agua) es
# VALOR DE ZONA. Un punto de río o quebrada y un pozo quedan como aviso: la dispersión entre puntos no es la
# incertidumbre del agua de una parcela (H06 de Agronomía sobre Territorio).
FUENTES_AGUA_DE_CANAL = ("canal", "reservorio", "toma")


# Nombres que el motor reconoce pero no toma del catálogo (dato de parcela u otro módulo): se anotan como ignorados.
VARIABLES_NO_USADAS = {"dotacion_agua": "la dotación entra por la consulta (agua.m3_por_mes), no por el catálogo",
                       "costo_produccion_por_t": "costo por tonelada (PEN/t); el margen necesita PEN/ha"}


def variables_conocidas() -> list[str]:
    """Nombres de variable de CONTRATO.md que integrar_csv_contrato reconoce; cualquier otro se rechaza con mensaje."""
    return sorted(set(VARIABLES_CONTRATO) | set(VARIABLES_ZONA) | set(VARIABLES_CE_SUELO) | set(VARIABLES_NO_USADAS))


def motivo_variable_desconocida(variable: str) -> str:
    m = f"variable '{variable}' no reconocida por el motor; nombres aceptados: {', '.join(variables_conocidas())}"
    v = variable.lower()
    if v.startswith(("ce_agua", "cew", "ecw")):
        m += (". Para la CE del agua de riego use 'ce_agua_riego' y ponga el tipo de agua (canal, reservorio, toma, "
              "río, quebrada, pozo) en la columna 'fuente_agua'")
    return m


@dataclass
class AguaPunto:
    """Lectura de CE de agua que no es la de un canal (punto de río o quebrada, pozo): solo contexto en avisos."""
    zona: str
    tipo: str  # "punto" | "pozo"
    punto: str
    fecha: str
    estacion: str
    cifra: Cifra


def es_hwsd(r: dict) -> bool:
    texto = " ".join(str(r.get(k) or "") for k in ("fuente", "metodo", "notas", "url_o_doi", "fuente_primaria")).lower()
    return "hwsd" in texto or "harmonized world soil" in texto


class Catalogo:
    def __init__(self, dir_repo: Path = DIR_REPO, dir_motor: Path = DIR_MOTOR, dir_agronomia: Path | None = DIR_AGRONOMIA):
        self.dir_repo = Path(dir_repo)
        self.dir_motor = Path(dir_motor)
        self.dir_agronomia = Path(dir_agronomia) if dir_agronomia else None
        self.fichas: dict[str, Ficha] = {}
        self.registro: list[Registro] = []
        self.reglas: dict[str, dict] = {}  # id -> fila CONTRATO.md de una regla de Agronomía aceptada
        self.contexto_zona: dict[tuple[str, str], Cifra] = {}  # (variable motor, zona) -> Cifra de zona (no de parcela)
        self.contexto_regional: list[tuple[str, str, Cifra]] = []  # (variable, zona, Cifra): solo para avisos
        self.contexto_agua: list[AguaPunto] = []  # CE de puntos de río/quebrada y de pozos: solo para avisos
        self.ausencias_calendario: dict[tuple[str, str], tuple] = {}  # (cultivo, zona) -> (periodo, url, confianza)
        self.tmax_pisco: dict[tuple[str, int], Cifra] = {}  # (zona, mes) -> media de las máximas diarias PISCOt
        self.lluvia_pisco: dict[tuple[str, str, int], Cifra] = {}  # (zona, escenario ICEN, mes) -> lluvia PISCOp mm
        self.anios_icen: dict[str, list[int]] = {}  # escenario ICEN -> años de la campaña (notas de PISCOp)
        self.contexto_icen = ""  # evento en curso según las notas del escenario fuerte (con su fuente)
        self.reglas_sanidad = leer_csv(self.dir_motor / "reglas_sanidad.csv")
        self.reglas_terreno = leer_csv(self.dir_motor / "reglas_terreno.csv")
        self._cargar()

    # ---- carga -------------------------------------------------------------------------
    def _cargar(self):
        for r in leer_csv(self.dir_motor / "catalogo_cultivos.csv"):
            self.fichas[r["cultivo"]] = Ficha(r["cultivo"], r["familia"], r["modulo"], r["leguminosa"] == "1", r["notas"])
        self._cargar_kc()
        self._cargar_duraciones()
        self._cargar_parametros()
        self._cargar_salinidad()
        self._cargar_nutrientes()
        self._cargar_ky()
        self.integrar_csv_contrato(self.dir_motor / "rendimiento_precio_drap.csv")
        self.integrar_csv_contrato(self.dir_motor / "costos_produccion.csv")
        if self.dir_agronomia and self.dir_agronomia.exists():
            self._cargar_agronomia()
        self._cargar_tmax_pisco()
        self._cargar_lluvia_pisco()
        self._armar_rampas()

    def _cargar_tmax_pisco(self):
        """Media mensual de las máximas diarias por zona (PISCOt 1981-2020, de Piura Datos). Si una zona trae varias
        celdas (sierra: Ayabaca y Huancabamba), la Cifra es la envolvente de sus rangos P10/P90."""
        ruta = self.dir_repo / "temperatura_pisco_zona.csv"
        if not ruta.exists():
            return
        juntas: dict[tuple[str, int], list[Cifra]] = {}
        for i, r in enumerate(leer_csv(ruta), start=2):
            if r["variable"] != "temperatura_max_media_mensual":
                self._anotar(ruta, i, r["cultivo"], r["variable"], IGNORADA,
                             "el motor solo usa la media de las máximas en la regla térmica grave")
                continue
            problemas = validar_fila_contrato(r)
            from .calendario_obs import MESES
            mes = MESES.get(r["fecha_o_periodo"].rsplit(",", 1)[-1].strip()[:3].lower())
            if mes is None:
                problemas.append(f"mes no reconocido en fecha_o_periodo: {r['fecha_o_periodo']!r}")
            if problemas:
                self._anotar(ruta, i, r["cultivo"], r["variable"], RECHAZADA, "; ".join(problemas))
                continue
            c = self._cifra_desde_fila(r)
            juntas.setdefault((r["zona"], mes), []).append(c.con(notas=f"{r.get('subzona') or r['lugar']}: {c.notas}"))
            self._anotar(ruta, i, r["cultivo"], r["variable"], ACEPTADA,
                         f"Tmáx media PISCOt de {r['zona']} mes {mes} (regla térmica grave)")
        for clave, cs in juntas.items():
            lo, hi = min(c.lo for c in cs), max(c.hi for c in cs)
            base = cs[0]
            if len(cs) > 1:
                base = base.con(valor=round(sum(c.valor for c in cs) / len(cs), 3),
                                notas=f"envolvente de {len(cs)} celdas PISCOt de la zona: " + " | ".join(c.notas for c in cs))
            self.tmax_pisco[clave] = base.con(valor_min=lo, valor_max=hi, variable="tmax_media")

    def _cargar_lluvia_pisco(self):
        """Lluvia mensual PISCOp por zona y escenario ICEN (Piura Datos). La sierra trae dos subzonas (Ayabaca,
        Huancabamba): se guarda la envolvente. Los años de cada escenario salen de las notas ('años [..]') y deben
        coincidir en todas las filas; el contexto del evento en curso sale de las notas del escenario fuerte."""
        ruta = self.dir_repo / "lluvia_zona_pisco.csv"
        if not ruta.exists():
            return
        from .calendario_obs import MESES
        filas = list(enumerate(leer_csv(ruta), start=2))

        def mes_y_anios(r):
            partes = r["fecha_o_periodo"].split(",")
            mes = MESES.get(partes[1].strip()[:3].lower()) if len(partes) > 1 else None
            m = re.search(r"años \[([\d, ]+)\]", r.get("notas") or "")
            return mes, ([int(x) for x in m.group(1).split(",")] if m else None)

        # campaña ICEN = ago(Y-1)-jul(Y), rotulada por Y: ene-jul usan los años Y y ago-dic los años Y-1
        for _, r in filas:
            mes, anios = mes_y_anios(r)
            esc = (r.get("escenario") or "").strip()
            if r["variable"] == "precipitacion_mensual" and mes == 1 and anios and esc in ESCENARIOS_ICEN:
                self.anios_icen.setdefault(esc, anios)
        juntas: dict[tuple[str, str, int], list[Cifra]] = {}
        for i, r in filas:
            esc, var = (r.get("escenario") or "").strip(), r["variable"]
            if var != "precipitacion_mensual":
                self._anotar(ruta, i, "", var, IGNORADA, "el motor usa la lluvia mensual; la de temporada es un resumen")
                continue
            problemas = validar_fila_contrato(r)
            if esc not in ESCENARIOS_ICEN:
                problemas.append(f"escenario '{esc}' no es ICEN ({', '.join(ESCENARIOS_ICEN)})")
            mes, anios = mes_y_anios(r)
            if mes is None:
                problemas.append(f"mes no reconocido en fecha_o_periodo: {r['fecha_o_periodo']!r}")
            if not anios:
                problemas.append("las notas no dicen los años del escenario ('años [..]')")
            elif mes is not None and esc in self.anios_icen:
                esperados = set(anios_del_mes(self.anios_icen[esc], mes))
                # en los bordes de PISCOp (1981-2019) una campaña queda partida: ago-dic 2019 entra sin su ene-jul
                fuera = {a for a in set(anios) - esperados if min(esperados) <= a <= max(esperados)}
                if fuera:
                    problemas.append(f"años {anios} no son los de la campaña {self.anios_icen[esc]} para el mes {mes}")
            if problemas:
                self._anotar(ruta, i, "", var, RECHAZADA, "; ".join(problemas))
                continue
            if esc == "el_nino_fuerte_extraordinario" and not self.contexto_icen and "Evento en curso" in r["notas"]:
                self.contexto_icen = r["notas"][r["notas"].index("Evento en curso"):].strip()
            c = self._cifra_desde_fila(r).con(variable="lluvia", notas=f"{r.get('subzona') or r['lugar']}: {r['notas']}")
            juntas.setdefault((r["zona"], esc, mes), []).append(c)
            self._anotar(ruta, i, "", var, ACEPTADA, f"lluvia PISCOp {r['zona']} {esc} mes {mes}: {c.texto(1)}")
        for clave, cs in juntas.items():
            base = cs[0]
            if len(cs) > 1:
                base = base.con(valor=round(sum(c.valor for c in cs) / len(cs), 1),
                                valor_min=min(c.lo for c in cs), valor_max=max(c.hi for c in cs),
                                notas=f"envolvente de {len(cs)} subzonas PISCOp: " + " | ".join(c.notas[:120] for c in cs))
            self.lluvia_pisco[clave] = base

    def _agro_anegamiento(self, ruta: Path):
        """Pérdida de rendimiento y tolerancia al anegamiento (fichas_anuales.csv). Solo se citan cuando hay exceso
        de agua: la duración del anegamiento en El Niño es desconocida (R4A024), así que no se aplican al margen."""
        if not ruta.exists():
            return
        for r in leer_csv(ruta):
            var = r.get("variable", "")
            if var not in ("perdida_rendimiento_anegamiento", "tolerancia_anegamiento", "tolerancia_encharcamiento"):
                continue
            cultivo, fila = r.get("cultivo", ""), r.get("id", "")
            problemas = validar_fila_contrato(r)
            if problemas:
                self._anotar(ruta, fila, cultivo, var, RECHAZADA, "; ".join(problemas))
                continue
            if cultivo not in self.fichas:
                self._anotar(ruta, fila, cultivo, var, IGNORADA, "cultivo fuera del catálogo")
                continue
            notas = r.get("notas") or ""
            if var == "perdida_rendimiento_anegamiento":
                m = re.search(r"duración ([\d\-]+ días)", notas)
                cuanto = f"con {m.group(1)} de anegamiento" if m else "promedio de duraciones de hasta 15 días"
                texto = f"pérdida media {float(r['valor']):g} % {cuanto}"
            else:
                texto = f"tolerancia {r['valor']}"
            f = self.fichas[cultivo]
            f.anegamiento.append(f"{texto} ({r['fuente'].split(',')[0]}, {r['tipo_evidencia']}, {fila})")
            self._anotar(ruta, fila, cultivo, var, ACEPTADA, f"{texto}; solo se cita si hay exceso de agua")

    def escribir_registro(self, ruta) -> None:
        """Registro de integración en TSV: archivo, fila, cultivo, variable, estado (aceptada/rechazada/ignorada), motivo."""
        import csv
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["archivo", "fila", "cultivo", "variable", "estado", "motivo"])
            for r in self.registro:
                w.writerow([r.archivo, r.fila, r.cultivo, r.variable, r.estado, r.motivo])

    def _anotar(self, archivo, fila, cultivo, variable, estado, motivo):
        self.registro.append(Registro(Path(str(archivo)).name, str(fila), cultivo, variable, estado, motivo))

    def _cargar_kc(self):
        for r in leer_csv(self.dir_repo / "fao56_kc_referencias.csv"):
            f = self.fichas.get(r["crop"])
            if f is None:
                continue
            kc = dict(ini=num(r["Kc_initial"]), mid_lo=num(r["Kc_mid_min"]), mid_hi=num(r["Kc_mid_max"]),
                      end_lo=num(r["Kc_end_min"]), end_hi=num(r["Kc_end_max"]), subtipo=r["fao_crop_subtype"],
                      fuente=r["source_table"], url=r["source_url"])
            if f.kc is None:
                f.kc = kc
            elif f.modulo == "perenne":  # perennes: ampliar el rango con todas las variantes
                f.kc["mid_lo"] = min(f.kc["mid_lo"], kc["mid_lo"])
                f.kc["mid_hi"] = max(f.kc["mid_hi"], kc["mid_hi"])
                f.kc["subtipo"] += f"; {kc['subtipo']}"

    def _cargar_duraciones(self):
        acum: dict[str, dict] = {}
        for r in leer_csv(self.dir_repo / "fao56_duracion_analogos.csv"):
            if r["crop"] not in self.fichas:
                continue
            cols = ["L_initial_days_as_printed", "L_development_days_as_printed", "L_mid_days_as_printed",
                    "L_late_days_as_printed"]
            d = acum.setdefault(r["crop"], {e: [] for e in ETAPAS})
            for e, c in zip(ETAPAS, cols):
                v = _dias(r[c])
                if v:
                    d[e] += list(v)
        for cultivo, d in acum.items():
            if all(d[e] for e in ETAPAS):
                f = self.fichas[cultivo]
                f.etapas = {e: (min(d[e]), max(d[e])) for e in ETAPAS}
                lo = sum(v[0] for v in f.etapas.values())
                hi = sum(v[1] for v in f.etapas.values())
                f.duracion = Cifra.rango(lo, hi, "días", "FAO-56 Tabla 11 (mín-máx de las regiones análogas)",
                                         "analogo_externo", "estimado", "ninguna región análoga es Piura; "
                                         "duración local por campaña desconocida", "duracion_ciclo", FAO56_URL)

    def _cargar_parametros(self):
        dur_inia = {}
        for r in leer_csv(self.dir_repo / "parametros_cultivo_v2.csv"):
            f = self.fichas.get(r["crop"])
            if f is None:
                continue
            p, lo, hi, url = r["parameter"], num(r["min_value"]), num(r["max_value"]), r["source_url"]
            fuente = r.get("geographic_scope") or url
            if p.startswith("pH_suelo"):
                duro = p.endswith(("apto", "adaptacion"))
                f.umbrales.append(Umbral("ph", lo, hi, "pH", duro, fuente, url))
            elif p.startswith(("profundidad_suelo", "profundidad_efectiva")):
                duro = "favorable" not in p
                f.umbrales.append(Umbral("profundidad_m", lo, None, "m", duro, fuente, url))
            elif p in ("temperatura_adaptacion",):
                f.umbrales.append(Umbral("tmedia", lo, hi, "°C", True, fuente, url))
            elif p in ("temperatura_media_apta", "temperatura_crecimiento_ideal", "temperatura_optima"):
                f.umbrales.append(Umbral("tmedia", lo, hi, "°C", False, fuente, url))
            elif p == "temperatura_crecimiento_lento_umbral":
                f.umbrales.append(Umbral("tmedia", hi, None, "°C", False, fuente, url))
            elif p == "temperatura_dano_calor_umbral":
                f.umbrales.append(Umbral("tmax", None, lo, "°C", False, fuente, url))
            elif p in ("duracion_verano", "duracion_invierno"):
                dur_inia.setdefault(r["crop"], []).append((lo, hi, url, fuente))
        for cultivo, vals in dur_inia.items():
            f = self.fichas[cultivo]
            lo, hi = min(v[0] for v in vals), max(v[1] for v in vals)
            f.duracion = Cifra.rango(lo, hi, "días", "INIA folleto 619 (verano 140-150 d, invierno 160-170 d)",
                                     "regional", "estimado", vals[0][3], "duracion_ciclo", vals[0][2])
            f.etapas = _reescalar_etapas(f.etapas, lo, hi)

    def _cargar_salinidad(self):
        for r in leer_csv(self.dir_motor / "umbrales_salinidad_fao29.csv"):
            f = self.fichas.get(r["cultivo"])
            if f is None:
                continue
            s = {k: num(r[k]) for k in r if k.startswith(("ECe_", "ECw_"))}
            s.update(fuente=r["fuente"], url=r["url_o_doi"], estado=r["estado"], notas=r["notas"],
                     tipo=r["tipo_evidencia"], proxy=r["cultivo_fao29"])
            f.salinidad = s if s["ECe_100"] is not None else None
            if f.salinidad:
                f.salinidad["defecto_clase"] = False

    def _cargar_nutrientes(self):
        for r in leer_csv(self.dir_repo / "nutrientes_cultivo_fao.csv"):
            f = self.fichas.get(r["crop"])
            if f is None:
                continue
            exp = r["measurement_type"].startswith("exportación")
            if exp and r["main_product_or_part"] in ("rastrojo", "restos vegetales"):
                destino = f.exportacion_residuo
            else:
                destino = f.exportacion if exp else f.absorcion
            for n, col in (("N", "N_kg_per_t"), ("P2O5", "P2O5_kg_per_t"), ("K2O", "K2O_kg_per_t")):
                v = num(r[col])
                if v is not None:
                    destino[n] = Cifra(v, None, None, f"kg {n}/t", r["source_table"], "bibliografico", "estimado",
                                       r["source_url"], f"{r['main_product_or_part']}; región fuente: "
                                       f"{r['source_region']}; sin calibrar en Piura", f"{n}_por_t")

    def _cargar_ky(self):
        for r in leer_csv(self.dir_repo / "fao_ky_respuesta_agua.csv"):
            f = self.fichas.get(r["crop"])
            if f is not None:
                f.ky = Cifra.rango(num(r["Ky_seasonal_min"]), num(r["Ky_seasonal_max"]), "adimensional",
                                   r["source_table"], "bibliografico", "estimado", r["limitation"], "Ky", r["source_url"])

    # ---- integración ---------------------------------------------------------------------
    def integrar_csv_contrato(self, ruta: Path, estricto: bool = False) -> int:
        """Integra filas con formato CONTRATO.md. Devuelve cuántas filas se usaron.

        Cada fila se valida (validacion.validar_fila_contrato); la que no cumple no entra y queda en el registro.
        Un archivo al que solo le falta la columna `zona` (formato anterior al cambio de CONTRATO.md) se acepta
        con zona vacía y la salvedad anotada; con `estricto=True` se rechaza entero."""
        ruta = Path(ruta)
        with open(ruta, newline="", encoding="utf-8") as fh:
            lector = csv.DictReader(fh)
            filas, cabecera = list(lector), lector.fieldnames or []
        faltan = faltan_columnas(cabecera)
        sin_zona = faltan == ["zona"]
        usadas = 0
        for i, r in enumerate(filas, start=2):
            fila_id = r.get("id") or r.get("id_registro") or r.get("regla_id") or f"línea {i}"
            cultivo, variable = ALIAS_CULTIVO.get(r.get("cultivo", ""), r.get("cultivo", "")), r.get("variable", "")
            if faltan and (estricto or not sin_zona):
                self._anotar(ruta, fila_id, cultivo, variable, RECHAZADA, f"faltan columnas de CONTRATO.md: {', '.join(faltan)}")
                continue
            if sin_zona:
                r = {**r, "zona": ""}
            problemas = validar_fila_contrato(r)
            if variable and variable not in variables_conocidas():
                problemas.append(motivo_variable_desconocida(variable))
            if problemas:
                self._anotar(ruta, fila_id, cultivo, variable, RECHAZADA, "; ".join(problemas))
                continue
            metodo = (r.get("metodo") or "").strip()
            if es_hwsd(r) and (variable in VARIABLES_CE_SUELO or variable.startswith(("ece", "ce_suelo"))):
                self._anotar(ruta, fila_id, cultivo, variable, RECHAZADA,
                             "ECe de HWSD: Piura Datos mostró que falla en las 4 zonas con dato de chacra; el motor no "
                             "usa HWSD para ECe")
                continue
            if variable == "ce_agua_riego":
                self._integrar_agua(ruta, fila_id, r)
                continue
            if variable in VARIABLES_ZONA:
                self._integrar_zona(ruta, fila_id, r, VARIABLES_ZONA[variable])
                continue
            if metodo == METODO_CE_NO_DECLARADO or variable in VARIABLES_CE_SUELO:
                aviso = (" (extracto no declarado: no es ECe de pasta saturada; entra por la consulta con "
                         "suelo.ce_metodo='ce_extracto_no_declarado')" if metodo == METODO_CE_NO_DECLARADO else "")
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA,
                             f"cumple el contrato; es dato de parcela, no del catálogo de cultivos{aviso}")
                continue
            destino = VARIABLES_CONTRATO.get(variable)
            f = self.fichas.get(cultivo)
            if destino is None:
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA, f"variable conocida que el motor no usa del "
                             f"catálogo: {VARIABLES_NO_USADAS[variable]}")
                continue
            if f is None:
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA, "cultivo fuera del catálogo del motor")
                continue
            if (r.get("unidad") or "").strip() not in UNIDAD_DESTINO[destino]:
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA,
                             f"unidad {r.get('unidad')} distinta de la que usa el motor para {destino} "
                             f"({'/'.join(UNIDAD_DESTINO[destino])}); no se convierte")
                continue
            if (r.get("fuente_primaria") or "").strip():
                r = {**r, "fuente": f"{r['fuente']} (cita a: {r['fuente_primaria'].strip()})"}
            if metodo == METODO_DOTACION:
                r = {**r, "notas": f"{r.get('notas', '')} [dotación asignada, no entrega medida]".strip()}
            extra = "; ".join(f"{k}={r[k]}" for k in ("id", "confianza", "subzona") if r.get(k))
            if extra:
                r = {**r, "notas": f"{r.get('notas', '')} [{extra}]".strip()}
            c = self._cifra_desde_fila(r)
            if not c.conocido:
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA, "estado desconocido: no reemplaza ningún dato")
                continue
            salvedad = " (archivo sin columna zona: tratada como zona vacía)" if sin_zona else ""
            if destino == "costo" and c.tipo_evidencia == "analogo_externo":
                c = ampliar_costo_analogo(c)
                salvedad += f" (costo análogo externo: rango ampliado a {c.texto(0)}; el reporte avisa)"
            zonas = [z for z in zonas_de_fila(r) if z != "piura_region"]
            if r.get("zonas_aplicables"):
                salvedad += f" (análogo multizona: zonas_aplicables={r['zonas_aplicables']})"
            if zonas:
                aceptadas = []
                for zona in zonas:
                    extra_ag = (f" [zona agregada: vale para {' y '.join(ZONAS_AGREGADAS[zona])} si no hay dato de la "
                                "zona exacta]") if zona in ZONAS_AGREGADAS else ""
                    actual = f.por_zona.get((destino, zona))
                    if destino == "costo" and _misma_prioridad(c, actual):
                        # dos costos de la misma zona y evidencia (p. ej. PEIHAP actual y optimizada): envolvente,
                        # no el último que llegó
                        f.por_zona[(destino, zona)] = actual.con(
                            valor_min=min(actual.lo, c.lo), valor_max=max(actual.hi, c.hi),
                            notas=f"{actual.notas}; envolvente con otra fila de la misma zona y evidencia: {c.texto(2)} "
                                  f"({c.notas[:80]})")
                        aceptadas.append(zona + " (envolvente)")
                    elif _mejor_o_igual(c, actual):
                        f.por_zona[(destino, zona)] = c
                        if destino in ("rendimiento", "precio"):
                            getattr(f, destino)[f"zona:{zona}"] = c
                        aceptadas.append(zona + extra_ag)
                if aceptadas:
                    usadas += 1
                    self._anotar(ruta, fila_id, cultivo, variable, ACEPTADA, f"solo para zona {', '.join(aceptadas)}{salvedad}")
                else:
                    self._anotar(ruta, fila_id, cultivo, variable, IGNORADA, f"ya hay dato de mayor prioridad para {', '.join(zonas)}")
                continue
            if destino in ("rendimiento", "precio"):
                tabla = getattr(f, destino)
                lugar = r.get("lugar") or "Piura (departamento)"
                ok = _mejor_o_igual(c, tabla.get(lugar))
                if ok:
                    tabla[lugar] = c
            else:
                actual = getattr(f, destino)
                ok = _mejor_o_igual(c, actual)
                if ok:
                    setattr(f, destino, c)
                    if destino == "duracion":
                        f.etapas = _reescalar_etapas(f.etapas, c.lo, c.hi)
            if ok:
                usadas += 1
                self._anotar(ruta, fila_id, cultivo, variable, ACEPTADA, f"{c.texto(1)} ({c.tipo_evidencia}){salvedad}")
            else:
                self._anotar(ruta, fila_id, cultivo, variable, IGNORADA, "ya hay un dato con evidencia de mayor prioridad")
        return usadas

    def _integrar_agua(self, ruta, fila_id, r: dict) -> None:
        """CE del agua: el agua de canal, reservorio o toma es VALOR DE ZONA; un punto
        de río o quebrada y un pozo van a contexto_agua (solo aviso)."""
        sub = (r.get("subzona") or "").strip()
        fecha = (r.get("fecha_o_periodo") or "").strip()
        fuente_agua = (r.get("fuente_agua") or "").strip()
        estacion = (r.get("estacion") or "").strip()
        estacion_txt = "estiaje" if estacion == "estiaje" else (f"estación {estacion}" if estacion and estacion != "desconocida"
                                                                  else "estación desconocida")
        if fuente_agua in FUENTES_AGUA_DE_CANAL:
            r = {**r, "notas": f"{r.get('notas', '')} [agua de {fuente_agua}; {estacion_txt}]".strip()}
            self._integrar_zona(ruta, fila_id, r, "ecw")
            return
        zonas = [z for z in zonas_de_fila(r) if z != "piura_region"]
        c = self._cifra_desde_fila(r)
        if not zonas or not c.conocido:
            self._anotar(ruta, fila_id, "", "ce_agua_riego", IGNORADA,
                         "estado desconocido: no reemplaza ningún dato" if zonas else "dato de agua sin código de zona")
            return
        tipo = "pozo" if fuente_agua == "pozo" else "punto"
        for z in zonas:
            self.contexto_agua.append(AguaPunto(z, tipo, sub or r.get("lugar", ""), fecha, estacion_txt, c))
        self._anotar(ruta, fila_id, "", "ce_agua_riego", ACEPTADA,
                     f"{'pozo' if tipo == 'pozo' else 'punto de río o quebrada'} {', '.join(zonas)} ({sub}, {fecha}, "
                     f"{estacion_txt}): {c.texto(3)}; solo aviso, no es el agua que llega a la parcela")

    def _integrar_zona(self, ruta, fila_id, r: dict, destino: str) -> None:
        """Dato de zona (ECw de río, pendiente predicha por DEM): se guarda como contexto de zona. Solo se usa si la
        parcela no trae el dato, y siempre etiquetado como valor de zona (motor.completar_con_zona)."""
        variable = r.get("variable", "")
        zonas = [z for z in zonas_de_fila(r) if z != "piura_region"]
        c = self._cifra_desde_fila(r)
        if not zonas:
            self._anotar(ruta, fila_id, "", variable, IGNORADA, "dato de zona sin código de zona")
            return
        if not c.conocido:
            self._anotar(ruta, fila_id, "", variable, IGNORADA, "estado desconocido: no reemplaza ningún dato")
            return
        sub = (r.get("subzona") or "").strip()
        if sub:  # p. ej. sierra_piura con dos subzonas: se guarda la envolvente (no se elige una)
            c = c.con(notas=f"{c.notas} [subzona {sub}]")
        for z in zonas:
            actual = self.contexto_zona.get((destino, z))
            if actual is not None and actual.conocido and sub:
                c_env = actual.con(valor_min=min(actual.lo, c.lo), valor_max=max(actual.hi, c.hi),
                                   notas=f"{actual.notas}; envolvente con {sub}")
                self.contexto_zona[(destino, z)] = c_env
            elif _mejor_o_igual(c, actual):
                self.contexto_zona[(destino, z)] = c
        self._anotar(ruta, fila_id, "", variable, ACEPTADA,
                     f"contexto de zona {', '.join(zonas)}{' (' + sub + ')' if sub else ''}: {c.texto(2)} "
                     f"({c.tipo_evidencia}); solo si la parcela no trae el dato, etiquetado como valor de zona")

    # ---- Piura Agronomía (datos_agronomia/) ------------------------------------------------
    def _cargar_agronomia(self):
        d = self.dir_agronomia
        self._agro_parametros(d / "parametros_cultivo_v2_propuesta.csv")
        self._agro_salinidad(d / "umbrales_salinidad_propuesta.csv", defecto_clase=False)
        self._agro_salinidad(d / "umbrales_salinidad_defecto_clase.csv", defecto_clase=True)
        self._agro_cultivares_salinidad(d / "fichas_anuales.csv")
        self._agro_anegamiento(d / "fichas_anuales.csv")
        self._agro_nutrientes(d / "nutrientes_cultivo_propuesta.csv")
        self._agro_kc(d / "fao56_kc_propuesta.csv")
        from . import calendario_obs
        for (cultivo, zona), v in calendario_obs.cargar(self, d / calendario_obs.ARCHIVO).items():
            self.fichas[cultivo].calendario[zona] = v
        from .reglas import cargar_reglas
        self.reglas = cargar_reglas(self, d)
        self._agro_perennes(d / "perennes.csv")
        self._agro_contexto_regional(d / "recuperacion_suelo.csv")

    # perennes.csv: solo lo que el módulo de perennes usa (Kc analógico, inicio de problemas por ECe, años a la
    # primera producción). El resto de variables queda anotado como no usado.
    VARIABLES_PERENNES = ("kc", "ece_inicio_problemas", "anos_a_primera_produccion", "anos_a_primera_cosecha_observada",
                          "meses_a_primera_cosecha")

    def _agro_perennes(self, ruta: Path):
        if not ruta.exists():
            return
        import re as _re
        no_usadas = 0
        for i, r in enumerate(leer_csv(ruta), start=2):
            rid, variable = r.get("id") or f"línea {i}", r.get("variable", "")
            cultivo = _re.sub(r"\s*\(.*\)$", "", r.get("cultivo", "")).strip()
            if variable not in self.VARIABLES_PERENNES:
                no_usadas += 1
                continue
            problemas = validar_fila_contrato(r)
            if problemas:
                self._anotar(ruta, rid, cultivo, variable, RECHAZADA, "; ".join(problemas))
                continue
            f = self.fichas.get(cultivo)
            if f is None or f.modulo != "perenne":
                self._anotar(ruta, rid, cultivo, variable, IGNORADA, "cultivo fuera del catálogo de perennes del motor")
                continue
            c = self._cifra_desde_fila(r)
            if not c.conocido:
                self._anotar(ruta, rid, cultivo, variable, IGNORADA, "estado desconocido: no reemplaza ningún dato")
                continue
            ref = f"{rid} {r.get('variedad') or ''} {r.get('etapa') or ''}".strip()
            if variable == "kc":
                if r.get("tipo_evidencia") == "bibliografico" and "FAO-56" in r.get("fuente", ""):
                    self._anotar(ruta, rid, cultivo, variable, IGNORADA, "duplica FAO-56 Tabla 12, ya cargada del repo")
                    continue
                if f.kc is None:
                    self._anotar(ruta, rid, cultivo, variable, IGNORADA, "sin Kc base; un Kc de una etapa no basta "
                                 "para el agua anual")
                    continue
                kc = f.kc
                if kc.get("no_fao56") and "Paredes" in r.get("fuente", "") and "Paredes" in kc.get("fuente", ""):
                    self._anotar(ruta, rid, cultivo, variable, IGNORADA, "duplica Paredes et al. 2024, ya cargado de "
                                 "fao56_kc_propuesta.csv")
                    continue
                if (r.get("etapa") or "").strip().lower() in ("inicial", "final", "ini", "end"):
                    self._anotar(ruta, rid, cultivo, variable, IGNORADA, "Kc de etapa inicial/final: el agua anual de "
                                 "planta adulta usa solo el Kc medio")
                    continue
                antes = (kc["mid_lo"], kc["mid_hi"])
                kc.setdefault("contraste", []).append(f"{c.valor:g} ({ref}; {c.tipo_evidencia}; {r.get('lugar', '')})")
                if kc["mid_lo"] <= c.valor <= kc["mid_hi"]:
                    self._anotar(ruta, rid, cultivo, variable, ACEPTADA, f"Kc {c.valor:g} ({c.tipo_evidencia}) cae dentro "
                                 f"de la envolvente {antes[0]}–{antes[1]}: se conserva la envolvente y se cita como contraste")
                else:
                    kc["mid_lo"], kc["mid_hi"] = min(kc["mid_lo"], c.valor), max(kc["mid_hi"], c.valor)
                    kc["subtipo"] += f"; análogo {ref}"
                    self._anotar(ruta, rid, cultivo, variable, ACEPTADA, f"Kc {c.valor:g} ({c.tipo_evidencia}, "
                                 f"{r.get('lugar', '')}) fuera de {antes[0]}–{antes[1]}: amplía la envolvente del agua "
                                 f"anual a {kc['mid_lo']}–{kc['mid_hi']}")
            elif variable == "ece_inicio_problemas":
                s_ = f.salinidad
                if s_ is None:
                    self._anotar(ruta, rid, cultivo, variable, IGNORADA, "sin curva de salinidad donde anotarlo")
                    continue
                s_["notas"] = (f"{s_.get('notas', '')}; contraste {rid}: síntomas desde ECe ~{c.valor:g} dS/m "
                               f"({c.tipo_evidencia}, {r.get('fuente_primaria') or r.get('fuente', '')[:60]}); inicio de "
                               "síntomas, no umbral de rendimiento").strip("; ")
                self._anotar(ruta, rid, cultivo, variable, ACEPTADA, f"ECe {c.valor:g} dS/m de inicio de problemas "
                             f"({c.tipo_evidencia}): no cambia el umbral ECe 100 % = {s_.get('ECe_100')} "
                             f"({'defecto de clase' if s_.get('defecto_clase') else s_.get('tipo')}); se anota como contraste")
            else:
                if variable == "meses_a_primera_cosecha":
                    c = Cifra(c.valor / 12, None if c.lo is None else c.lo / 12, None if c.hi is None else c.hi / 12,
                              "años", c.fuente, c.tipo_evidencia, c.estado, c.url_o_doi, f"{c.notas} (meses ÷ 12)", variable)
                zonas = [z for z in zonas_de_fila(r) if z != "piura_region"] or [""]
                for z in zonas:
                    if _mejor_o_igual(c, f.primera_produccion.get(z)):
                        f.primera_produccion[z] = c
                self._anotar(ruta, rid, cultivo, variable, ACEPTADA, f"años a la primera producción {c.texto(2)} "
                             f"({c.tipo_evidencia}) para {', '.join(z or 'cualquier zona' for z in zonas)}")
        if no_usadas:
            self._anotar(ruta, f"{no_usadas} filas", "", "", IGNORADA, "variables de perennes que el motor no modela")

    CONTEXTO_REGIONAL = ("ece_clase_afectacion_dominante", "napa_freatica_sev_mediana", "ce_agua_subterranea")

    def _agro_contexto_regional(self, ruta: Path):
        """Cifras regionales de suelo/agua (FAO/UNALM 1990, ANA 2015): solo contexto en avisos, nunca dato de parcela."""
        if not ruta.exists():
            return
        for r in leer_csv(ruta):
            if r.get("variable") not in self.CONTEXTO_REGIONAL:
                continue
            rid = r.get("id", "")
            problemas = validar_fila_contrato(r)
            if es_hwsd(r):
                problemas.append("HWSD no se usa para ECe")
            if problemas:
                self._anotar(ruta, rid, "", r["variable"], RECHAZADA, "; ".join(problemas))
                continue
            c = self._cifra_desde_fila(r)
            for z in zonas_de_fila(r):
                self.contexto_regional.append((r["variable"], z, c))
            self._anotar(ruta, rid, "", r["variable"], ACEPTADA, f"contexto regional {r.get('zona')}: {c.texto(2)} "
                         f"({c.tipo_evidencia}); solo aviso, nunca reemplaza el dato de la parcela")

    def _agro_parametros(self, ruta: Path):
        if not ruta.exists():
            return
        filas = leer_csv(ruta)
        validas: dict[tuple[str, str], dict] = {}
        for r in filas:
            cultivo, par = r.get("crop", ""), r.get("parameter", "")
            problemas = validar_parametro(r) + validar_zona_columna(r)
            if problemas:
                self._anotar(ruta, r.get("parameter_key", "").split("|")[-1], cultivo, par, RECHAZADA, "; ".join(problemas))
            elif cultivo not in self.fichas:
                self._anotar(ruta, r.get("parameter_key", "").split("|")[-1], cultivo, par, IGNORADA, "cultivo fuera del catálogo")
            else:
                validas[(cultivo, par)] = r
        # coherencia entre filas: óptimo dentro del absoluto; favorable ≥ mínima apta
        pares = (("pH_suelo_optimo", "pH_suelo_absoluto_ecocrop"), ("temperatura_optima", "temperatura_adaptacion"))
        malas = set()
        for cultivo in {c for c, _ in validas}:
            for opt, abso in pares:
                o, a = validas.get((cultivo, opt)), validas.get((cultivo, abso))
                if o and a and not (num(a["min_value"]) <= num(o["min_value"]) <= num(o["max_value"]) <= num(a["max_value"])):
                    malas |= {(cultivo, opt, f"{opt} no está dentro de {abso}"), (cultivo, abso, f"{opt} no está dentro de {abso}")}
            dep, depr = validas.get((cultivo, "profundidad_suelo_favorable_minima")), validas.get((cultivo, "profundidad_suelo_apta_minima"))
            if dep and depr and num(dep["min_value"]) < num(depr["min_value"]):
                malas |= {(cultivo, "profundidad_suelo_favorable_minima", "DEP < DEPR"),
                          (cultivo, "profundidad_suelo_apta_minima", "DEP < DEPR")}
        for cultivo, par, motivo in malas:
            r = validas.pop((cultivo, par), None)
            if r:
                self._anotar(ruta, r["parameter_key"].split("|")[-1], cultivo, par, RECHAZADA, motivo)
        self._ecocrop = {}
        for (cultivo, par), r in validas.items():
            f = self.fichas[cultivo]
            lo, hi, url = num(r["min_value"]), num(r["max_value"]), r["source_url"]
            fuente = f"FAO EcoCrop vía Piura Agronomía ({r['geographic_scope']})"
            if par == "temperatura_umbral_estres_reproductivo":
                fuente = f"{r['geographic_scope']} vía Piura Agronomía ronda 7b, confianza 0.3"
                f.umbral_floracion = Umbral("tmax_floracion", lo, hi, "°C", False, fuente, url,
                                            etiqueta="umbral de estrés reproductivo en floración")
                self._anotar(ruta, r["parameter_key"].split("|")[-1], cultivo, par, ACEPTADA,
                             f"{lo}–{hi} {r['unit']} (bibliografico; se compara el inferior con la Tmáx media PISCOt "
                             "de los meses de floración, regla blanda)")
                continue
            self._ecocrop.setdefault(cultivo, {})[par] = (lo, hi, url, fuente, r.get("applicability_note", ""))
            if par == "temperatura_adaptacion":
                f.umbrales.append(Umbral("tmedia", lo, hi, "°C", True, fuente, url,
                                         etiqueta="rango absoluto EcoCrop (TMIN–TMAX)"))
                f.umbrales.append(Umbral("tmax", None, hi, "°C", False, fuente, url,
                                         etiqueta="límite absoluto EcoCrop TMAX"))
            elif par == "temperatura_optima":
                f.umbrales.append(Umbral("tmedia", lo, hi, "°C", False, fuente, url, nivel="nota",
                                         etiqueta="óptimo EcoCrop"))
            self._anotar(ruta, r["parameter_key"].split("|")[-1], cultivo, par, ACEPTADA,
                         f"{lo}–{hi} {r['unit']} (bibliografico, rango de especie)")

    def _armar_rampas(self):
        """pH y profundidad pasan de corte duro a rampa. EcoCrop (si se cargó) manda; si no, el rango del repo se
        vuelve el tramo apto y el límite absoluto queda desconocido."""
        eco = getattr(self, "_ecocrop", {})
        for cultivo, f in self.fichas.items():
            e = eco.get(cultivo, {})
            viejos_ph = [u for u in f.umbrales if u.variable == "ph"]
            viejos_prof = [u for u in f.umbrales if u.variable == "profundidad_m"]
            f.umbrales = [u for u in f.umbrales if u.variable not in ("ph", "profundidad_m")]
            opt, abso = e.get("pH_suelo_optimo"), e.get("pH_suelo_absoluto_ecocrop")
            if opt or abso:
                base = opt or abso
                f.rampas["ph"] = Rampa("ph", "pH", base[0], base[1], abso[0] if abso else None, abso[1] if abso else None,
                                       base[3], base[2], "bibliografico",
                                       "rango de especie EcoCrop (global, no de variedad ni de Piura)")
            elif viejos_ph:
                apto = next((u for u in viejos_ph if u.duro), viejos_ph[0])
                f.rampas["ph"] = Rampa("ph", "pH", apto.minimo, apto.maximo, None, None, apto.fuente, apto.url,
                                       apto.tipo_evidencia, "rango del repo; límite absoluto desconocido")
            dep, depr = e.get("profundidad_suelo_favorable_minima"), e.get("profundidad_suelo_apta_minima")
            if dep or depr:
                base = depr or dep
                f.rampas["profundidad_m"] = Rampa("profundidad_m", "m", (dep or depr)[0], None,
                                                  depr[0] if depr else None, None, base[3], base[2], "bibliografico",
                                                  "DEPR = mínima apta (descarta), DEP = favorable (avisa); EcoCrop")
            elif viejos_prof:
                duros = [u.minimo for u in viejos_prof if u.duro and u.minimo is not None]
                blandos = [u.minimo for u in viejos_prof if not u.duro and u.minimo is not None]
                abs_min = max(duros) if duros else None
                apto_min = max(blandos + duros) if (blandos or duros) else None
                u0 = viejos_prof[0]
                f.rampas["profundidad_m"] = Rampa("profundidad_m", "m", apto_min, None, abs_min, None, u0.fuente,
                                                  u0.url, u0.tipo_evidencia, "rango del repo")

    def _agro_salinidad(self, ruta: Path, defecto_clase: bool):
        if not ruta.exists():
            return
        for r in leer_csv(ruta):
            cultivo = r.get("cultivo", "")
            problemas = validar_salinidad(r) + validar_zona_columna(r)
            if defecto_clase and not (r.get("notas") or "").startswith("es_defecto_clase=true"):
                problemas.append("archivo de defectos de clase sin marca es_defecto_clase=true")
            if problemas:
                self._anotar(ruta, cultivo, cultivo, "ECe", RECHAZADA, "; ".join(problemas))
                continue
            f = self.fichas.get(cultivo)
            if f is None:
                self._anotar(ruta, cultivo, cultivo, "ECe", IGNORADA, "cultivo fuera del catálogo")
                continue
            actual = f.salinidad
            if actual is not None and (defecto_clase or TIPOS_EVIDENCIA.index(r["tipo_evidencia"]) > TIPOS_EVIDENCIA.index(actual["tipo"])):
                self._anotar(ruta, cultivo, cultivo, "ECe", IGNORADA, "ya hay umbral FAO-29 de mayor prioridad")
                continue
            s = {k: num(r[k]) for k in r if k.startswith(("ECe_", "ECw_"))}
            s.update(fuente=r["fuente"], url=r["url_o_doi"], estado=r["estado"], notas=r["notas"],
                     tipo=r["tipo_evidencia"], proxy=r.get("cultivo_fao29", ""), defecto_clase=defecto_clase)
            f.salinidad = s
            self._anotar(ruta, cultivo, cultivo, "ECe", ACEPTADA,
                         f"ECe 100 % = {s['ECe_100']} dS/m ({r['tipo_evidencia']})"
                         + ("; defecto de clase: menor confianza, nunca descarta" if defecto_clase else ""))

    def _agro_cultivares_salinidad(self, ruta: Path):
        """fichas_anuales.csv (ronda 7 de Agronomía): umbrales ECe por cultivar (filas ece_umbral con variedad) y la
        alternativa rotulada (notas con 'ALTERNATIVA ROTULADA'). Solo se agregan a un cultivo que ya tiene umbral
        principal; no lo reemplazan."""
        if not ruta.exists():
            return
        alternativas: dict[str, dict[str, float]] = {}
        for i, r in enumerate(leer_csv(ruta), start=2):
            var = r.get("variable", "")
            alternativa = "ALTERNATIVA ROTULADA" in (r.get("notas") or "")
            con_variedad = var == "ece_umbral" and (r.get("variedad") or "").strip()
            if not (con_variedad or (alternativa and var in ("ece_umbral", "pendiente_salinidad_b"))):
                continue
            cultivo = ALIAS_CULTIVO.get(r["cultivo"], r["cultivo"])
            fila_id = r.get("id") or f"línea {i}"
            problemas = validar_fila_contrato(r)
            if problemas:
                self._anotar(ruta, fila_id, cultivo, var, RECHAZADA, "; ".join(problemas))
                continue
            f = self.fichas.get(cultivo)
            if f is None or f.salinidad is None:
                self._anotar(ruta, fila_id, cultivo, var, IGNORADA, "cultivo sin umbral principal en el catálogo")
                continue
            if con_variedad:
                f.salinidad.setdefault("cultivares", {})[r["variedad"].strip()] = num(r["valor"])
                f.salinidad["cultivares_fuente"] = f"{r['fuente'][:90]} ({r['tipo_evidencia']}, {r['lugar']})"
                self._anotar(ruta, fila_id, cultivo, var, ACEPTADA, f"umbral ECe del cultivar {r['variedad']} = "
                             f"{r['valor']} dS/m: amplía el rango del umbral, no reemplaza el principal")
            else:
                alternativas.setdefault(cultivo, {})[var] = num(r["valor"])
                if var == "ece_umbral":  # la nota cita 'a/b/clase'; sirve si la fila de pendiente no pasa el contrato
                    import re
                    m = re.search(r"\b\d+(?:\.\d+)?/(\d+(?:\.\d+)?)/[A-Z]+\b", r.get("notas") or "")
                    if m:
                        alternativas[cultivo]["pendiente_en_nota"] = (num(m.group(1)), fila_id)
                self._anotar(ruta, fila_id, cultivo, var, ACEPTADA, "alternativa rotulada como estimación: solo en notas")
        for cultivo, alt in alternativas.items():
            g = lambda k: f"{alt[k]:g}" if alt.get(k) is not None else "desconocido"
            pend = f"{g('pendiente_salinidad_b')} %/dS/m"
            if alt.get("pendiente_salinidad_b") is None and alt.get("pendiente_en_nota"):
                b, fid = alt["pendiente_en_nota"]
                pend = f"{b:g} %/dS/m (citada en la nota de {fid}; la fila de pendiente no pasó el contrato)"
            self.fichas[cultivo].salinidad["alternativa"] = (
                f"alternativa {g('ece_umbral')} dS/m y {pend} "
                "(FAO-56 T23): estimación rotulada, no recomendada; probable corrimiento de fila de FAO-48 Tabla 13")

    def _agro_nutrientes(self, ruta: Path):
        if not ruta.exists():
            return
        for r in leer_csv(ruta):
            cultivo = r.get("crop", "")
            problemas = validar_nutriente(r) + validar_zona_columna(r)
            if problemas:
                self._anotar(ruta, cultivo, cultivo, r.get("measurement_type", ""), RECHAZADA, "; ".join(problemas))
                continue
            f = self.fichas.get(cultivo)
            if f is None:
                self._anotar(ruta, cultivo, cultivo, r["measurement_type"], IGNORADA, "cultivo fuera del catálogo")
                continue
            exp = r["measurement_type"].startswith("exportación")
            destino = f.exportacion if exp else f.absorcion
            nombre = "exportación" if exp else "absorción"
            ya = {n: c.valor for n, c in destino.items()}
            nuevos = {n: num(r[col]) for n, col in (("N", "N_kg_per_t"), ("P2O5", "P2O5_kg_per_t"), ("K2O", "K2O_kg_per_t"))}
            if ya and all(ya.get(n) == v for n, v in nuevos.items() if v is not None):
                self._anotar(ruta, cultivo, cultivo, nombre, ACEPTADA, "coincide con la cifra ya cargada del repo; se conserva")
                continue
            if ya:
                self._anotar(ruta, cultivo, cultivo, nombre, IGNORADA, f"ya hay {nombre} del repo (bibliografico)")
                continue
            for n, v in nuevos.items():
                if v is not None:
                    destino[n] = Cifra(v, None, None, f"kg {n}/t", r["source_table"], "analogo_externo", "estimado",
                                       r["source_url"], f"{r['main_product_or_part']}; región fuente: {r['source_region']}"
                                       f" ({r.get('source_year') or 'año no indicado'}); {r.get('note', '')}; sin calibrar "
                                       "en Piura; comparabilidad: misma especie y parte cosechada, otro clima/manejo",
                                       f"{n}_por_t")
            self._anotar(ruta, cultivo, cultivo, nombre, ACEPTADA,
                         f"N/P2O5/K2O {nuevos['N']}/{nuevos['P2O5']}/{nuevos['K2O']} kg/t (analogo_externo, {r['source_region']})")

    def _agro_kc(self, ruta: Path):
        if not ruta.exists():
            return
        for r in leer_csv(ruta):
            cultivo = r.get("crop", "")
            problemas = validar_kc(r) + validar_zona_columna(r)
            if problemas:
                self._anotar(ruta, cultivo, cultivo, "Kc", RECHAZADA, "; ".join(problemas))
                continue
            f = self.fichas.get(cultivo)
            if f is None:
                self._anotar(ruta, cultivo, cultivo, "Kc", IGNORADA, "cultivo fuera del catálogo")
                continue
            if f.kc is not None:
                self._anotar(ruta, cultivo, cultivo, "Kc", IGNORADA, "ya hay Kc de FAO-56 Tabla 12")
                continue
            f.kc = dict(ini=num(r["Kc_initial"]), mid_lo=num(r["Kc_mid_min"]), mid_hi=num(r["Kc_mid_max"]),
                        end_lo=num(r["Kc_end_min"]), end_hi=num(r["Kc_end_max"]), subtipo=r["fao_crop_subtype"],
                        fuente=r["source_table"], url=r["source_url"], no_fao56=True,
                        notas="Kc publicado por Paredes et al. 2024 con el método FAO-56; NO es un valor de la Tabla 12 de FAO-56")
            self._anotar(ruta, cultivo, cultivo, "Kc", ACEPTADA,
                         f"Kc media {r['Kc_mid_min']}–{r['Kc_mid_max']} (marcado: no es Kc de FAO-56 Tabla 12)")

    # ---- fichas por zona ---------------------------------------------------------------------
    def ficha(self, nombre: str, zona: str | None = None) -> Ficha:
        """Ficha con los datos específicos de la zona (si los hay) sobre los generales."""
        f = self.fichas[nombre]
        zonas = [zona] + [ag for ag, cubre in ZONAS_AGREGADAS.items() if zona in cubre] if zona else []
        if not any(z in zonas for _, z in f.por_zona):
            return f
        cambios = {}

        def de_zona(destino):
            return next((f.por_zona[(destino, z)] for z in zonas if (destino, z) in f.por_zona), None)
        c = de_zona("costo")
        if c is not None:
            cambios["costo"] = c
        for destino in ("rendimiento", "precio"):
            v = de_zona(destino)
            if v is not None and f"zona:{zona}" not in getattr(f, destino):
                cambios[destino] = {**getattr(f, destino), f"zona:{zona}": v}
        d = de_zona("duracion")
        if d is not None:
            cambios["duracion"] = d
            cambios["etapas"] = _reescalar_etapas(f.etapas, d.lo, d.hi)
        return replace(f, **cambios)

    @staticmethod
    def _cifra_desde_fila(r: dict) -> Cifra:
        v, lo, hi = num(r.get("valor")), num(r.get("valor_min")), num(r.get("valor_max"))
        nota_centro = ""
        if v is None and lo is not None and hi is not None and r.get("estado") != "desconocido":
            v, nota_centro = (lo + hi) / 2, "valor central = punto medio del rango (la fila solo traía mín-máx)"
        estado = r.get("estado") or ("desconocido" if v is None else "estimado")
        if estado == "desconocido" or v is None:
            return Cifra.desconocido(r.get("unidad", ""), r.get("variable", ""), r.get("notas", ""),
                                     r.get("fuente") or "sin dato")
        return Cifra(v, lo, hi, r.get("unidad", ""), r.get("fuente", ""), r.get("tipo_evidencia", "prediccion"),
                     estado, r.get("url_o_doi", ""), " ".join(x for x in (r.get("metodo", ""), r.get("notas", ""), nota_centro) if x),
                     r.get("variable", ""))

    def anuales(self) -> list[Ficha]:
        return [f for f in self.fichas.values() if f.modulo == "anual"]

    def perennes(self) -> list[Ficha]:
        return [f for f in self.fichas.values() if f.modulo == "perenne"]


def _reescalar_etapas(etapas: dict | None, lo: float, hi: float) -> dict | None:
    """Reescala proporcionalmente las etapas FAO-56 a un total de [lo, hi] días."""
    if not etapas:
        return etapas
    tot_lo = sum(v[0] for v in etapas.values())
    tot_hi = sum(v[1] for v in etapas.values())
    return {e: (v[0] * lo / tot_lo, v[1] * hi / tot_hi) for e, v in etapas.items()}


def _misma_prioridad(nueva: Cifra, actual: Cifra | None) -> bool:
    return (actual is not None and actual.conocido and nueva.conocido
            and TIPOS_EVIDENCIA.index(nueva.tipo_evidencia) == TIPOS_EVIDENCIA.index(actual.tipo_evidencia))


def _mejor_o_igual(nueva: Cifra, actual: Cifra | None) -> bool:
    if actual is None or not actual.conocido:
        return True
    if not nueva.conocido:
        return False
    return TIPOS_EVIDENCIA.index(nueva.tipo_evidencia) <= TIPOS_EVIDENCIA.index(actual.tipo_evidencia)
