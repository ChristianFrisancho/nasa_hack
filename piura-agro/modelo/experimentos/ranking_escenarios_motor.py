"""Ranking de features por escenario ICEN contra el motor consolidado (ronda 5, pedido de las 08:20).

Relanzable sobre cualquier versión del motor:
    python3 experimentos/ranking_escenarios_motor.py --motor ../consolidado/motor --etiqueta r6 [--parcelas 12 --semillas 2]
o con variables MOTOR_DIR y MOTOR_ETIQUETA. Corre con el python del motor (python3 del sistema), desde cualquier carpeta.

Qué hace. Por zona sortea parcelas con valores puntuales dentro de los rangos publicados (ECe, pH, pendiente, CEw, napa),
para que el motor pueda decidir. Para cada parcela, escenario ICEN y feature, borra el dato (None) y mide si cambia el
top-1 de cultivos y el número de secuencias viables de 2 campañas. Incertidumbre: IC 95 % bootstrap sobre parcelas
(1000 remuestreos) y rango entre semillas. No es un dato del terreno; es la sensibilidad del motor a cada dato.

Rangos (todos con fuente, ninguno inventado aquí):
- ECe: zonas.csv (Bajo 1.6-8.2, medida); otras zonas U(0.5, 12), rango hipótesis de params/escenario_rangos.csv.
- pH: suelos/datos/profundidad_ph_por_zona.csv (pH_rango_zona). Profundidad: 100 cm, cota baja HWSD2 (estimado).
- Pendiente: U(0, p90) de suelos/datos/pendiente_por_zona.csv.
- CEw: rango del río de la zona en suelos/datos/cew_por_zona.csv (nivel resumen); Bajo sin río: pozos de tesis Cura Mori.
- Napa: sorteo entre sin dato, 1 m y 3 m (los tres casos de R5.1); no hay napa medida por parcela.

Marca de no informativo. Si el P50 del margen de cada cultivo aceptado es idéntico entre escenarios (motor r6: el margen
sale de DRAP y el clima no entra), la importancia por escenario solo refleja los filtros (calendario, temperatura,
exceso de agua) y se marca "no_informativo_margen". En r7, si entra el riego por escenario, la marca se apaga sola.
"""
import argparse, csv, hashlib, json, os, pathlib, random, subprocess, sys, time

AQUI = pathlib.Path(__file__).resolve().parent
B = AQUI.parents[1]  # /workspace/piura-agro

ap = argparse.ArgumentParser()
ap.add_argument("--motor", default=os.environ.get("MOTOR_DIR", str(B / "consolidado/motor")))
ap.add_argument("--etiqueta", default=os.environ.get("MOTOR_ETIQUETA", "actual"))
ap.add_argument("--parcelas", type=int, default=int(os.environ.get("PARCELAS", 12)))
ap.add_argument("--semillas", type=int, default=int(os.environ.get("SEMILLAS", 2)))
ap.add_argument("--zonas", default="chira_sullana,bajo_piura,medio_piura,alto_piura,san_lorenzo")
ap.add_argument("--sin-secuencias", action="store_true", help="más rápido: solo top-1 de cultivos")
ap.add_argument("--tests", action="store_true", help="corre pytest del motor y anota el resultado")
A = ap.parse_args()
MOTOR = pathlib.Path(A.motor).resolve()
os.chdir(MOTOR)
sys.path.insert(0, str(MOTOR))
from motor_rotacion import Consulta, evaluar, comparar_secuencias  # noqa: E402
try:
    from motor_rotacion.catalogo import ESCENARIOS_ICEN as ESCENARIOS  # motor r6 en adelante
except ImportError:  # versiones viejas
    from motor_rotacion.clima import ESCENARIOS  # noqa: E402


def version_motor():
    """Commit git si lo hay; si no, huella SHA256 del código (motor_rotacion/*.py) y de datos_repo/SHA256SUMS."""
    v = {"motor_dir": str(MOTOR), "etiqueta": A.etiqueta, "escenarios": list(ESCENARIOS)}
    try:
        v["commit"] = subprocess.run(["git", "-C", str(MOTOR), "rev-parse", "HEAD"], capture_output=True, text=True,
                                     check=True).stdout.strip()
    except Exception:
        v["commit"] = "sin_git"
    h = hashlib.sha256()
    for p in sorted((MOTOR / "motor_rotacion").glob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    v["sha256_codigo"] = h.hexdigest()[:16]
    s = MOTOR / "datos_repo/SHA256SUMS"
    v["sha256_datos_repo"] = hashlib.sha256(s.read_bytes()).hexdigest()[:16] if s.exists() else "sin_SHA256SUMS"
    rondas = [l.split("(")[0].strip("# \n") for l in open(MOTOR / "README.md", encoding="utf-8") if l.startswith("## Ronda")]
    v["ultima_ronda_readme"] = rondas[-1] if rondas else "?"
    if A.tests:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], capture_output=True, text=True)
        v["tests"] = (r.stdout.strip().splitlines() or ["?"])[-1]
    return v


ZM = {"chira_sullana": "chira", "bajo_piura": "bajo_piura", "medio_piura": "medio_piura", "alto_piura": "alto_piura",
      "san_lorenzo": "san_lorenzo"}
PTS = json.loads((B / "modelo/scripts/puntos.json").read_text())
Z = {r["zona"]: r for r in csv.DictReader(open(B / "modelo/params/zonas.csv"))}
PH = {}
for r in csv.DictReader(open(B / "suelos/datos/profundidad_ph_por_zona.csv")):
    if r["variable"] == "pH_rango_zona" and r["zona"] not in PH:
        PH[r["zona"]] = (float(r["valor_min"]), float(r["valor_max"]))
P90 = {r["zona"]: float(r["valor"]) for r in csv.DictReader(open(B / "suelos/datos/pendiente_por_zona.csv"))
       if r["variable"] == "pendiente_p90_cultivo"}
CEW = {}
for r in csv.DictReader(open(B / "suelos/datos/cew_por_zona.csv")):
    if r["nivel"] == "resumen" and r["fuente_agua"] == "rio" and r["valor_min"] and r["zona"] not in CEW:
        CEW[r["zona"]] = (float(r["valor_min"]), float(r["valor_max"]), "río resumen")
CEW.setdefault("bajo_piura", (0.13, 1.12, "pozos de tesis Cura Mori (UNP 2019)"))
FEATURES = [("suelo", "ece_ds_m"), ("agua", "ecw_ds_m"), ("suelo", "ph"), ("suelo", "profundidad_cm"),
            ("suelo", "pendiente_pct"), ("suelo", "napa_m")]


def parcela(z, rng):
    zm = ZM[z]
    ece = (float(Z[z]["ece_min"]), float(Z[z]["ece_max"])) if Z[z]["ece_min"] else (0.5, 12.0)
    lo, hi, _ = CEW[zm]
    return {"parcela": {"punto": [PTS[z]["lat"], PTS[z]["lon"]], "area_ha": 1.0, "provincia": None, "zona": zm},
            "suelo": {"ece_ds_m": round(rng.uniform(*ece), 2), "ph": round(rng.uniform(*PH[zm]), 2),
                      "profundidad_cm": {"valor_min": 100.0, "valor_max": 100.0, "tipo_evidencia": "prediccion",
                                         "estado": "estimado", "fuente": "HWSD2 clase >100 cm (cota baja)"},
                      "pendiente_pct": round(rng.uniform(0, P90[zm]), 2), "drenaje": None,
                      "napa_m": rng.choice([None, 1.0, 3.0])},
            "agua": {"m3_por_mes": None, "ecw_ds_m": round(rng.uniform(lo, hi), 3)},
            "presupuesto_pen": None, "cultivo_anterior": None, "mes_siembra": 8, "horizonte_meses": 6}


def correr(d, esc, quitar=None):
    d = json.loads(json.dumps(d)); d["escenario"] = esc
    if quitar:
        d[quitar[0]][quitar[1]] = None
    c = Consulta.desde_dict(d)
    r = evaluar(c)
    p50 = {}
    for e in r.evaluaciones:
        if e.decision == "aceptado" and e.margen_mc:
            p50[e.cultivo] = round(e.margen_mc.get("p50") or 0)
    riego = None
    if r.ranking:
        e1 = next(e for e in r.evaluaciones if e.cultivo == r.ranking[0])
        if e1.agua and e1.agua.riego_neto_mm and e1.agua.riego_neto_mm.valor is not None:
            riego = round(e1.agua.riego_neto_mm.valor, 1)
    nsec = None if A.sin_secuencias else sum(s.viable for s in comparar_secuencias(c, 2))
    return {"top1": r.ranking[0] if r.ranking else "ninguno", "nsec": nsec, "p50": p50, "riego_top1_mm": riego}


def ic(v, rng, n=1000):
    if not v:
        return (None, None, None)
    m = sum(v) / len(v)
    bs = sorted(sum(rng.choice(v) for _ in v) / len(v) for _ in range(n))
    return (100 * m, 100 * bs[int(0.025 * n)], 100 * bs[int(0.975 * n) - 1])


def main():
    t0 = time.time()
    ver = version_motor()
    zonas = A.zonas.split(",")
    reg = []  # una fila por semilla, zona, parcela, escenario, feature
    margen_igual = True
    for s in range(A.semillas):
        rng = random.Random(1000 + s)
        for z in zonas:
            for k in range(A.parcelas):
                d = parcela(z, rng)
                base = {e: correr(d, e) for e in ESCENARIOS}
                ref = base[ESCENARIOS[0]]["p50"]
                for e in ESCENARIOS[1:]:
                    comun = set(ref) & set(base[e]["p50"])
                    if any(ref[c] != base[e]["p50"][c] for c in comun):
                        margen_igual = False
                for e in ESCENARIOS:
                    b = base[e]
                    reg.append(dict(semilla=s, zona=z, parcela=k, escenario=e, feature="(base)", top1=b["top1"],
                                    cambia_top1=int(b["top1"] != base[ESCENARIOS[0]]["top1"]),
                                    cambia_sec=None if b["nsec"] is None else int(b["nsec"] != base[ESCENARIOS[0]]["nsec"]),
                                    riego_top1_mm=b["riego_top1_mm"]))
                    for f in FEATURES:
                        if d[f[0]][f[1]] is None:  # napa sorteada "sin dato": quitarla no es ablación
                            continue
                        a = correr(d, e, f)
                        reg.append(dict(semilla=s, zona=z, parcela=k, escenario=e, feature=f[1], top1=a["top1"],
                                        cambia_top1=int(a["top1"] != b["top1"]),
                                        cambia_sec=None if a["nsec"] is None else int(a["nsec"] != b["nsec"]),
                                        riego_top1_mm=a["riego_top1_mm"]))
            print(f"semilla {s} lista ({time.time() - t0:.0f} s)", flush=True)
    marca = "no_informativo_margen" if margen_igual else "informativo"
    rng = random.Random(7)
    out = []
    for e in ESCENARIOS:
        for f in ["(base)"] + [x[1] for x in FEATURES]:
            for z in zonas + ["todas"]:
                filas = [r for r in reg if r["escenario"] == e and r["feature"] == f and (z == "todas" or r["zona"] == z)]
                if not filas:
                    continue
                t = ic([r["cambia_top1"] for r in filas], rng)
                q = ic([r["cambia_sec"] for r in filas if r["cambia_sec"] is not None], rng)
                porsem = [100 * sum(r["cambia_top1"] for r in filas if r["semilla"] == s) /
                          max(1, sum(1 for r in filas if r["semilla"] == s)) for s in range(A.semillas)]
                rg = sorted(r["riego_top1_mm"] for r in filas if r["riego_top1_mm"] is not None)
                out.append(dict(etiqueta=A.etiqueta, escenario=e, feature=f, zona=z, n=len(filas),
                                cambio_top1_pct=round(t[0], 1), ic95_lo=round(t[1], 1), ic95_hi=round(t[2], 1),
                                rango_semillas=f"{min(porsem):.1f}-{max(porsem):.1f}",
                                cambio_sec_pct=None if q[0] is None else round(q[0], 1),
                                sec_ic95=None if q[0] is None else f"{q[1]:.1f}-{q[2]:.1f}",
                                riego_top1_mm_mediana=rg[len(rg) // 2] if rg else None,
                                marca=marca if f != "(base)" else "base: % de parcelas cuyo top-1 difiere de " + ESCENARIOS[0]))
    dest = B / "modelo/experimentos"
    with open(dest / f"ranking_escenarios_motor_{A.etiqueta}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    with open(dest / f"ranking_escenarios_motor_{A.etiqueta}_parcelas.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(reg[0])); w.writeheader(); w.writerows(reg)
    ver.update(parcelas_por_zona=A.parcelas, semillas=A.semillas, marca=marca, margen_p50_igual_entre_escenarios=margen_igual,
               segundos=round(time.time() - t0), rangos_cew={k: v for k, v in CEW.items()})
    (dest / f"ranking_escenarios_motor_{A.etiqueta}_meta.json").write_text(json.dumps(ver, indent=1, ensure_ascii=False))
    print(json.dumps(ver, ensure_ascii=False))
    for r in out:
        if r["zona"] == "todas":
            print(r["escenario"], r["feature"], r["cambio_top1_pct"], f"[{r['ic95_lo']}, {r['ic95_hi']}]", r["rango_semillas"],
                  r["cambio_sec_pct"], r["marca"])


if __name__ == "__main__":
    main()
