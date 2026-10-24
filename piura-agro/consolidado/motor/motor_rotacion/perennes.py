"""Módulo aparte para perennes: ¿conviene instalarlo aquí? No entran en las secuencias de anuales.

Agua anual en plena producción = Σ_mes max(0, Kc_mid × ET0 − lluvia). Kc_mid es la envolvente de todas las variantes
FAO-56 del cultivo (p. ej. cítricos según cobertura). El costo es el anual de producción; el de instalación es desconocido.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agua import FUENTE, AguaCultivo
from .catalogo import Catalogo, FAO56_URL, Ficha
from .cifra import Cifra
from .clima import ClimaEscenario
from .entradas import Consulta
from .estado_suelo import EstadoSuelo
from .filtros import (ADVIERTE, NO_EVALUABLE, Contexto, decision, f_agua, f_calendario, f_drenaje, f_pendiente,
                      f_normas, f_ph, f_presupuesto, f_profundidad, f_salinidad, f_sanidad)

FILTROS_PERENNES = (f_salinidad, f_drenaje, f_pendiente, f_agua, f_sanidad, f_calendario, f_ph, f_profundidad,
                    f_presupuesto, f_normas)


@dataclass
class EvaluacionPerenne:
    cultivo: str
    familia: str
    decision: str
    veredictos: list
    agua: AguaCultivo
    rendimiento: Cifra
    precio: Cifra
    costo_anual_ha: Cifra
    faltantes: list
    primera_produccion: Cifra | None = None

    @property
    def n_alertas(self) -> int:
        return sum(v.resultado in (ADVIERTE, NO_EVALUABLE) for v in self.veredictos)


def agua_anual(ficha: Ficha, clima: ClimaEscenario, eficiencia: Cifra) -> AguaCultivo:
    if ficha.kc is None:
        return AguaCultivo(False, notas=[f"Kc de {ficha.cultivo} desconocido: agua anual no calculable"])
    kc = ficha.kc
    mensual, lo_t, hi_t = [], 0.0, 0.0
    for i, m in enumerate(range(1, 13)):
        et0, ll = clima.cifra(m, "ET0"), clima.cifra(m, "lluvia")
        if not et0.conocido:
            return AguaCultivo(False, notas=["ET0 desconocida en el escenario"])
        lo = max(0.0, kc["mid_lo"] * et0.lo - (ll.hi if ll.conocido else 0))
        hi = kc["mid_hi"] * et0.hi
        lo_t, hi_t = lo_t + lo, hi_t + hi
        mensual.append((i, m, Cifra.rango(lo, hi, "mm", FUENTE, variable=f"riego neto mes {m}")))
    nota = f"Kc medio {kc['mid_lo']}-{kc['mid_hi']} ({kc['subtipo']}); planta adulta, año completo"
    if kc.get("no_fao56"):
        nota += f"; Kc NO es de FAO-56: {kc.get('fuente', '')} ({kc.get('notas', '')})"
    out = AguaCultivo(True, mensual=mensual)
    out.riego_neto_mm = Cifra.rango(lo_t, hi_t, "mm/año", FUENTE, notas=nota, variable="riego neto anual", url=FAO56_URL)
    out.riego_neto_m3_ha = Cifra.rango(lo_t * 10, hi_t * 10, "m3/ha/año", FUENTE, notas=nota, variable="riego neto anual")
    out.riego_bruto_m3_ha = (Cifra.rango(lo_t * 10 / eficiencia.hi, hi_t * 10 / eficiencia.lo, "m3/ha/año", FUENTE,
                                         notas=nota + "; / eficiencia", variable="riego bruto anual")
                             if eficiencia.conocido else
                             Cifra.desconocido("m3/ha/año", "riego bruto anual", "eficiencia desconocida"))
    out.notas.append("plantones y años de formación usan menos agua; no modelado")
    return out


def evaluar_perenne(ficha: Ficha, consulta: Consulta, estado: EstadoSuelo, clima: ClimaEscenario,
                    cat: Catalogo) -> EvaluacionPerenne:
    agua = agua_anual(ficha, clima, consulta.agua.eficiencia)
    costo = ficha.costo or Cifra.desconocido("PEN/ha/año", "costo de producción", f"sin costo para {ficha.cultivo}")
    perenne = Cifra(365.0, None, None, "días", "perenne: evaluación de un año de producción", "prediccion",
                    "estimado", notas="no es la vida útil", variable="periodo evaluado")
    fam_ant = cat.fichas[consulta.cultivo_anterior].familia if consulta.cultivo_anterior in cat.fichas else None
    c2 = consulta if consulta.horizonte_meses >= 12 else _con_horizonte(consulta, 12)
    from .motor import alerta_fen, zona_parcela
    zona, _ = zona_parcela(consulta, clima)
    ficha = cat.ficha(ficha.cultivo, zona)
    ctx = Contexto(ficha, c2, estado, clima, agua, perenne, list(range(1, 13)), costo, cat.reglas_sanidad,
                   cat.reglas_terreno, consulta.cultivo_anterior, fam_ant, zona, cat.reglas, alerta_fen(consulta, cat)[0])
    veredictos = [f(ctx) for f in FILTROS_PERENNES]
    faltantes = [x for v in veredictos for x in v.faltantes]
    primera = ficha.primera_produccion.get(zona or "") or ficha.primera_produccion.get("")
    faltantes += [f"costo de instalación de {ficha.cultivo}"]
    if primera is None:
        faltantes.append(f"años hasta primera cosecha de {ficha.cultivo}")
    if ficha.kc and ficha.kc.get("contraste"):
        agua.notas.append("Kc contrastado con: " + "; ".join(ficha.kc["contraste"][-4:]))
    rend = ficha.por_lugar(ficha.rendimiento, consulta.provincia, "t/ha", "rendimiento", zona)
    precio = ficha.por_lugar(ficha.precio, consulta.provincia, "PEN/kg", "precio en chacra", zona)
    return EvaluacionPerenne(ficha.cultivo, ficha.familia, decision(veredictos), veredictos, agua, rend, precio, costo,
                             list(dict.fromkeys(faltantes)), primera)


def _con_horizonte(c: Consulta, meses: int) -> Consulta:
    from dataclasses import replace
    return replace(c, horizonte_meses=meses)
