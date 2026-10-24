"""Local web server and live adapter for Piura's published rotation engine.

Run from the repository root with: python dashboard/server.py
The listener binds to loopback only; the JSON endpoint evaluates the real
Python motor and never substitutes invented soil measurements.
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MOTOR = ROOT / "piura-agro" / "consolidado" / "motor"
sys.path.insert(0, str(MOTOR))

from motor_rotacion.entradas import Consulta  # noqa: E402
from motor_rotacion.motor import evaluar  # noqa: E402
from motor_rotacion.reporte import evaluacion_a_dict, perenne_a_dict  # noqa: E402

REFERENCE_POINTS = {
    "bajo_piura": (-5.42, -80.74),
    "medio_piura": (-5.33, -80.68),
    "alto_piura": (-5.09, -80.16),
    "chira": (-4.90, -80.69),
    "san_lorenzo": (-4.85, -80.25),
    "sierra_piura": (-4.64, -79.71),
}
POOR_DRAINAGE_UNITS = {"Pajarito", "Ramón"}
UNIT_CONDITION = {"Palo Verde": "aluvial", "Piura": "aluvial", "Cerezal": "arenoso",
                  "Pajarito": "salino", "Ramón": "salino", "Curumuy": "yesoso"}


def _number(value):
    if value in (None, ""):
        return None
    return float(value)


def build_consulta(payload: dict) -> tuple[Consulta, list[str]]:
    zone = payload.get("zone", "bajo_piura")
    if zone not in REFERENCE_POINTS:
        raise ValueError("Elige una zona agrícola de Piura válida.")
    crop = payload.get("previous_crop") or ""
    family = payload.get("previous_family") or None
    soil_unit = payload.get("soil_unit") or ""
    condition = payload.get("soil_condition") or UNIT_CONDITION.get(soil_unit, "")
    drainage = payload.get("drainage") or None
    notes = ["Clima de referencia NASA POWER/PISCOp; coordenada representativa, no ubicación exacta de la parcela."]
    if not drainage and (soil_unit in POOR_DRAINAGE_UNITS or condition == "salino"):
        drainage = "pobre"
        notes.append("Drenaje pobre inferido de la descripción cartográfica salina; confírmalo en el lote.")
    if soil_unit == "Cerezal" or condition == "arenoso":
        notes.append("La textura arenosa se conserva como contexto; el motor no tiene parámetros de textura por cultivo para puntuarla.")
    if condition == "arido":
        notes.append("La aridez entra por clima y lluvia regional; el agua de riego debe informarse por separado.")
    if condition == "agrietado":
        notes.append("Grietas/expansividad no se puntúan: la cartografía no confirma Vertisol y hace falta medir arcilla/expansividad.")
    if condition == "yesoso" or soil_unit == "Curumuy":
        notes.append("Yeso/carbonatos no se puntúan sin análisis químico del perfil.")
    if soil_unit in ("Pajarito", "Ramón") or condition == "salino":
        notes.append("La cartografía señala salinidad, pero no da una ECe parcelaria: ingresa una medición para comparar umbrales de cultivo.")

    drainage_options = {"bueno", "moderado", "pobre"}
    if drainage and drainage not in drainage_options:
        raise ValueError("Drenaje debe ser bueno, moderado, pobre o sin medición.")
    lat, lon = REFERENCE_POINTS[zone]
    irrigation_mode = payload.get("irrigation_mode", "irrigated")
    if irrigation_mode != "rainfed" and not payload.get("water_m3_by_month"):
        notes.append("Se aplicó el volumen mensual indicado como constante para los 12 meses; usa la tabla mensual si la dotación varía.")
    monthly_water = (0 if irrigation_mode == "rainfed" else payload.get("water_m3_by_month") or
                     _number(payload.get("water_m3_month")))
    irrigation_efficiency = _number(payload.get("irrigation_efficiency"))
    request = {
        "parcela": {"punto": [lat, lon], "area_ha": _number(payload.get("area_ha")) or 1.0,
                    "provincia": "Piura", "zona": zone},
        "suelo": {"ece_ds_m": _number(payload.get("ece")), "ph": _number(payload.get("ph")),
                  "profundidad_cm": _number(payload.get("depth_cm")), "pendiente_pct": _number(payload.get("slope_pct")),
                  "drenaje": drainage, "napa_m": _number(payload.get("water_table_m")),
                  "psi_pct": _number(payload.get("psi_pct")),
                  "ce_metodo": payload.get("ece_method") or "pasta_saturada"},
        "agua": {"m3_por_mes": monthly_water, "ecw_ds_m": _number(payload.get("ecw")),
                 "eficiencia": irrigation_efficiency,
                 "intervalo_turno_dias": _number(payload.get("irrigation_interval_days"))},
        "presupuesto_pen": _number(payload.get("budget_pen")),
        "cultivo_anterior": payload.get("previous_model_crop") or (crop if crop in {
            "arroz", "maiz amarillo duro", "maiz choclo", "frijol grano", "frijol verde", "caupi", "arveja",
            "frijol de palo", "algodon", "papa", "piquillo", "zapallo", "cebolla", "yuca", "mango", "limon",
            "banano", "uva", "cacao", "cafe", "papaya"} else None),
        "familia_anterior": family,
        "condicion_suelo": condition if condition in {"salino", "arido", "arenoso", "yesoso", "agrietado", "aluvial"} else None,
        "escenario": payload.get("scenario") or "sin_el_nino",
        "mes_siembra": int(payload.get("planting_month") or 1),
        "horizonte_meses": int(payload.get("horizon_months") or 12),
        "plagas_presentes": payload.get("pests") or [],
        "fertilizacion_prevista": {
            key: value for key, value in {
                "N": _number(payload.get("fertilizer_n")),
                "P2O5": _number(payload.get("fertilizer_p")),
                "K2O": _number(payload.get("fertilizer_k")),
            }.items() if value is not None
        },
    }
    return Consulta.desde_dict(request), notes


def evaluate_payload(payload: dict) -> dict:
    consulta, notes = build_consulta(payload)
    result = evaluar(consulta)
    ranking = result.ranking
    rank_by_crop = {crop: index + 1 for index, crop in enumerate(ranking)}
    evaluations = [evaluacion_a_dict(e) for e in result.evaluaciones]
    evaluations.sort(key=lambda item: (rank_by_crop.get(item["cultivo"], 10_000), item["decision"], item["cultivo"]))
    perennials = [perenne_a_dict(item) for item in result.perennes]
    perennials.sort(key=lambda item: (item["decision"] != "aceptado", item["cultivo"]))
    return {
        "engine": "motor_rotacion v1",
        "zone": payload.get("zone", "bajo_piura"),
        "climateZone": result.clima.zona.nombre,
        "climateDistanceKm": result.clima.zona.distancia_km,
        "previousCrop": payload.get("previous_crop") or "sin historial",
        "soilUnit": payload.get("soil_unit") or "sin unidad seleccionada",
        "soilCondition": payload.get("soil_condition") or UNIT_CONDITION.get(payload.get("soil_unit"), "sin condición seleccionada"),
        "rankingRule": ("Tras seguridad y rotación familiar, prioriza mayor umbral de tolerancia a salinidad; el valor real de ECe sigue siendo necesario." if (payload.get("soil_condition") or UNIT_CONDITION.get(payload.get("soil_unit"))) == "salino" else
                        "Tras seguridad y rotación familiar, prioriza menor riego neto estimado para gestionar el déficit y la baja retención." if (payload.get("soil_condition") or UNIT_CONDITION.get(payload.get("soil_unit"))) in {"arido", "arenoso"} else
                        "Orden del motor: restricciones y alertas, familia anterior, margen conservador, aptitud del suelo y agua."),
        "notes": notes,
        "summary": result.mensaje,
        "ranking": ranking,
        "accepted": [item for item in evaluations if item["decision"] == "aceptado"],
        "withoutData": [item for item in evaluations if item["decision"] == "sin_datos"],
        "rejected": [item for item in evaluations if item["decision"] == "descartado"],
        "perennials": perennials,
        "globalMissing": result.faltantes_globales,
        "warnings": result.avisos,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):  # noqa: N802
        if urlparse(self.path).path != "/api/evaluate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("El formulario está vacío o supera el límite permitido.")
            payload = json.loads(self.rfile.read(length))
            response = evaluate_payload(payload)
            body = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
            self.send_response(400)
        except Exception as error:  # surface model failures to the client without leaking a traceback
            body = json.dumps({"error": f"No se pudo evaluar la parcela: {error}"}, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Servir Raíz y ejecutar el motor de rotación en local.")
    parser.add_argument("--host", default="127.0.0.1", help="Por seguridad, solo escucha en loopback por defecto.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Raíz con motor en vivo: http://{args.host}:{args.port}/dashboard/ (Ctrl+C para terminar)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
