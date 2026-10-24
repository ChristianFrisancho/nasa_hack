#!/usr/bin/env python3
"""H06 (Agronomía, ronda 6; ampliado en ronda 7 a pedido de Territorio): dispersión ENTRE puntos de CE del agua por zona y tipo de
fuente (río, quebrada, canal, reservorio, pozo), sin mezclar tipos. No es la incertidumbre de una parcela.

Entradas: evidencia_observada.csv (ce_agua_riego y ce_agua_subterranea) y, sólo para leer, ../suelos/datos/cew_por_zona.csv de
Territorio (filas nivel=punto de pozo y reservorio que no están en mi tabla: PSI 2011 San Lorenzo, tesis UNP de Cura Mori y Castilla,
ERH IRHS asignado por Territorio a medio_piura y bajo_piura).
- Puntos con valor: mediana; P10-P90 sólo si n >= 5 (interpolación lineal); mín y máx de los puntos.
- Fuentes que sólo publican rango (pozos): no hay valores pozo por pozo (los Cuadros 9.5-9.9 del ERH son imágenes y el PDF no es
  accesible desde aquí), así que mediana y P10-P90 quedan vacíos; se da la envolvente de los rangos publicados y el número de pozos
  que declara cada fuente.
- 0.04 dS/m (IRHS-46, Piura) se marca dudoso y sale de la envolvente: ver DUDOSO.
Todo se redondea a 2 decimales con redondeo comercial (4.115 -> 4.12), igual que Territorio.
Escribe anexos/cew_resumen_zona.csv. Uso: python3 tools/cew_resumen_zona.py"""
import csv, re, statistics
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
B = Path(__file__).resolve().parents[1]
TERR = B.parent / "suelos" / "datos" / "cew_por_zona.csv"
DUDOSO = 0.04
NOTA_DUDOSO = ("0.04 dS/m (IRHS-46, Piura; ERH ANA cap. 9) es dudoso y queda fuera de la envolvente: 40 µS/cm es casi agua destilada, "
               "el mismo pozo trae dureza 0.02 ppm CaCO3 (también ~1000 veces menor que lo normal) y los demás pozos publicados del valle "
               "empiezan en 0.13-0.16 dS/m. Parece un error de unidad o de transcripción en la fuente; no se corrige, sólo se excluye.")
def r2(x):
    return "" if x is None else str(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
def tipo(variable, lugar, fuente_agua=""):
    if fuente_agua: return fuente_agua
    l = lugar.lower()
    if variable == "ce_agua_subterranea" or "pozo" in l: return "pozo"
    for k, t in (("reservorio", "reservorio"), ("canal", "canal"), ("quebrada", "quebrada"), ("río", "rio"), ("rio ", "rio")):
        if l.startswith(k) or f" {k}" in l[:25]: return t
    return "desconocido"
def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)
def n_pozos(*txt):
    m = re.search(r"(\d+) pozos", " ".join(txt)); return int(m.group(1)) if m else None
def main():
    g = {}
    def grupo(z, t): return g.setdefault((z, t), dict(v=[], est=0, rangos={}, sin=0, pts=[], terr=[]))
    for r in csv.DictReader(open(B / "evidencia_observada.csv", encoding="utf-8")):
        if r["variable"] not in ("ce_agua_riego", "ce_agua_subterranea"): continue
        e = grupo(r["zona"], tipo(r["variable"], r["lugar"]))
        if r["valor"]:
            e["v"].append(float(r["valor"])); e["est"] += r["estado"] == "estimado"; e["pts"].append(f"{r['subzona'] or r['lugar'][:30]}={r['valor']}")
        elif r["valor_min"]:  # rango sin valor central; los duplicados (mismo rango y lugar) cuentan una vez
            e["rangos"][(r["lugar"], r["valor_min"], r["valor_max"])] = (float(r["valor_min"]), float(r["valor_max"]), n_pozos(r["lugar"], r["metodo"], r["notas"]), r["estado"])
        else: e["sin"] += 1
    if TERR.exists():
        for r in csv.DictReader(open(TERR, encoding="utf-8")):
            if r.get("nivel") != "punto" or r.get("fuente_agua") not in ("pozo", "reservorio"): continue
            e = grupo(r["zona"], r["fuente_agua"]); e["terr"].append(r["punto"])
            if r["valor"]:
                e["v"].append(float(r["valor"])); e["pts"].append(f"{r['punto']}={r['valor']} (Territorio)")
            elif r["valor_min"]:
                e["rangos"][(r["punto"], r["valor_min"], r["valor_max"])] = (float(r["valor_min"]), float(r["valor_max"]), n_pozos(r["lugar"], r["metodo"], r["notas"]), r["estado"])
    out = []
    for (z, t), e in sorted(g.items()):
        v = e["v"]; n = len(v); rg = list(e["rangos"].values())
        mins = [a for a, b, k, s in rg if a != DUDOSO]; maxs = [b for a, b, k, s in rg]
        hubo_dudoso = any(a == DUDOSO for a, b, k, s in rg)
        npz = [k for a, b, k, s in rg if k]
        nota = "Dispersión entre puntos de la zona; NO es la incertidumbre de una parcela."
        if n: nota += " Puntos superficiales: muestras puntuales oct-2024 (estiaje); los estimados por balance entran con su valor central (rango en insumos/cew_ana_r4.csv)."
        if n and n < 5: nota += " n < 5: P10-P90 no se calcula; mín-máx sólo describe los puntos."
        if rg: nota += (f" {len(rg)} fuente(s) con sólo rango publicado ({'+'.join(str(k) for k in npz) or '?'} pozos declarados): sin valores pozo por pozo, "
                        "mediana y P10-P90 quedan vacíos; rango_min/max_publicado es la envolvente de los rangos.")
        if hubo_dudoso: nota += " " + NOTA_DUDOSO
        if any(s == "estimado" for a, b, k, s in rg): nota += " Incluye la clase C3 (0.75-2.25 dS/m) que el ERH da para la mayoría de los pozos: estimado."
        if e["terr"]: nota += f" Puntos tomados de suelos/datos/cew_por_zona.csv (Territorio, sólo lectura): {', '.join(e['terr'])}."
        if not n and not rg: nota += " Sin cifra: desconocido."
        out.append(dict(zona=z, tipo_fuente_agua=t, n_puntos=n, n_estimados_balance=e["est"],
                        mediana_dS_m=r2(statistics.median(v)) if n else "", p10_dS_m=r2(pct(v, .1)) if n >= 5 else "",
                        p90_dS_m=r2(pct(v, .9)) if n >= 5 else "", min_dS_m=r2(min(v)) if n else "", max_dS_m=r2(max(v)) if n else "",
                        filas_solo_rango=len(rg), n_pozos_declarados=sum(npz) if npz else "",
                        rango_min_publicado=r2(min(mins)) if mins else "", rango_max_publicado=r2(max(maxs)) if maxs else "",
                        excluido_dudoso=r2(DUDOSO) if hubo_dudoso else "", filas_sin_cifra=e["sin"], puntos=";".join(e["pts"]), nota=nota))
    with open(B / "anexos/cew_resumen_zona.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(f"OK {len(out)} filas -> anexos/cew_resumen_zona.csv")
if __name__ == "__main__":
    main()
