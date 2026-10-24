"""Filtros duros. Cada filtro es una función pura Contexto -> Veredicto; el orden vive en una sola tupla.

Todos los filtros se ejecutan aunque uno descarte, para que el usuario vea todas las razones.
Resultados: pasa | advierte | descarta | no_evaluable (falta un dato: se reporta, no se inventa).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .agua import AguaCultivo
from .catalogo import ESCENARIOS_NINO, Ficha
from .cifra import Cifra
from .clima import ClimaEscenario
from .entradas import Consulta
from .estado_suelo import EstadoSuelo

PASA, ADVIERTE, DESCARTA, NO_EVALUABLE = "pasa", "advierte", "descarta", "no_evaluable"


@dataclass
class Veredicto:
    filtro: str
    resultado: str
    motivo: str
    fuente: str = ""
    tipo_evidencia: str = ""
    cifras: dict = field(default_factory=dict)
    faltantes: list = field(default_factory=list)
    grave: bool = False  # 'probable no apto': no descarta (umbral no exacto) pero manda el cultivo al final del orden

    def a_dict(self) -> dict:
        return {"filtro": self.filtro, "resultado": self.resultado, "motivo": self.motivo, "fuente": self.fuente,
                "tipo_evidencia": self.tipo_evidencia, "cifras": {k: v.a_dict() for k, v in self.cifras.items()},
                "faltantes": self.faltantes, "probable_no_apto": self.grave}


@dataclass
class Contexto:
    ficha: Ficha
    consulta: Consulta
    estado: EstadoSuelo
    clima: ClimaEscenario
    agua: AguaCultivo | None
    duracion: Cifra
    meses_ciclo: list  # meses calendario cubiertos por la duración máxima
    costo: Cifra
    reglas_sanidad: list
    reglas_terreno: list
    cultivo_anterior: str | None = None
    familia_anterior: str | None = None
    zona: str | None = None  # zona CONTRATO.md de la parcela (dada o inferida)
    reglas: dict = field(default_factory=dict)  # reglas de Piura Agronomía aceptadas (id -> fila)
    alerta_fen: bool | None = None  # alerta ENFEN de Niño costero vigente (None = no se sabe)
    tmax_media: dict = field(default_factory=dict)  # mes -> Cifra de la media de las máximas diarias (PISCOt, zona)
    ausencia_calendario: tuple | None = None  # (periodo, url, confianza) si la DRAP registra 0 ha en la zona


def _aplica(aplica_a: str, ficha: Ficha) -> bool:
    if aplica_a in ("anual", "perenne"):
        return ficha.modulo == aplica_a
    if aplica_a.startswith("*"):
        excluidos = aplica_a[1:].lstrip("-").split(";") if "-" in aplica_a else []
        return ficha.cultivo not in excluidos
    return ficha.cultivo in aplica_a.split(";")


# ---------------------------------------------------------------------------------------- salinidad
PUNTOS = (100, 90, 75, 50, 0)


def fraccion_rendimiento(ece: float, s: dict) -> float:
    """Interpolación lineal (Maas-Hoffman por tramos) entre los puntos FAO-29 de 100/90/75/50/0 %."""
    xs = [s[f"ECe_{p}"] for p in PUNTOS]
    if ece <= xs[0]:
        return 1.0
    if ece >= xs[-1]:
        return 0.0
    for (x0, p0), (x1, p1) in zip(zip(xs, PUNTOS), zip(xs[1:], PUNTOS[1:])):
        if x0 <= ece <= x1:
            return (p0 + (p1 - p0) * (ece - x0) / (x1 - x0)) / 100
    return 0.0


CLASES_FAO29 = (1.0, 0.9, 0.75, 0.5, 0.0)
NAPA_MIN_M = 2.0  # FAO-29 cap. 2 (R4A026): ECe ≈ 1.5·ECw y los umbrales valen con napa ≥ 2 m


def _bajar_un_tramo(f: float) -> float:
    """Amplía la cota inferior del rendimiento relativo un tramo de la tabla FAO-29 (1 → 0.9 → 0.75 → 0.5 → 0)."""
    menores = [c for c in CLASES_FAO29 if c < f - 1e-9]
    return max(menores) if menores else 0.0


def condicion_napa(estado: EstadoSuelo) -> tuple[bool, str]:
    """(napa ≥ 2 m comprobada, texto)."""
    napa = estado.napa_m
    if not napa.conocido:
        return False, "napa freática desconocida"
    if napa.lo >= NAPA_MIN_M:
        return True, f"napa {napa.texto(1)} (≥ {NAPA_MIN_M:g} m)"
    return False, f"napa {napa.texto(1)} (< {NAPA_MIN_M:g} m o puede serlo)"


def f_salinidad(ctx: Contexto) -> Veredicto:
    """Salinidad FAO-29 + aviso de sodicidad si se informó PSI (FAO-29 no modela el sodio)."""
    v = _f_salinidad_fao29(ctx)
    psi = ctx.consulta.suelo.psi_pct
    if psi is not None and psi.conocido and psi.hi >= 15 and ctx.estado.ece is ctx.consulta.suelo.ece:
        v.motivo += (f"; PSI {psi.texto(1)} {'supera' if psi.lo >= 15 else 'puede superar'} 15 % (límite de suelo "
                     "sódico, USDA Handbook 60): riesgo de sodicidad y mala estructura no incluido en el rendimiento")
        if v.resultado == PASA:
            v.resultado = ADVIERTE
    return v


def _f_salinidad_fao29(ctx: Contexto) -> Veredicto:
    """Salinidad FAO-29 con la condición de napa (R4A026).

    Los umbrales de ECe se aplican como exactos solo con ECe medida en la parcela y napa ≥ 2 m. Si la napa es
    más somera o desconocida, o la ECe no es medida, o el umbral es un defecto de clase, el filtro nunca descarta:
    avisa y amplía un tramo la cota inferior del rendimiento relativo (supuesto del motor, no calibrado)."""
    s = ctx.ficha.salinidad
    ece, ecw = ctx.estado.ece, ctx.consulta.agua.ecw
    if s is None:
        medida = f"; ECe de la parcela {ece.texto(1)}" if ece.conocido else ""
        return Veredicto("salinidad", NO_EVALUABLE, f"umbral de salinidad de {ctx.ficha.cultivo} desconocido "
                         f"en FAO-29{medida}: tolerancia no verificable", faltantes=[f"umbral ECe de {ctx.ficha.cultivo}"])
    base = dict(fuente=f"{s['fuente']} ({s['proxy'] or ctx.ficha.cultivo})", tipo_evidencia=s["tipo"])
    if not ece.conocido and not ecw.conocido:
        return Veredicto("salinidad", NO_EVALUABLE, "ECe del suelo y ECw del agua desconocidas",
                         faltantes=["ECe del suelo (dS/m)", "ECw del agua de riego (dS/m)"], **base)
    napa_ok, napa_txt = condicion_napa(ctx.estado)
    ece_medida = ece.conocido and ece.tipo_evidencia == "medicion_local"
    if not ece.conocido and not napa_ok:
        return Veredicto("salinidad", NO_EVALUABLE, f"solo se conoce la ECw del agua y {napa_txt}: la estimación "
                         f"ECe ≈ 1.5·ECw de FAO-29 exige napa ≥ {NAPA_MIN_M:g} m y lavado 15-20 %; hay que medir la ECe",
                         faltantes=["ECe del suelo medida (dS/m)", "profundidad de la napa freática (m)"], **base)
    # ECe efectiva: la de la parcela; el equilibrio 1.5·ECw solo vale con napa ≥ 2 m. Se usa el peor de ambos.
    usar_ecw = ecw.conocido and napa_ok
    lo = max(x for x in (ece.lo if ece.conocido else 0, 1.5 * ecw.lo if usar_ecw else 0))
    hi = max(x for x in (ece.hi if ece.conocido else 0, 1.5 * ecw.hi if usar_ecw else 0))
    razones = []
    if not napa_ok:
        razones.append(napa_txt)
    if not ece_medida:
        razones.append("ECe no medida en la parcela" + (" (se usó 1.5·ECw)" if not ece.conocido else f" ({ece.tipo_evidencia})"))
    if s.get("defecto_clase"):
        razones.append("umbral por defecto de clase de tolerancia (menor confianza)")
    extracto_nd = ece.conocido and ece is ctx.consulta.suelo.ece and ctx.consulta.suelo.ce_metodo == "ce_extracto_no_declarado"
    if extracto_nd:
        razones.append("CE de suelo con extracto no declarado: no es ECe de pasta saturada (si el extracto fue más "
                       "diluido, 1:1 a 1:5, la ECe real es mayor que la cifra)")
    exacto = not razones
    f_lo, f_hi = fraccion_rendimiento(hi, s), fraccion_rendimiento(lo, s)
    cult = s.get("cultivares") or {}
    pendiente = 50.0 / (s["ECe_50"] - s["ECe_100"])  # %/dS/m, la misma que la tabla (Cerda 1982: misma pendiente)
    u_min = min([s["ECe_100"], *cult.values()])
    u_max = max([s["ECe_100"], *cult.values()])
    ece50_tolerante = u_max + 50.0 / pendiente  # el 50 % del cultivar más tolerante
    if cult:  # Maas-Hoffman con el umbral de cada extremo
        f_lo = min(f_lo, max(0.0, 1 - pendiente * max(0.0, hi - u_min) / 100))
        f_hi = max(f_hi, min(1.0, 1 - pendiente * max(0.0, lo - u_max) / 100))
    txt_cult = ""
    if cult:
        sensibles = [k for k, v in sorted(cult.items(), key=lambda kv: kv[1]) if v < hi]
        txt_cult = (f"; por cultivar: {', '.join(f'{k} {v:g}' for k, v in sorted(cult.items(), key=lambda kv: kv[1]))} "
                    f"dS/m" + (f" ({', '.join(sensibles)} ya pierde rendimiento)" if sensibles else ""))
    nota_amp = ""
    if not exacto:
        f_lo = _bajar_un_tramo(f_lo)
        if extracto_nd:  # segunda fuente de incertidumbre independiente: otro tramo
            f_lo = _bajar_un_tramo(f_lo)
        nota_amp = (f"; cota inferior ampliada un tramo de la tabla FAO-29 (supuesto del motor, no calibrado) porque: "
                    f"{'; '.join(razones)}")
    frac = Cifra.rango(f_lo, f_hi, "fracción", f"motor v1: interpolación FAO-29 sobre ECe {lo:.2f}-{hi:.2f} dS/m",
                       "prediccion", "estimado", f"umbrales {s['proxy'] or ctx.ficha.cultivo} ({s['estado']}); "
                       f"{s['notas']}{nota_amp}", "rendimiento relativo por salinidad")
    nota_umbral = "sin rango en la tabla" + ("; DEFECTO DE CLASE, menor confianza" if s.get("defecto_clase") else "")
    r100 = r50 = (None, None)
    if cult:
        nota_umbral = (f"rango = umbrales por cultivar {', '.join(f'{k} {v:g}' for k, v in cult.items())} dS/m "
                       f"({s.get('cultivares_fuente', '')}), misma pendiente {pendiente:.1f} %/dS/m")
        r100 = (u_min, u_max)
        r50 = (u_min + 50.0 / pendiente, ece50_tolerante)
    if s.get("alternativa"):
        nota_umbral += f"; {s['alternativa']}"
    est = s["estado"] if s["estado"] != "desconocido" else "estimado"
    cifras = {"fraccion_rendimiento_salinidad": frac,
              "ECe_umbral_100": Cifra(s["ECe_100"], *r100, "dS/m", s["fuente"], s["tipo"], est, s["url"], nota_umbral,
                                      "ECe 100 %"),
              "ECe_umbral_50": Cifra(s["ECe_50"], *r50, "dS/m", s["fuente"], s["tipo"], est, s["url"], nota_umbral,
                                     "ECe 50 %")}
    faltan = [] if ece_medida else ["ECe del suelo medida en la parcela"]
    faltan += [] if napa_ok or ctx.estado.napa_m.conocido else ["profundidad de la napa freática (m)"]
    faltan += [] if ecw.conocido else ["ECw del agua de riego"]
    origen = "ECe medida" if ece_medida else ("ECe estimada 1.5·ECw" if not ece.conocido else "ECe estimada")
    if extracto_nd:
        origen = "CE medida (extracto no declarado, tratada como cota inferior de la ECe)"
        faltan.append("método del extracto de la CE (pasta saturada o relación suelo:agua)")

    rango_txt = f"{lo:.1f}" if lo == hi else f"{lo:.1f}-{hi:.1f}"
    if exacto:
        if lo >= ece50_tolerante:
            return Veredicto("salinidad", DESCARTA, f"{origen} {rango_txt} dS/m ≥ ECe al 50 % de rendimiento "
                             f"({s['ECe_50']} dS/m); {napa_txt}", cifras=cifras, faltantes=faltan, **base)
        if hi > u_min:
            return Veredicto("salinidad", ADVIERTE, f"{origen} {rango_txt} dS/m supera el umbral sin pérdida "
                             f"({s['ECe_100']} dS/m{txt_cult}); rendimiento relativo {frac.texto(2)}", cifras=cifras,
                             faltantes=faltan, **base)
        res = PASA if ecw.conocido else ADVIERTE
        return Veredicto("salinidad", res, f"{origen} {rango_txt} dS/m ≤ umbral {s['ECe_100']} dS/m; {napa_txt}"
                         + ("" if ecw.conocido else "; ECw desconocida: evaluación parcial"), cifras=cifras,
                         faltantes=faltan, **base)
    porque = "; ".join(razones)
    if lo >= ece50_tolerante:
        motivo = (f"probable no apto: {origen} {rango_txt} dS/m ≥ ECe al 50 % ({s['ECe_50']} dS/m), pero el umbral "
                  f"no se aplica como exacto ({porque}); rendimiento relativo {frac.texto(2)}")
    elif hi > u_min:
        motivo = (f"{origen} {rango_txt} dS/m supera el umbral sin pérdida ({s['ECe_100']} dS/m{txt_cult}); umbral no exacto "
                  f"({porque}); rendimiento relativo {frac.texto(2)} con incertidumbre ampliada")
    else:
        motivo = (f"{origen} {rango_txt} dS/m ≤ umbral {s['ECe_100']} dS/m, pero el umbral no se aplica como exacto "
                  f"({porque}); rendimiento relativo {frac.texto(2)} con incertidumbre ampliada")
    return Veredicto("salinidad", ADVIERTE, motivo, cifras=cifras, faltantes=faltan, grave=lo >= ece50_tolerante, **base)


# ---------------------------------------------------------------------------------------- terreno
def _reglas(ctx: Contexto, variable: str) -> list[dict]:
    return [r for r in ctx.reglas_terreno if r["variable"] == variable and _aplica(r["aplica_a"], ctx.ficha)]


def f_drenaje(ctx: Contexto) -> Veredicto:
    reglas = _reglas(ctx, "drenaje")
    d = ctx.estado.drenaje
    if d is None:
        if any(r["accion"] == DESCARTA for r in reglas):
            return Veredicto("drenaje", NO_EVALUABLE, f"drenaje desconocido y {ctx.ficha.cultivo} se descarta con "
                             "drenaje pobre", faltantes=["drenaje de la parcela"])
        return Veredicto("drenaje", NO_EVALUABLE, "drenaje desconocido", faltantes=["drenaje de la parcela"])
    peor = None
    for r in reglas:
        if r["operador"] == "=" and d == r["umbral"]:
            if peor is None or (r["accion"] == DESCARTA):
                peor = r
    if peor:
        return Veredicto("drenaje", peor["accion"], peor["motivo"], peor["fuente"], peor["tipo_evidencia"])
    return Veredicto("drenaje", PASA, f"drenaje {d}")


def f_pendiente(ctx: Contexto) -> Veredicto:
    p = ctx.estado.pendiente_pct
    reglas = sorted(_reglas(ctx, "pendiente_pct"), key=lambda r: -float(r["umbral"]))
    if not p.conocido:
        return Veredicto("pendiente", NO_EVALUABLE, "pendiente desconocida", faltantes=["pendiente (%)"])
    for r in reglas:
        u = float(r["umbral"])
        if p.lo > u:
            return Veredicto("pendiente", r["accion"], f"pendiente {p.texto()}: {r['motivo']}", r["fuente"],
                             r["tipo_evidencia"], {"pendiente": p})
        if p.hi > u:
            return Veredicto("pendiente", ADVIERTE, f"pendiente {p.texto()} cruza el umbral {u} %: {r['motivo']}",
                             r["fuente"], r["tipo_evidencia"], {"pendiente": p})
    return Veredicto("pendiente", PASA, f"pendiente {p.texto()}", cifras={"pendiente": p})


# ---------------------------------------------------------------------------------------- agua
def f_agua(ctx: Contexto) -> Veredicto:
    ag, c = ctx.agua, ctx.consulta
    if ag is None or not ag.disponible:
        return Veredicto("agua", NO_EVALUABLE, "; ".join(ag.notas) if ag else "demanda de agua no calculada",
                         faltantes=[f"Kc o duración por etapa de {ctx.ficha.cultivo}"])
    if not c.area_ha.conocido:
        return Veredicto("agua", NO_EVALUABLE, "área de la parcela desconocida: no se puede comparar m3 disponibles",
                         faltantes=["área de la parcela (ha)"])
    ef = c.agua.eficiencia
    peor, faltan, motivos = PASA, [], []
    oferta_lo = demanda_hi_tot = 0.0
    for _, mes, neto in ag.mensual:
        disp = c.agua.m3_por_mes[mes]
        dem_lo = neto.lo * 10 * c.area_ha.lo / (ef.hi if ef.conocido else 1.0)
        dem_hi = neto.hi * 10 * c.area_ha.hi / (ef.lo if ef.conocido else 1.0)
        if not disp.conocido:
            faltan.append(f"agua disponible en mes {mes}")
            continue
        oferta_lo += min(disp.lo, dem_hi)
        demanda_hi_tot += dem_hi
        if disp.hi < dem_lo:
            peor = DESCARTA
            motivos.append(f"mes {mes}: disponible {disp.texto(0)} < demanda mínima {dem_lo:,.0f} m3")
        elif disp.lo < dem_hi and peor != DESCARTA:
            peor = ADVIERTE
            motivos.append(f"mes {mes}: disponible {disp.texto(0)} puede no cubrir {dem_hi:,.0f} m3")
    if not ef.conocido:
        faltan.append("eficiencia de riego (se comparó con riego neto: demanda real mayor)")
        if peor == PASA:
            peor = ADVIERTE
            motivos.append("cubre el riego neto, pero sin eficiencia no se sabe si cubre el riego bruto")
    n_meses_falta = sum(f.startswith("agua disponible") for f in faltan)
    if n_meses_falta and n_meses_falta >= len(ag.mensual) and peor != DESCARTA:
        return Veredicto("agua", NO_EVALUABLE, "agua disponible por mes desconocida",
                         faltantes=["agua de riego disponible por mes (m3)"])
    if any(f.startswith("agua disponible") for f in faltan) and peor == PASA:
        peor = NO_EVALUABLE
    cifras = {"riego_neto_ciclo": ag.riego_neto_m3_ha}
    if ctx.ficha.ky is not None and demanda_hi_tot > 0 and peor in (ADVIERTE, DESCARTA):
        r = oferta_lo / demanda_hi_tot
        cifras["fraccion_rendimiento_agua"] = Cifra.rango(max(0.0, 1 - ctx.ficha.ky.hi * (1 - r)), 1.0, "fracción",
                                                          "motor v1: 1−Ya/Ym = Ky(1−ETa/ETm)", "prediccion", "estimado",
                                                          f"peor caso oferta/demanda = {r:.2f}; Ky {ctx.ficha.ky.texto(2)}",
                                                          "rendimiento relativo por déficit hídrico")
    motivo = "; ".join(motivos[:4]) or "el agua disponible cubre la demanda mensual"
    return Veredicto("agua", peor, motivo, "FAO-56 + agua declarada", "prediccion", cifras, faltan)


# ---------------------------------------------------------------------------------------- sanidad
def f_sanidad(ctx: Contexto) -> Veredicto:
    ant, cult = ctx.cultivo_anterior, ctx.ficha.cultivo
    if ant is None and not ctx.consulta.plagas_presentes:
        return Veredicto("sanidad", NO_EVALUABLE, "cultivo anterior y plagas presentes desconocidos",
                         faltantes=["cultivo anterior"])
    peor, motivos, fuentes, tipos = PASA, [], [], []
    for r in ctx.reglas_sanidad:
        afectados = r["cultivos_afectados"].split(";")
        agente = r["agente"]
        if agente == "mismo_cultivo":
            dispara = ant == cult
        elif agente == "misma_familia":
            dispara = ant != cult and ctx.familia_anterior == ctx.ficha.familia
        else:
            presente = agente in ctx.consulta.plagas_presentes
            arrastre = ant in afectados
            dispara = cult in afectados and (presente or arrastre)
        if dispara:
            motivos.append(f"{agente}: {r['motivo']}")
            fuentes.append(r["fuente"])
            tipos.append(r["tipo_evidencia"])
            if r["accion"] == DESCARTA:
                peor = DESCARTA
            elif peor == PASA:
                peor = ADVIERTE
    if not motivos:
        return Veredicto("sanidad", PASA, f"sin riesgo sanitario registrado tras {ant or 'cultivo desconocido'}")
    return Veredicto("sanidad", peor, "; ".join(motivos), "; ".join(dict.fromkeys(fuentes)),
                     "; ".join(dict.fromkeys(tipos)))


# ---------------------------------------------------------------------------------------- calendario
FRACCION_MESES_TERMICA = 0.75  # supuesto del motor: "todos o casi todos los meses del ciclo" = al menos el 75 %


def termica_grave(ctx: Contexto) -> str:
    """'Probable no apto' térmico: en al menos FRACCION_MESES_TERMICA de los meses del ciclo la media de las máximas
    diarias (PISCOt de la zona, P10-P90 entre años) pasa el TMAX absoluto EcoCrop, o la Tmín baja del TMIN absoluto.
    No se usa el día más caluroso del mes (POWER Tmax_max_C): un solo día no define el mes. Un mes cuenta solo si
    todo su rango queda fuera. El clima del repo no trae Tmín; como Tmín ≤ Tmedia, una Tmedia entera bajo TMIN prueba que la Tmín
    también lo está. Un mes sin dato no cuenta como fuera. Devuelve el motivo o ''."""
    meses = list(dict.fromkeys(ctx.meses_ciclo))
    absolutos = [u for u in ctx.ficha.umbrales if u.etiqueta.startswith(("rango absoluto EcoCrop", "límite absoluto EcoCrop"))]
    tmax = min((u.maximo for u in absolutos if u.variable == "tmax" and u.maximo is not None), default=None)
    tmin = max((u.minimo for u in absolutos if u.variable == "tmedia" and u.minimo is not None), default=None)
    if not meses or (tmax is None and tmin is None):
        return ""
    calientes, frios = [], []
    for mes in meses:
        t = ctx.tmax_media.get((mes - 1) % 12 + 1)
        if tmax is not None and t is not None and t.conocido and t.lo > tmax:
            calientes.append(mes)
        tm = ctx.clima.cifra(mes, "tmedia")
        if tmin is not None and tm.conocido and tm.hi < tmin:
            frios.append(mes)
    minimo = FRACCION_MESES_TERMICA * len(meses)
    partes = []
    if len(calientes) >= minimo:
        partes.append(f"media de las máximas diarias (PISCOt 1981-2020 de la zona, P10 entre años) sobre el TMAX "
                      f"absoluto EcoCrop {tmax} °C en "
                      f"{len(calientes)} de {len(meses)} meses del ciclo {calientes}")
    if len(frios) >= minimo:
        partes.append(f"Tmín bajo el TMIN absoluto EcoCrop {tmin} °C en {len(frios)} de {len(meses)} meses del ciclo "
                      f"{frios} (deducido: Tmedia ya está bajo TMIN)")
    if not partes:
        return ""
    return ("probable no apto: " + "; ".join(partes) + f" (umbral: al menos el {FRACCION_MESES_TERMICA:.0%} de los meses, "
            "supuesto del motor; EcoCrop es rango de especie, no de variedad local)").replace("75%", "75 %")


def meses_floracion(ctx: Contexto) -> list[int]:
    """Meses calendario que puede cubrir la etapa media FAO-56 (floración-llenado), desde el inicio más temprano
    (inicial y desarrollo mínimos) hasta el final más tardío (inicial, desarrollo y media máximos)."""
    e = ctx.ficha.etapas or {}
    if not ctx.meses_ciclo or not all(k in e for k in ("inicial", "desarrollo", "media")):
        return []
    d0 = e["inicial"][0] + e["desarrollo"][0]
    d1 = e["inicial"][1] + e["desarrollo"][1] + e["media"][1]
    mes0 = ctx.meses_ciclo[0]
    return [(mes0 - 1 + k) % 12 + 1 for k in range(int(d0 // 30.4), int(d1 // 30.4) + 1)]


def exceso_agua(ctx: Contexto) -> tuple[str, list[str], bool]:
    """Exceso de agua en el ciclo con la lluvia PISCOp del escenario ICEN: 'exceso' si la lluvia mediana del mes
    supera la ET0 mediana (el año típico del escenario deja agua sobrante), 'posible' si solo la supera el año más
    lluvioso (P90 o máx.). Pesa (ADVIERTE) con exceso y drenaje no bueno. La pérdida por anegamiento del cultivo se
    cita como contexto: la duración del anegamiento en El Niño es desconocida (R4A024), así que no entra al margen."""
    if ctx.clima.fuente_lluvia != "PISCOp":
        return "", [], False
    exceso, posible = [], []
    for m in dict.fromkeys(ctx.meses_ciclo):
        ll, et0 = ctx.clima.cifra(m, "lluvia"), ctx.clima.cifra(m, "ET0")
        if not (ll.conocido and et0.conocido):
            continue
        if ll.valor > et0.valor:
            exceso.append(f"mes {(m - 1) % 12 + 1}: lluvia mediana {ll.valor:.0f} mm > ET0 {et0.valor:.0f} mm")
        elif ll.hi > et0.valor:
            posible.append(f"mes {(m - 1) % 12 + 1}: {ll.hi:.0f} mm en el año más lluvioso > ET0 {et0.valor:.0f} mm")
    if not exceso and not posible:
        return "", [], False
    drenaje = ctx.estado.drenaje or "desconocido"
    if exceso:
        txt = f"exceso de agua con la lluvia PISCOp del escenario {ctx.consulta.escenario} ({'; '.join(exceso[:3])})"
        txt += f" y drenaje {drenaje}: riesgo de anegamiento" if drenaje != "bueno" else "; drenaje bueno"
    else:
        txt = f"posible exceso de agua en el año más lluvioso del escenario (lluvia PISCOp: {'; '.join(posible[:3])})"
    perdidas = ctx.ficha.anegamiento
    if perdidas:
        txt += f". Pérdida por anegamiento citada para {ctx.ficha.cultivo}: {'; '.join(perdidas[:2])}"
    faltan = ["duración del anegamiento en El Niño (R4A024: INDECI no publica cuántos días quedó el agua; sin ella "
              "la pérdida no se aplica al margen)"]
    if not perdidas:
        faltan.append(f"tolerancia al anegamiento de {ctx.ficha.cultivo} (no está en los datos de Agronomía)")
    return txt, faltan, bool(exceso) and drenaje != "bueno"


def floracion_calor(ctx: Contexto) -> tuple[str, str, str]:
    """Regla blanda: Tmáx media PISCOt de los meses de floración contra el umbral INFERIOR de estrés reproductivo
    (no contra el TMAX absoluto EcoCrop). Devuelve (resultado, motivo, faltante). Probable no apto solo si hasta el
    año fresco (P10) pasa el umbral en FRACCION_MESES_TERMICA de los meses de floración; si no, advertencia."""
    u = ctx.ficha.umbral_floracion
    if u is None or u.minimo is None:
        return PASA, "", ""
    meses = meses_floracion(ctx)
    if not meses:
        return PASA, "", f"meses de floración de {ctx.ficha.cultivo} (sin etapas FAO-56)"
    datos = {m: ctx.tmax_media.get(m) for m in meses}
    if not any(t is not None and t.conocido for t in datos.values()):
        return PASA, "", f"Tmáx media PISCO de la zona en floración (meses {meses})"
    seguro = [m for m, t in datos.items() if t is not None and t.conocido and t.lo > u.minimo]
    mediana = [m for m, t in datos.items() if t is not None and t.conocido and t.valor is not None and t.valor > u.minimo]
    posible = [m for m, t in datos.items() if t is not None and t.conocido and t.hi > u.minimo]
    if not posible:
        return PASA, "", ""
    detalle = ", ".join(f"mes {m} {t.valor:g} [{t.lo:g}–{t.hi:g}]" for m, t in datos.items() if t is not None and t.conocido)
    base = (f"floración-llenado (meses {meses}): Tmáx media PISCOt {detalle} °C contra el {u.etiqueta} "
            f"{u.minimo:g}–{u.maximo:g} °C ({u.fuente}; {u.url})")
    if len(seguro) >= FRACCION_MESES_TERMICA * len(meses):
        return "grave", (f"probable no apto: {base}; hasta el año fresco (P10) pasa {u.minimo:g} °C en {len(seguro)} de "
                         f"{len(meses)} meses"), ""
    cuando = (f"la mediana ya pasa {u.minimo:g} °C en meses {mediana}" if mediana
              else f"solo el año cálido (P90) pasa {u.minimo:g} °C en meses {posible}")
    return ADVIERTE, f"{base}; {cuando}: riesgo de aborto de flores y vainas", ""


NOTA_TMAX_POWER = ("solo nota, sin peso en alertas ni en el orden: Piura Datos marcó la Tmáx POWER 'no usar sin "
                   "corregir' (difiere más de 3 °C de PISCO-SENAMHI en restricciones/temperatura_media_max_min_zona.csv)")


def f_calendario(ctx: Contexto) -> Veredicto:
    dur, horiz = ctx.duracion, ctx.consulta.horizonte_meses * 30.4
    motivos, faltan, cifras, peor = [], [], {}, PASA

    def subir(nuevo):
        nonlocal peor
        orden = (PASA, NO_EVALUABLE, ADVIERTE, DESCARTA)
        peor = max(peor, nuevo, key=orden.index)

    if ctx.ficha.modulo == "perenne":
        pass  # perennes: no se compara duración con el horizonte; solo clima
    elif not dur.conocido:
        subir(NO_EVALUABLE)
        faltan.append(f"duración del ciclo de {ctx.ficha.cultivo}")
    else:
        cifras["duracion"] = dur
        if dur.lo > horiz:
            subir(DESCARTA)
            motivos.append(f"ciclo {dur.texto(0)} > horizonte {ctx.consulta.horizonte_meses} meses")
        elif dur.hi > horiz:
            subir(ADVIERTE)
            motivos.append(f"ciclo {dur.texto(0)} puede exceder el horizonte de {ctx.consulta.horizonte_meses} meses")
    fuente_extra = ""
    if ctx.ficha.modulo == "anual" and ctx.meses_ciclo:
        from .calendario_obs import FUENTE as F_CAL, evaluar_mes
        mes0, zona = ctx.meses_ciclo[0], ctx.zona
        v = ctx.ficha.calendario.get(zona) if zona else None
        if v is None:
            donde = f"en {zona}" if zona else "(zona desconocida)"
            aus = ctx.ausencia_calendario
            if aus:
                subir(ADVIERTE)
                motivos.insert(0, f"sin ventana de siembra observada de {ctx.ficha.cultivo} {donde}: la DRAP "
                               f"({aus[0]}) registra 0 ha de {ctx.ficha.cultivo} en la zona (ausencia observada, "
                               f"confianza {aus[2]:g}; {aus[1]}); no hay práctica local que respalde la siembra")
            else:
                motivos.append(f"sin ventana de siembra observada (DRAP 2016-2024) de {ctx.ficha.cultivo} {donde}: "
                               "no se sabe si el mes {mes0} es práctica local".replace("{mes0}", str(mes0)))
        else:
            fuente_extra = f"; {F_CAL}"
            pos = evaluar_mes(v, mes0)
            if pos == "dentro":
                motivos.append(f"siembra en mes {mes0} dentro de lo observado en {zona} ({v.describir()}); ventana "
                               "observada, no recomendación")
            elif pos == "borde":
                motivos.append(f"siembra en mes {mes0} a un mes de lo observado en {zona} ({v.describir()}); ventana "
                               "observada, no recomendación")
            else:
                subir(ADVIERTE)
                motivos.append(f"siembra en mes {mes0} FUERA de las ventanas observadas en {zona} ({v.describir()}): "
                               "poca experiencia local en ese mes; no es un descarte ni una recomendación")
    termicos = [u for u in ctx.ficha.umbrales if u.variable in ("tmedia", "tmax")]
    notas_opt, rango_opt, notas_calor = [], "", []
    if not termicos:
        faltan.append(f"rango térmico de {ctx.ficha.cultivo} (no está en los datos)")
        prov = ctx.consulta.provincia
        if prov:
            # sustituto: ¿hay producción registrada (DRAP) del cultivo en la provincia de la parcela?
            if ctx.ficha.tiene_registro_en(prov):
                motivos.append(f"sin rango térmico; hay producción registrada en la provincia {prov} (DRAP, regional)")
            else:
                subir(ADVIERTE)
                motivos.append(f"sin rango térmico y sin producción registrada en la provincia {prov} (DRAP): "
                               "adaptación al clima local no verificada")
    for u in termicos:
        for mes in dict.fromkeys(ctx.meses_ciclo):
            t = ctx.clima.cifra(mes, u.variable)
            if not t.conocido:
                continue
            fuera_total = (u.minimo is not None and t.hi < u.minimo) or (u.maximo is not None and t.lo > u.maximo)
            fuera_parcial = (u.minimo is not None and t.lo < u.minimo) or (u.maximo is not None and t.hi > u.maximo)
            rango = f"{u.minimo if u.minimo is not None else '−'}–{u.maximo if u.maximo is not None else '−'} °C"
            if u.variable == "tmax" and u.maximo is not None and t.hi >= u.maximo:
                # la Tmáx POWER no pesa: Datos la marcó 'no usar sin corregir' (ver NOTA_TMAX_POWER)
                pisco = ctx.tmax_media.get(mes)
                media = f", media de las máximas PISCOt {pisco.texto()}" if pisco is not None and pisco.conocido else ""
                notas_calor.append(f"mes {mes} {t.texto()} ≥ {u.etiqueta or 'umbral de daño por calor'} {u.maximo} °C"
                                   f"{media}")
            elif u.duro and fuera_total:
                subir(DESCARTA)
                motivos.append(f"mes {mes}: Tmedia {t.texto()} fuera del {u.etiqueta or 'rango de adaptación'} {rango}")
            elif fuera_parcial and u.variable == "tmedia" and u.nivel == "nota":
                notas_opt.append(mes)
                rango_opt = rango
            elif fuera_parcial and u.variable == "tmedia":
                subir(ADVIERTE)
                motivos.append(f"mes {mes}: Tmedia {t.texto()} sale del rango {'de adaptación' if u.duro else 'óptimo'}"
                               f" {rango}")
    if notas_calor:
        motivos.append(f"día más caluroso (POWER Tmax_max_C): {'; '.join(notas_calor)} ({NOTA_TMAX_POWER})")
    if notas_opt:
        motivos.append(f"Tmedia fuera del óptimo EcoCrop {rango_opt} en meses {list(dict.fromkeys(notas_opt))} "
                       "(solo nota: sin peso en la decisión)")
    if any(u.etiqueta.startswith("rango absoluto EcoCrop") for u in termicos):
        faltan.append("Tmín mensual (el clima del repo no la trae: el límite inferior EcoCrop se compara con Tmedia)")
    motivo_agua, falta_agua, pesa_agua = exceso_agua(ctx)
    faltan.extend(falta_agua)
    if pesa_agua:
        subir(ADVIERTE)
    if motivo_agua:
        motivos.insert(0, motivo_agua)
    if ctx.ficha.notas and ctx.ficha.modulo == "anual":
        motivos.append(ctx.ficha.notas)
    grave = termica_grave(ctx)
    res_flor, motivo_flor, falta_flor = floracion_calor(ctx)
    if falta_flor:
        faltan.append(falta_flor)
    if res_flor == "grave":
        grave = "; ".join(x for x in (grave, motivo_flor) if x)
    elif motivo_flor:
        subir(ADVIERTE)
        motivos.insert(0, motivo_flor)
    if not ctx.tmax_media and any(u.variable == "tmax" for u in ctx.ficha.umbrales):
        faltan.append("Tmáx media PISCO de la zona (°C): sin ella la regla térmica grave no evalúa calor")
    if grave:
        subir(ADVIERTE)
        motivos.insert(0, grave)
    if peor == ADVIERTE and ctx.ficha.modulo != "perenne" and not dur.conocido:
        peor = NO_EVALUABLE  # una advertencia (p. ej. exceso de agua) no vuelve evaluable un ciclo sin duración
    motivo = "; ".join(dict.fromkeys(motivos[:7])) or "ciclo dentro del horizonte"
    return Veredicto("calendario", peor, motivo, "FAO-56/INIA duración; NASA POWER temperatura y ET0; PISCOp lluvia por escenario ICEN; PISCOt Tmáx media (regla grave); umbrales SENASA/MIDAGRI"
                     + fuente_extra, "prediccion", cifras, faltan, grave=bool(grave))


# ---------------------------------------------------------------------------------------- pH, profundidad
APTO, MARGINAL, NO_APTO = "apto", "marginal", "no_apto"
FRANJA_CAPILAR = Cifra.rango(0.3, 0.5, "m", "Piura Territorio, suelos/datos/profundidad_ph_por_zona.csv (franja "
                             "capilar; rango de la revisión agronómica, sin fuente primaria verificada)", "bibliografico",
                             "estimado", "se resta a la napa para obtener la profundidad útil de raíces",
                             "franja_capilar")


def clase_aptitud(a_min: float | None, a_max: float | None) -> str:
    if a_min is not None and a_min >= 1.0:
        return APTO
    if a_max is not None and a_max <= 0.0:
        return NO_APTO
    return MARGINAL


def _cifra_aptitud(rampa, a_min, a_max, nombre: str) -> Cifra:
    if a_min is None or a_max is None:
        return Cifra.desconocido("0-1", f"aptitud {nombre}", "límite absoluto desconocido: aptitud fuera del rango apto "
                                 "no calculable", fuente=rampa.fuente)
    return Cifra.rango(a_min, a_max, "0-1", f"motor v1: rampa lineal ({rampa.describir()}); {rampa.fuente}",
                       "prediccion", "estimado", "1 = dentro del rango apto; 0 = en o más allá del límite absoluto",
                       f"aptitud {nombre}")


def profundidad_efectiva(estado: EstadoSuelo) -> tuple[Cifra, list[str], list[str]]:
    """min(profundidad física, napa − franja capilar). Devuelve (cifra en m, notas, faltantes)."""
    fis, napa = estado.profundidad_cm, estado.napa_m
    notas, faltan = [], []
    if not napa.conocido:
        faltan.append("profundidad de la napa freática (m)")
        if not fis.conocido:
            return Cifra.desconocido("m", "profundidad efectiva", "profundidad física y napa desconocidas"), notas, faltan
        notas.append("napa desconocida: se usó solo la profundidad física (la efectiva puede ser menor)")
        return Cifra.rango(fis.lo / 100, fis.hi / 100, "m", fis.fuente, fis.tipo_evidencia, fis.estado,
                           "profundidad física; napa desconocida", "profundidad efectiva"), notas, faltan
    lim_lo = max(0.0, napa.lo - FRANJA_CAPILAR.hi)
    lim_hi = max(0.0, napa.hi - FRANJA_CAPILAR.lo)
    if fis.conocido:
        lo, hi = min(fis.lo / 100, lim_lo), min(fis.hi / 100, lim_hi)
        notas.append(f"profundidad efectiva = mín(física {fis.texto(0)}, napa {napa.texto(1)} − franja capilar "
                     f"{FRANJA_CAPILAR.texto(1)})")
    else:
        lo, hi = 0.0, lim_hi
        faltan.append("profundidad física del suelo")
        notas.append(f"profundidad física desconocida: efectiva entre 0 y napa − franja capilar ({lim_hi:.2f} m)")
    return Cifra.rango(lo, hi, "m", f"motor v1: mín(física, napa − franja capilar); {FRANJA_CAPILAR.fuente}",
                       "prediccion", "estimado", "; ".join(notas), "profundidad efectiva"), notas, faltan


def f_ph(ctx: Contexto) -> Veredicto:
    """Rampa apto/marginal/no apto. Fuera del límite absoluto avisa; descarta solo con pH medido y umbral local o
    regional (EcoCrop es un rango global de especie)."""
    rampa, ph = ctx.ficha.rampas.get("ph"), ctx.estado.ph
    if rampa is None:
        return Veredicto("pH", NO_EVALUABLE, f"sin rango de pH para {ctx.ficha.cultivo} en los datos",
                         faltantes=[f"rango de pH de {ctx.ficha.cultivo}"])
    if not ph.conocido:
        return Veredicto("pH", NO_EVALUABLE, "pH de la parcela desconocido", faltantes=["pH de la parcela"])
    a_min, a_max = rampa.aptitud_intervalo(ph.lo, ph.hi)
    clase = clase_aptitud(a_min, a_max)
    apt = _cifra_aptitud(rampa, a_min, a_max, "pH")
    base = dict(fuente=f"{rampa.fuente} {rampa.url}", tipo_evidencia=rampa.tipo_evidencia,
                cifras={"pH": ph, "aptitud_pH": apt})
    desc = rampa.describir()
    if clase == APTO:
        return Veredicto("pH", PASA, f"pH {ph.texto()} apto ({desc})", **base)
    if clase == NO_APTO:
        local = ph.tipo_evidencia == "medicion_local" and ph.estado == "observado" and rampa.tipo_evidencia in ("medicion_local", "regional")
        res = DESCARTA if local else ADVIERTE
        extra = "" if local else "; no se descarta: el límite es un rango global de especie (descarte solo con pH medido y evidencia local)"
        return Veredicto("pH", res, f"pH {ph.texto()} no apto: fuera del límite absoluto ({desc}){extra}",
                         grave=not local, **base)
    if a_min is None:
        return Veredicto("pH", ADVIERTE, f"pH {ph.texto()} fuera del rango apto {desc}; límite absoluto desconocido",
                         **base)
    if a_min <= 0.0:
        return Veredicto("pH", ADVIERTE, f"pH {ph.texto()} marginal y puede llegar al límite absoluto ({desc}); "
                         f"aptitud {apt.texto(2)}", **base)
    return Veredicto("pH", PASA, f"pH {ph.texto()} marginal ({desc}); aptitud {apt.texto(2)}: penalización suave",
                     **base)


def f_profundidad(ctx: Contexto) -> Veredicto:
    """Compara la profundidad que pide el cultivo (DEPR mínima apta, DEP favorable) con la profundidad efectiva."""
    rampa = ctx.ficha.rampas.get("profundidad_m")
    if rampa is None:
        return Veredicto("profundidad", NO_EVALUABLE, f"sin profundidad mínima para {ctx.ficha.cultivo} en los datos",
                         faltantes=[f"profundidad de raíces de {ctx.ficha.cultivo}"])
    ef, notas, faltan = profundidad_efectiva(ctx.estado)
    if not ef.conocido:
        return Veredicto("profundidad", NO_EVALUABLE, "profundidad del suelo y napa desconocidas",
                         faltantes=["profundidad del suelo"] + faltan)
    a_min, a_max = rampa.aptitud_intervalo(ef.lo, ef.hi)
    apt = _cifra_aptitud(rampa, a_min, a_max, "profundidad")
    base = dict(fuente=f"{rampa.fuente} {rampa.url}", tipo_evidencia=rampa.tipo_evidencia,
                cifras={"profundidad_efectiva": ef, "aptitud_profundidad": apt}, faltantes=faltan)
    desc, txt = rampa.describir(), f"profundidad efectiva {ef.texto(2)}"
    nota = f" ({'; '.join(notas)})" if notas else ""
    if rampa.abs_min is not None and ef.hi < rampa.abs_min:
        return Veredicto("profundidad", DESCARTA, f"{txt} < mínima apta {rampa.abs_min} m ({desc}){nota}", **base)
    if rampa.abs_min is not None and ef.lo < rampa.abs_min:
        return Veredicto("profundidad", ADVIERTE, f"{txt} puede quedar bajo la mínima apta {rampa.abs_min} m "
                         f"({desc}){nota}", **base)
    if rampa.apto_min is not None and ef.lo < rampa.apto_min:
        return Veredicto("profundidad", ADVIERTE, f"{txt} marginal: menor que la favorable {rampa.apto_min} m; "
                         f"aptitud {apt.texto(2)}{nota}", **base)
    return Veredicto("profundidad", PASA, f"{txt} apta ({desc}){nota}", **base)


# ---------------------------------------------------------------------------------------- presupuesto
def f_presupuesto(ctx: Contexto) -> Veredicto:
    costo, area, pres = ctx.costo, ctx.consulta.area_ha, ctx.consulta.presupuesto_pen
    faltan = [n for n, c in ((f"costo de producción de {ctx.ficha.cultivo}", costo), ("área", area),
                             ("presupuesto", pres)) if not c.conocido]
    if faltan:
        return Veredicto("presupuesto", NO_EVALUABLE, f"no evaluable: falta {', '.join(faltan)}", faltantes=faltan)
    total_lo, total_hi = costo.lo * area.lo, costo.hi * area.hi
    cifras = {"costo_total": Cifra.rango(total_lo, total_hi, "PEN", f"motor v1: costo/ha × área; {costo.fuente}",
                                         notas=f"costo/ha {costo.tipo_evidencia}: {costo.notas}", variable="costo total"),
              "costo_ha": costo}
    base = dict(fuente=costo.fuente, tipo_evidencia=costo.tipo_evidencia, cifras=cifras)
    sin_rango = costo.valor_min is None
    if total_lo > pres.hi and not sin_rango:
        return Veredicto("presupuesto", DESCARTA, f"costo {total_lo:,.0f}-{total_hi:,.0f} PEN > presupuesto "
                         f"{pres.texto(0)}", **base)
    if total_hi > pres.lo:
        nota = " (promedio sin dispersión conocida)" if sin_rango else ""
        return Veredicto("presupuesto", ADVIERTE, f"costo {total_lo:,.0f}-{total_hi:,.0f} PEN{nota} puede superar "
                         f"presupuesto {pres.texto(0)}", **base)
    return Veredicto("presupuesto", PASA, f"costo {total_lo:,.0f}-{total_hi:,.0f} PEN ≤ presupuesto", **base)


# ---------------------------------------------------------------------------------------- normas y riesgos
ZONAS_INUNDABLES = ("bajo_piura",)  # R4R003 cita Bajo Piura como parcela inundable típica (FEN 2017)


def f_normas(ctx: Contexto) -> Veredicto:
    """Reglas de Piura Agronomía: arroz y drenaje (R4R001/R4R002), riesgo FEN (R4R003, R4A021/22, R4A025) y
    algodón (RM 0251-94-AG: ventanas de siembra, campo limpio, socas, chupadera, rastrojo)."""
    from . import reglas as rg
    R, cult = ctx.reglas, ctx.ficha.cultivo
    if not R:
        return Veredicto("normas", NO_EVALUABLE, "reglas de Piura Agronomía no cargadas")
    peor, motivos, fuentes, tipos = PASA, [], [], []

    def regla(rid, res, texto):
        nonlocal peor
        r = R[rid]
        if res == ADVIERTE:
            peor = ADVIERTE
        motivos.append(f"[{rid}] {texto}")
        fuentes.append(f"{r['fuente'].split(' (')[0]} {r['url_o_doi']}")
        tipos.append(r["tipo_evidencia"])

    est = ctx.estado
    napa_ok, napa_txt = condicion_napa(est)
    # arroz y drenaje
    if cult == "arroz" and "R4R001" in R:
        if est.drenaje == "pobre" or (est.napa_m.conocido and est.napa_m.lo < NAPA_MIN_M):
            regla("R4R001", ADVIERTE, f"arroz con drenaje {est.drenaje or 'desconocido'} y {napa_txt}: la lámina "
                  "sube la napa y la ECe tras la campaña (magnitud desconocida)")
        elif not (est.drenaje == "bueno" and napa_ok):
            regla("R4R001", ADVIERTE, f"arroz con drenaje {est.drenaje or 'desconocido'} y {napa_txt}: no se puede "
                  "descartar que suba la napa y la ECe; medir napa")
        elif "R4R002" in R:
            regla("R4R002", PASA, "drenaje bueno y napa ≥ 2 m: la lámina de arroz puede lavar sales")
    # riesgo FEN
    if "R4R003" in R:
        inundable = ctx.zona in ZONAS_INUNDABLES or est.drenaje == "pobre"
        en_campo = ctx.ficha.modulo == "perenne" or any(m in (1, 2, 3, 4) for m in ctx.meses_ciclo)
        alerta = ctx.consulta.escenario in ESCENARIOS_NINO or ctx.alerta_fen
        if inundable and en_campo and alerta:
            cifras = []
            for rid in ("R4A021", "R4A022"):
                if rid in R:
                    cifras.append(f"{R[rid]['valor']} ha {'perdidas' if rid == 'R4A021' else 'afectadas'}")
            regla("R4R003", ADVIERTE, "alerta de Niño costero, parcela inundable "
                  f"({ctx.zona or ''}{' / ' if ctx.zona and est.drenaje == 'pobre' else ''}{'drenaje pobre' if est.drenaje == 'pobre' else ''}) "
                  f"y cultivo en campo entre enero y abril: riesgo alto de pérdida (FEN 2017 en Piura: "
                  f"{', '.join(cifras) or 'cifras no cargadas'}; probabilidad para esta parcela desconocida)")
    # algodón
    if cult == "algodon":
        ant = ctx.cultivo_anterior
        if ant == "algodon":
            for rid, txt in (("R4R004", "tras algodón se exige campo limpio 75-80 días (destrucción de rastrojo y "
                              "plantas) antes de volver a sembrar"),
                             ("R4R006", "socas (rebrote del algodón anterior) prohibidas"),
                             ("R4R005", "gorgojo de la chupadera: al menos 1 campaña sin algodón")):
                if rid in R:
                    regla(rid, ADVIERTE, txt)
        mes = ctx.meses_ciclo[0] if ctx.meses_ciclo else None
        if ctx.zona and mes:
            vents = rg.ventanas_algodon(R, ctx.zona)
            if vents:
                dentro = [(r, rg.mes_en_ventana(mes, rg.ventana(r))) for r in vents if rg.ventana(r)]
                txt = "; ".join(f"{r['variedad']} {r['valor']}" for r, _ in dentro)
                rid0 = dentro[0][0]["id"]
                if all(d == "no" for _, d in dentro):
                    regla(rid0, ADVIERTE, f"siembra en mes {mes} fuera de las ventanas legales de {ctx.zona} ({txt})")
                else:
                    ok = [f"{r['variedad']}{' (parcial)' if d == 'parcial' else ''}" for r, d in dentro if d != "no"]
                    regla(rid0, PASA, f"mes {mes} dentro de la ventana legal de {', '.join(ok)} en {ctx.zona} ({txt})")
        elif mes:
            motivos.append("zona de la parcela desconocida: no se pudo verificar la ventana legal de siembra del algodón")
        if "R4S001" in R:
            if ctx.consulta.incorporar_residuos:
                regla("R4S001", ADVIERTE, "prohibido incorporar el rastrojo de algodón (RM 0251-94-AG Art. 12): "
                      "el balance de nutrientes lo calcula como retirado")
            else:
                regla("R4S001", PASA, "rastrojo de algodón se retira/destruye por norma: no aporta al suelo")
    if not motivos:
        return Veredicto("normas", PASA, "ninguna regla de Agronomía aplica")
    return Veredicto("normas", peor, "; ".join(motivos), "; ".join(dict.fromkeys(fuentes)),
                     "; ".join(dict.fromkeys(tipos)))


FILTROS_ANUALES = (f_salinidad, f_drenaje, f_pendiente, f_agua, f_sanidad, f_calendario, f_ph, f_profundidad,
                   f_presupuesto, f_normas)


CRITICOS = ("salinidad", "agua", "calendario")


def decision(veredictos: list[Veredicto]) -> str:
    """descartado si algún filtro descarta; sin_datos si 2 o más filtros críticos no son evaluables; si no, aceptado.

    `sin_datos` evita que un cultivo del que no sabemos nada aparezca como recomendado por no haber chocado con nada.
    """
    if any(v.resultado == DESCARTA for v in veredictos):
        return "descartado"
    if sum(v.filtro in CRITICOS and v.resultado == NO_EVALUABLE for v in veredictos) >= 2:
        return "sin_datos"
    return "aceptado"
