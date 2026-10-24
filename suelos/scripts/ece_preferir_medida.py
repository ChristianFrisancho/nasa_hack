"""Pasa HWSD a contexto en datos/zonas_ece_drenaje_fen.csv y pone la CE medida en chacra
(Piura Datos, restricciones/evidencia_observada.csv) como fuente preferente. Idempotente:
correr después de zonas_ece_drenaje_fen.py."""
import os, pandas as pd
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(B, "datos", "zonas_ece_drenaje_fen.csv")
EV = "/workspace/piura-agro/restricciones/evidencia_observada.csv"
d = pd.read_csv(P, dtype=object)
ev = pd.read_csv(EV, dtype=str).drop_duplicates("id_registro").set_index("id_registro")
AVISO = {"chira": "HWSD contradice CE medida en chacra (0.10 dS/m, Sullana 2024) frente a 1.36 de HWSD",
         "medio_piura": "HWSD contradice CE medida en chacra (0.95 dS/m, UNP Túpac Amaru 2013-14) frente a 2.74 de HWSD",
         "bajo_piura": "HWSD contradice CE medida en chacra (3.44-8.2 dS/m, Tablazo Sur La Unión 2024, 40 predios) frente a 1.51 de HWSD",
         "alto_piura": "HWSD contradice CE medida en chacra (0.46-0.6 dS/m, El Huaro 2021) frente a 1.15 de HWSD"}
SUFIJO = " (fuente: Piura Datos, ver su carpeta en /workspace/piura-agro/restricciones/evidencia_observada.csv). Solo contexto: no usar como ECe."
# 1) HWSD -> contexto
hw = d.variable.isin(["ECe_0_20cm", "ECe_40_60cm", "fraccion_suelo_salino_EC_ge_4"]) & d.fuente.fillna("").str.contains("HWSD")
for i in d.index[hw]:
    z = d.at[i, "zona"]
    av = AVISO.get(z, "HWSD sin CE medida en chacra para validar en esta zona y contradicho en las 4 zonas que sí la tienen (Chira, Medio, Bajo y Alto Piura)")
    d.at[i, "variable"] = d.at[i, "variable"] + "_HWSD2_contexto"
    d.at[i, "notas"] = av + SUFIJO + " " + str(d.at[i, "notas"] or "")
# 2) ECe_0_20cm sin HWSD: desconocido, apunta a la medida
for (z, s), g in d[d.variable == "ECe_0_20cm_HWSD2_contexto"].groupby(["zona", "subzona"]):
    if ((d.variable == "ECe_0_20cm") & (d.subzona == s)).any(): continue
    base = g.iloc[0].copy()
    for c in ["valor", "valor_min", "valor_max", "fuente", "url_o_doi", "metodo", "lugar", "lat", "lon"]: base[c] = None
    base["variable"] = "ECe_0_20cm"; base["tipo_evidencia"] = "regional"; base["estado"] = "desconocido"
    base["fecha_o_periodo"] = ""; base["resolucion"] = "zona"
    base["notas"] = ("Sin ECe zonal confiable: HWSD descartado (contradice CE medida en chacra, fuente Piura Datos). "
                     "Ver ECe_medida_local (puntual, no representa toda la zona)" + (" y ECe_suelo_superficial_rango_local / ECe_clase_salina_FAO_UNALM_1990." if z == "bajo_piura" else "."))
    d = pd.concat([d, base.to_frame().T], ignore_index=True)
# 3) ECe_medida_local desde Piura Datos
MED = {"chira": ["1386a6d8a8b5"], "medio_piura": ["fb5485e3b51a"], "bajo_piura": ["5dad6de9a1a2"], "alto_piura": ["b45b9092b73a"]}
for z, ids in MED.items():
    r = ev.loc[ids[0]]
    for i in d.index[(d.variable == "ECe_medida_local") & (d.zona == z)]:
        for c in ["valor", "valor_min", "valor_max", "lugar", "lat", "lon", "fecha_o_periodo", "url_o_doi"]:
            d.at[i, c] = None if pd.isna(r[c]) else r[c]
        d.at[i, "fuente"] = f"{r['fuente']} (recopilado por Piura Datos, restricciones/evidencia_observada.csv id {ids[0]})"
        d.at[i, "metodo"] = "CE de suelo medida en laboratorio; extracto no declarado en la fuente (puede ser pasta saturada, 1:1 o 1:2.5)"
        d.at[i, "tipo_evidencia"] = "medicion_local"; d.at[i, "estado"] = "observado"; d.at[i, "resolucion"] = "parcela/sector"
        extra = {"chira": " Una sola muestra de una parcela de limón (10.3 mS/m); sin rango porque es un único dato.",
                 "medio_piura": " Una sola parcela experimental; sin rango porque es un único dato.",
                 "bajo_piura": " 40 predios del Tablazo Sur; 42.5 % salino-sódicos y 5 % salinos (USDA). El Tablazo es la parte más salina, no el valle entero.",
                 "alto_piura": " Sector arrocero El Huaro (Buenos Aires, Morropón)."}[z]
        d.at[i, "notas"] = ("Fuente preferente de CE de suelo en la zona. Valor puntual: no representa toda la zona. Si el extracto fuera 1:1, "
                            "ECe sería ~1.8-3.0 veces mayor (ver decisión r5)." + extra + " Notas de Piura Datos: " + str(r["notas"])[:400])
d.to_csv(P, index=False)
print(d[d.variable.str.contains("ECe")][["variable", "zona", "subzona", "valor", "valor_min", "valor_max", "estado"]].to_string())
