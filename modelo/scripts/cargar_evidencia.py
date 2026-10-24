"""Cargador de restricciones/evidencia_observada.csv con lint del CONTRATO (ronda 3).

Valida por codigo (no a mano) y escribe:
  resultados/lint_evidencia.csv  una fila por problema (nivel error/aviso, regla, id_registro, detalle)
  data/evidencia_modelo.csv      las cifras que el modelo usa, por variable, cultivo y zona del modelo, con fuente
Reglas del CONTRATO.md: 18 campos obligatorios; unidades SI o agricolas de la lista; tipo_evidencia y estado de las
listas; 'desconocido' => valor vacio; valor_min <= valor <= valor_max; analogo_externo y prediccion con notas.
Ademas: UTF-8, id_registro unico, duplicados de clave con cifras distintas, zona legible, lat/lon dentro de Piura.
Uso: python scripts/cargar_evidencia.py [--estricto]  (con --estricto sale con 1 si hay errores)
"""
import csv, re, sys, pathlib
import pandas as pd

B = pathlib.Path(__file__).resolve().parents[1]
SRC = B.parent / "restricciones/evidencia_observada.csv"
CONTRATO = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "lugar", "lat", "lon",
            "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado", "notas"]
UNID_CONTRATO = {"mm", "mm/día", "kg/ha", "t/ha", "dS/m", "cmol/kg", "%", "°C", "días", "PEN/ha"}
TIPOS = {"medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion"}
ESTADOS = {"observado", "estimado", "desconocido"}
LAT, LON = (-6.5, -3.3), (-81.5, -79.0)  # caja amplia del departamento de Piura
ZONA_RE = re.compile(r"Zona(?: asignada)?: ([^.]+)\.")
ZONA_MAP = {"Valle del Chira": ["chira_sullana"], "Medio y Bajo Piura": ["bajo_piura", "medio_piura"],
            "San Lorenzo": ["san_lorenzo"], "Alto Piura": ["alto_piura"]}
ZONA_COL = {"chira": "chira_sullana", "bajo_piura": "bajo_piura", "medio_piura": "medio_piura", "alto_piura": "alto_piura",
            "san_lorenzo": "san_lorenzo", "medio_bajo_piura": "medio_bajo_piura"}  # columna zona de Piura Datos (ronda 2)
CULT_MAP = {"arroz": "arroz", "maíz amarillo duro": "maiz_amarillo_duro", "algodón": "algodon", "frijol": "frijol",
            "frijol caupí": "caupi", "camote": "camote", "mango": "mango", "limón": "limon", "uva": "uva"}
csv.field_size_limit(10**9)


def num(s):
    try:
        return float(s) if str(s).strip() else None
    except ValueError:
        return "x"


def lint(d):
    p = []
    add = lambda nivel, regla, i, det: p.append(dict(nivel=nivel, regla=regla, id_registro=i, detalle=det))
    falt = [c for c in CONTRATO + ["id_registro"] if c not in d.columns]
    if falt:
        add("error", "cabecera", "", f"faltan columnas {falt}")
        return p
    if d.id_registro.duplicated().any():
        for i in d.id_registro[d.id_registro.duplicated()]:
            add("error", "id_duplicado", i, "id_registro repetido")
    for r in d.itertuples(index=False):
        i = r.id_registro
        for c in ["variable", "unidad", "cultivo", "lugar", "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia", "estado"]:
            if not str(getattr(r, c)).strip():
                add("error", "obligatorio_vacio", i, c)
        if r.unidad not in UNID_CONTRATO:
            add("aviso", "unidad_fuera_lista_contrato", i, r.unidad)
        if r.tipo_evidencia not in TIPOS:
            add("error", "tipo_evidencia", i, r.tipo_evidencia)
        if r.estado not in ESTADOS:
            add("error", "estado", i, r.estado)
        v, lo, hi = num(r.valor), num(r.valor_min), num(r.valor_max)
        if "x" in (v, lo, hi):
            add("error", "numero_invalido", i, f"{r.valor}|{r.valor_min}|{r.valor_max}")
            continue
        if r.estado == "desconocido" and any(x is not None for x in (v, lo, hi)):
            add("error", "desconocido_con_cifra", i, "")
        if r.estado != "desconocido" and v is None and (lo is None or hi is None):
            add("error", "sin_cifra_no_desconocido", i, "")
        if lo is not None and hi is not None and lo > hi:
            add("error", "min_mayor_max", i, f"{lo}>{hi}")
        if v is not None and ((lo is not None and v < lo) or (hi is not None and v > hi)):
            add("error", "valor_fuera_rango", i, f"{lo}<={v}<={hi}")
        if v is not None and lo is None and hi is None and "rango" not in r.notas.lower():
            add("aviso", "sin_rango_sin_explicacion", i, "CONTRATO pide que notas diga por que no hay rango")
        if r.tipo_evidencia in ("analogo_externo", "prediccion") and len(r.notas.strip()) < 20:
            add("error", "notas_insuficientes", i, r.tipo_evidencia)
        la, lo_ = num(r.lat), num(r.lon)
        if la not in (None, "x") and not (LAT[0] <= la <= LAT[1]):
            add("aviso", "lat_fuera_piura", i, r.lat)
        if lo_ not in (None, "x") and not (LON[0] <= lo_ <= LON[1]):
            add("aviso", "lon_fuera_piura", i, r.lon)
    clave = ["variable", "cultivo", "variedad", "etapa", "lugar", "fecha_o_periodo", "unidad"]
    g = d[d.estado != "desconocido"].groupby(clave).valor.nunique()
    for k in g[g > 1].index:
        add("aviso", "misma_clave_cifras_distintas", "", "|".join(map(str, k)))
    dr = d[d.variable.isin(["rendimiento", "precio_chacra"])]
    sin_zona = dr[~dr.notas.str.contains(r"Zona(?: asignada)?: [^.]+\.")]
    if len(sin_zona):
        add("aviso", "rendimiento_precio_sin_zona_en_notas", "", f"{len(sin_zona)} registros")
    return p


def extraer(d):
    """Cifras para el modelo con su fuente. Rendimiento DRAP por zona: mediana y n (todas las fuentes regionales observadas)."""
    out = []
    r = d[(d.variable == "rendimiento") & (d.estado == "observado") & (d.unidad == "t/ha")].copy()
    # ronda 4: Piura Datos agrego la columna zona (un solo formato). Si falta, se usa la zona de notas (formato r3).
    zc = r["zona"].map(ZONA_COL) if "zona" in r else pd.Series(index=r.index, dtype=object)
    zn = r.notas.str.extract(ZONA_RE)[0].map(lambda z: ZONA_MAP.get(z, [None])[0] if len(ZONA_MAP.get(z, [])) == 1 else None)
    r["zm"] = zc.fillna(zn)
    r["v"] = pd.to_numeric(r.valor, errors="coerce")
    # solo el extractor DRAP distrito-año (corregido por Piura Datos en ronda 3); el compendio INEI usa CDR, no distritos
    r = r[r.cultivo.isin(CULT_MAP) & (r.archivo_origen == "drap_distrito_anual.csv")].dropna(subset=["v"])
    r = r[~((r.cultivo == "algodón") & (r.fecha_o_periodo.astype(str).str.startswith("2015")))]  # ronda 4: algodon 2015 año parcial DRAP (igual que rend_zona.py)
    mb = r[r.zm.isin(["medio_piura", "bajo_piura", "medio_bajo_piura"])]
    for c in sorted(r.cultivo.unique()):
        for zm in ["chira_sullana", "bajo_piura", "medio_piura", "alto_piura", "san_lorenzo"]:
            g, nota = r[(r.cultivo == c) & (r.zm == zm)], f"zona '{zm}'"
            if zm in ("medio_piura", "bajo_piura") and len(g) < 3:  # como en r3: Medio y Bajo juntos si la zona sola no alcanza
                g, nota = mb[mb.cultivo == c], "Medio y Bajo Piura juntos (la zona sola tiene n<3)"
            if not len(g):
                continue
            out.append(dict(variable="rendimiento", cultivo=CULT_MAP[c], zona=zm, valor=g.v.median(), valor_min=g.v.quantile(.1),
                            valor_max=g.v.quantile(.9), n=len(g), unidad="t/ha", estado="observado", tipo_evidencia="regional",
                            fuente="; ".join(sorted(g.archivo_origen.unique())), ids="|".join(g.id_registro.head(5)),
                            notas=f"mediana de {len(g)} registros {nota} (Piura Datos)"))
    for var in ["dotacion_agua_riego", "dotacion_asignada", "eficiencia_operativa_riego", "fraccion_area_con_sales",
                "fraccion_area_drenaje_salinidad", "fraccion_area_napa_menor_1m", "fraccion_area_napa_1_a_1_5m", "ce_suelo",
                "agua_riego_consumo"]:
        for x in d[d.variable == var].itertuples(index=False):
            out.append(dict(variable=var, cultivo=x.cultivo, zona=x.lugar, valor=num(x.valor), valor_min=num(x.valor_min),
                            valor_max=num(x.valor_max), n=1, unidad=x.unidad, estado=x.estado, tipo_evidencia=x.tipo_evidencia,
                            fuente=x.fuente[:160], ids=x.id_registro, notas=x.notas[:200]))
    return pd.DataFrame(out)


def main():
    raw = SRC.read_bytes()
    raw.decode("utf-8")  # falla si no es UTF-8
    d = pd.read_csv(SRC, dtype=str, keep_default_na=False)
    p = pd.DataFrame(lint(d), columns=["nivel", "regla", "id_registro", "detalle"])
    p.to_csv(B / "resultados/lint_evidencia.csv", index=False)
    e = extraer(d)
    e.to_csv(B / "data/evidencia_modelo.csv", index=False)
    print(f"evidencia_observada.csv: {len(d)} filas; lint: {int((p.nivel == 'error').sum())} errores, {int((p.nivel == 'aviso').sum())} avisos")
    print(p.groupby(["nivel", "regla"]).size().to_string())
    print(f"evidencia_modelo.csv: {len(e)} filas")
    if "--estricto" in sys.argv and (p.nivel == "error").any():
        sys.exit(1)


if __name__ == "__main__":
    main()
