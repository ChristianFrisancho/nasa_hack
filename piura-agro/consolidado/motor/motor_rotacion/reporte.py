"""Salida JSON (dict) y texto legible en español."""
from __future__ import annotations

from .cifra import Cifra
from .filtros import DESCARTA


def _c(x):
    if isinstance(x, Cifra):
        return x.a_dict()
    if isinstance(x, dict):
        return {k: _c(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_c(v) for v in x]
    if hasattr(x, "a_dict"):
        return x.a_dict()
    return x


def _agua_dict(a):
    if a is None or not a.disponible:
        return {"disponible": False, "notas": a.notas if a else []}
    return {"disponible": True, "etapas": _c(a.etapas),
            "riego_neto_mensual_mm": [{"mes": m, "cifra": c.a_dict()} for _, m, c in a.mensual],
            "etc_total": _c(a.etc_total), "riego_neto_mm": _c(a.riego_neto_mm),
            "riego_neto_m3_ha": _c(a.riego_neto_m3_ha), "riego_bruto_m3_ha": _c(a.riego_bruto_m3_ha), "notas": a.notas}


def estado_a_dict(e):
    return {"ECe": _c(e.ece), "pH": _c(e.ph), "profundidad_cm": _c(e.profundidad_cm), "drenaje": e.drenaje or
            "desconocido", "balance_kg_ha": _c(e.balance), "agua_neta_acumulada_m3_ha": _c(e.agua_neta_m3_ha),
            "historial": list(e.historial), "notas": list(e.notas)}


def evaluacion_a_dict(e) -> dict:
    return {"cultivo": e.cultivo, "familia": e.familia, "decision": e.decision, "mes_siembra": e.mes_siembra,
            "motivos_descarte": e.motivos_descarte(), "veredictos": [v.a_dict() for v in e.veredictos],
            "duracion": _c(e.duracion), "agua": _agua_dict(e.agua),
            "nutrientes": {"absorcion": _c(e.nutrientes.absorcion), "exportacion": _c(e.nutrientes.exportacion),
                           "residuo_devuelto": _c(e.nutrientes.residuo_devuelto), "notas": e.nutrientes.notas},
            "rendimiento": _c(e.rendimiento), "precio_chacra": _c(e.precio), "costo_ha": _c(e.costo_ha),
            "margen_ha": _c(e.margen_ha),
            "deja_en_suelo": [{"concepto": k, "valor": _c(v)} for k, v in e.deja_en_suelo],
            "datos_faltantes": e.faltantes,
            "estado_tras_cosecha": estado_a_dict(e.estado_tras_cosecha) if e.estado_tras_cosecha else None}


def perenne_a_dict(p) -> dict:
    return {"cultivo": p.cultivo, "familia": p.familia, "decision": p.decision,
            "veredictos": [v.a_dict() for v in p.veredictos], "agua_anual": _agua_dict(p.agua),
            "rendimiento": _c(p.rendimiento), "precio_chacra": _c(p.precio), "costo_anual_ha": _c(p.costo_anual_ha),
            "anios_a_primera_produccion": _c(p.primera_produccion), "datos_faltantes": p.faltantes}


def resultado_a_dict(r) -> dict:
    c = r.consulta
    return {"motor": "motor_rotacion v1", "zona_clima": {"zona": r.clima.zona.nombre, "distancia_km": r.clima.zona.distancia_km,
                                                    "escenario": r.clima.escenario, "anios": r.clima.anios},
            "parcela": {"lat": c.lat, "lon": c.lon, "provincia": c.provincia, "area_ha": _c(c.area_ha)},
            "mensaje": r.mensaje, "ranking": r.ranking,
            "aceptados": [evaluacion_a_dict(e) for e in sorted(
                (e for e in r.evaluaciones if e.decision == "aceptado"), key=lambda e: r.ranking.index(e.cultivo))],
            "descartados": [{"cultivo": e.cultivo, "motivos": e.motivos_descarte(),
                             "veredictos": [v.a_dict() for v in e.veredictos]}
                            for e in r.evaluaciones if e.decision == "descartado"],
            "sin_datos_suficientes": [{"cultivo": e.cultivo, "datos_faltantes": e.faltantes,
                                       "veredictos": [v.a_dict() for v in e.veredictos]}
                                      for e in r.evaluaciones if e.decision == "sin_datos"],
            "perennes": [perenne_a_dict(p) for p in r.perennes],
            "avisos": r.avisos, "agua_usada": {"ECw": _c(c.agua.ecw)}, "pendiente_usada": _c(c.suelo.pendiente_pct),
            "datos_faltantes_globales": r.faltantes_globales}


def secuencia_a_dict(s) -> dict:
    return {"cultivos": list(s.cultivos), "viable": s.viable, "motivo": s.motivo, "alertas": s.alertas,
            "meses_usados": _c(s.meses_usados), "cabe_en_horizonte": s.cabe_en_horizonte,
            "margen_total_ha": _c(s.margen_total_ha), "agua_neta_total_m3_ha": _c(s.agua_neta_total_m3_ha),
            "pasos": [{"cultivo": p.cultivo, "mes_siembra": p.mes_siembra, "decision": p.evaluacion.decision,
                       "alertas": p.evaluacion.n_alertas} for p in s.pasos],
            "estado_final": estado_a_dict(s.estado_final)}


# ------------------------------------------------------------------------------------------- texto
MARCA = {"pasa": "ok", "advierte": "!", "descarta": "X", "no_evaluable": "?"}


def resultado_a_texto(r, max_aceptados: int = 5) -> str:
    c, L = r.consulta, []
    L.append(f"MOTOR DE ROTACIÓN v1 · zona climática {r.clima.zona.nombre} ({r.clima.zona.distancia_km} km) · "
             f"escenario {r.clima.escenario} ({len(r.clima.anios)} años: {', '.join(map(str, r.clima.anios[:8]))}"
             f"{'…' if len(r.clima.anios) > 8 else ''})")
    L.append(f"Parcela {c.lat:.3f}, {c.lon:.3f} · área {c.area_ha.texto(2)} · ECe {c.suelo.ece.texto(2)} · "
             f"ECw {c.agua.ecw.texto(2)} · pH {c.suelo.ph.texto(1)} · drenaje {c.suelo.drenaje or 'desconocido'} · "
             f"anterior {c.cultivo_anterior or 'desconocido'} · siembra mes {c.mes_siembra}")
    L.append(f"Zona CONTRATO: {r.zona or 'desconocida'} ({r.zona_origen}) · pendiente usada "
             f"{c.suelo.pendiente_pct.texto(1) if c.suelo.pendiente_pct else 'desconocida'}")
    L.append("")
    L.append(r.mensaje)
    if r.avisos:
        L.append("AVISOS:")
        L += [f" * {a}" for a in r.avisos]
    for i, nombre in enumerate(r.ranking[:max_aceptados], 1):
        e = next(x for x in r.evaluaciones if x.cultivo == nombre)
        L.append("")
        L.append(f"{i}. {e.cultivo.upper()} ({e.familia}) · advertencias {e.n_advierte} · no evaluables {e.n_alertas - e.n_advierte}")
        L.append(f"   Duración: {e.duracion.texto(0)} [{e.duracion.tipo_evidencia}]")
        if e.agua and e.agua.disponible:
            et = " | ".join(f"{k} {v['riego_neto_mm'].texto(0)}" for k, v in e.agua.etapas.items())
            L.append(f"   Riego neto por etapa: {et}")
            L.append(f"   Riego neto ciclo: {e.agua.riego_neto_m3_ha.texto(0)} · bruto: {e.agua.riego_bruto_m3_ha.texto(0)}")
            for n in e.agua.notas:
                L.append(f"   Nota agua: {n}")
        else:
            L.append("   Agua: desconocida (" + "; ".join(e.agua.notas if e.agua else []) + ")")
        nut = e.nutrientes
        L.append("   Absorción N/P2O5/K2O: " + " / ".join(nut.absorcion[n].texto(0) for n in ("N", "P2O5", "K2O")))
        L.append("   Exportación N/P2O5/K2O: " + " / ".join(nut.exportacion[n].texto(0) for n in ("N", "P2O5", "K2O")))
        L.append(f"   Rendimiento: {e.rendimiento.texto(2)} [{e.rendimiento.tipo_evidencia}] · precio "
                 f"{e.precio.texto(2)} · costo {e.costo_ha.texto(0)} [{e.costo_ha.tipo_evidencia}] · margen "
                 f"{e.margen_ha.texto(0)}" + (f" [{texto_mc(e.margen_mc)}]" if e.margen_mc else ""))
        deja = [f"{k} {v.texto(1)}" if isinstance(v, Cifra) else v for k, v in e.deja_en_suelo]
        L.append("   Deja en el suelo: " + "; ".join(deja))
        for v in e.veredictos:
            if v.resultado != "pasa":
                L.append(f"   [{MARCA[v.resultado]}] {v.filtro}: {v.motivo}")
        if e.faltantes:
            L.append("   Datos que pueden cambiar la recomendación: " + "; ".join(e.faltantes[:8]))
    if len(r.ranking) > max_aceptados:
        L.append(f"\nOtros aceptados: {', '.join(r.ranking[max_aceptados:])}")
    sd = [e for e in r.evaluaciones if e.decision == "sin_datos"]
    if sd:
        L.append("\nSIN DATOS SUFICIENTES (no descartados, tampoco recomendados)")
        for e in sd:
            L.append(f" - {e.cultivo}: falta " + "; ".join(e.faltantes[:4]))
    desc = [e for e in r.evaluaciones if e.decision == "descartado"]
    if desc:
        L.append("\nDESCARTADOS")
        for e in desc:
            L.append(f" - {e.cultivo}: " + " | ".join(e.motivos_descarte()))
    if r.perennes:
        L.append("\nPERENNES (módulo aparte, un año en producción)")
        for p in r.perennes:
            mot = [f"{v.filtro}: {v.motivo}" for v in p.veredictos if v.resultado == DESCARTA]
            agua = p.agua.riego_neto_m3_ha.texto(0) if p.agua.disponible else "agua desconocida"
            pp = (f" · 1.ª producción {p.primera_produccion.texto(2)} [{p.primera_produccion.tipo_evidencia}]"
                  if p.primera_produccion else "")
            L.append(f" - {p.cultivo}: {p.decision} · riego neto {agua} · costo anual {p.costo_anual_ha.texto(0)} "
                     f"[{p.costo_anual_ha.tipo_evidencia}]{pp} · alertas {p.n_alertas}"
                     + (f" · {' | '.join(mot)}" if mot else ""))
    if r.faltantes_globales:
        L.append("\nDATOS QUE FALTAN (de más a menos cultivos afectados):")
        L += [f" - {f}" for f in r.faltantes_globales[:12]]
    return "\n".join(L)


def _pen(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def texto_mc(mc: dict | None) -> str:
    """P10/P50/P90 y probabilidad de margen negativo (Monte Carlo, incertidumbre.py) o 'no calculable'."""
    if not mc:
        return "P10/P(margen<0) no calculables (falta algún costo, precio o rendimiento)"
    return (f"P10 {_pen(mc['p10'])} · P50 {_pen(mc['p50'])} · P90 {_pen(mc['p90'])} PEN/ha · "
            f"P(margen<0) {_prob(mc['prob_negativo'])}")


def _prob(p: float) -> str:
    if p == 0:
        from .incertidumbre import N_MUESTRAS
        return f"0 de {N_MUESTRAS} simulaciones (no es imposible: supuesto de factores independientes)"
    return "<1 %" if p < 0.005 else f"{p * 100:.0f} %"


def secuencias_a_texto(secs, n: int = 5) -> str:
    if not secs:
        return "SECUENCIAS: ninguna (no hay cultivos anuales aceptados para combinar)"
    L = [f"SECUENCIAS ({len(secs)} comparadas; se muestran {min(n, len(secs))})",
         "   orden: viables y que caben → sin pasos 'probable no apto' → mayor P10 del margen (Monte Carlo, "
         "redondeado a 100 PEN) → menos agua → menor ECe final → mejor balance P+K → menos alertas"]
    for s in secs[:n]:
        e = s.estado_final
        L.append(f" - {' → '.join(s.cultivos)}: {'viable' if s.viable else 'NO viable'} · meses {s.meses_usados.texto(1)} "
                 f"(cabe: {s.cabe_en_horizonte}) · margen {s.margen_total_ha.texto(0)} [{texto_mc(s.margen_mc)}]"
                 + (f" · {s.graves} paso(s) probable no apto" if s.graves else "") + " · agua neta "
                 f"{s.agua_neta_total_m3_ha.texto(0)} · ECe final {e.ece.texto(2)} · balance P2O5 "
                 f"{e.balance['P2O5'].texto(0)} · K2O {e.balance['K2O'].texto(0)} · N {e.balance['N'].texto(0)}"
                 + (f" · {s.motivo}" if s.motivo else ""))
    return "\n".join(L)


def escenarios_a_dict(escs) -> list:
    out = []
    for e in escs:
        viables = [s for s in e.secuencias if s.viable]
        out.append({"etiqueta": e.etiqueta, "ecw_ds_m": e.ecw, "es_dato": False,
                    "dato_que_falta": "CE del agua de riego (ECw) de la parcela",
                    "ranking_anuales": e.resultado.ranking,
                    "sin_datos": [x.cultivo for x in e.resultado.evaluaciones if x.decision == "sin_datos"],
                    "descartados": [x.cultivo for x in e.resultado.evaluaciones if x.decision == "descartado"],
                    "secuencias_viables": len(viables), "secuencias_comparadas": len(e.secuencias),
                    "secuencias": [secuencia_a_dict(s) for s in e.secuencias[:5]]})
    return out


def escenarios_a_texto(escs, base_secs=None, n: int = 3) -> str:
    if not escs:
        return ""
    L = ["ESCENARIOS DE AGUA (la ECw de la parcela es DESCONOCIDA; estos valores son ESCENARIOS, no datos)",
         "   DATO QUE FALTA: CE del agua de riego (ECw, dS/m) de su canal o pozo. Con ese dato el motor usa uno solo.",
         "   Proyección de ECe tras cada cosecha: envolvente entre la ECe previa y 1,5·ECw (FAO-29, régimen permanente)."]
    if base_secs is not None:
        nb = sum(s.viable for s in base_secs)
        L.append(f"   Sin escenario (ECw desconocida o solo valor de zona): {nb} de {len(base_secs)} secuencias viables")
    for e in escs:
        r, viables = e.resultado, [s for s in e.secuencias if s.viable]
        L.append(f" [{e.etiqueta}] anuales aceptados {len(r.ranking)} · orden: {', '.join(r.ranking[:6]) or 'ninguno'}"
                 f" · secuencias viables {len(viables)} de {len(e.secuencias)}")
        for s in viables[:n]:
            L.append(f"     - {' → '.join(s.cultivos)}: P10 {('%s PEN/ha' % _pen(s.margen_mc['p10'])) if s.margen_mc else 'no calculable'}"
                     f" · P(margen<0) {_prob(s.margen_mc['prob_negativo']) if s.margen_mc else '?'}"
                     f" · ECe final {s.estado_final.ece.texto(2)}"
                     + (f" · {s.graves} paso(s) probable no apto" if s.graves else ""))
        if not viables:
            mot = e.secuencias[0].motivo if e.secuencias else "sin anuales aceptados"
            L.append(f"     ninguna viable; primera razón: {mot[:220]}")
    rk = [tuple(e.resultado.ranking[:3]) for e in escs]
    L.append("   El orden de los 3 primeros " + ("NO cambia" if len(set(rk)) == 1 else "CAMBIA") +
             " entre escenarios; la viabilidad de las secuencias: " +
             " / ".join(f"{e.ecw:g}→{sum(s.viable for s in e.secuencias)}" for e in escs))
    return "\n".join(L)


def _exceso_agua(r) -> list[str]:
    return [e.cultivo for e in r.evaluaciones for v in e.veredictos
            if v.filtro == "calendario" and v.motivo.startswith("exceso de agua")]


def escenarios_clima_a_dict(ec) -> dict:
    out = []
    for esc, r in ec.resultados.items():
        acept = sorted((e for e in r.evaluaciones if e.decision == "aceptado"), key=lambda e: r.ranking.index(e.cultivo))
        out.append({"escenario": esc, "anios_campania": r.clima.anios, "fuente_lluvia": r.clima.fuente_lluvia,
                    "primero": ec.primeros[esc],
                    "orden": [{"cultivo": e.cultivo, "p10": e.margen_mc["p10"] if e.margen_mc else None,
                               "p50": e.margen_mc["p50"] if e.margen_mc else None,
                               "probablemente_no_apto": bool(e.n_graves)} for e in acept],
                    "aceptados": [e.cultivo for e in acept],
                    "descartados": [{"cultivo": e.cultivo, "motivos": e.motivos_descarte()}
                                    for e in r.evaluaciones if e.decision == "descartado"],
                    "sin_datos": [e.cultivo for e in r.evaluaciones if e.decision == "sin_datos"],
                    "exceso_de_agua": _exceso_agua(r)})
    return {"escenarios": out, "primer_lugar_cambia": ec.primer_lugar_cambia, "contexto_icen": ec.contexto_icen}


def escenarios_clima_a_texto(ec, n: int = 5) -> str:
    d = escenarios_clima_a_dict(ec)
    L = ["ESCENARIOS CLIMÁTICOS (clasificación ICEN de la campaña ago-jul; lluvia PISCOp de la zona; ET0 y "
         "temperatura NASA POWER en las mismas campañas)"]
    for x in d["escenarios"]:
        L.append(f"  {x['escenario']} ({len(x['anios_campania'])} campañas: {', '.join(map(str, x['anios_campania']))}; "
                 f"lluvia {x['fuente_lluvia']})")
        if not x["orden"]:
            L.append("     ningún cultivo anual pasa los filtros duros")
        for i, o in enumerate(x["orden"][:n], 1):
            p = (f"P10 {_pen(o['p10'])} / P50 {_pen(o['p50'])} PEN/ha" if o["p10"] is not None
                 else "P10/P50 no calculables")
            L.append(f"     {i}. {o['cultivo']}: {p}" + (" (PROBABLEMENTE NO APTO)" if o["probablemente_no_apto"] else ""))
        desc = ", ".join(z["cultivo"] for z in x["descartados"]) or "ninguno"
        L.append(f"     aceptados {len(x['aceptados'])}, descartados {len(x['descartados'])} ({desc})"
                 + (f", sin datos {len(x['sin_datos'])}" if x["sin_datos"] else ""))
        if x["exceso_de_agua"]:
            L.append(f"     exceso de agua (lluvia PISCOp mediana > ET0) en el ciclo de: {', '.join(x['exceso_de_agua'])}")
    seq = " → ".join(f"{x['escenario']}: {x['primero'] or 'ninguno'}" for x in d["escenarios"])
    if d["primer_lugar_cambia"]:
        L.append(f"  El primer lugar cambia entre escenarios ({seq}).")
    else:
        L.append(f"  El primer lugar no cambia entre escenarios ({seq}).")
    if d["contexto_icen"]:
        L.append(f"  Aviso (contexto, no regla): {d['contexto_icen']}")
    return "\n".join(L)
