"""Ronda 5: CEw contra el MOTOR CONSOLIDADO del equipo (consolidado/motor, motor_rotacion v1), no contra el modelo
propio de Piura Modelos. Uso (desde consolidado/motor):  python3 ../../modelo/experimentos/cew_motor.py

Parcela tipo por zona, solo con datos con fuente:
- punto: modelo/scripts/puntos.json
- ECe: Bajo [1.2, 12] (zonas.csv; FAO/UNALM 1990 vía Territorio). Chira, Medio, Alto y San Lorenzo sin ECe zonal (ronda 5:
  Territorio descartó HWSD porque contradice la CE medida en chacra). ECE_MODO=desconocida (por defecto) la pasa como
  desconocida; ECE_MODO=rango_global pasa el rango hipótesis 0.5-12 de params/escenario_rangos.csv (sufijo _eceglobal)
- pH: suelos/datos/profundidad_ph_por_zona.csv pH_rango_zona; profundidad física HWSD2 de esa tabla (m -> cm)
- pendiente [0, p90]: suelos/datos/pendiente_por_zona.csv (GLO-30 + WorldCover; el ruido del DEM la infla en plano)
- agua m3/mes: null en la base (el reparto mensual de la dotación no tiene fuente); variante con_agua = dotación
  ANA PGRH / 12 uniforme (zonas.csv; asignada, no entregada), 1 ha
- drenaje: null (no hay clase por parcela; zonas.csv solo da fracción de área)
Variantes de napa: desconocida (null), 1 m (somera, Bajo: ANA 2015 SEV 11 de 41 < 1 m), 3 m (>= 2 m, FAO-29 aplica).
Variantes de ECw: null (falta), 0.5/1.5/3.0 (escenarios del propio motor), rango río de suelos/datos/cew_por_zona.csv,
Chira 0.373-1.167 (Coronel 2021).
Salidas: modelo/experimentos/cew_motor_resumen.csv y cew_motor_ablacion.csv
"""
import csv, os, json, pathlib, sys, time
B = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(B / "consolidado/motor"))
from motor_rotacion import Consulta, evaluar, comparar_secuencias  # noqa: E402
# Ronda 6 del motor: escenarios ICEN (sin_el_nino, el_nino_moderado, el_nino_fuerte_extraordinario); "normal" ya no existe
ESCENARIO = os.environ.get("MOTOR_ESCENARIO", "sin_el_nino")

PTS = json.loads((B / "modelo/scripts/puntos.json").read_text())
ZM = {"chira_sullana": "chira", "bajo_piura": "bajo_piura", "medio_piura": "medio_piura", "alto_piura": "alto_piura",
      "san_lorenzo": "san_lorenzo"}
Z = {r["zona"]: r for r in csv.DictReader(open(B / "modelo/params/zonas.csv"))}
PH, PROF = {}, {}
for r in csv.DictReader(open(B / "suelos/datos/profundidad_ph_por_zona.csv")):
    if r["variable"] == "pH_rango_zona" and r["zona"] not in PH:
        PH[r["zona"]] = [float(r["valor_min"]), float(r["valor_max"])]
    if r["variable"] == "profundidad_fisica_suelo_HWSD2" and r["zona"] not in PROF and r["valor_min"]:
        # HWSD2 clase 1 = ">100 cm" (cota inferior abierta). Chira: 73 % clase 1, 27 % clase 3 (0.1 m mínimo):
        # se usa la clase dominante, 100 cm como cota inferior conservadora, estimado.
        PROF[r["zona"]] = {"valor_min": 100.0, "valor_max": 100.0, "tipo_evidencia": "prediccion", "estado": "estimado",
                           "fuente": "HWSD2 vía suelos/datos/profundidad_ph_por_zona.csv (clase >100 cm)"}
P90 = {r["zona"]: float(r["valor"]) for r in csv.DictReader(open(B / "suelos/datos/pendiente_por_zona.csv"))
       if r["variable"] == "pendiente_p90_cultivo" and r["zona"] != "sierra_piura"}
ECE_MODO = os.environ.get("ECE_MODO", "desconocida")
SUF = "" if ECE_MODO == "desconocida" else "_eceglobal"


def ECE(z):
    """Ronda 5: ECe zonal de zonas.csv; vacía (HWSD descartado por Territorio) = desconocida, o el rango global
    hipótesis 0.5-12 de params/escenario_rangos.csv con ECE_MODO=rango_global (intervalo ancho, no dato)."""
    if Z[z]["ece_min"]:
        return [float(Z[z]["ece_min"]), float(Z[z]["ece_max"])]
    if ECE_MODO == "desconocida":
        return None
    return {"valor_min": 0.5, "valor_max": 12.0, "tipo_evidencia": "prediccion", "estado": "estimado",
            "fuente": "ECe zonal desconocida: rango global hipotesis de modelo/params/escenario_rangos.csv"}


# CEw leída de suelos/datos/cew_por_zona.csv (Territorio). Todo es de estiaje (sep-nov) o de estación desconocida; no hay
# medidas de avenida (dic-abr), cuando la dilución la baja.
CEW_CSV = list(csv.DictReader(open(B / "suelos/datos/cew_por_zona.csv")))


def _num(r):
    if r["valor_min"] and r["valor_max"]:
        lo, hi = float(r["valor_min"]), float(r["valor_max"])
        return lo if lo == hi else [lo, hi]
    return float(r["valor"]) if r["valor"] else None


def _cew(zona, fuente, nivel="resumen", punto=None):
    """Desde 07:55 Territorio usa una sola variable (ce_agua_riego) y el origen en fuente_agua (mapa_variables_motor.csv)."""
    for r in CEW_CSV:
        if r["zona"] == zona and r["nivel"] == nivel and r["fuente_agua"] == fuente \
                and (punto is None or r["punto"] == punto) and _num(r) is not None:
            return _num(r)
    return None


# Lecturas ANA 2024 de unidad ambigua; el motor las rechaza (catalogo.CEW_EN_DISPUTA). Territorio las publica desde 07:57
# con el valor estimado por balance iónico (estado=estimado: RPiur4 9.03, RPiur5 9.92, QSFran1 5.0); QCarn1 sigue desconocido.
EN_DISPUTA = ("QCarn1", "QSFran1", "RPiur4", "RPiur5")


def rio_sin_disputa(zona):
    """Rango del río con los puntos medidos, sin las lecturas en disputa (lo que aceptaría el motor si leyera el río)."""
    v = []
    for r in CEW_CSV:
        if r["zona"] == zona and r["nivel"] == "punto" and r["fuente_agua"] == "rio" \
                and not (r["punto"] in EN_DISPUTA and r["fecha_o_periodo"].startswith("2024")):
            x = _num(r)
            if x is not None:
                v += x if isinstance(x, list) else [x]
    return [min(v), max(v)] if v else None


CEW_RIO = {zm: _cew(zm, "rio") for zm in ("chira", "medio_piura", "alto_piura", "san_lorenzo", "bajo_piura")}
# canal, reservorio o toma (agua que entra a los canales): Chira salida de Poechos (RChir3, ANA oct-2024, reservorio),
# San Lorenzo reservorio (PSI c. 2011). Es lo único que el motor toma como valor de zona (catalogo.FUENTES_AGUA_DE_CANAL).
CEW_CANAL = {zm: _cew(zm, "canal") or _cew(zm, "reservorio") or _cew(zm, "toma") for zm in CEW_RIO}
# pozos de tesis (solo resumen): Cura Mori (Bajo, UNP 2019, 5 pozos) y Castilla/Progreso Bajo (Medio, UNP 2018, 7 pozos)
CEW_POZO = {"bajo_piura": _cew("bajo_piura", "pozo", "punto", "UNP2019_CuraMori"),
            "medio_piura": _cew("medio_piura", "pozo", "punto", "UNP2018_Castilla")}


def consulta(z, napa=None, ecw=None, quitar=None, con_agua=False):
    zm = ZM[z]
    d = {"parcela": {"punto": [PTS[z]["lat"], PTS[z]["lon"]], "area_ha": 1.0, "provincia": None, "zona": zm},
         "suelo": {"ece_ds_m": ECE(z), "ph": PH.get(zm),
                   "profundidad_cm": PROF.get(zm), "pendiente_pct": [0.0, P90[zm]], "drenaje": None, "napa_m": napa},
         "agua": {"m3_por_mes": round(float(Z[z]["dotacion_m3_ha_anio"]) / 12) if con_agua else None, "ecw_ds_m": ecw},
         "presupuesto_pen": None, "cultivo_anterior": None, "escenario": ESCENARIO, "mes_siembra": 8, "horizonte_meses": 6}
    if quitar:
        sec, campo = quitar
        d[sec][campo] = None
    return Consulta.desde_dict(d)


def correr(c):
    r = evaluar(c)
    s = comparar_secuencias(c, 2)
    via = [x for x in s if x.viable]
    return dict(n_aceptados=len(r.ranking), top1=r.ranking[0] if r.ranking else "ninguno", top3="|".join(r.ranking[:3]),
                sec_viables=len(via), sec_total=len(s), sec_top="+".join(via[0].cultivos) if via else "ninguna")


def main():
    out = B / "modelo/experimentos"
    filas = []
    for z in ZM:
        zm = ZM[z]
        ecws = {"falta": None, "esc_0.5": 0.5, "esc_1.5": 1.5, "esc_3.0": 3.0}
        if CEW_RIO[zm]:
            ecws["rio_zona"] = CEW_RIO[zm]
            if rio_sin_disputa(zm) and rio_sin_disputa(zm) != CEW_RIO[zm]:
                ecws["rio_sin_disputa"] = rio_sin_disputa(zm)
        if zm == "chira":
            ecws["chira_coronel"] = [0.373, 1.167]
        if CEW_CANAL[zm] is not None:
            ecws["canal_toma"] = CEW_CANAL[zm]
        if CEW_POZO.get(zm):
            ecws["pozo_tesis"] = CEW_POZO[zm]
        for napa_lbl, napa in (("napa_desconocida", None), ("napa_1m", 1.0), ("napa_3m", 3.0)):
            for e_lbl, e in ecws.items():
                t = time.time()
                f = dict(zona=z, napa=napa_lbl, ecw=e_lbl, ecw_valor=json.dumps(e), **correr(consulta(z, napa, e)))
                filas.append(f)
                print(z, napa_lbl, e_lbl, f["n_aceptados"], f["top1"], f["sec_viables"], f["sec_total"], f["sec_top"],
                      f"{time.time() - t:.1f}s", flush=True)
    with open(out / f"cew_motor_resumen{SUF}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    # ablación "falta el dato" sobre el motor: base = napa desconocida + ECw de río de la zona (o escenario 1.5 en Bajo)
    ab = []
    feats = [("suelo", "ece_ds_m"), ("suelo", "ph"), ("suelo", "profundidad_cm"), ("suelo", "pendiente_pct"),
             ("agua", "ecw_ds_m")]
    for z in ZM:
        zm = ZM[z]
        e0 = CEW_RIO[zm] or 1.5
        base = correr(consulta(z, None, e0))
        for sec, campo in feats:
            q = correr(consulta(z, None, e0, quitar=(sec, campo)))
            ab.append(dict(zona=z, base_ecw=json.dumps(e0), feature=campo, top1_base=base["top1"], top1_sin=q["top1"],
                           cambia_top1=int(base["top1"] != q["top1"]), aceptados_base=base["n_aceptados"],
                           aceptados_sin=q["n_aceptados"], sec_viables_base=base["sec_viables"], sec_viables_sin=q["sec_viables"],
                           sec_top_base=base["sec_top"], sec_top_sin=q["sec_top"]))
            print("abl", z, campo, ab[-1]["top1_base"], "->", q["top1"], base["sec_viables"], "->", q["sec_viables"], flush=True)
    for z in ZM:  # variante: agregar la dotación uniforme (supuesto de reparto, no dato)
        e0 = CEW_RIO[ZM[z]] or 1.5
        base, q = correr(consulta(z, None, e0)), correr(consulta(z, None, e0, con_agua=True))
        ab.append(dict(zona=z, base_ecw=json.dumps(e0), feature="agregar_dotacion_uniforme", top1_base=base["top1"],
                       top1_sin=q["top1"], cambia_top1=int(base["top1"] != q["top1"]), aceptados_base=base["n_aceptados"],
                       aceptados_sin=q["n_aceptados"], sec_viables_base=base["sec_viables"], sec_viables_sin=q["sec_viables"],
                       sec_top_base=base["sec_top"], sec_top_sin=q["sec_top"]))
        print("agua", z, base["top1"], "->", q["top1"], base["sec_viables"], "->", q["sec_viables"], flush=True)
    with open(out / f"cew_motor_ablacion{SUF}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ab[0])); w.writeheader(); w.writerows(ab)


if __name__ == "__main__":
    main()
