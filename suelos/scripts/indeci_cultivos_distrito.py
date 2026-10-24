#!/usr/bin/env python3
"""Lee la tabla de daños (cultivo afectado/perdido, ha) por distrito de un Informe de Emergencia INDECI (PDF).
Asigna cada número a la columna cuyo centro (fila DEPA.) está más cerca. Verifica que la suma de distritos = provincia.
Uso: indeci_cultivos_distrito.py <pdf> <pagina_1based> <salida.csv>"""
import sys, re, pdfplumber, pandas as pd
pdf, pag, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
p = pdfplumber.open(pdf).pages[pag - 1]
ws = p.extract_words(keep_blank_chars=False)
heads = [w for w in ws if w["text"] == "CULTIVO"]
assert len(heads) == 2, heads
rows = {}
for w in ws: rows.setdefault(round(w["top"]), []).append(w)
# fusionar filas con top a <=2 pt
keys = sorted(rows); merged = []
for k in keys:
    if merged and k - merged[-1][0] <= 2: merged[-1][1].extend(rows[k])
    else: merged.append([k, list(rows[k])])
def es_total(r): return any(w["text"] in ("DEPA.", "DPTO.") for w in r) and any(re.fullmatch(r"[\d.]+", w["text"]) for w in r) or (r and min(r, key=lambda w: w["x0"])["text"] == "TOTAL")
dep = next(r for _, r in merged if es_total(r))
nums = [w for w in dep if re.fullmatch(r"[\d.]+", w["text"])]
cent = [(w["x0"] + w["x1"]) / 2 for w in nums]
ca = min(range(len(cent)), key=lambda i: abs(cent[i] - (heads[0]["x0"] + heads[0]["x1"]) / 2))
cp = min(range(len(cent)), key=lambda i: abs(cent[i] - (heads[1]["x0"] + heads[1]["x1"]) / 2))
res = []
for _, r in merged:
    r = sorted(r, key=lambda w: w["x0"])
    t0 = r[0]["text"].replace("DISTR.", "DIST.")
    if t0 not in ("DEPA.", "DPTO.", "PROV.", "DIST.", "TOTAL"): continue
    lab = []; vals = {}
    for w in r[1:]:
        if re.fullmatch(r"[\d.]+", w["text"]) and w["x0"] > 140:
            c = (w["x0"] + w["x1"]) / 2
            j = min(range(len(cent)), key=lambda i: abs(cent[i] - c))
            vals[j] = float(w["text"])
        elif w["x0"] < 150: lab.append(w["text"])
    res.append(dict(nivel={"TOTAL": "DEPA"}.get(t0, t0.rstrip(".")), nombre=" ".join(lab), cultivo_afectado_ha=vals.get(ca, 0.0), cultivo_perdido_ha=vals.get(cp, 0.0)))
d = pd.DataFrame(res)
# control de sumas
prov = None; acc = {}
for _, x in d.iterrows():
    if x.nivel == "PROV":
        prov = x.nombre; acc[prov] = [x.cultivo_afectado_ha, x.cultivo_perdido_ha, 0, 0]
        if x.cultivo_afectado_ha == 0 and x.cultivo_perdido_ha == 0: acc[prov][:2] = [None, None]  # provincia sin total en la tabla
    elif x.nivel == "DIST": acc[prov][2] += x.cultivo_afectado_ha; acc[prov][3] += x.cultivo_perdido_ha
ok = True
for k, (a, b, sa, sb) in acc.items():
    if a is None: print(f"{k:12s} sin total de provincia; suma dist {sa:9.2f} {sb:9.2f}"); continue
    good = abs(a - sa) < 0.01 and abs(b - sb) < 0.01
    ok &= good
    print(f"{k:12s} prov {a:9.2f} {b:9.2f}  suma dist {sa:9.2f} {sb:9.2f} {'OK' if good else 'NO CUADRA'}")
dd = d[d.nivel.isin(["DEPA", "DPTO"])]
dpt = dd.loc[(dd.cultivo_afectado_ha + dd.cultivo_perdido_ha).idxmax()]
sd = d[d.nivel == "DIST"]
okd = abs(dpt.cultivo_afectado_ha - sd.cultivo_afectado_ha.sum()) < 0.05 and abs(dpt.cultivo_perdido_ha - sd.cultivo_perdido_ha.sum()) < 0.05
ok &= okd
print("depto", dpt.cultivo_afectado_ha, dpt.cultivo_perdido_ha, "suma dist", round(sd.cultivo_afectado_ha.sum(), 3), round(sd.cultivo_perdido_ha.sum(), 3), "OK" if okd else "NO CUADRA")
d["control_suma"] = "OK" if ok else "revisar"
d.to_csv(out, index=False)
