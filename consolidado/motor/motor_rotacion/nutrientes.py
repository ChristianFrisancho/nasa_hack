"""Absorción y exportación de N, P2O5 y K2O por rendimiento. Coeficientes de extracción (kg/t), nunca dosis de abonado."""
from __future__ import annotations

from dataclasses import dataclass, field

from .catalogo import Ficha
from .cifra import Cifra, operar

NUTRIENTES = ("N", "P2O5", "K2O")


@dataclass
class Nutrientes:
    absorcion: dict = field(default_factory=dict)  # kg/ha
    exportacion: dict = field(default_factory=dict)  # kg/ha que salen de la parcela
    residuo_devuelto: dict = field(default_factory=dict)  # kg/ha que quedan si se incorporan restos
    notas: list = field(default_factory=list)


def balance_nutrientes(ficha: Ficha, rendimiento: Cifra, incorporar_residuos: bool | None) -> Nutrientes:
    out = Nutrientes()
    for n in NUTRIENTES:
        ab = ficha.absorcion.get(n)
        ex = ficha.exportacion.get(n)
        ex_res = ficha.exportacion_residuo.get(n)
        out.absorcion[n] = (operar("*", rendimiento, ab, "kg/ha", f"absorción {n}", f"rendimiento × absorción {n}/t")
                            if ab else Cifra.desconocido("kg/ha", f"absorción {n}", "sin coeficiente de absorción"))
        ex_prod = (operar("*", rendimiento, ex, "kg/ha", f"exportación {n}", f"rendimiento × exportación {n}/t")
                   if ex else None)
        res = (operar("*", rendimiento, ex_res, "kg/ha", f"residuo {n}", f"rendimiento × {n}/t en restos")
               if ex_res else None)
        if res is None and ex_prod is not None and out.absorcion[n].conocido and ex_prod.conocido:
            res = operar("-", out.absorcion[n], ex_prod, "kg/ha", f"residuo {n}", "absorción − exportación")
            if res.lo < 0:
                res = Cifra.rango(0, max(res.hi, 0), "kg/ha", res.fuente, notas=res.notas + "; recortado a ≥0 "
                                  "(coeficientes de fuentes distintas)", variable=f"residuo {n}")
        out.residuo_devuelto[n] = res or Cifra.desconocido("kg/ha", f"residuo {n}", "sin coeficientes de restos")
        if ex_prod is None:
            out.exportacion[n] = Cifra.desconocido("kg/ha", f"exportación {n}",
                                                   "sin coeficiente de exportación del producto")
        elif incorporar_residuos is True or not out.residuo_devuelto[n].conocido:
            out.exportacion[n] = ex_prod
        elif incorporar_residuos is False:
            out.exportacion[n] = operar("+", ex_prod, out.residuo_devuelto[n], "kg/ha", f"exportación {n}",
                                        "producto + restos retirados")
        else:  # destino de restos desconocido: rango entre incorporar y retirar
            total = operar("+", ex_prod, out.residuo_devuelto[n], "kg/ha", f"exportación {n}", "producto + restos")
            out.exportacion[n] = Cifra.rango(ex_prod.lo, total.hi, "kg/ha", total.fuente, notas="manejo de restos "
                                             "desconocido: rango entre incorporarlos y retirarlos",
                                             variable=f"exportación {n}")
    if ficha.leguminosa:
        out.notas.append("leguminosa: la fijación biológica de N es desconocida (depende de nodulación, inoculante y "
                         "riego) y no equivale a N mineral disponible; no se suma al balance")
    out.notas.append("P y K no se crean por rotación: lo exportado solo se repone con aporte externo")
    return out
