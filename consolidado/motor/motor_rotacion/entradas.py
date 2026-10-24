"""Consulta del usuario desde JSON. Ningún campo ausente se rellena con un número: queda `desconocido`."""
from __future__ import annotations

from dataclasses import dataclass, field

from .cifra import Cifra
from .clima import centroide, validar_escenario
from .validacion import ZONAS

CE_METODOS = ("pasta_saturada", "ce_extracto_no_declarado")
UNIDADES_SUELO = {"ece_ds_m": "dS/m", "ph": "pH", "profundidad_cm": "cm", "pendiente_pct": "%"}
DRENAJES = ("bueno", "moderado", "pobre")


def cifra_entrada(x, unidad: str, variable: str, fuente: str = "dato ingresado por el usuario") -> Cifra:
    """número -> observado; [a, b] -> estimado (rango); dict con campos de contrato; None -> desconocido."""
    if x is None:
        return Cifra.desconocido(unidad, variable, f"{variable} no informado")
    if isinstance(x, (int, float)):
        return Cifra(float(x), None, None, unidad, fuente, "medicion_local", "observado", variable=variable,
                     notas="valor puntual ingresado; sin rango informado")
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return Cifra.rango(float(x[0]), float(x[1]), unidad, fuente, "medicion_local", "estimado",
                           "rango ingresado por el usuario", variable)
    if isinstance(x, dict):
        v = x.get("valor")
        lo, hi = x.get("valor_min"), x.get("valor_max")
        if v is None and lo is not None and hi is not None:
            v = (lo + hi) / 2
        if v is None:
            return Cifra.desconocido(unidad, variable, x.get("notas", ""))
        return Cifra(float(v), lo, hi, x.get("unidad", unidad), x.get("fuente", fuente),
                     x.get("tipo_evidencia", "medicion_local"), x.get("estado", "estimado"),
                     x.get("url_o_doi", ""), x.get("notas", ""), variable)
    raise ValueError(f"formato no reconocido para {variable}: {x!r}")


@dataclass
class Suelo:
    ece: Cifra
    ph: Cifra
    profundidad_cm: Cifra
    pendiente_pct: Cifra
    drenaje: str | None  # bueno | moderado | pobre | None (desconocido)
    napa_m: Cifra = None  # profundidad de la napa freática (m); desconocida si no se informa
    ce_metodo: str = "pasta_saturada"  # o 'ce_extracto_no_declarado' (CONTRATO.md): no se trata como ECe sin avisar
    psi_pct: Cifra = None  # porcentaje de sodio intercambiable (PSI/ESP), si se midió


@dataclass
class Agua:
    m3_por_mes: dict  # mes -> Cifra (m3 disponibles en el mes para toda la parcela)
    ecw: Cifra
    eficiencia: Cifra
    intervalo_turno_dias: Cifra


@dataclass
class Consulta:
    lat: float
    lon: float
    area_ha: Cifra
    provincia: str | None
    suelo: Suelo
    agua: Agua
    presupuesto_pen: Cifra
    cultivo_anterior: str | None
    escenario: str
    mes_siembra: int
    horizonte_meses: int
    plagas_presentes: list[str] = field(default_factory=list)
    candidatos: list[str] | None = None
    incorporar_residuos: bool | None = None
    fertilizacion_prevista: dict = field(default_factory=dict)  # 'N'|'P2O5'|'K2O' -> kg/ha
    zona: str | None = None  # zona CONTRATO.md dada por el usuario (alto_piura, medio_piura, bajo_piura, ...)
    distrito: str | None = None  # si no hay zona, la zona se deduce de datos_repo/distrito_zona.csv
    alerta_enfen: bool | None = None  # None = se usa el comunicado ENFEN cargado (R4A025) si está vigente

    @staticmethod
    def desde_dict(d: dict) -> "Consulta":
        par = d.get("parcela", {})
        if "punto" in par:
            lat, lon = par["punto"]
        elif "poligono" in par:
            lat, lon = centroide(par["poligono"])
        else:
            raise ValueError("parcela necesita 'punto' [lat, lon] o 'poligono' [[lat, lon], ...]")
        s = d.get("suelo", {}) or {}
        drenaje = s.get("drenaje")
        if drenaje is not None and drenaje not in DRENAJES:
            raise ValueError(f"drenaje debe ser uno de {DRENAJES} o null")
        suelo = Suelo(cifra_entrada(s.get("ece_ds_m"), "dS/m", "ECe"),
                      cifra_entrada(s.get("ph"), "pH", "pH"),
                      cifra_entrada(s.get("profundidad_cm"), "cm", "profundidad efectiva"),
                      cifra_entrada(s.get("pendiente_pct"), "%", "pendiente"), drenaje,
                      cifra_entrada(s.get("napa_m"), "m", "profundidad de la napa freática"),
                      s.get("ce_metodo") or (s["ece_ds_m"].get("metodo") if isinstance(s.get("ece_ds_m"), dict)
                                             and s["ece_ds_m"].get("metodo") in CE_METODOS else None)
                      or "pasta_saturada",
                      cifra_entrada(s.get("psi_pct"), "%", "PSI (sodio intercambiable)"))
        if suelo.ce_metodo not in CE_METODOS:
            raise ValueError(f"suelo.ce_metodo debe ser uno de {CE_METODOS}")
        a = d.get("agua", {}) or {}
        m3 = a.get("m3_por_mes")
        if isinstance(m3, dict):
            meses = {int(k): cifra_entrada(v, "m3/mes", f"agua mes {k}") for k, v in m3.items()}
            meses = {m: meses.get(m, Cifra.desconocido("m3/mes", f"agua mes {m}", "mes no informado"))
                     for m in range(1, 13)}
        else:
            meses = {m: cifra_entrada(m3, "m3/mes", f"agua mes {m}") for m in range(1, 13)}
        agua = Agua(meses, cifra_entrada(a.get("ecw_ds_m"), "dS/m", "ECw"),
                    cifra_entrada(a.get("eficiencia"), "fracción", "eficiencia de riego"),
                    cifra_entrada(a.get("intervalo_turno_dias"), "días", "intervalo entre turnos"))
        esc = d.get("escenario", "sin_el_nino")
        validar_escenario(esc)
        mes = int(d.get("mes_siembra", 1))
        if not 1 <= mes <= 12:
            raise ValueError("mes_siembra entre 1 y 12")
        zona = par.get("zona")
        if zona is not None and zona not in ZONAS:
            raise ValueError(f"parcela.zona debe ser una de {[z for z in ZONAS if z]} o null")
        return Consulta(lat=float(lat), lon=float(lon),
                        area_ha=cifra_entrada(par.get("area_ha"), "ha", "área"),
                        provincia=par.get("provincia"), suelo=suelo, agua=agua,
                        presupuesto_pen=cifra_entrada(d.get("presupuesto_pen"), "PEN", "presupuesto"),
                        cultivo_anterior=d.get("cultivo_anterior"), escenario=esc, mes_siembra=mes,
                        horizonte_meses=int(d.get("horizonte_meses", 12)),
                        plagas_presentes=list(d.get("plagas_presentes", [])),
                        candidatos=d.get("candidatos"), incorporar_residuos=d.get("incorporar_residuos"),
                        fertilizacion_prevista=d.get("fertilizacion_prevista", {}) or {},
                        zona=zona or None, distrito=par.get("distrito") or None,
                        alerta_enfen=d.get("alerta_enfen"))
