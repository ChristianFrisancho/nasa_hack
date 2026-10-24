"""Margen como distribución, no solo intervalo (para ordenar y para P(margen < 0)).

Supuestos del motor (no calibrados, se reportan junto a cada cifra):
- cada factor (rendimiento base, fracciones por sal y agua, precio, costo) es uniforme e independiente dentro de
  su rango; un valor sin rango es constante;
- los rangos DRAP son percentiles 10-90, así que tratar el rango como soporte completo subestima las colas;
- semilla fija derivada del nombre (zlib.crc32): mismas entradas, mismo resultado.
"""
from __future__ import annotations

import zlib

import numpy as np

from .cifra import Cifra

N_MUESTRAS = 4000
SUPUESTO = ("Monte Carlo del motor v1: factores uniformes e independientes dentro de su rango (rangos DRAP p10-p90 "
            "tratados como soporte), semilla fija; no calibrado")


def _rng(clave: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(clave.encode("utf-8")))


def muestras(c: Cifra, rng: np.random.Generator, n: int = N_MUESTRAS) -> np.ndarray | None:
    if c is None or not c.conocido:
        return None
    if c.lo == c.hi:
        return np.full(n, float(c.lo))
    return rng.uniform(c.lo, c.hi, n)


def muestras_margen(rend_base: Cifra, factores: list[Cifra], precio: Cifra, costo: Cifra, clave: str,
                    n: int = N_MUESTRAS) -> np.ndarray | None:
    """margen (PEN/ha) = rend_base × Π factores × 1000 × precio − costo. None si falta un dato."""
    rng = _rng(clave)
    r = muestras(rend_base, rng, n)
    if r is None:
        return None
    for f in factores:
        m = muestras(f, rng, n)
        if m is None:
            return None
        r = r * m
    p, c = muestras(precio, rng, n), muestras(costo, rng, n)
    if p is None or c is None:
        return None
    return r * 1000 * p - c


def muestras_uniformes(lo: float, hi: float, clave: str, n: int = N_MUESTRAS) -> np.ndarray:
    return _rng(clave).uniform(lo, hi, n) if hi > lo else np.full(n, float(lo))


def resumen(m: np.ndarray | None) -> dict | None:
    if m is None:
        return None
    return {"p10": float(np.percentile(m, 10)), "p50": float(np.percentile(m, 50)),
            "p90": float(np.percentile(m, 90)), "prob_negativo": float((m < 0).mean()), "media": float(m.mean()),
            "n": int(m.size), "supuesto": SUPUESTO}
