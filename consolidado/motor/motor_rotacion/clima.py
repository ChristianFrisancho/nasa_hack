"""Clima mensual por zona y escenario climático ICEN. ET0 y temperaturas: NASA POWER (clima_piura_mensual_1981_2025.csv
del repo) en los años de las campañas del escenario. Lluvia: PISCOp de Piura Datos (lluvia_zona_pisco.csv) por zona
CONTRATO.md; si la zona no tiene PISCOp queda la lluvia POWER y se avisa. CHIRPS no se usa en la costa."""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .catalogo import DIR_MOTOR, DIR_REPO, ESCENARIOS_ICEN, anios_del_mes, leer_csv, num
from .cifra import Cifra

ESCENARIOS = ESCENARIOS_ICEN
VARIABLES = {"ET0": ("ET0_approx_mm", "mm/mes"), "lluvia": ("rain_mm", "mm/mes"), "tmedia": ("Tmean_C", "°C"),
             "tmax": ("Tmax_max_C", "°C"), "dias_lluvia_20": ("days_rain_ge_20mm", "días/mes")}
FUENTE = "NASA POWER (MERRA-2/CERES) mensual 1981-2025, repo nasa_hack clima_piura_mensual_1981_2025.csv"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


@dataclass(frozen=True)
class Zona:
    nombre: str
    clave_csv: str
    lat: float
    lon: float
    distancia_km: float


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def centroide(poligono: list[list[float]]) -> tuple[float, float]:
    """Centroide simple (promedio de vértices [lat, lon]); suficiente para elegir la zona climática."""
    return (sum(p[0] for p in poligono) / len(poligono), sum(p[1] for p in poligono) / len(poligono))


def zona_mas_cercana(lat: float, lon: float, dir_motor: Path = DIR_MOTOR) -> Zona:
    zonas = leer_csv(Path(dir_motor) / "zonas_nasa_power.csv")
    mejor = min(zonas, key=lambda z: haversine_km(lat, lon, float(z["lat"]), float(z["lon"])))
    return Zona(mejor["zona"], mejor["zona_clima_csv"], float(mejor["lat"]), float(mejor["lon"]),
                round(haversine_km(lat, lon, float(mejor["lat"]), float(mejor["lon"])), 1))


@lru_cache(maxsize=4)
def _filas(dir_repo: str) -> tuple:
    return tuple(leer_csv(Path(dir_repo) / "clima_piura_mensual_1981_2025.csv"))


def _pct(vals: list[float], q: float) -> float:
    vals = sorted(vals)
    k = (len(vals) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return vals[f] + (vals[c] - vals[f]) * (k - f)


@dataclass
class ClimaEscenario:
    zona: Zona
    escenario: str
    anios: list[int]  # campañas ago(Y-1)-jul(Y) rotuladas por Y (ene-jul del año Y, ago-dic del año Y-1)
    mensual: dict  # mes(1-12) -> {variable: Cifra}
    fuente_lluvia: str = "NASA POWER"

    def cifra(self, mes: int, variable: str) -> Cifra:
        return self.mensual[(mes - 1) % 12 + 1][variable]


def validar_escenario(escenario: str) -> None:
    if escenario not in ESCENARIOS:
        raise ValueError(f"escenario '{escenario}' desconocido: use uno de los escenarios climáticos ICEN "
                         f"{', '.join(ESCENARIOS)}")


def clima_escenario(lat: float, lon: float, escenario: str, anios: list[int], dir_repo: Path = DIR_REPO,
                    dir_motor: Path = DIR_MOTOR) -> ClimaEscenario:
    """anios: campañas del escenario según la clasificación ICEN (Catalogo.anios_icen)."""
    validar_escenario(escenario)
    if not anios:
        raise ValueError(f"no hay años de campaña para el escenario {escenario} (falta lluvia_zona_pisco.csv)")
    zona = zona_mas_cercana(lat, lon, dir_motor)
    por_mes = {m: set(anios_del_mes(anios, m)) for m in range(1, 13)}
    datos: dict[int, dict[str, list[float]]] = {m: {v: [] for v in VARIABLES} for m in range(1, 13)}
    for r in _filas(str(dir_repo)):
        m = int(r["month"])
        if r["zone"] != zona.clave_csv or int(r["year"]) not in por_mes[m]:
            continue
        for v, (col, _) in VARIABLES.items():
            x = num(r[col])
            if x is not None:
                datos[m][v].append(x)
    mensual = {}
    for m in range(1, 13):
        mensual[m] = {}
        for v, (_, unidad) in VARIABLES.items():
            xs = datos[m][v]
            if not xs:
                mensual[m][v] = Cifra.desconocido(unidad, v, f"sin años con dato para {escenario} en {zona.nombre}")
                continue
            if len(xs) >= 5:
                lo, hi, metodo = _pct(xs, 0.1), _pct(xs, 0.9), "p10-p90"
            else:
                lo, hi, metodo = min(xs), max(xs), "mín-máx"
            c = Cifra.rango(lo, hi, unidad, FUENTE, "prediccion", "estimado",
                            f"{metodo} de {len(xs)} años de las campañas {escenario}; celda POWER {zona.nombre}, "
                            f"no estación", v, URL)
            mensual[m][v] = c.con(valor=round(_pct(xs, 0.5), 3))
    return ClimaEscenario(zona, escenario, anios, mensual)


def con_lluvia_pisco(clima: ClimaEscenario, lluvia: dict[int, Cifra]) -> ClimaEscenario:
    """Reemplaza la lluvia POWER por la PISCOp de la zona (los 12 meses)."""
    mensual = {m: {**v, "lluvia": lluvia[m]} for m, v in clima.mensual.items()}
    return ClimaEscenario(clima.zona, clima.escenario, clima.anios, mensual, "PISCOp")
