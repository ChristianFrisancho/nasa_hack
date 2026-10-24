#!/usr/bin/env python3
"""Extrae tablas de rendimiento y precio en chacra de los Compendios INEI Piura
(texto de pdftotext -layout en restricciones/fuentes/) a un CSV crudo en
restricciones/insumos/compendio_inei.csv con las columnas del CONTRATO.

Reglas de atípicos (registradas en decisions.tsv):
  A1 serie regional: valor > 1,8 x mediana de los otros años del mismo cultivo -> vacío, desconocido.
  A2 tabla por CDR: valor > 2,5 x máximo regional no atípico del cultivo -> vacío, desconocido.
Uso: python3 tools/extraer_pdfs.py
"""
import csv, re, statistics, sys, unicodedata
sys.path.insert(0, __import__('os').path.dirname(__file__))
from zonas import MEDIO_BAJO
from contrato import normalizar
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FUENTES = BASE / "fuentes"
SALIDA = BASE / "insumos" / "compendio_inei.csv"

CAMPOS = ["variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona",
          "lugar", "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi", "metodo",
          "tipo_evidencia", "estado", "notas", "fecha_consulta"]

DOCS = {
    "2017": dict(txt="inei_compendio_piura_2017.txt",
                 fuente="INEI, Compendio Estadístico Piura 2017 (fuente primaria MINAGRI / DRA Piura - Agencias Agrarias)",
                 url="https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1505/libro.pdf"),
    "2025": dict(txt="inei_compendio_piura_2025.txt",
                 fuente="INEI, Compendio Estadístico Piura 2025 (fuente primaria MIDAGRI)",
                 url="INEI CompDptal2025 (URL exacta no verificada); copia local restricciones/fuentes/inei_compendio_piura_2025.pdf"),
}

# (doc, título exacto que inicia la tabla, tipo, años o columnas)
CDR = ["Total", "Piura", "Chulucanas", "San Lorenzo", "Chira", "Huancabamba", "Huarmaca", "Ayabaca"]
# CDR Piura (agencia agraria Piura) junta Medio y Bajo Piura: zona medio_bajo_piura (CONTRATO 24-oct).
ZONA = {"Total": "piura_region", "Piura": MEDIO_BAJO, "Chulucanas": "alto_piura",
        "San Lorenzo": "san_lorenzo", "Chira": "chira", "Huancabamba": "sierra_piura",
        "Huarmaca": "sierra_piura", "Ayabaca": "sierra_piura"}
TABLAS = [
    ("2017", "12.8 PIURA: RENDIMIENTO POR HECTÁREA", "serie_rend", [str(a) for a in range(2010, 2017)]),
    ("2017", "12.9 PIURA: RENDIMIENTO TÉCNICO POR CENTRO DE DESARROLLO RURAL, SEGÚN PRINCIPALES PRODUCTOS, 2016", "cdr_rend", "2016"),
    ("2017", "12.9 PIURA: RENDIMIENTO TÉCNICO POR CENTRO DE DESARROLLO RURAL, SEGÚN PRINCIPALES PRODUCTOS, 2015", "cdr_rend", "2015"),
    ("2017", "12.13 PIURA: PRECIOS PROMEDIOS EN CHACRA", "serie_precio", [str(a) for a in range(2010, 2017)]),
    ("2025", "12.9 PIURA: RENDIMIENTO POR HECTÁREA", "serie_rend", [str(a) for a in range(2020, 2025)]),
    ("2025", "12.10 PIURA: RENDIMIENTO TÉCNICO POR CENTRO DE DESARROLLO RURAL", "cdr_rend", "2024"),
    ("2025", "12.14 PIURA: PRECIOS PROMEDIOS EN CHACRA", "serie_precio", [str(a) for a in range(2020, 2025)]),
]

# Nombres rotos por pdftotext y sinónimos -> cultivo canónico
CANON = {
    "arroz": "arroz", "arroz cascara": "arroz", "limon": "limón", "limon sutil": "limón", "limonero": "limón",
    "mango": "mango", "mango ciruelo": "mango ciruelo", "palto": "palta", "palta": "palta",
    "uva": "uva", "vid": "uva", "platano": "banano/plátano", "banano o platano": "banano/plátano",
    "platano convencional": "banano/plátano convencional", "platano organico": "banano/plátano orgánico",
    "maiz amarillo duro": "maíz amarillo duro", "maiz amilaceo": "maíz amiláceo", "maiz choclo": "choclo",
    "choclo": "choclo", "algodon": "algodón", "algodon rama": "algodón", "frijol castilla o caupi": "frijol caupí",
    "frijol castilla": "frijol caupí", "frijol grano seco": "frijol grano seco (agregado)",
    "frijol grano seco sierra": "frijol grano seco sierra", "frijol de palo": "frijol de palo",
    "frijol loc tao": "frijol loctao", "cacao": "cacao", "cafe": "café", "cafe pergamino": "café",
    "cana para etanol": "caña etanol", "cana de azucar etanol": "caña etanol", "cana azucar": "caña de azúcar",
    "cana de azucar": "caña de azúcar", "cana para alcohol": "caña de azúcar", "soya": "soya", "soy a": "soya",
    "uv a": "uva", "papay a": "papaya", "papayo": "papaya", "papay o": "papaya", "papaya": "papaya",
    "maracuy a": "maracuyá", "chirimoy a": "chirimoya", "arv eja grano seco": "arveja grano seco",
    "arv eja grano v erde": "arveja grano verde", "arveja grano seco": "arveja grano seco",
    "arveja grano verde": "arveja grano verde", "platano conv encional": "banano/plátano convencional",
    "naranjo": "naranja", "naranja": "naranja", "haba grano seco": "haba", "haba": "haba",
    "cebada grano": "cebada", "cebada": "cebada", "aji paprika": "ají páprika", "aji piquillo": "ají piquillo",
    "cocotero": "cocotero", "esparrago": "espárrago", "lucuma": "lúcuma", "mani": "maní", "melon": "melón",
    "sandia": "sandía", "sorgo grano": "sorgo grano", "sorgo escobero": "sorgo escobero",
}

def sin_tilde(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def canon(nombre):
    k = re.sub(r"\s+", " ", sin_tilde(nombre).lower().replace("/p", "")).strip()
    k = k.replace("sutil", "sutil")
    return CANON.get(k, k)

def num(tok):
    tok = tok.strip()
    if tok in ("-", ""):
        return None
    return float(tok.replace(" ", "").replace(",", "."))

FILA = re.compile(r"^\s*([A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ /\.\-]*?)\s{2,}(.*\S)\s*$")
TOK = re.compile(r"-|\d+(?:,\d+)?")

def filas(lineas, inicio, n_cols):
    """Devuelve [(nombre, [valores])] desde la línea del título hasta 'Fuente'."""
    out = []
    for ln in lineas[inicio + 1:]:
        plano = ln.replace(" ", "")
        if plano.startswith("Fuente") or plano.startswith("Fuente:") or plano.lower().startswith("fuente"):
            break
        m = FILA.match(ln)
        if not m:
            continue
        nombre, resto = m.group(1).strip(), m.group(2)
        toks = TOK.findall(resto)
        if nombre.lower().startswith("principales"):
            continue  # fila de encabezado con años
        if not toks or re.search(r"[A-Za-z]", resto.replace("P", "")):
            continue  # encabezados
        if len(toks) != n_cols:
            raise SystemExit(f"ERROR fila '{nombre}': {len(toks)} valores, se esperaban {n_cols}: {resto!r}")
        out.append((nombre, [num(t) for t in toks]))
    if not out:
        raise SystemExit(f"ERROR tabla vacía en línea {inicio + 1}")
    return out

def fmt(v):
    return "" if v is None else f"{v:g}"

def main():
    hoy = "2026-10-24"
    registros, series_rend = [], {}
    tablas = []
    for doc, titulo, tipo, cols in TABLAS:
        d = DOCS[doc]
        lineas = (FUENTES / d["txt"]).read_text(encoding="utf-8").splitlines()
        idx = [i for i, l in enumerate(lineas) if l.strip().startswith(titulo)]
        if len(idx) != 1:
            raise SystemExit(f"ERROR: título '{titulo}' aparece {len(idx)} veces en {d['txt']}")
        n = len(cols) if isinstance(cols, list) else len(CDR)
        tablas.append((doc, titulo, tipo, cols, filas(lineas, idx[0], n), d))
    # 1) series regionales de rendimiento por cultivo. A1 se evalúa dentro de cada tabla (década),
    #    porque entre compendios cambian definiciones (p. ej. café pergamino).
    atipico_reg, motivo = set(), {}
    for doc, titulo, tipo, cols, fs, d in tablas:
        if tipo != "serie_rend":
            continue
        for nombre, vals in fs:
            c = canon(nombre)
            por_anio = {a: v for a, v in zip(cols, vals) if v is not None}
            for a, v in por_anio.items():
                series_rend.setdefault(c, {})[a] = v
                otros = [x for b, x in por_anio.items() if b != a]
                if len(otros) >= 2 and v > 1.8 * statistics.median(otros):
                    atipico_reg.add((c, a)); motivo[(c, a)] = "regla A1 (>1,8 x mediana de otros años de la misma tabla)"
            # A3: columna 2022 del Compendio 2025 en filas sin 2023-2024 (perennes) con saltos sistemáticos
            if doc == "2025" and "2022" in por_anio and "2023" not in por_anio and "2024" not in por_anio:
                base = [por_anio[a] for a in ("2020", "2021") if a in por_anio]
                if base and por_anio["2022"] > 1.5 * statistics.mean(base) and (c, "2022") not in atipico_reg:
                    atipico_reg.add((c, "2022")); motivo[(c, "2022")] = "regla A3 (columna 2022 de perennes con saltos sistemáticos en la tabla: vid 900,1, mango 105,2; >1,5 x media 2020-21)"
    ref_max = {}
    for c, por_anio in series_rend.items():
        ok = [v for a, v in por_anio.items() if (c, a) not in atipico_reg]
        if ok:
            ref_max[c] = max(ok)
    # totales departamentales de las tablas CDR también sirven de referencia
    for doc, titulo, tipo, cols, fs, d in tablas:
        if tipo == "cdr_rend":
            for nombre, vals in fs:
                c = canon(nombre)
                if vals[0] is not None and (c not in series_rend or vals[0] <= 1.8 * ref_max.get(c, vals[0])):
                    ref_max[c] = max(ref_max.get(c, 0), vals[0])
    for doc, titulo, tipo, cols, fs, d in tablas:
        tabla_id = titulo.split(" PIURA")[0]
        for nombre, vals in fs:
            c = canon(nombre)
            pares = list(zip(cols, vals)) if isinstance(cols, list) else list(zip(CDR, vals))
            for clave, v in pares:
                if v is None:
                    continue
                prelim = doc == "2025" and tipo == "serie_precio" and clave in ("2023", "2024")
                notas = [f"Tabla {tabla_id}, fila '{nombre}'."]
                estado, valor = "observado", fmt(v)
                zona = "piura_region"
                if tipo == "serie_precio":
                    variable, unidad = "precio_chacra", "PEN/kg"
                    lugar, periodo = "Piura (departamento)", clave
                    metodo = "Precio promedio en chacra pagado al productor, promedio anual departamental (MIDAGRI); copiado de tabla del compendio"
                    if c == "algodón" and doc == "2025":
                        estado, valor = "desconocido", ""
                        notas.append(f"Cifra publicada {fmt(v)} PEN/kg descartada: fila idéntica a alfalfa y ~10 veces menor que 2010-2016 (2,58-4,23).")
                    if prelim:
                        if estado != "desconocido":
                            estado = "estimado"
                        notas.append("Cifra preliminar (2023/P, 2024/P) según la fuente.")
                elif tipo == "serie_rend":
                    variable, unidad = "rendimiento", "t/ha"
                    lugar, periodo = "Piura (departamento)", clave
                    metodo = "Rendimiento promedio departamental = producción / superficie cosechada (MIDAGRI); copiado de tabla del compendio"
                    if (c, clave) in atipico_reg:
                        estado, valor = "desconocido", ""
                        notas.append(f"Cifra publicada {fmt(v)} t/ha descartada por {motivo[(c, clave)]}.")
                else:
                    variable, unidad = "rendimiento", "t/ha"
                    lugar, periodo = (f"CDR {clave}" if clave != "Total" else "Piura (departamento, total de los CDR)"), cols
                    metodo = "Rendimiento técnico por Centro de Desarrollo Rural (agencias agrarias DRA Piura / MIDAGRI); copiado de tabla del compendio"
                    zona = ZONA[clave]
                    r = ref_max.get(c) or ref_max.get(re.sub(r" (convencional|orgánico)$", "", c))
                    if re.search(r" (convencional|orgánico)$", c):
                        r = max(r or 0, ref_max.get(re.sub(r" (convencional|orgánico)$", "", c), 0))
                    if r and v > 2.5 * r:
                        estado, valor = "desconocido", ""
                        notas.append(f"Cifra publicada {fmt(v)} t/ha descartada por regla A2 (>2,5 x máximo regional {fmt(r)}).")
                    if c == "uva" and cols == "2016":
                        notas.append("Uva 2016 ≈47,9 t/ha en todos los CDR: posible relleno con el promedio; usar con cautela.")
                registros.append(dict(variable=variable, valor=valor, valor_min="", valor_max="", unidad=unidad,
                                      cultivo=c, variedad="", etapa="cosecha", zona=zona, lugar=lugar, lat="", lon="",
                                      fecha_o_periodo=periodo, fuente=d["fuente"], url_o_doi=d["url"],
                                      metodo=metodo, tipo_evidencia="regional", estado=estado,
                                      notas=" ".join(notas + ["Sin rango publicado: valor_min/valor_max vacíos."]),
                                      fecha_consulta=hoy))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows([normalizar(r) for r in registros])
    des = sum(r["estado"] == "desconocido" for r in registros)
    print(f"OK {len(registros)} registros -> {SALIDA} ({des} desconocidos por atípico)")

if __name__ == "__main__":
    main()
