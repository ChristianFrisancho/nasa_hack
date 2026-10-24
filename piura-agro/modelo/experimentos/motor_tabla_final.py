"""Ronda 5, punto 4: tabla final por cultivo y zona contra el MOTOR CONSOLIDADO (consolidado/motor, motor_rotacion v1).
Para cada zona y cultivo anual: decisión y puesto en la base, y qué pasa si falta cada dato.
Base (igual que la ablación de cew_motor.py): parcela de 1 ha en el punto de la zona, siembra en agosto, horizonte 6 meses,
escenario ICEN sin_el_nino (motor r6; antes "normal"), napa sin dato, CEw del río de la zona (Bajo: escenario 1.5 del motor), pH, profundidad y pendiente de
suelos/datos. Dos bases de ECe:
  zonal          ECe tal como está hoy en params/zonas.csv: Bajo [1.2, 12]; las otras 4 zonas desconocida (HWSD descartado).
  rango_global   las 4 zonas sin ECe reciben el rango hipótesis 0.5-12 de params/escenario_rangos.csv (no es dato).
Cambios: quitar ece_ds_m, ph, profundidad_cm, pendiente_pct, ecw_ds_m; agregar napa 1 m (somera) y napa 3 m.
Celda: "puesto/aceptados" si aceptado, "descartado", o "sin_datos". sec = secuencias de 2 cultivos viables que lo incluyen.
Se corre desde consolidado/motor. Salidas: experimentos/motor_tabla_final.csv (larga) y motor_tabla_final_resumen.csv."""
import csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cew_motor as CM  # noqa: E402
from motor_rotacion import evaluar, comparar_secuencias  # noqa: E402

CAMBIOS = [("base", None), ("sin_ece", ("suelo", "ece_ds_m")), ("sin_ph", ("suelo", "ph")),
           ("sin_profundidad", ("suelo", "profundidad_cm")), ("sin_pendiente", ("suelo", "pendiente_pct")),
           ("sin_cew", ("agua", "ecw_ds_m")), ("napa_1m", "napa1"), ("napa_3m", "napa3")]


def estado(c):
    r = evaluar(c)
    s = comparar_secuencias(c, 2)
    pos = {n: i + 1 for i, n in enumerate(r.ranking)}
    out = {}
    for e in r.evaluaciones:
        sec = sum(1 for x in s if x.viable and e.cultivo in x.cultivos)
        celda = f"{pos[e.cultivo]}/{len(r.ranking)}" if e.cultivo in pos else e.decision
        out[e.cultivo] = (celda, sec)
    return out


def main():
    filas = []
    for modo in ("zonal", "rango_global"):
        CM.ECE_MODO = "desconocida" if modo == "zonal" else "rango_global"
        for z, zm in CM.ZM.items():
            e0 = CM.CEW_RIO[zm] or 1.5
            for nombre, cam in CAMBIOS:
                if cam in ("napa1", "napa3"):
                    c = CM.consulta(z, 1.0 if cam == "napa1" else 3.0, e0)
                else:
                    c = CM.consulta(z, None, e0, quitar=cam)
                for cult, (celda, sec) in estado(c).items():
                    filas.append(dict(base_ece=modo, zona=z, cambio=nombre, cultivo=cult, celda=celda, sec_viables=sec))
            print(modo, z, flush=True)
    out = pathlib.Path(__file__).parent
    with open(out / "motor_tabla_final.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    # resumen ancho: una fila por (base_ece, zona, cultivo), una columna por cambio
    res = {}
    for f in filas:
        k = (f["base_ece"], f["zona"], f["cultivo"])
        res.setdefault(k, {"base_ece": k[0], "zona": k[1], "cultivo": k[2]})[f["cambio"]] = f"{f['celda']} ({f['sec_viables']})"
    with open(out / "motor_tabla_final_resumen.csv", "w", newline="") as fh:
        cols = ["base_ece", "zona", "cultivo"] + [n for n, _ in CAMBIOS]
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(res.values())

    escribir_md(filas, out / "motor_tabla_final.md")


def escribir_md(filas, ruta):
    """Tabla corta para resultados.md: cultivos del top-6 de la base rango_global, por zona."""
    idx = {(f["base_ece"], f["zona"], f["cambio"], f["cultivo"]): f for f in filas}

    def corta(f, base=None):
        c = f["celda"]
        t = c.split("/")[0] if "/" in c else ("s/d" if c == "sin_datos" else "desc.")
        if base is not None and f["sec_viables"] != base["sec_viables"]:
            t += f" (sec {base['sec_viables']}→{f['sec_viables']})"
        return t
    cab = ["Zona", "Cultivo", "Hoy (ECe zonal)", "Base (ECe 0.5-12)", "Sin ECe", "Sin pH", "Sin profundidad",
           "Sin pendiente", "Sin CEw", "Napa 1 m", "Hoy + napa 3 m"]
    L = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    nombres = {"chira_sullana": "Chira", "bajo_piura": "Bajo", "medio_piura": "Medio", "alto_piura": "Alto",
               "san_lorenzo": "San Lorenzo"}
    for z in CM.ZM:
        base = [f for f in filas if f["base_ece"] == "rango_global" and f["zona"] == z and f["cambio"] == "base"
                and "/" in f["celda"]]
        base.sort(key=lambda f: int(f["celda"].split("/")[0]))
        for b in base[:6]:
            cu = b["cultivo"]
            g = lambda cam, modo="rango_global": idx[(modo, z, cam, cu)]
            fila = [nombres[z], cu, corta(g("base", "zonal")), f"{b['celda']} (sec {b['sec_viables']})"]
            fila += [corta(g(c), b) for c in ("sin_ece", "sin_ph", "sin_profundidad", "sin_pendiente", "sin_cew",
                                              "napa_1m")]
            fila.append(corta(g("napa_3m", "zonal")))
            L.append("| " + " | ".join(fila) + " |")
    ruta.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
