"""Ronda 7b: afina el umbral de Tmáx en floración de la arveja (para_motor/parametros_cultivo_v2_propuesta.csv)
y agrega la fila de AUSENCIA de arveja en el calendario DRAP de bajo_piura (para_motor/calendario_siembra_cosecha_piura.csv).
Se ejecuta DESPUÉS de build_ronda7.py (idempotente). Solo escribe en cultivos/para_motor/."""
import os, pandas as pd
D = os.path.dirname(os.path.abspath(__file__)); PM = os.path.join(D, "para_motor")

# ---- (a) umbral de estrés reproductivo: afinar nota con SENASA BPA, Tmáx diaria vs media y PISCOt ----
f = os.path.join(PM, "parametros_cultivo_v2_propuesta.csv"); p = pd.read_csv(f, dtype=str, keep_default_na=False)
key = "arveja|Pisum sativum|cosecha|temperatura_umbral_estres_reproductivo|floracion|R7"
R7B = ("[R7B] Umbral sobre Tmax del AIRE (maxima diaria), no media del dia: Osorio et al. 2023 — >25 °C ya danha, "
       ">27 °C aborto severo, 28-32 °C umbral de campo (Jeuffroy 1990: 31; Guilioni 1997: 33/30 dia/noche). "
       "SENASA BPA arveja (SENASA 2020 §3.2, filas R7A004/R7A005 del calendario_drap): optimo 15-18 °C y "
       "'por encima de 30 °C afecta la calidad del producto cosechado'. En el motor comparese con la Tmax MEDIA "
       "mensual (PISCOt tmax_media, promedio de las maximas diarias), NO con la maxima absoluta: bajo_piura jun-sep "
       "tiene Tmax media 26.7-27.8 °C (jun 27.70, jul 26.72, ago 26.93, set 27.82; P10-P90 del conjunto 25.5-29.3 °C; "
       "verificado en consolidado/motor/datos_repo/temperatura_pisco_zona.csv), asi que jun y set ya cruzan el umbral "
       "de 27 y el P90 (29.3) lo cruza esos meses, mientras que el TMAX absoluto EcoCrop de 30 no se cruza (por eso el "
 "motor hoy no baja la arveja). Variable propuesta como umbral POR ETAPA: hoy el motor NO la reconoce: "
 "validacion.PARAMETROS_RECONOCIDOS solo admite temperatura_adaptacion y temperatura_optima en este archivo, por "
 "lo que catalogo._agro_parametros RECHAZA esta fila ('parametro no reconocido'). Para que el motor baje la arveja "
 "hacen falta DOS cambios del equipo del motor (no editables por Agronomia): (1) agregar "
 "temperatura_umbral_estres_reproductivo:(°C,True) a PARAMETROS_RECONOCIDOS en validacion.py; (2) en _agro_parametros "
 "crear Umbral(tmax, None, 27, soft) comparada contra tmax_media (PISCOt) de los meses de floracion, analoga a "
 "temperatura_dano_calor_umbral (que solo existe por ciclo y se lee de datos_repo/parametros_cultivo_v2.csv, no de "
 "este archivo). NO usar temperatura_adaptacion para esto: su TMAX es el absoluto EcoCrop (30 °C), no el umbral de "
 "aborto. confianza 0.3; estado propuesta_agente1_no_calibrada.")
m = p.parameter_key == key
assert m.sum() == 1, f"se esperaba 1 fila {key}, hay {m.sum()}"
p.loc[m, "applicability_note"] = p.loc[m, "applicability_note"].apply(lambda s: s if "[R7B]" in s else s + " " + R7B)
p.to_csv(f, index=False)

# ---- (b) fila de AUSENCIA de arveja en el calendario DRAP de bajo_piura ----
f = os.path.join(PM, "calendario_siembra_cosecha_piura.csv"); c = pd.read_csv(f, dtype=str, keep_default_na=False)
DRAP_URL = ("https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-"
            "de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp")
nota = ("[R7B] AUSENCIA verificada: la DRAP 2016-2024 (raw/drap_dataset.csv, 124514 filas, corte 2025-05-27) "
        "registra 0 ha de arveja (grano seco y verde) en los distritos de bajo_piura -> ha=0, estado observado. "
        "La arveja SOLO aparece en sierra_piura (1955 filas 2016-2024: Ayabaca, Huancabamba y distritos altos de "
        "Morropon) y en san_lorenzo (59 filas: Paimas y Suyo), zona por distrito segun suelos/datos/distrito_zona.csv "
        "(union por UBIGEO). Fila sin ventana de siembra a proposito: el motor (calendario_obs) la marca RECHAZADA "
        "('sin ventana') y conserva su aviso 'sin ventana observada'; es un marcador documental de ausencia.")
fila = {"crop": "arveja", "zona": "bajo_piura", "desfase_siembra_cosecha_observado": "", "mes_pico_cosecha": "",
        "mes_pico_siembra": "", "ventana_cosecha_observada": "", "ventana_siembra_observada": "", "confianza": "0.9",
        "source_url": DRAP_URL, "periodo": "2016-2024 (9 campañas calendario)",
        "validation_status": "observado_ausencia_en_drap_agente1", "applicability_note": nota}
ya = (c.crop == "arveja") & (c.zona == "bajo_piura") & (c.validation_status == "observado_ausencia_en_drap_agente1")
if not ya.any():
    c = pd.concat([c, pd.DataFrame([fila])[c.columns.tolist()]], ignore_index=True)
else:
    for k, v in fila.items():
        c.loc[ya, k] = v
c.to_csv(f, index=False)
print("R7b ok: nota (a) aplicada; fila ausencia (b) presente:",
      int(((c.crop=='arveja')&(c.zona=='bajo_piura')&(c.validation_status=='observado_ausencia_en_drap_agente1')).sum()))
