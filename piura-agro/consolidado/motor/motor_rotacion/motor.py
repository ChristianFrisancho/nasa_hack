"""Puerta de entrada: evaluar(consulta) y comparar_secuencias(consulta)."""
from __future__ import annotations

import itertools
import math
import unicodedata
from dataclasses import dataclass, field, replace

from .agua import AguaCultivo, demanda_agua
from functools import lru_cache

from .catalogo import ESCENARIOS_ICEN, ESCENARIOS_NINO, DIR_REPO, Catalogo, Ficha, leer_csv
from .cifra import Cifra, operar, escalar
from .clima import ClimaEscenario, clima_escenario, con_lluvia_pisco
from .entradas import Consulta
from .validacion import ZONAS_PARCELA
from .estado_suelo import EstadoSuelo, actualizar_tras_cosecha
from .filtros import (ADVIERTE, DESCARTA, FILTROS_ANUALES, NO_EVALUABLE, Contexto, Veredicto, decision)
from .nutrientes import NUTRIENTES, Nutrientes, balance_nutrientes
from . import incertidumbre as inc
from .reglas import alerta_enfen_vigente

ZONA_POR_CLIMA = {"Bajo Piura": "bajo_piura", "Chira Sullana": "chira", "San Lorenzo": "san_lorenzo",
                  "Ayabaca": "sierra_piura", "Huancabamba": "sierra_piura"}


DISTRITO_ZONA = DIR_REPO / "distrito_zona.csv"  # copia de suelos/datos/distrito_zona.csv (Piura Territorio)
F_DISTRITO = "suelos/datos/distrito_zona.csv (Piura Territorio; sectores hidráulicos ANA y límites INEI)"


def _clave(texto: str) -> str:
    """Nombre comparable: sin tildes, mayúsculas y sin espacios ('Tambogrande' = 'TAMBO GRANDE')."""
    sin_tilde = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return sin_tilde.upper().replace(" ", "")


@lru_cache(maxsize=1)
def _distritos() -> dict[str, list[dict]]:
    filas: dict[str, list[dict]] = {}
    for r in leer_csv(DISTRITO_ZONA):
        filas.setdefault(_clave(r["distrito"]), []).append(r)
    return filas


def zona_de_distrito(distrito: str, provincia: str | None) -> tuple[str | None, str]:
    """Zona CONTRATO.md deducida del distrito. Devuelve (zona, origen). zona es None si el distrito no está, se
    repite en varias provincias sin provincia que lo desempate, o cae en piura_region (sin zona de parcela)."""
    filas = _distritos().get(_clave(distrito), [])
    if provincia:
        filas = [r for r in filas if _clave(r["provincia"]) == _clave(provincia)] or filas
    if not filas:
        return None, f"el distrito {distrito} no está en {F_DISTRITO}"
    if len(filas) > 1:
        return None, (f"el distrito {distrito} existe en varias provincias "
                      f"({', '.join(r['provincia'] for r in filas)}): indique parcela.provincia")
    r = filas[0]
    if r["zona"] not in ZONAS_PARCELA:
        return None, (f"el distrito {r['distrito']} ({r['provincia']}) está en {r['zona']} en {F_DISTRITO}, que no es "
                      "una zona de parcela")
    origen = f"deducida del distrito {r['distrito']} ({r['provincia']}), {F_DISTRITO}: {r['criterio']}"
    if r["ambiguo"] and r["ambiguo"] != "no":
        origen += f"; distrito ambiguo ({r['ambiguo']}); alternativa {r['zona_alternativa'] or 'no indicada'}"
    return r["zona"], origen


def zona_parcela(consulta: Consulta, clima: ClimaEscenario) -> tuple[str | None, str]:
    """Zona CONTRATO.md de la parcela, en este orden: la del usuario; la deducida del distrito; la inferida de la celda
    climática más cercana."""
    if consulta.zona:
        return consulta.zona, "dada por el usuario"
    previo = ""
    if consulta.distrito:
        z, origen = zona_de_distrito(consulta.distrito, consulta.provincia)
        if z:
            return z, origen
        previo = f"{origen}; "
    z = ZONA_POR_CLIMA.get(clima.zona.nombre)
    if z:
        return z, (f"{previo}inferida de la zona climática más cercana ({clima.zona.nombre}); Alto y Medio Piura no "
                   "tienen celda propia: si la parcela está allí, indique parcela.zona o parcela.distrito")
    return None, f"{previo}desconocida"


def lluvia_de_zona(clima: ClimaEscenario, cat: Catalogo, zona: str | None) -> tuple[ClimaEscenario, list[str]]:
    """Lluvia PISCOp de la zona y escenario ICEN; sin ella queda la lluvia POWER de la celda, con aviso."""
    lluvia = {m: cat.lluvia_pisco.get((zona, clima.escenario, m)) for m in range(1, 13)}
    if zona and all(lluvia.values()):
        return con_lluvia_pisco(clima, lluvia), []
    return clima, [f"Lluvia: no hay PISCOp para la zona {zona or 'desconocida'} en el escenario {clima.escenario}; se usa "
                   f"la lluvia NASA POWER de la celda {clima.zona.nombre} (reanálisis, menos fiable en la costa)"]


def alerta_fen(consulta: Consulta, cat: Catalogo) -> tuple[bool | None, str]:
    if consulta.alerta_enfen is not None:
        return bool(consulta.alerta_enfen), "indicada en la consulta"
    return alerta_enfen_vigente(cat.reglas)

_CATALOGO: Catalogo | None = None


def catalogo_por_defecto() -> Catalogo:
    global _CATALOGO
    if _CATALOGO is None:
        _CATALOGO = Catalogo()
    return _CATALOGO


@dataclass
class EvaluacionCultivo:
    cultivo: str
    familia: str
    modulo: str
    decision: str  # aceptado | descartado
    veredictos: list
    duracion: Cifra
    agua: AguaCultivo | None
    nutrientes: Nutrientes | None
    rendimiento: Cifra
    precio: Cifra
    costo_ha: Cifra
    margen_ha: Cifra
    deja_en_suelo: list
    faltantes: list
    estado_tras_cosecha: EstadoSuelo | None = None
    mes_siembra: int = 1
    margen_mc: dict | None = None  # p10, p50, p90, prob_negativo (incertidumbre.py)
    muestras_margen: object = None  # np.ndarray, para sumar en secuencias
    aptitud_suelo: float | None = None  # mínima aptitud garantizada (pH, profundidad); None = desconocida

    @property
    def n_alertas(self) -> int:
        return sum(v.resultado in (ADVIERTE, NO_EVALUABLE) for v in self.veredictos)

    @property
    def n_advierte(self) -> int:
        return sum(v.resultado == ADVIERTE for v in self.veredictos)

    @property
    def n_graves(self) -> int:
        return sum(v.grave for v in self.veredictos)

    def motivos_descarte(self) -> list[str]:
        return [f"{v.filtro}: {v.motivo}" for v in self.veredictos if v.resultado == DESCARTA]


@dataclass
class Resultado:
    consulta: Consulta
    clima: ClimaEscenario
    evaluaciones: list
    ranking: list  # nombres de cultivos aceptados, mejor primero
    perennes: list
    mensaje: str
    faltantes_globales: list = field(default_factory=list)
    zona: str | None = None
    zona_origen: str = ""
    avisos: list = field(default_factory=list)  # avisos globales (napa, arroz previo, ENFEN)

    def a_dict(self) -> dict:
        from .reporte import resultado_a_dict
        return resultado_a_dict(self)

    def a_texto(self) -> str:
        from .reporte import resultado_a_texto
        return resultado_a_texto(self)


def _meses_ciclo(mes_siembra: int, dur: Cifra) -> list[int]:
    n = math.ceil((dur.hi if dur.conocido else 365) / 30.4)
    return [(mes_siembra - 1 + i) % 12 + 1 for i in range(max(n, 1))]


def evaluar_cultivo(ficha: Ficha, consulta: Consulta, estado: EstadoSuelo, clima: ClimaEscenario, cat: Catalogo,
                    cultivo_anterior: str | None) -> EvaluacionCultivo:
    agua = demanda_agua(ficha, clima, consulta.mes_siembra, consulta.agua.eficiencia)
    if agua.disponible:
        dur = agua.duracion_dias.con(fuente=ficha.duracion.fuente if ficha.duracion else agua.duracion_dias.fuente,
                                     tipo_evidencia=ficha.duracion.tipo_evidencia if ficha.duracion else "prediccion")
    else:
        dur = ficha.duracion or Cifra.desconocido("días", "duración ciclo", f"duración de {ficha.cultivo} no está "
                                                  "en los datos")
    costo = ficha.costo or Cifra.desconocido("PEN/ha", "costo de producción", f"sin costo para {ficha.cultivo}")
    fam_ant = cat.fichas[cultivo_anterior].familia if cultivo_anterior in cat.fichas else None
    zona, _ = zona_parcela(consulta, clima)
    ficha = cat.ficha(ficha.cultivo, zona)
    alerta, _ = alerta_fen(consulta, cat)
    ctx = Contexto(ficha, consulta, estado, clima, agua, dur, _meses_ciclo(consulta.mes_siembra, dur), costo,
                   cat.reglas_sanidad, cat.reglas_terreno, cultivo_anterior, fam_ant, zona, cat.reglas, alerta,
                   {m: c for (z, m), c in cat.tmax_pisco.items() if z == zona},
                   cat.ausencias_calendario.get((ficha.cultivo, zona)) if zona else None)
    veredictos = [f(ctx) for f in FILTROS_ANUALES]
    dec = decision(veredictos)

    rend_base = ficha.por_lugar(ficha.rendimiento, consulta.provincia, "t/ha", "rendimiento", zona)
    precio = ficha.por_lugar(ficha.precio, consulta.provincia, "PEN/kg", "precio en chacra", zona)
    rend, factores = rend_base, []
    for v in veredictos:
        for clave in ("fraccion_rendimiento_salinidad", "fraccion_rendimiento_agua"):
            if clave in v.cifras:
                factores.append(v.cifras[clave])
            if clave in v.cifras and rend.conocido:
                rend = operar("*", rend, v.cifras[clave], "t/ha", "rendimiento esperado",
                              f"rendimiento DRAP × {clave.replace('_', ' ')}")
    if rend is not rend_base and rend.conocido:
        rend = rend.con(notas=f"base: {rend_base.texto(2)} ({rend_base.fuente}, {rend_base.tipo_evidencia}); "
                              + rend.notas)
    incorporar = consulta.incorporar_residuos
    if ficha.cultivo == "algodon" and "R4S001" in cat.reglas:
        incorporar = False  # RM 0251-94-AG Art. 12: el rastrojo de algodón no se incorpora
    nut = balance_nutrientes(ficha, rend, incorporar)
    ingreso = operar("*", escalar(rend, 1000, "kg/ha", "producción", "t→kg"), precio, "PEN/ha", "ingreso bruto",
                     "producción × precio en chacra")
    margen = operar("-", ingreso, costo, "PEN/ha", "margen", "ingreso − costo de producción")
    estado_post = actualizar_tras_cosecha(estado, ficha.cultivo, ficha.leguminosa, nut.exportacion,
                                          agua.riego_neto_m3_ha if agua.disponible else None, consulta.agua.ecw,
                                          consulta.fertilizacion_prevista, _efecto_arroz(ficha, estado, cat))
    deja = _deja_en_suelo(ficha, nut, estado_post, cat)
    faltantes = []
    for v in veredictos:
        faltantes += v.faltantes
    for nombre, c in (("rendimiento", rend_base), ("precio en chacra", precio), ("costo de producción", costo)):
        if not c.conocido:
            faltantes.append(f"{nombre} de {ficha.cultivo}")
    faltantes += [n for n in agua.notas if "desconocid" in n]
    clave = f"{ficha.cultivo}|{consulta.mes_siembra}|{cultivo_anterior}|{len(estado.historial)}"
    m = inc.muestras_margen(rend_base, factores, precio, costo, clave)
    apt = [v.cifras.get(k) for v in veredictos for k in ("aptitud_pH", "aptitud_profundidad") if k in v.cifras]
    aptitud = min((a.lo for a in apt if a.conocido), default=None) if apt and all(a.conocido for a in apt) else None
    return EvaluacionCultivo(ficha.cultivo, ficha.familia, ficha.modulo, dec, veredictos, dur, agua, nut, rend, precio,
                             costo, margen, deja, list(dict.fromkeys(faltantes)), estado_post, consulta.mes_siembra,
                             inc.resumen(m), m, aptitud)


def _efecto_arroz(ficha: Ficha, estado: EstadoSuelo, cat: Catalogo) -> str | None:
    if ficha.cultivo != "arroz" or "R4R001" not in cat.reglas:
        return None
    napa = estado.napa_m
    if estado.drenaje == "pobre" or (napa.conocido and napa.lo < 2.0):
        return "sube"
    if estado.drenaje == "bueno" and napa.conocido and napa.lo >= 2.0:
        return "lava" if "R4R002" in cat.reglas else None
    return "posible"


def _deja_en_suelo(ficha: Ficha, nut: Nutrientes, post: EstadoSuelo, cat: Catalogo) -> list:
    deja = []
    for n in NUTRIENTES:
        r = nut.residuo_devuelto[n]
        if ficha.cultivo == "algodon" and "R4S001" in cat.reglas:
            r = Cifra.desconocido("kg/ha", f"residuo {n}", "no se incorpora: RM 0251-94-AG Art. 12 prohíbe incorporar el "
                                  "rastrojo de algodón (R4S001)", fuente="Piura Agronomía R4S001")
        deja.append(("residuo " + n, r))
    if ficha.leguminosa:
        deja.append(("nota", "leguminosa: posible aporte de N por fijación, cantidad desconocida; no reemplaza N mineral"))
    agentes = [r["agente"] for r in cat.reglas_sanidad
               if ficha.cultivo in r["cultivos_afectados"].split(";") and r["agente"] not in ("mismo_cultivo",
                                                                                          "misma_familia")]
    if agentes:
        deja.append(("nota", f"puede dejar inóculo/plaga para hospedantes: {', '.join(agentes)}"))
    deja.append(("ECe tras cosecha", post.ece))
    for n in ("P2O5", "K2O"):
        deja.append((f"balance {n} acumulado", post.balance[n]))
    return deja


def _clave_ranking(e: EvaluacionCultivo, fam_ant: str | None):
    """Primero sin 'probable no apto', luego sin pérdida casi segura (P90 < 0); menos alertas; luego margen conservador (P10 de Monte Carlo, redondeado a 100 PEN), aptitud de suelo
    y agua. El punto medio del intervalo ya no se usa: favorecía rangos muy anchos."""
    riego = e.agua.riego_neto_m3_ha.hi if (e.agua and e.agua.disponible) else float("inf")
    p10 = e.margen_mc["p10"] if e.margen_mc else None
    # pérdida casi segura (P90 del margen < 0): detrás de los que pueden ganar, aunque tengan menos alertas
    pierde = bool(e.margen_mc) and e.margen_mc["p90"] < 0
    return (e.n_graves, pierde, e.n_alertas, e.n_advierte, e.familia == fam_ant, 0 if p10 is not None else 1,
            -round(p10 / 100) if p10 is not None else 0, -(e.aptitud_suelo if e.aptitud_suelo is not None else 0),
            riego)


def _contexto(cat: Catalogo, variable: str, zona: str | None) -> Cifra | None:
    """Cifra de zona (catalogo.contexto_zona) para la zona exacta o una agregada que la contiene."""
    from .validacion import ZONAS_AGREGADAS
    if not zona:
        return None
    if (variable, zona) in cat.contexto_zona:
        return cat.contexto_zona[(variable, zona)]
    for ag, partes in ZONAS_AGREGADAS.items():
        if zona in partes and (variable, ag) in cat.contexto_zona:
            return cat.contexto_zona[(variable, ag)]
    return None


def completar_con_zona(consulta: Consulta, cat: Catalogo, clima: ClimaEscenario) -> tuple[Consulta, list[str]]:
    """Si la parcela no trae ECw o pendiente, usa el valor de su zona (si existe) como RANGO etiquetado 'valor de
    zona'. Nunca se usa si la parcela trae su propio dato. Devuelve la consulta completada y los avisos."""
    zona, _ = zona_parcela(consulta, clima)
    avisos, agua, suelo = [], consulta.agua, consulta.suelo
    ecw_z = _contexto(cat, "ecw", zona)
    if not agua.ecw.conocido and ecw_z is not None:
        c = ecw_z.con(notas=f"VALOR DE ZONA {zona}, no de su parcela: {ecw_z.notas}".strip(), variable="ECw (zona)")
        agua = replace(agua, ecw=c)
        avisos.append(f"ECw de la parcela desconocida: se usa el valor de zona {zona} {c.texto(2)} "
                      f"[{c.tipo_evidencia}, {c.fuente[:70]}…]. Es {_tipo_agua(ecw_z.notas)} medida en un punto, no "
                      "en su toma: mida la CE de su agua de riego")
    p50, p90 = _contexto(cat, "pendiente_p50", zona), _contexto(cat, "pendiente_p90", zona)
    if (suelo.pendiente_pct is None or not suelo.pendiente_pct.conocido) and p50 is not None and p90 is not None:
        c = Cifra(p50.valor, 0.0, p90.hi, "%", f"{p50.fuente} (Piura Territorio vía Piura Datos)", "prediccion",
                  "estimado", p50.url_o_doi, f"VALOR DE ZONA {zona}, no de su parcela: mediana {p50.texto(1)}; 90 % "
                  f"del área cultivada de la zona ≤ {p90.texto(1)} (DEM 30 m, no sirve para nivelación); su parcela "
                  "puede estar fuera del rango", "pendiente (zona)")
        suelo = replace(suelo, pendiente_pct=c)
        avisos.append(f"Pendiente de la parcela desconocida: se usa la de la zona {zona} (predicción DEM 30 m) "
                      f"0–{p90.hi:g} % (mediana {p50.texto(1)}); mida la pendiente de su parcela")
    return replace(consulta, agua=agua, suelo=suelo), avisos


def _tipo_agua(notas: str) -> str:
    """'[agua de reservorio; estiaje]' en las notas de la ECw de zona -> 'agua de reservorio, estiaje'."""
    import re
    m = re.search(r"\[agua de ([^;\]]+); ([^\]]+)\]", notas or "")
    return f"agua de {m.group(1)}, {m.group(2)}" if m else "agua de fuente no declarada"


def avisos_agua(cat: Catalogo, zona: str | None) -> list[str]:
    """Puntos de río o quebrada y pozos de la zona: rango y estación, solo como aviso."""
    from .validacion import ZONAS_AGREGADAS
    if not zona:
        return []
    out = []
    for tipo in ("punto", "pozo"):
        ps = [p for p in cat.contexto_agua if p.tipo == tipo and (p.zona == zona or zona in ZONAS_AGREGADAS.get(p.zona, ()))]
        if not ps:
            continue
        lo, hi = min(p.cifra.lo for p in ps), max(p.cifra.hi for p in ps)
        estaciones = ", ".join(sorted({p.estacion for p in ps}))
        if tipo == "punto":
            n_ana = sum(1 for p in ps if "ANA" in (p.cifra.fuente or ""))
            est = [p for p in ps if "ANA" in (p.cifra.fuente or "") and p.cifra.estado == "estimado"]
            est_txt = ("; de ellos estimados por balance iónico o sólidos disueltos (la unidad impresa del informe no "
                       "cierra): " + ", ".join(f"{p.punto} {p.cifra.texto(2)}" for p in est)) if est else ""
            out.append(f"Agua de río o quebrada en {zona}: {len(ps)} puntos ({n_ana} puntos ANA 2024) con CE {lo:g}–{hi:g} "
                       f"dS/m ({estaciones}{est_txt}). No es el agua que llega a su parcela; por eso siguen los "
                       "escenarios de ECw")
        else:
            out.append(f"Agua de pozo en {zona}: {len(ps)} lectura(s) de tesis con CE {lo:g}–{hi:g} dS/m ({estaciones}; "
                       f"{', '.join(sorted({p.punto for p in ps}))}). Solo cuenta si riega con pozo")
    return out


def avisos_contexto_regional(consulta: Consulta, cat: Catalogo, zona: str | None) -> list[str]:
    """Cifras regionales (FAO/UNALM 1990, ANA 2015) solo como contexto cuando falta el dato de la parcela."""
    from .validacion import ZONAS_AGREGADAS
    falta = {"ece_clase_afectacion_dominante": not consulta.suelo.ece.conocido
             or "no_declarado" in (consulta.suelo.ce_metodo or ""),
             "napa_freatica_sev_mediana": consulta.suelo.napa_m is None or not consulta.suelo.napa_m.conocido,
             "ce_agua_subterranea": not consulta.agua.ecw.conocido}
    texto = {"ece_clase_afectacion_dominante": "ECe de la clase de afectación dominante (escenario de clase, no ECe "
                                               "de parcela)",
             "napa_freatica_sev_mediana": "napa freática por SEV (mediana y rango; no es la napa de su parcela)",
             "ce_agua_subterranea": "CE del agua subterránea (solo si riega con pozo)"}
    out = avisos_agua(cat, zona) if falta["ce_agua_subterranea"] else []
    for var, z, c in cat.contexto_regional:
        if zona and (z == zona or zona in ZONAS_AGREGADAS.get(z, ())) and falta.get(var):
            out.append(f"Contexto regional {z}: {texto[var]} {c.texto(2)} [{c.tipo_evidencia}, "
                       f"{(c.fuente or '')[:60]}]; no reemplaza el dato de su parcela")
    return out


def evaluar(consulta: Consulta, catalogo: Catalogo | None = None, estado: EstadoSuelo | None = None) -> Resultado:
    from .perennes import evaluar_perenne
    cat = catalogo or catalogo_por_defecto()
    clima = clima_escenario(consulta.lat, consulta.lon, consulta.escenario, cat.anios_icen.get(consulta.escenario),
                            cat.dir_repo, cat.dir_motor)
    clima, aviso_lluvia = lluvia_de_zona(clima, cat, zona_parcela(consulta, clima)[0])
    consulta_original = consulta
    consulta, avisos_zona = completar_con_zona(consulta, cat, clima)
    avisos_zona = aviso_lluvia + avisos_zona
    estado = estado or EstadoSuelo.desde_consulta(consulta)
    nombres = consulta.candidatos or list(cat.fichas)
    desconocidos = [n for n in nombres if n not in cat.fichas]
    if desconocidos:
        raise ValueError(f"cultivos no catalogados: {desconocidos}")
    anuales = [cat.fichas[n] for n in nombres if cat.fichas[n].modulo == "anual"]
    perennes = [cat.fichas[n] for n in nombres if cat.fichas[n].modulo == "perenne"]
    evals = [evaluar_cultivo(f, consulta, estado, clima, cat, consulta.cultivo_anterior) for f in anuales]
    fam_ant = cat.fichas[consulta.cultivo_anterior].familia if consulta.cultivo_anterior in cat.fichas else None
    aceptados = sorted((e for e in evals if e.decision == "aceptado"), key=lambda e: _clave_ranking(e, fam_ant))
    pers = [evaluar_perenne(f, consulta, estado, clima, cat) for f in perennes]
    pers.sort(key=lambda e: (e.decision != "aceptado", e.n_alertas))
    sin_datos = [e.cultivo for e in evals if e.decision == "sin_datos"]
    if aceptados:
        mensaje = (f"{len(aceptados)} de {len(evals)} cultivos anuales pasan los filtros duros. "
                   f"Primero en el orden: {aceptados[0].cultivo}.")
    else:
        mensaje = _mensaje_ninguno(evals) if evals else "No se evaluaron cultivos anuales."
    graves = [e.cultivo for e in aceptados if e.n_graves]
    if graves:
        mensaje += (f" {len(graves)} de los aceptados son PROBABLEMENTE NO APTOS (no se descartan porque el umbral no "
                    f"se puede aplicar como exacto; van al final del orden): {', '.join(graves)}.")
    if sin_datos:
        mensaje += (f" Sin datos suficientes para decidir (no se recomiendan): {', '.join(sin_datos)}.")
    analogos = []
    for e in evals + pers:
        costo = getattr(e, "costo_ha", None) or getattr(e, "costo_anual_ha", None)
        if costo is not None and costo.conocido and costo.tipo_evidencia == "analogo_externo":
            e.faltantes.append(f"costo local de {e.cultivo} en Piura (se usó un costo análogo externo "
                               f"{costo.texto(0)}: incertidumbre del margen ampliada)")
            analogos.append(e.cultivo)
    globales = _agrupar_faltantes(evals + pers)
    zona, zona_origen = zona_parcela(consulta, clima)
    avisos = avisos_zona + _avisos_globales(consulta, estado, cat) + avisos_contexto_regional(consulta_original, cat, zona)
    if analogos:
        avisos.append("Costo análogo externo (otra región o especie) en: " + ", ".join(analogos) + ". Su rango se "
                      "amplió a ×1/2–×2 (supuesto del motor) y el margen es más incierto; no es costo de Piura")
    return Resultado(consulta, clima, evals, [e.cultivo for e in aceptados], pers, mensaje, globales, zona,
                     zona_origen, avisos)


@dataclass
class EscenariosClima:
    """La misma parcela evaluada en los tres escenarios climáticos ICEN."""
    resultados: dict  # escenario ICEN -> Resultado, en el orden de ESCENARIOS_ICEN
    contexto_icen: str = ""

    @property
    def primeros(self) -> dict:
        return {esc: (r.ranking[0] if r.ranking else None) for esc, r in self.resultados.items()}

    @property
    def primer_lugar_cambia(self) -> bool:
        return len(set(self.primeros.values())) > 1


def evaluar_escenarios(consulta: Consulta, catalogo: Catalogo | None = None) -> EscenariosClima:
    cat = catalogo or catalogo_por_defecto()
    return EscenariosClima({esc: evaluar(replace(consulta, escenario=esc), cat) for esc in ESCENARIOS_ICEN},
                           cat.contexto_icen)


def _avisos_globales(consulta: Consulta, estado: EstadoSuelo, cat: Catalogo) -> list[str]:
    from .filtros import condicion_napa
    avisos = []
    napa_ok, napa_txt = condicion_napa(estado)
    if not napa_ok:
        avisos.append(f"{napa_txt}: los umbrales de salinidad FAO-29 no se aplican como exactos (exigen ECe medida y "
                      "napa ≥ 2 m, R4A026); se avisa y se amplía la incertidumbre en vez de descartar")
    if consulta.cultivo_anterior == "arroz" and "R4R001" in cat.reglas:
        if estado.drenaje == "bueno" and estado.napa_m.conocido and estado.napa_m.lo >= 2.0:
            avisos.append("cultivo anterior arroz con drenaje bueno y napa ≥ 2 m: pudo lavar sales (R4R002)")
        else:
            avisos.append(f"cultivo anterior arroz con drenaje {estado.drenaje or 'desconocido'} y {napa_txt}: la ECe "
                          "pudo subir tras la campaña (R4R001); si la ECe no se midió después del arroz, medirla")
    alerta, txt = alerta_fen(consulta, cat)
    if cat.contexto_icen:
        avisos.append(f"Contexto ICEN (aviso, no regla): {cat.contexto_icen} [fuente: notas del escenario "
                      "el_nino_fuerte_extraordinario en lluvia_zona_pisco.csv de Piura Datos]")
    if alerta and consulta.escenario not in ESCENARIOS_NINO:
        avisos.append(f"[R4A025] {txt}. El escenario elegido es '{consulta.escenario}': compare con "
                      "'el_nino_fuerte_extraordinario' (ESCENARIOS CLIMÁTICOS). El riesgo de inundación ene-abr "
                      "(R4R003) sí se aplica a parcelas inundables.")
    elif alerta is None and "R4A025" in cat.reglas:
        avisos.append(f"[R4A025] {txt}")
    return avisos


def _agrupar_faltantes(evals: list) -> list[str]:
    """Agrupa faltantes iguales salvo el nombre del cultivo: 'umbral de pH de <cultivo> (12: arroz, ...)'."""
    grupos: dict[str, list[str]] = {}
    for e in evals:
        for f in dict.fromkeys(e.faltantes):
            clave = f.replace(e.cultivo, "<cultivo>")
            grupos.setdefault(clave, [])
            if e.cultivo not in grupos[clave]:
                grupos[clave].append(e.cultivo)
    orden = sorted(grupos, key=lambda k: (-len(grupos[k]), k))
    out = []
    for k in orden:
        cs = grupos[k]
        if "<cultivo>" in k:
            muestra = ", ".join(cs[:4]) + ("…" if len(cs) > 4 else "")
            out.append(f"{k} ({len(cs)} cultivos: {muestra})")
        else:
            out.append(f"{k} (afecta a {len(cs)} cultivos)")
    return out


def _mensaje_ninguno(evals: list) -> str:
    por_filtro: dict[str, list[str]] = {}
    for e in evals:
        for v in e.veredictos:
            if v.resultado == DESCARTA:
                por_filtro.setdefault(v.filtro, []).append(e.cultivo)
    partes = [f"{f} descarta {len(c)} ({', '.join(c[:5])}{'…' if len(c) > 5 else ''})" for f, c in
              sorted(por_filtro.items(), key=lambda x: -len(x[1]))]
    return ("Ningún cultivo anual evaluado es viable con estos datos. Restricciones a resolver: "
            + "; ".join(partes) + ".")


# ------------------------------------------------------------------------------------------- secuencias
@dataclass
class PasoSecuencia:
    cultivo: str
    mes_siembra: int
    evaluacion: EvaluacionCultivo


@dataclass
class Secuencia:
    cultivos: tuple
    viable: bool
    pasos: list
    estado_final: EstadoSuelo
    meses_usados: Cifra
    cabe_en_horizonte: str  # si | no | quizas | desconocido
    margen_total_ha: Cifra
    agua_neta_total_m3_ha: Cifra
    alertas: int
    motivo: str = ""
    graves: int = 0
    margen_mc: dict | None = None  # p10, p50, p90, prob_negativo de la suma de márgenes


def clave_secuencia(s: Secuencia):
    """Orden robusto de secuencias (motor v1).

    1) viables y que caben en el horizonte, sin pasos 'probable no apto'; 2) mayor P10 del margen total (Monte Carlo; redondeado a 100 PEN para
    que diferencias de ruido no decidan); 3) desempate: menos agua neta (cota alta), menor ECe final (cota alta),
    mejor balance P2O5+K2O (cota baja); 4) menos alertas. El punto medio del intervalo no interviene."""
    inf = float("inf")
    p10 = s.margen_mc["p10"] if s.margen_mc else None
    agua = s.agua_neta_total_m3_ha.hi if s.agua_neta_total_m3_ha.conocido else inf
    ece = s.estado_final.ece.hi if s.estado_final.ece.conocido else inf
    bal = [s.estado_final.balance[n] for n in ("P2O5", "K2O")]
    salud = -(sum(b.lo for b in bal)) if all(b.conocido for b in bal) else inf
    return (not s.viable, s.cabe_en_horizonte != "si", s.graves, p10 is None, -round(p10 / 100) if p10 is not None else 0,
            agua, ece, salud, s.alertas)


def clave_secuencia_v0(s: Secuencia):
    """Orden de v0 (punto medio del margen). Se conserva solo para el test de regresión y la comparación."""
    return (not s.viable, s.cabe_en_horizonte != "si", not s.margen_total_ha.conocido, s.alertas,
            -(s.margen_total_ha.valor if s.margen_total_ha.conocido else 0))


def ordenar_secuencias(secuencias: list) -> list:
    return sorted(secuencias, key=clave_secuencia)


def comparar_secuencias(consulta: Consulta, largo: int = 2, max_candidatos: int = 6,
                        catalogo: Catalogo | None = None, horizonte_meses: int | None = None) -> list[Secuencia]:
    """Compara secuencias de `largo` cultivos anuales distintos tomados de los mejores aceptados.

    Cada paso se reevalúa con el estado de suelo actualizado tras la cosecha anterior, el cultivo previo real y el
    mes de siembra siguiente a la cosecha (duración máxima). El horizonte total es `horizonte_meses`
    (por defecto 12 × largo / 2, mínimo el horizonte de la consulta).
    """
    if largo not in (2, 3):
        raise ValueError("largo debe ser 2 o 3")
    cat = catalogo or catalogo_por_defecto()
    base = evaluar(consulta, cat)
    consulta = base.consulta  # completada con valores de zona (ECw, pendiente) si la parcela no los trae
    candidatos = base.ranking[:max_candidatos]
    horiz = horizonte_meses or max(consulta.horizonte_meses, 6 * largo)
    clima = base.clima
    out = []
    for combo in itertools.permutations(candidatos, largo):
        estado = EstadoSuelo.desde_consulta(consulta)
        anterior, mes, pasos = consulta.cultivo_anterior, consulta.mes_siembra, []
        meses_lo = meses_hi = 0.0
        viable, motivo = True, ""
        margen = Cifra(0.0, None, None, "PEN/ha", "motor v1", "prediccion", "estimado", variable="margen secuencia")
        suma_mc = 0.0
        for cultivo in combo:
            restante = max(1, int(horiz - meses_hi))
            c_paso = replace(consulta, mes_siembra=mes, cultivo_anterior=anterior, horizonte_meses=restante)
            ev = evaluar_cultivo(cat.fichas[cultivo], c_paso, estado, clima, cat, anterior)
            pasos.append(PasoSecuencia(cultivo, mes, ev))
            if ev.decision != "aceptado":
                razones = ev.motivos_descarte() or [
                    "datos insuficientes en filtros críticos: " + "; ".join(
                        f"{v.filtro}: {v.motivo}" for v in ev.veredictos if v.resultado == NO_EVALUABLE)]
                viable, motivo = False, f"{cultivo} (siembra mes {mes}): " + "; ".join(razones)
                break
            estado = ev.estado_tras_cosecha
            margen = operar("+", margen, ev.margen_ha, "PEN/ha", "margen secuencia", "suma de márgenes")
            suma_mc = None if (suma_mc is None or ev.muestras_margen is None) else suma_mc + ev.muestras_margen
            d = ev.duracion
            if not d.conocido:
                meses_lo = meses_hi = float("nan")
                break
            meses_lo += d.lo / 30.4
            meses_hi += d.hi / 30.4
            mes = (mes - 1 + math.ceil(d.hi / 30.4)) % 12 + 1
            anterior = cultivo
        if math.isnan(meses_hi):
            usados, cabe = Cifra.desconocido("meses", "meses usados"), "desconocido"
        else:
            usados = Cifra.rango(meses_lo, meses_hi, "meses", "motor v1: suma de duraciones", variable="meses usados")
            cabe = "si" if meses_hi <= horiz else ("no" if meses_lo > horiz else "quizas")
        if cabe == "no" and viable:
            viable, motivo = False, f"la secuencia usa {usados.texto(1)} > horizonte {horiz} meses"
        mc = inc.resumen(suma_mc) if (viable and isinstance(suma_mc, inc.np.ndarray)) else None
        out.append(Secuencia(combo, viable, pasos, estado, usados, cabe, margen, estado.agua_neta_m3_ha,
                             sum(p.evaluacion.n_alertas for p in pasos), motivo,
                             sum(p.evaluacion.n_graves for p in pasos), mc))
    return ordenar_secuencias(out)


# ------------------------------------------------------------------ escenarios de agua cuando falta la ECw
ESCENARIOS_ECW = (0.5, 1.5, 3.0)  # supuesto del motor, dS/m: agua buena, media y salina (FAO-29: sin/ligera-moderada/severa restricción)
FUENTE_ESCENARIO = "ESCENARIO del motor (no es dato): FAO-29 clases de restricción por ECw <0.7, 0.7–3.0, >3.0 dS/m"


@dataclass
class EscenarioAgua:
    ecw: float
    etiqueta: str
    resultado: Resultado
    secuencias: list


def ecw_parcela_desconocida(consulta: Consulta) -> bool:
    return not consulta.agua.ecw.conocido


def escenarios_ecw(consulta: Consulta, catalogo: Catalogo | None = None, largo: int = 2, max_candidatos: int = 6,
                   valores=ESCENARIOS_ECW) -> list[EscenarioAgua]:
    """Si la parcela no trae ECw, corre evaluar + comparar_secuencias con tres ECw explícitas, etiquetadas como
    ESCENARIO. Si la parcela trae ECw, devuelve [] (se usa la suya). Un valor de zona no cuenta como dato de parcela."""
    if not ecw_parcela_desconocida(consulta):
        return []
    cat = catalogo or catalogo_por_defecto()
    out = []
    for v in valores:
        etiqueta = f"ESCENARIO ECw {v:g} dS/m"
        c = Cifra(v, None, None, "dS/m", FUENTE_ESCENARIO, "prediccion", "estimado",
                  notas=f"{etiqueta}: no es dato; falta la CE del agua de riego (ECw) de la parcela", variable="ECw")
        cv = replace(consulta, agua=replace(consulta.agua, ecw=c))
        out.append(EscenarioAgua(v, etiqueta, evaluar(cv, cat), comparar_secuencias(cv, largo, max_candidatos, cat)))
    return out
