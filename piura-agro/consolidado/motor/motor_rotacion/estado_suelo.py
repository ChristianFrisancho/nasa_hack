"""Estado del suelo y del agua que se arrastra entre cosechas de una secuencia."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .cifra import Cifra, operar
from .entradas import Consulta
from .nutrientes import NUTRIENTES

FUENTE_ECE = "motor v1: FAO-29 ECe de equilibrio ≈ 1.5·ECw (fracción de lavado 15-20 %)"


@dataclass(frozen=True)
class EstadoSuelo:
    ece: Cifra
    ph: Cifra
    profundidad_cm: Cifra
    pendiente_pct: Cifra
    drenaje: str | None
    balance: dict  # nutriente -> Cifra kg/ha acumulado desde el inicio de la secuencia
    agua_neta_m3_ha: Cifra
    historial: tuple = ()
    notas: tuple = ()
    napa_m: Cifra = Cifra.desconocido("m", "profundidad de la napa freática", "no informada")

    @staticmethod
    def desde_consulta(c: Consulta) -> "EstadoSuelo":
        cero = lambda n: Cifra(0.0, None, None, "kg/ha", "motor v1: origen del balance", "prediccion", "estimado",
                               notas="balance relativo al inicio de la secuencia, no stock del suelo", variable=n)
        return EstadoSuelo(c.suelo.ece, c.suelo.ph, c.suelo.profundidad_cm, c.suelo.pendiente_pct, c.suelo.drenaje,
                           {n: cero(f"balance {n}") for n in NUTRIENTES},
                           Cifra(0.0, None, None, "m3/ha", "motor v1", "prediccion", "estimado",
                                 variable="agua neta acumulada"),
                           napa_m=c.suelo.napa_m if c.suelo.napa_m is not None else
                           Cifra.desconocido("m", "profundidad de la napa freática", "no informada"))


def actualizar_tras_cosecha(estado: EstadoSuelo, cultivo: str, leguminosa: bool, exportacion: dict,
                            riego_neto_m3_ha: Cifra | None, ecw: Cifra, fertilizacion: dict,
                            efecto_arroz: str | None = None) -> EstadoSuelo:
    """`efecto_arroz` (reglas R4R001/R4R002): 'sube' (drenaje pobre o napa < 2 m), 'posible' (no verificable),
    'lava' (drenaje bueno y napa ≥ 2 m) o None (no es arroz)."""
    notas = list(estado.notas)
    # salinidad: el riego lleva la ECe hacia 1.5·ECw; sin modelo de lavado se toma la envolvente
    if ecw.conocido and estado.ece.conocido:
        eq_lo, eq_hi = 1.5 * ecw.lo, 1.5 * ecw.hi
        ece = Cifra.rango(min(estado.ece.lo, eq_lo), max(estado.ece.hi, eq_hi), "dS/m", FUENTE_ECE,
                          notas=f"envolvente entre ECe previa ({estado.ece.texto(2)}) y equilibrio con ECw "
                                f"{ecw.texto(2)}; sin modelo de lavado ni napa", variable="ECe")
    elif ecw.conocido:
        ece = Cifra.rango(1.5 * ecw.lo, 1.5 * ecw.hi, "dS/m", FUENTE_ECE, notas="ECe inicial desconocida: "
                          "solo el equilibrio con el agua de riego", variable="ECe")
    else:
        ece = Cifra.desconocido("dS/m", "ECe", f"ECw desconocida: no se puede proyectar la ECe tras {cultivo}")
    if efecto_arroz == "sube":
        previa = estado.ece.texto(2) if estado.ece.conocido else "desconocida"
        ece = Cifra.desconocido("dS/m", "ECe", f"R4R001: tras arroz con drenaje deficiente o napa < 2 m la napa y la ECe "
                                f"suben (magnitud desconocida); al menos la ECe previa {previa}",
                                fuente="Piura Agronomía R4R001 (FAO-29 cap. 2)")
        notas.append(f"{cultivo}: ECe tras la campaña desconocida (sube, R4R001); medir antes del siguiente cultivo")
    elif efecto_arroz == "posible":
        notas.append(f"{cultivo}: napa o drenaje no verificados; la ECe puede haber subido (R4R001)")
    elif efecto_arroz == "lava":
        notas.append(f"{cultivo}: drenaje bueno y napa ≥ 2 m, la lámina puede lavar sales (R4R002; no se cuantifica)")
    if not estado.napa_m.conocido or estado.napa_m.lo < 2.0:
        if ece.conocido:
            ece = ece.con(notas=ece.notas + "; equilibrio 1.5·ECw no garantizado: napa < 2 m o desconocida (FAO-29)")
    balance = {}
    for n in NUTRIENTES:
        aporte = fertilizacion.get(n)
        ap = Cifra(float(aporte or 0), None, None, "kg/ha", "fertilización prevista ingresada" if aporte else
                   "sin aportes registrados", "medicion_local" if aporte else "prediccion", "estimado",
                   variable=f"aporte {n}")
        if n == "N" and leguminosa:
            balance[n] = Cifra.desconocido("kg/ha", "balance N", f"{cultivo} es leguminosa: fijación de N desconocida")
            continue
        salida = operar("-", ap, exportacion.get(n) or Cifra.desconocido("kg/ha", f"exportación {n}"),
                        "kg/ha", f"balance {n}", "aporte − exportación")
        balance[n] = operar("+", estado.balance[n], salida, "kg/ha", f"balance {n}", "balance previo + campaña")
        if not aporte:
            notas.append(f"{cultivo}: sin aportes de {n} registrados")
    agua = (operar("+", estado.agua_neta_m3_ha, riego_neto_m3_ha, "m3/ha", "agua neta acumulada", "suma de riego neto")
            if riego_neto_m3_ha is not None else
            Cifra.desconocido("m3/ha", "agua neta acumulada", f"riego de {cultivo} desconocido"))
    return replace(estado, ece=ece, balance=balance, agua_neta_m3_ha=agua,
                   historial=estado.historial + (cultivo,), notas=tuple(dict.fromkeys(notas)))
