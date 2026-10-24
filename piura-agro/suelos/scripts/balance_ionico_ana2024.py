"""Balance iónico explícito de los 6 puntos ANA IT 0076-2024 (Cuadro 6.3, pp. 20-21) con iones mayores.
Salida: datos/balance_ionico_ana2024.csv (una fila por punto, sumas explícitas, CE con y sin cloruro, decisión).
Pesos equivalentes (g/eq): Ca 20.04, Mg 12.153, Na 22.99, K 39.10, HCO3 61.02, SO4 48.03, Cl 35.45.
CE ≈ Σ meq/L / 10 (USDA Handbook 60, Richards 1954). Tolerancia de electroneutralidad: Standard Methods 1030E.
"""
import os
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos")
PE = {"Ca": 20.04, "Mg": 12.153, "Na": 22.99, "K": 39.10, "HCO3": 61.02, "SO4": 48.03, "Cl": 35.45}
# mg/L del Cuadro 6.3 (Ca, Mg, Na, K, HCO3, SO4, Cl) y cifra de CE impresa (rótulo "µs/cm")
IONES = {
    "QCarn1": ((96.745, 52.188, 235.300, 0.54, 1137, 546, 0.11), "10.4"),
    "QSFran1": ((318.241, 96.819, 676.753, 3.45, 959, 1151, 0.21), "5"),
    "RPiur4": ((484.728, 163.356, 1198.125, 11.39, 2377, 797, 0.09), "9.03"),
    "RPiur5": ((505.794, 175.611, 1321.393, 6.72, 218, 1290, 3288), "9.92"),
    "RPiur13": ((290.616, 106.780, 845.146, 4.62, 237, 685, 1595), "5980"),
    "RPiur6": ((55.920, 16.460, 65.991, 2.21, 166, 69, 81), "740"),
}


def fila(p, mg, impreso):
    v = dict(zip(PE, mg))
    meq = {i: v[i] / PE[i] for i in PE}
    cat = sum(meq[i] for i in ("Ca", "Mg", "Na", "K"))
    an_cl = sum(meq[i] for i in ("HCO3", "SO4", "Cl"))
    an_sin = an_cl - meq["Cl"]
    cbe = 100 * (cat - an_cl) / (cat + an_cl)
    tol = 5 if an_cl > 10 else 2
    cl_impl = (cat - an_sin) * PE["Cl"]  # cloruro que cerraría el balance
    det = lambda ks: " + ".join(f"{i} {v[i]:g} mg/L / {PE[i]} = {meq[i]:.2f}" for i in ks)
    imp = float(impreso)
    ce_imp_uS = imp / 1000
    # Decisión
    if p in ("RPiur13", "RPiur6"):
        cl_cred, ce, est, dec = "sí", ce_imp_uS, "observado", (
            f"Unidad µS/cm coherente: {ce_imp_uS:.3f} dS/m frente a cationes/10 {cat/10:.2f} y aniones/10 {an_cl/10:.2f}. Punto de control.")
    elif p == "QCarn1":
        cl_cred, ce, est, dec = "no (0.11 mg/L con Na 235 mg/L), pero irrelevante: aniones sin Cl ya superan a cationes", None, "desconocido", (
            f"La cifra impresa leída en mS/cm (10.4 dS/m) es 3-5 veces las dos sumas ({cat/10:.2f} por cationes, {an_sin/10:.2f} por aniones sin Cl); "
            "en µS/cm (0.0104) es imposible. Las sumas no cierran entre sí (error "
            f"{cbe:+.1f} %): no hay una cifra defendible. Cota: agua salina ~1.9-3.0 dS/m, no usada como valor.")
    elif p in ("QSFran1", "RPiur4"):
        cl_cred, ce, est, dec = (f"no: {v['Cl']:g} mg/L con Na {v['Na']:g} mg/L; el balance pide ~{cl_impl:.0f} mg/L de Cl", imp, "estimado", (
            f"Sin el Cl impreso los aniones ({an_sin:.1f} meq/L) quedan {cat-an_sin:.1f} meq/L por debajo de los cationes; con él no cambia "
            f"({an_cl:.1f}). El Cl impreso no es creíble, así que la suma de aniones subestima. Los cationes no dependen del Cl: CE ≈ {cat/10:.2f} dS/m, "
            f"a {100*(imp-cat/10)/(cat/10):+.0f} % de la cifra impresa leída en mS/cm ({imp:g} dS/m). Se fija {imp:g} dS/m (impresa, confirmada por cationes)."))
    else:  # RPiur5
        cl_cred, ce, est, dec = (f"sí: {v['Cl']:g} mg/L, coherente con Na {v['Na']:g} mg/L (Na/Cl {meq['Na']/meq['Cl']:.2f} meq/meq)", imp, "estimado", (
            f"Sin Cl la suma de aniones ({an_sin:.1f} meq/L, {an_sin/10:.2f} dS/m) es imposible frente a cationes {cat:.1f}; con Cl ({an_cl:.1f}) "
            f"sobra {an_cl-cat:.1f} meq/L (error {cbe:+.1f} %, fuera de ±5 %). La impresa en mS/cm ({imp:g}) queda entre cationes/10 ({cat/10:.2f}) "
            f"y aniones/10 ({an_cl/10:.2f}), a {100*(imp-cat/10)/(cat/10):+.0f} % de los cationes. Se fija {imp:g} dS/m; rango = las dos sumas."))
    rmin = round(min(cat, an_cl if cl_cred.startswith("sí") else cat) / 10, 2) if ce is not None and p not in ("RPiur13", "RPiur6") else ""
    rmax = round(max(cat, an_cl) / 10, 2) if p == "RPiur5" else (round(max(cat / 10, imp), 2) if ce is not None and p not in ("RPiur13", "RPiur6") else "")
    if p in ("QSFran1", "RPiur4"):
        rmin, rmax = round(min(cat / 10, imp), 2), round(max(cat / 10, imp), 2)
    return dict(punto=p, ce_impresa=impreso, cationes_detalle=det(("Ca", "Mg", "Na", "K")), cationes_meq=round(cat, 2),
                aniones_detalle=det(("HCO3", "SO4", "Cl")), aniones_con_cl_meq=round(an_cl, 2), aniones_sin_cl_meq=round(an_sin, 2),
                error_balance_con_cl_pct=round(cbe, 1), error_balance_sin_cl_pct=round(100 * (cat - an_sin) / (cat + an_sin), 1), tolerancia_pct=tol,
                ce_cationes_dS_m=round(cat / 10, 2), ce_aniones_con_cl_dS_m=round(an_cl / 10, 2), ce_aniones_sin_cl_dS_m=round(an_sin / 10, 2),
                cl_que_cierra_mg_l=round(cl_impl), cl_impreso_creible=cl_cred, ce_impresa_como_uS_dS_m=ce_imp_uS, ce_impresa_como_mS_dS_m=imp,
                ce_adoptada_dS_m="" if ce is None else round(ce, 4), valor_min=rmin, valor_max=rmax, estado=est,
                metodo="ce_in_situ_monitoreo_ana" if p in ("RPiur13", "RPiur6") else "balance_ionico", decision=dec,
                fuente="ANA-AAA JZ, IT N.º 0076-2024, Cuadro 6.3 pp. 20-21 (informes MA2434827/28)")


if __name__ == "__main__":
    df = pd.DataFrame([fila(p, *x) for p, x in IONES.items()])
    # Cierre del coordinador (08:04): la cifra adoptada es la de Piura Datos (restricciones/aviso_territorio_cew.md + cierre),
    # no la de este balance. Este archivo queda como evidencia. La cifra impresa de QCarn1 se retira de todas partes.
    FINAL = {"RPiur4": (7.86, 5.56, 9.03), "QCarn1": (3.23, 1.94, 3.23), "QSFran1": (5.0, 3.97, 5.34), "RPiur5": (9.92, 9.73, 12.32)}  # Piura Datos 08:12
    df["ce_final_Datos_dS_m"] = df.punto.map(lambda p: FINAL[p][0] if p in FINAL else "")
    df["final_min"] = df.punto.map(lambda p: FINAL[p][1] if p in FINAL else "")
    df["final_max"] = df.punto.map(lambda p: FINAL[p][2] if p in FINAL else "")
    df["nota_final"] = df.punto.map(lambda p: "La cifra adoptada es la de Piura Datos (cierre del coordinador 08:04, precisión de Datos 08:12): "
                                    "metodo balance_ionico, estimado; las columnas ce_adoptada/valor_min/valor_max/decision de este archivo son la propuesta "
                                    "previa de Territorio y quedan solo como evidencia." if p in FINAL else "Punto de control; sin cambio.")
    m = df.punto == "QCarn1"
    for c in ("ce_impresa", "ce_impresa_como_uS_dS_m", "ce_impresa_como_mS_dS_m"): df[c] = df[c].astype(object); df.loc[m, c] = "retirada"
    df.loc[m, "decision"] = ("La cifra impresa no cierra con la química en ninguna unidad y se retira. Balance: cationes "
                             + df.loc[m, "ce_cationes_dS_m"].astype(str) + " dS/m, aniones con Cl " + df.loc[m, "ce_aniones_con_cl_dS_m"].astype(str) + " dS/m.")
    df.to_csv(os.path.join(D, "balance_ionico_ana2024.csv"), index=False)
    print(df[["punto", "cationes_meq", "aniones_con_cl_meq", "aniones_sin_cl_meq", "error_balance_con_cl_pct", "ce_cationes_dS_m",
              "ce_aniones_con_cl_dS_m", "ce_aniones_sin_cl_dS_m", "cl_que_cierra_mg_l", "ce_adoptada_dS_m", "valor_min", "valor_max", "estado"]].to_string())
