"""Cifra trazable según CONTRATO.md y aritmética de intervalos."""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace

TIPOS_EVIDENCIA = ("medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion")
ESTADOS = ("observado", "estimado", "desconocido")


@dataclass(frozen=True)
class Cifra:
    valor: float | None
    valor_min: float | None
    valor_max: float | None
    unidad: str
    fuente: str
    tipo_evidencia: str = "prediccion"
    estado: str = "estimado"
    url_o_doi: str = ""
    notas: str = ""
    variable: str = ""

    def __post_init__(self):
        if self.tipo_evidencia not in TIPOS_EVIDENCIA:
            raise ValueError(f"tipo_evidencia inválido: {self.tipo_evidencia}")
        if self.estado not in ESTADOS:
            raise ValueError(f"estado inválido: {self.estado}")
        if self.estado == "desconocido" and self.valor is not None:
            raise ValueError("una cifra desconocida no lleva valor")

    @staticmethod
    def desconocido(unidad: str, variable: str = "", notas: str = "", fuente: str = "sin dato") -> "Cifra":
        return Cifra(None, None, None, unidad, fuente, "prediccion", "desconocido", notas=notas, variable=variable)

    @staticmethod
    def rango(lo: float, hi: float, unidad: str, fuente: str, tipo: str = "prediccion",
              estado: str = "estimado", notas: str = "", variable: str = "", url: str = "") -> "Cifra":
        lo, hi = min(lo, hi), max(lo, hi)
        return Cifra(round((lo + hi) / 2, 4), round(lo, 4), round(hi, 4), unidad, fuente, tipo, estado,
                     url, notas, variable)

    @property
    def conocido(self) -> bool:
        return self.estado != "desconocido" and self.valor is not None

    @property
    def lo(self) -> float | None:
        if not self.conocido:
            return None
        return self.valor_min if self.valor_min is not None else self.valor

    @property
    def hi(self) -> float | None:
        if not self.conocido:
            return None
        return self.valor_max if self.valor_max is not None else self.valor

    def con(self, **cambios) -> "Cifra":
        return replace(self, **cambios)

    def a_dict(self) -> dict:
        return asdict(self)

    def texto(self, decimales: int = 1) -> str:
        if not self.conocido:
            return f"desconocido ({self.unidad})"
        f = lambda x: f"{x:,.{decimales}f}".replace(",", " ")
        if self.lo == self.hi:
            return f"{f(self.valor)} {self.unidad}"
        return f"{f(self.lo)}–{f(self.hi)} {self.unidad}"


def _peor_evidencia(*cs: Cifra) -> str:
    return max((c.tipo_evidencia for c in cs), key=TIPOS_EVIDENCIA.index)


def operar(op: str, a: Cifra, b: Cifra, unidad: str, variable: str, formula: str) -> Cifra:
    """Combina dos cifras no negativas (+, -, *, /). Resultado: predicción del motor con la peor evidencia de entrada en notas."""
    if not (a.conocido and b.conocido):
        faltan = [c.variable or c.unidad for c in (a, b) if not c.conocido]
        return Cifra.desconocido(unidad, variable, f"falta: {', '.join(faltan)}", fuente=f"motor v1: {formula}")
    if op == "+":
        lo, hi = a.lo + b.lo, a.hi + b.hi
    elif op == "-":
        lo, hi = a.lo - b.hi, a.hi - b.lo
    elif op == "*":
        prods = [a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi]
        lo, hi = min(prods), max(prods)
    elif op == "/":
        if b.lo <= 0:
            return Cifra.desconocido(unidad, variable, "divisor puede ser 0", fuente=f"motor v1: {formula}")
        quots = [a.lo / b.lo, a.lo / b.hi, a.hi / b.lo, a.hi / b.hi]
        lo, hi = min(quots), max(quots)
    else:
        raise ValueError(op)
    fuentes = "; ".join(dict.fromkeys(c.fuente for c in (a, b)))
    return Cifra.rango(lo, hi, unidad, f"motor v1: {formula}", "prediccion", "estimado",
                       notas=f"evidencia de entrada más débil: {_peor_evidencia(a, b)}; entradas: {fuentes}",
                       variable=variable)


def escalar(a: Cifra, k: float, unidad: str, variable: str, formula: str) -> Cifra:
    if not a.conocido:
        return Cifra.desconocido(unidad, variable, a.notas or f"falta {a.variable}", fuente=f"motor v1: {formula}")
    return Cifra.rango(a.lo * k, a.hi * k, unidad, f"motor v1: {formula}", "prediccion", "estimado",
                       notas=f"evidencia de entrada: {a.tipo_evidencia}; {a.fuente}", variable=variable)
