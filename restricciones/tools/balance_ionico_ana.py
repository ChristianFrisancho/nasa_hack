#!/usr/bin/env python3
"""Balance iónico de las 4 lecturas de CE ambiguas del IT ANA 0076-2024 (UH Piura, oct-2024), con cationes y aniones del
mismo informe (fuentes_r4/php2IO9KS.txt, Cuadro de resultados, informes de ensayo MA2434827/MA2434828). RPiur13 y RPiur6, del
mismo cuadro y con CE inequívoca en µS/cm, sirven de control. Salida: anexos/balance_ionico_ana.csv
CE estimada (dS/m) por dos vías: suma de cationes (meq/L) / 10 y STD (suma de iones, mg/L) / 640 (USSL, Richards 1954)."""
import csv
from pathlib import Path
B = Path(__file__).resolve().parents[1]
CE_LEIDA = {"QCarn1": 10.4, "QSfra1": 5, "RPiur4": 9.03, "RPiur5": 9.92, "RPiur13": 5980, "RPiur6": 740}  # µS/cm en el cuadro
# mg/L, transcritos del cuadro (líneas ~1340-1436 del texto). Cl de QCarn1/QSfra1/RPiur4 tal como figura (0,11 / 0,21 / 0,09).
D = {"QCarn1": dict(Ca=96.745, Mg=52.188, Na=235.300, K=0.54, HCO3=1137, Cl=0.11, SO4=546),
     "QSfra1": dict(Ca=318.241, Mg=96.819, Na=676.753, K=3.45, HCO3=959, Cl=0.21, SO4=1151),
     "RPiur4": dict(Ca=484.728, Mg=163.356, Na=1198.125, K=11.39, HCO3=2377, Cl=0.09, SO4=797),
     "RPiur5": dict(Ca=505.794, Mg=175.611, Na=1321.393, K=6.72, HCO3=218, Cl=3288, SO4=1290),
     "RPiur13": dict(Ca=290.616, Mg=106.780, Na=845.146, K=4.62, HCO3=237, Cl=1595, SO4=685),
     "RPiur6": dict(Ca=55.920, Mg=16.460, Na=65.991, K=2.21, HCO3=166, Cl=81, SO4=69)}
EQ = dict(Ca=20.04, Mg=12.15, Na=22.99, K=39.10, HCO3=61.02, Cl=35.45, SO4=48.03)
def main():
    out = []
    for p, d in D.items():
        cat = sum(d[i] / EQ[i] for i in ("Ca", "Mg", "Na", "K")); an = sum(d[i] / EQ[i] for i in ("HCO3", "Cl", "SO4"))
        err = 100 * (cat - an) / (cat + an); std = sum(d.values())
        ce_cat, ce_std = cat / 10, std / 640
        l = CE_LEIDA[p]
        out.append(dict(punto=p, ce_leida=l, cationes_meq=round(cat, 1), aniones_meq=round(an, 1), error_balance_pct=round(err, 1),
                        std_mg_l=round(std), ce_est_cationes_dS_m=round(ce_cat, 2), ce_est_std_dS_m=round(ce_std, 2), ce_est_aniones_dS_m=round(an / 10, 2),
                        si_uS_cm_dS_m=l / 1000, si_mS_cm_dS_m=l))
    with (B / "anexos/balance_ionico_ana.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    for r in out: print(r)
if __name__ == "__main__":
    main()
