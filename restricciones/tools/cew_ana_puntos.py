#!/usr/bin/env python3
"""R4-1: CE del agua superficial por punto (ANA-AAA Jequetepeque-Zarumilla, monitoreos oct-2024 UH Piura y UH Chira).
Coordenadas y zona: suelos/datos/cew_por_zona.csv de Piura Territorio (solo lectura). Cifra y unidad: releídas por mí
en el PDF del informe (fuentes_r4/*.txt), no copiadas de Territorio. Cada cifra se busca en el texto del PDF; si no
aparece, el script falla.  Escribe insumos/cew_ana_r4.csv.  Uso: python3 tools/cew_ana_puntos.py
"""
import csv, sys
from pathlib import Path
from contrato import normalizar
from balance_ionico_ana import D as IONES, EQ
BASE = Path(__file__).resolve().parents[1]
TERR = BASE.parent / "suelos" / "datos" / "cew_por_zona.csv"
OUT = BASE / "insumos" / "cew_ana_r4.csv"
C = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon",
     "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","fuente_primaria","subzona","fecha_consulta"]
PIU = ("ANA-AAA Jequetepeque-Zarumilla, Informe Técnico N.º 0076-2024-ANA-AAA.JZ/KFDB, I monitoreo participativo de calidad de recursos hídricos superficiales, UH 1378 Piura (21-25 oct 2024)",
       "https://siar.regionpiura.gob.pe/documentos/repositorio/php2IO9KS.PDF", "php2IO9KS.txt")
CHI = ("ANA-AAA Jequetepeque-Zarumilla, Informe Técnico N.º 0074-2024-ANA-AAA.JZ/KFDB, I monitoreo de calidad de recursos hídricos superficiales, UH 138 Chira (9-17 oct 2024, estiaje)",
       "https://siar.regionpiura.gob.pe/documentos/repositorio/phpyrdxHS.PDF", "phpyrdxHS.txt")
# punto -> (cifra tal como sale en la tabla de resultados del PDF, informe). Unidad impresa en la tabla: µs/cm.
PUB = {"QPfie1": ("172", PIU), "RPusm2": ("197", PIU), "RHuar3": ("510", PIU), "QSing1": ("61", PIU),
       "QSing2": ("348", PIU), "RBigo2": ("483", PIU), "RPiur2": ("741", PIU), "RPiur11": ("621", PIU), "RCmed1": ("345", PIU),
       "RPiur13": ("5980", PIU), "RPiur6": ("740", PIU),
       "QCarn1": ("10.4", PIU), "QSFran1": ("5", PIU), "RPiur4": ("9.03", PIU), "RPiur5": ("9.92", PIU),
       "RPbla1": ("90.3", CHI), "RSpab1": ("227", CHI), "RMaca1": ("334", CHI), "RQuir1": ("449", CHI), "RMaca4": ("436", CHI),
       "RQuir3": ("445", CHI), "RQuir2": ("591", CHI), "RChir2": ("514", CHI), "RChir3": ("590", CHI), "RChir4": ("665", CHI),
       "RChir11": ("848", CHI), "RChir6": ("1707", CHI), "RChir7": ("4980", CHI),
       "QTimb1": ("347", CHI), "RChip1": ("417", CHI), "RChip2": ("1877", CHI), "RChip4": ("888", CHI), "RChir12": ("4110", CHI)}
# Cifras impresas como µs/cm que son imposibles con los iones del mismo cuadro 6.3 (bicarbonatos 959-2377 mg/L, calcio 97-506 mg/L):
AMBIGUAS = {"QCarn1", "QSFran1", "RPiur4", "RPiur5"}
# Ronda 6 (H01/H02 de Agronomía): error de balance > 10 % -> no se elige una sola vía; valor = STD/640, rango = mín y máx de las vías
# (en RPiur4 el máximo es la lectura 9,03, que reproduce la vía de cationes 9,00).
CON_RANGO = {"QCarn1", "RPiur4"}
H03 = (" Nota H03 (Agronomía, ronda 6): el Gráfico 6.7 del informe, en µS/cm, muestra estos puntos casi en cero, así que el gráfico no"
       " justifica leerlos en mS/cm; lo que sostiene el orden de magnitud es el balance iónico punto a punto.")

def balance(p):
    """CE estimada por suma de cationes/10 y STD/640; la lectura 'cierra' como mS/cm si cae en [0,8 x mín, 1,2 x máx] de las dos."""
    d = IONES["QSfra1" if p == "QSFran1" else p]
    cat = sum(d[i] / EQ[i] for i in ("Ca", "Mg", "Na", "K")); an = sum(d[i] / EQ[i] for i in ("HCO3", "Cl", "SO4"))
    std = sum(d.values()); e1, e2, e3 = cat / 10, std / 640, an / 10; l = float(PUB[p][0]); err = 100 * (cat - an) / (cat + an)
    txt = (f"Ca {d['Ca']}, Mg {d['Mg']}, Na {d['Na']}, K {d['K']}, HCO3 {d['HCO3']}, Cl {d['Cl']}, SO4 {d['SO4']} mg/L; cationes {cat:.1f} meq/L, "
           f"aniones {an:.1f} meq/L (error de balance {100*(cat-an)/(cat+an):+.1f} %); CE estimada = cationes/10 = {e1:.2f} dS/m y STD/640 = {std:.0f}/640 = {e2:.2f} dS/m."
           + f" Tercera vía, suma de aniones/10 = {e3:.2f} dS/m"
           + (f" (con el cloruro impreso de {d['Cl']} mg/L, inverosímil en agua tan salina: esta vía queda sesgada hacia abajo y es una cota baja)." if d['Cl'] < 1 and err > 0 else
              (f" (aquí los aniones superan a los cationes, así que el cloruro impreso de {d['Cl']} mg/L no explica el descuadre)." if d['Cl'] < 1 else "."))
           + H03)
    return dict(cierra=0.8 * min(e1, e2) <= l <= 1.2 * max(e1, e2), txt=txt, std=std, e1=e1, e2=e2, e3=e3, err=err)

def main():
    textos = {s[2]: (BASE / "fuentes_r4" / s[2]).read_text(encoding="utf-8") for s in (PIU, CHI)}
    terr = {r["punto"]: r for r in csv.DictReader(TERR.open(encoding="utf-8")) if r["nivel"] == "punto" and "2024" in r["fecha_o_periodo"]}
    rows, err = [], []
    for p, (cifra, src) in PUB.items():
        t = terr.get(p)
        if not t: err.append(f"{p}: no está en cew_por_zona.csv"); continue
        if f" {cifra} " not in textos[src[2]].replace("\n", " "): err.append(f"{p}: '{cifra}' no aparece en {src[2]}"); continue
        base = dict(variable="ce_agua_riego", unidad="dS/m", cultivo="todos", variedad="", etapa="", zona=t["zona"], lugar=t["lugar"],
                    lat=t["lat"], lon=t["lon"], fecha_o_periodo=t["fecha_o_periodo"].split(" ")[0], fuente=src[0], url_o_doi=src[1],
                    tipo_evidencia="medicion_local", fuente_primaria="", subzona=p, fecha_consulta="2026-10-24", valor_min="", valor_max="")
        orig = f"Cifra original: {cifra} µs/cm (unidad impresa en la tabla de resultados del informe, verificada por Piura Datos en el PDF)."
        comun = (" Agua superficial (río o quebrada), muestra puntual en estiaje (oct-2024): no es CE en cabecera de parcela ni promedio anual."
                 " Coordenadas y zona tomadas de Piura Territorio (suelos/datos/cew_por_zona.csv).")
        bal = balance(p) if p in AMBIGUAS else None
        if p in CON_RANGO:
            vias = [bal["e1"], bal["e2"], bal["e3"]]
            lo, hi = min(vias), max(vias + ([float(cifra)] if bal["cierra"] else []))
            leida = (f"La lectura {cifra} (en mS/cm) coincide con la vía de cationes y se toma como techo del rango." if bal["cierra"] else
                     f"La lectura {cifra} leída como mS/cm ({cifra} dS/m) NO está soportada por la química: ninguna vía pasa de {max(vias):.2f} dS/m ({cifra} dS/m pediría unos {float(cifra)*10:.0f} meq/L de cationes y el cuadro da {bal['e1']*10:.1f}); no se usa.")
            base.update(valor=f"{bal['e2']:.2f}", valor_min=f"{lo:.2f}", valor_max=f"{hi:.2f}", estado="estimado", metodo="balance_ionico",
                        notas=(f"{orig} Ronda 6, reconciliado con Agronomía (H01/H02): {bal['txt']} Error de balance {bal['err']:+.1f} %, mayor que 10 %: "
                               f"no se elige una sola vía. Valor = STD/640 = {bal['e2']:.2f} dS/m; rango = de la vía más baja ({lo:.2f}) a la más alta ({hi:.2f}). {leida} "
                               "Leída como µS/cm daría " + f"{float(cifra)/1000:.4f}" + f" dS/m, imposible con {bal['std']:.0f} mg/L de sales. "
                               "Cálculo en tools/balance_ionico_ana.py y anexos/balance_ionico_ana.csv." + comun))
        elif bal and bal["cierra"]:
            base.update(valor=cifra, estado="estimado", metodo="balance_ionico",
                        notas=(f"{orig} Unidad decidida por balance iónico con cationes y aniones del mismo cuadro (informe de ensayo MA2434827): {bal['txt']} "
                               f"La cifra cierra como mS/cm (= dS/m): valor = {cifra} dS/m. Sin rango: una sola lectura; las dos estimaciones del balance no son un intervalo de la medición. Leída como µS/cm daría {float(cifra)/1000:.4f} dS/m, imposible con {bal['std']:.0f} mg/L de sales. "
                               f"Control con el mismo método: RPiur13 (5980 µS/cm) estima 6,02/5,88 dS/m y RPiur6 (740 µS/cm) 0,71/0,71 dS/m. "
                               "Cálculo en tools/balance_ionico_ana.py y anexos/balance_ionico_ana.csv." + comun))
        elif p in AMBIGUAS:
            base.update(valor="", estado="desconocido", metodo="ce_in_situ_unidad_ambigua",
                        notas=(f"{orig} Leída como µS/cm daría {float(cifra)/1000:.4f} dS/m, imposible: el mismo punto trae bicarbonatos de 959 a 2377 mg/L y calcio de 97 a 506 mg/L "
                               "(cuadro 6.3), lo que exige más de 1 dS/m. Leída como mS/cm daría {cifra} dS/m; Piura Territorio la usa así, pero su propio balance de aniones "
                               "da unas 2,5 veces menos en QCarn1. El informe solo declara fuera de ECA a RPiur13, lo que tampoco cuadra con la lectura en mS/cm. "
                               "Sin cifra fiable: valor vacío. Lo seguro es que el agua es salina (> 1 dS/m).").replace("{cifra}", cifra)
                        + f" Ronda 5, balance iónico con el mismo cuadro: {bal['txt']} No cierra ni como µS/cm ni como mS/cm (10,4 dS/m pediría ~100 meq/L de cationes): sigue desconocido." + comun)
        else:
            ds = float(cifra) / 1000
            base.update(valor=f"{ds:.4g}", estado="observado", metodo="ce_in_situ_monitoreo_ana",
                        notas=f"{orig} Conversión: µS/cm ÷ 1000 = dS/m. Sin rango: una sola lectura." + comun)
        rows.append(base)
    if err: print("\n".join("FALLA " + e for e in err)); sys.exit(1)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=C); w.writeheader(); w.writerows([normalizar(x) for x in rows])
    print(f"OK {len(rows)} puntos -> {OUT.relative_to(BASE)} ({sum(r['estado']=='observado' for r in rows)} observados, {sum(r['estado']=='estimado' for r in rows)} por balance iónico, {sum(r['estado']=='desconocido' for r in rows)} desconocidos)")
main()
