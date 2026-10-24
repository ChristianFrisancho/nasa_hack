"""Demanda de agua FAO-56: ETc = Kc × ET0 con curva de Kc lineal por etapa, sobre clima mensual del escenario.

Rango de cada cifra = combinación de extremos: duración de etapas (mín/máx de análogos), Kc (mín/máx de tabla),
ET0 (p10/p90 del escenario). Lluvia efectiva acotada entre 0 y la lluvia p90 del mes, por eso el riego neto
sale como intervalo ancho: no se usa una fracción efectiva fija que parezca exacta.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from .catalogo import ETAPAS, FAO56_URL, Ficha
from .cifra import Cifra
from .clima import ClimaEscenario

DIAS_MES = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
FUENTE = "motor v1: FAO-56 ETc = Kc×ET0 (Kc lineal por etapa); ET0 NASA POWER; Kc y etapas FAO-56"


def _calendario(mes_inicio: int, n_dias: int) -> list[int]:
    """Mes calendario (1-12) de cada día del ciclo, empezando el día 1 de mes_inicio. Año de 365 días."""
    meses = []
    m, d = mes_inicio, 0
    while len(meses) < n_dias:
        meses.append(m)
        d += 1
        if d >= DIAS_MES[m - 1]:
            m, d = m % 12 + 1, 0
    return meses


def _kc_diario(kc: dict, etapas: dict, mid: float, end: float) -> list[tuple[str, float]]:
    out = []
    li, ld, lm, ll = (round(etapas[e]) for e in ETAPAS)
    ini = kc["ini"]
    out += [("inicial", ini)] * li
    out += [("desarrollo", ini + (mid - ini) * (i + 1) / max(ld, 1)) for i in range(ld)]
    out += [("media", mid)] * lm
    out += [("final", mid + (end - mid) * (i + 1) / max(ll, 1)) for i in range(ll)]
    return out


@dataclass
class AguaCultivo:
    disponible: bool
    etapas: dict = field(default_factory=dict)  # etapa -> {dias, ETc_mm, lluvia_mm, riego_neto_mm}
    mensual: list = field(default_factory=list)  # [(orden, mes, Cifra riego neto mm)]
    etc_total: Cifra | None = None
    riego_neto_mm: Cifra | None = None
    riego_neto_m3_ha: Cifra | None = None
    riego_bruto_m3_ha: Cifra | None = None
    duracion_dias: Cifra | None = None
    notas: list = field(default_factory=list)


def demanda_agua(ficha: Ficha, clima: ClimaEscenario, mes_siembra: int, eficiencia: Cifra) -> AguaCultivo:
    if ficha.kc is None or ficha.etapas is None:
        falta = "Kc" if ficha.kc is None else "duración por etapa"
        return AguaCultivo(False, notas=[f"{falta} desconocido para {ficha.cultivo}: demanda de agua no calculable"])
    kc = ficha.kc
    variantes_et = ("lo", "hi")
    acum_etapa: dict[str, dict[str, list[float]]] = {e: {"dias": [], "etc": [], "lluvia": [], "neto": []} for e in ETAPAS}
    acum_mes: dict[tuple[int, int], list[float]] = {}
    totales = {"etc": [], "neto": [], "dias": []}
    falta_clima = False
    for dur, (mid, end), et in itertools.product((0, 1), ((kc["mid_lo"], kc["end_lo"]), (kc["mid_hi"], kc["end_hi"])),
                                                 variantes_et):
        etapas = {e: ficha.etapas[e][dur] for e in ETAPAS}
        serie = _kc_diario(kc, etapas, mid, end)
        meses = _calendario(mes_siembra, len(serie))
        por_etapa = {e: {"etc": 0.0, "lluvia": 0.0, "neto": 0.0, "dias": 0} for e in ETAPAS}
        por_mes: dict[tuple[int, int], float] = {}
        orden, mes_prev = 0, meses[0] if meses else mes_siembra
        for (etapa, k), m in zip(serie, meses):
            if m != mes_prev:
                orden, mes_prev = orden + 1, m
            et0 = clima.cifra(m, "ET0")
            ll = clima.cifra(m, "lluvia")
            if not et0.conocido:
                falta_clima = True
                continue
            et0_d = (et0.lo if et == "lo" else et0.hi) / DIAS_MES[m - 1]
            # caso bajo de riego: ET0 bajo y toda la lluvia p90 efectiva; caso alto: ET0 alto y lluvia no efectiva
            lluvia_d = ((ll.hi if ll.conocido else 0.0) / DIAS_MES[m - 1]) if et == "lo" else 0.0
            etc = k * et0_d
            neto = max(0.0, etc - lluvia_d)
            pe = por_etapa[etapa]
            pe["etc"] += etc
            pe["lluvia"] += (ll.hi if ll.conocido else 0.0) / DIAS_MES[m - 1]
            pe["neto"] += neto
            pe["dias"] += 1
            por_mes[(orden, m)] = por_mes.get((orden, m), 0.0) + neto
        for e in ETAPAS:
            for k2 in ("dias", "etc", "lluvia", "neto"):
                acum_etapa[e][k2].append(por_etapa[e][k2])
        for key, v in por_mes.items():
            acum_mes.setdefault(key, []).append(v)
        totales["etc"].append(sum(p["etc"] for p in por_etapa.values()))
        totales["neto"].append(sum(p["neto"] for p in por_etapa.values()))
        totales["dias"].append(len(serie))
    if falta_clima:
        return AguaCultivo(False, notas=["ET0 desconocida en algún mes del escenario: demanda no calculable"])

    def rng(xs, unidad, var, notas=""):
        return Cifra.rango(min(xs), max(xs), unidad, FUENTE, "prediccion", "estimado",
                           notas or f"Kc {kc['subtipo']} ({kc['fuente']}); etapas FAO-56 análogas", var, FAO56_URL)

    out = AguaCultivo(True)
    for e in ETAPAS:
        a = acum_etapa[e]
        out.etapas[e] = {
            "dias": rng(a["dias"], "días", f"duración etapa {e}"),
            "ETc_mm": rng(a["etc"], "mm", f"ETc etapa {e}"),
            "lluvia_p90_mm": rng(a["lluvia"], "mm", f"lluvia p90 etapa {e}", "lluvia p90 del escenario; "
                                 "techo de la lluvia efectiva"),
            "riego_neto_mm": rng(a["neto"], "mm", f"riego neto etapa {e}"),
        }
    out.mensual = [(o, m, rng([*v, 0.0] if len(v) < 8 else v, "mm", f"riego neto mes {m}",
                              "mes cubierto solo por algunas variantes de duración" if len(v) < 8 else ""))
                   for (o, m), v in sorted(acum_mes.items())]
    out.etc_total = rng(totales["etc"], "mm", "ETc ciclo")
    out.riego_neto_mm = rng(totales["neto"], "mm", "riego neto ciclo")
    out.riego_neto_m3_ha = Cifra.rango(out.riego_neto_mm.lo * 10, out.riego_neto_mm.hi * 10, "m3/ha", FUENTE,
                                       notas="1 mm = 10 m3/ha", variable="riego neto ciclo")
    if eficiencia.conocido:
        out.riego_bruto_m3_ha = Cifra.rango(out.riego_neto_m3_ha.lo / eficiencia.hi,
                                            out.riego_neto_m3_ha.hi / eficiencia.lo, "m3/ha", FUENTE,
                                            notas=f"riego neto / eficiencia ({eficiencia.texto(2)}, "
                                                  f"{eficiencia.tipo_evidencia})", variable="riego bruto ciclo")
    else:
        out.riego_bruto_m3_ha = Cifra.desconocido("m3/ha", "riego bruto ciclo",
                                                  "eficiencia de riego no informada; solo se reporta riego neto")
    out.duracion_dias = rng(totales["dias"], "días", "duración ciclo")
    if ficha.cultivo == "arroz":
        out.notas.append("arroz: no incluye percolación, lámina de inundación ni preparación (pudelado); "
                         "el riego real es mayor: tomar la cifra como cota inferior")
    return out
