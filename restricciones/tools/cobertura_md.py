#!/usr/bin/env python3
"""cobertura.csv + anexos/huecos_priorizados.csv -> cobertura.md (matriz cultivo x suelo x zona por tipo_evidencia y huecos).
Uso: python3 tools/cobertura.py && python3 tools/cobertura_md.py"""
from pathlib import Path
import pandas as pd
B = Path(__file__).resolve().parents[1]
d = pd.read_csv(B / "cobertura.csv")
h = pd.read_csv(B / "anexos" / "huecos_priorizados.csv")
CULT = ["arroz", "maíz amarillo duro", "algodón", "frijol", "frijol caupí", "frijol verde", "frijol de palo", "papaya", "camote", "quinua",
        "limón", "mango", "uva", "todos"]
Z = ["chira", "medio_piura", "bajo_piura", "medio_bajo_piura", "san_lorenzo", "alto_piura", "sierra_piura", "piura_region", "fuera de Piura"]
S = ["genérico", "salino_sódico", "tablazo_arenoso"]
T = [("medicion_local", "ML"), ("regional", "R"), ("bibliografico", "B"), ("analogo_externo", "AE"), ("prediccion", "P"), ("desconocido", "desc.")]
g = d.groupby(["cultivo", "suelo", "zona"])[[f"n_{t}" for t, _ in T] + ["n_registros"]].sum().reset_index()
g["o"] = g.cultivo.map(CULT.index) * 1000 + g.suelo.map(S.index) * 100 + g.zona.map(Z.index)
g = g.sort_values("o")
lin = ["| cultivo | suelo | zona | " + " | ".join(a for _, a in T) + " | total |", "|" + "---|" * (len(T) + 4)]
for _, r in g.iterrows():
    lin.append(f"| {r.cultivo} | {r.suelo} | {r.zona} | " + " | ".join(str(int(r[f'n_{t}'])) or "0" for t, _ in T) + f" | {int(r.n_registros)} |")
MOD_C = ["arroz", "maíz amarillo duro", "algodón", "frijol", "frijol caupí", "camote"]
MOD_Z = ["chira", "medio_piura", "bajo_piura", "san_lorenzo", "alto_piura"]
hay = set(zip(g.cultivo, g.zona))
vac = [f"{c} en {z}" for c in MOD_C for z in MOD_Z if (c, z) not in hay]
hl = ["| # | cultivo | zona | feature | rango del feature | importancia | lo más cercano |", "|---|---|---|---|---|---|---|"]
for _, r in h.head(30).iterrows():
    hl.append(f"| {r.prioridad} | {r.cultivo} | {r.zona} | {r.feature} | {r.rango_en_cultivo_zona} | {r.importancia:.1f} | {r.lo_mas_cercano} |")
if len(h) > 30: hl.append(f"\nSe muestran 30 de {len(h)}; el resto está en `anexos/huecos_priorizados.csv`.")
res = "; ".join(f"{k} {v}" for k, v in h.feature.value_counts().items()) + f". Total {len(h)} huecos; en {int((h.lo_mas_cercano == 'nada').sum())} no hay ni un reemplazo."
n = sum(1 for _ in open(B / "evidencia_observada.csv", encoding="utf-8")) - 1
txt = (B / "tools" / "cobertura_plantilla.md").read_text(encoding="utf-8")
txt = txt.replace("{matriz}", "\n".join(lin)).replace("{huecos}", "\n".join(hl)).replace("{resumen}", res).replace("{n}", str(n))
txt = txt.replace("{vacias}", (", ".join(vac) + f" ({len(vac)} de {len(MOD_C) * len(MOD_Z)})") if vac else "ninguna")
(B / "cobertura.md").write_text(txt, encoding="utf-8")
print(f"OK cobertura.md ({len(g)} filas de matriz, {len(h)} huecos)")
