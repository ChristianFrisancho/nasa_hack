"""Precompute a compact quick calculator that also works on static hosting.

The reference scenario deliberately leaves field-only measurements unknown.
It uses the repository's Bajo Piura example normalized to one hectare (6,000
m³/ha/month) and ANA's documented 57% medium/low Piura irrigation efficiency.
"""
from __future__ import annotations

import json
import gzip
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard.server import evaluate_payload  # noqa: E402

DASH = Path(__file__).resolve().parent
DATA = DASH / "data"
UNITS = ["Piura", "Cerezal", "Pajarito"]  # only the drainage class affects the engine; UI choice is shown separately
MODES = {"normal": "aluvial", "salino": "salino", "agua": "arenoso"}


def measure(value):
    if not isinstance(value, dict):
        return None
    return {key: value.get(key) for key in ("valor", "valor_min", "valor_max", "unidad", "fuente",
                                             "tipo_evidencia", "estado", "notas", "url_o_doi", "variable")}


def simplify(value):
    if isinstance(value, dict):
        if "valor" in value:
            return measure(value)
        return {key: simplify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [simplify(item) for item in value]
    return value


def compact_candidate(item, detailed=True):
    water = item.get("agua") or {}
    if not detailed:
        return {
            "cultivo": item.get("cultivo"), "familia": item.get("familia"), "decision": item.get("decision"),
            "puesto": item.get("puesto"), "explicacion_puesto": item.get("explicacion_puesto", ""),
            "motivos_descarte": [(reason or "")[:180] for reason in (item.get("motivos_descarte") or [])[:2]],
            "duracion": measure(item.get("duracion")),
            "agua": {"riego_bruto_m3_ha": measure(water.get("riego_bruto_m3_ha"))},
            "rendimiento": measure(item.get("rendimiento")),
            "margen_mc": {key: (item.get("margen_mc") or {}).get(key) for key in ("p10", "p50", "p90")},
            "alertas": item.get("alertas"), "alertas_directas": item.get("alertas_directas"),
            "datos_faltantes": (item.get("datos_faltantes") or []),
            "anios_a_primera_produccion": measure(item.get("anios_a_primera_produccion")),
            "agua_anual": simplify(item.get("agua_anual")),
        }
    return {
        "cultivo": item.get("cultivo"), "familia": item.get("familia"), "decision": item.get("decision"),
        "puesto": item.get("puesto"), "explicacion_puesto": item.get("explicacion_puesto", ""),
        "motivos_descarte": [(reason or "")[:400] for reason in (item.get("motivos_descarte") or [])],
        "veredictos": [{"filtro": v.get("filtro"), "resultado": v.get("resultado"),
                        "motivo": (v.get("motivo") or "")[:800], "fuente": v.get("fuente"),
                        "tipo_evidencia": v.get("tipo_evidencia"), "cifras": simplify(v.get("cifras", {})),
                        "faltantes": v.get("faltantes", []), "probable_no_apto": v.get("probable_no_apto", False)}
                       for v in item.get("veredictos", [])],
        "duracion": measure(item.get("duracion")),
        "agua": simplify(water),
        "nutrientes": simplify(item.get("nutrientes")),
        "deja_en_suelo": simplify(item.get("deja_en_suelo", [])),
        "estado_tras_cosecha": simplify(item.get("estado_tras_cosecha")),
        "rendimiento": measure(item.get("rendimiento")),
        "precio_chacra": measure(item.get("precio_chacra")),
        "costo_ha": measure(item.get("costo_ha")),
        "margen_ha": measure(item.get("margen_ha")),
        "margen_mc": {key: (item.get("margen_mc") or {}).get(key) for key in ("p10", "p50", "p90")},
        "aptitud_suelo": item.get("aptitud_suelo"), "alertas": item.get("alertas"),
        "alertas_directas": item.get("alertas_directas"),
        "datos_faltantes": (item.get("datos_faltantes") or []),
    }


def main():
    crops = json.loads((DATA / "dashboard.json").read_text(encoding="utf-8"))["drapCrops"]
    signatures = sorted({(crop.get("motorCrop", ""), crop.get("family", "")) for crop in crops})
    signatures.append(("", ""))  # no previous crop / no family restriction
    output = {}
    scenarios = [(mode, poor) for mode in MODES for poor in (False, True)]
    total = len(signatures) * 12 * len(scenarios)
    done = 0
    for model_crop, family in signatures:
        for month in range(1, 13):
            for mode, poor in scenarios:
                condition = MODES[mode]
                unit = "Pajarito" if poor else ("Cerezal" if mode == "agua" else "Piura")
                payload = {
                    "previous_crop": model_crop or ("sin historial" if not family else "cultivo previo"),
                    "previous_family": family,
                    "previous_model_crop": model_crop,
                    "zone": "bajo_piura", "planting_month": month, "area_ha": 1,
                    "irrigation_mode": "irrigated", "water_m3_month": 6000,
                    "irrigation_efficiency": 0.57,
                    "soil_unit": unit, "soil_condition": condition,
                    "drainage": "pobre" if poor else "",
                    "scenario": "sin_el_nino",
                }
                result = evaluate_payload(payload)
                result["accepted"] = [compact_candidate(item, index == 0)
                                       for index, item in enumerate(result["accepted"])]
                result["withoutData"] = [compact_candidate(item, False) for item in result["withoutData"]]
                result["rejected"] = [compact_candidate(item, False) for item in result["rejected"]]
                result["perennials"] = [compact_candidate(item, False) for item in result["perennials"]]
                result["notes"] = []
                result["warnings"] = []
                result["globalMissing"] = []
                key = "|".join((model_crop, family, str(month), mode, "pobre" if poor else "sin_drenaje_pobre"))
                output[key] = result
                done += 1
            if done % 72 == 0:
                print(f"Escenarios rápidos: {done}/{total}", flush=True)
    out = DATA / "quick_rotation.json.gz"
    raw = json.dumps(output, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    out.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    print(f"{out.relative_to(ROOT)}: {len(output)} combinaciones, {len(raw):,} bytes sin comprimir, {out.stat().st_size:,} bytes gzip")


if __name__ == "__main__":
    main()
