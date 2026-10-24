"""Construye reglas_rotacion.csv y recuperacion_suelo.csv (formato CONTRATO + columnas extra).
Regla: si la fuente no da magnitud o plazo, valor vacío y estado=desconocido. Nada inventado."""
import os, pandas as pd
from fuentes import F
D=os.path.dirname(os.path.abspath(__file__))
C=["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","lugar","lat","lon","fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas"]
def row(src,**k):
    r={c:"" for c in C}; r["fuente"],r["url_o_doi"]=F[src]; r.update(k)
    for c in ("valor","valor_min","valor_max"): r[c]="" if r[c] in (None,"") else str(r[c])
    if r["estado"]=="desconocido": r["valor"]=""
    return r

LEG=["frijol caupi","frijol castilla/grano seco","mani","soya","arveja"]
CER=["maiz amarillo duro","maiz amilaceo","arroz","trigo","sorgo"]
R=[]
def regla(previo,sig,tipo,cond,efecto,src,conf,**k):
    r=row(src,cultivo=sig,**k); r.update(cultivo_previo=previo,cultivo_siguiente=sig,tipo_efecto=tipo,condicion=cond,efecto=efecto,confianza=conf); R.append(r)

# 1. Leguminosa de grano -> cereal (Zhao 2022, global)
for p in LEG:
    for s in CER:
        regla(p,s,"N_residual_y_no_N","precultivo leguminoso vs precultivo no leguminoso; beneficio cae con más N fertilizante y más diversidad del sistema",
              "aumenta rendimiento del cereal siguiente","ZHAO22",0.5,variable="cambio_rendimiento_cultivo_siguiente",valor=20,valor_min=7,valor_max=32,unidad="% vs testigo",
              metodo="metaanálisis (11 768 observaciones, 462 ensayos)",tipo_evidencia="analogo_externo",estado="estimado",
              notas="media global 20%; min/max = 7% en ambientes de alto rendimiento y 32% en bajo rendimiento (no es IC). Efecto agregado por grupo de leguminosas, no medido para este par ni en Piura; la fuente reporta beneficio consistente en arroz, trigo y maíz.")
# 2. Leguminosa -> maíz/sorgo (Franke 2018, SSA): magnitud absoluta y con N
for p in ["frijol caupi","mani","soya"]:
    for s in ["maiz amarillo duro","sorgo"]:
        regla(p,s,"N_residual_y_no_N","sin N fertilizante en el cereal","aumenta rendimiento del cereal siguiente","FRANKE18",0.4,
              variable="cambio_rendimiento_cultivo_siguiente",valor=0.49,unidad="t grano/ha",metodo="revisión sistemática (44 publicaciones, 199 obs.)",tipo_evidencia="analogo_externo",estado="estimado",
              notas="media general leguminosa->cereal en África subsahariana (= +41% del cereal continuo); la fuente indica respuesta mayor en maíz que en sorgo/mijo y mayor tras soya y maní que tras caupí; sin rango publicado en el resumen. Clima y suelos distintos a Piura.")
        regla(p,s,"no_N","cereal con 60-120 kg N/ha","beneficio persiste aun con N","FRANKE18",0.4,
              variable="cambio_rendimiento_cultivo_siguiente",valor=0.32,unidad="t grano/ha",metodo="revisión sistemática",tipo_evidencia="analogo_externo",estado="estimado",
              notas="= 59% de la respuesta sin N; la fuente lo usa como evidencia de efectos no-N. Sin rango en el resumen.")
# 3. Algodón -> algodón: gusano rosado (Piura)
regla("algodon","algodon","plaga_compartida","rastrojos de algodón no destruidos (SENASA recomienda gradeo y arado)","aumenta riesgo de Pectinophora gossypiella","SENASA_PECTINO",0.5,
      variable="cambio_riesgo_plaga",unidad="categoría",lugar="Bajo Piura (El Tallán, Sechura)",fecha_o_periodo="2018",metodo="evaluación fitosanitaria oficial",tipo_evidencia="regional",estado="desconocido",
      notas="dirección documentada (la plaga sobrevive en rastrojos); la fuente no da magnitud de incidencia ni plazo de vacío sanitario, por eso valor vacío.")
# 4. Spodoptera frugiperda: MAD <-> algodón/zapallo/leguminosas
for o in ["algodon","frijol caupi","frijol castilla/grano seco","zapallo"]:
    for p,s in [("maiz amarillo duro",o),(o,"maiz amarillo duro")]:
        regla(p,s,"plaga_compartida","sucesión sin control del cogollero","mantiene/aumenta riesgo de Spodoptera frugiperda","SENASA_MAD",0.4,
              variable="cambio_riesgo_plaga",unidad="categoría",metodo="guía oficial (hospedantes listados)",tipo_evidencia="regional",estado="desconocido",
              notas="la guía BPA MAD lista hospedantes compartidos con algodón, zapallo y leguminosas; no cuantifica efecto de la sucesión. Leguminosas concretas no nombradas: caupí/castilla incluidos por pertenecer al grupo.")
# 5. Elasmopalpus: MAD <-> frijol/arveja
for o in ["frijol caupi","frijol castilla/grano seco","arveja"]:
    for p,s in [("maiz amarillo duro",o),(o,"maiz amarillo duro")]:
        regla(p,s,"plaga_compartida","sucesión en suelo seco/arenoso sin manejo","mantiene riesgo de Elasmopalpus lignosellus","SENASA_MAD",0.4,
              variable="cambio_riesgo_plaga",unidad="categoría",metodo="guía oficial (hospedantes listados)",tipo_evidencia="regional",estado="desconocido",
              notas="la guía indica que hospeda frijol/arveja/pallar; sin magnitud. 'frijol' no especifica especie.")
# 6. Maíz -> maíz: Diatraea en residuos
regla("maiz amarillo duro","maiz amarillo duro","plaga_compartida","residuos/tallos de maíz en campo","mantiene riesgo de Diatraea saccharalis","SENASA_MAD",0.4,
      variable="cambio_riesgo_plaga",unidad="categoría",metodo="guía oficial",tipo_evidencia="regional",estado="desconocido",notas="guía: residuos/tallos son hospederos; sin magnitud.")
# 7. Banano -> banano: Fusarium R4T
regla("banano","banano","patogeno_suelo","suelo con Foc R4T confirmado (Piura 2021)","no asumir saneamiento del suelo tras un año de rotación","SENASA_R4T",0.5,
      variable="plazo_saneamiento_suelo",unidad="años",lugar="Piura",fecha_o_periodo="2021",metodo="comunicado oficial de brote",tipo_evidencia="regional",estado="desconocido",
      notas="la fuente solo dice que un año no basta; plazo real desconocido. Rige reglamento de bioseguridad.")
# 8. Meloidogyne (papaya)
regla("papaya","hospedante de Meloidogyne (diagnosticar)","nematodo","suelo infestado","riesgo de nematodo agallador en siguiente hospedante","SENASA_PAPAYA",0.3,
      variable="cambio_riesgo_plaga",unidad="categoría",metodo="guía oficial",tipo_evidencia="regional",estado="desconocido",
      notas="la guía pide rotar según rango de hospedantes y diagnóstico de especie; no lista cultivos ni magnitud.")
# 9. Arroz -> arroz: Pomacea
regla("arroz","arroz","plaga_compartida","agua de arrozal con caracol manzana","mantiene riesgo de Pomacea canaliculata","SENASA_POMACEA",0.4,
      variable="cambio_riesgo_plaga",unidad="categoría",lugar="Piura",fecha_o_periodo="2021",metodo="comunicado oficial",tipo_evidencia="regional",estado="desconocido",notas="intervención histórica 2021; presencia actual y magnitud desconocidas.")
# 10. Yuca -> yuca
regla("yuca","yuca","plaga_compartida","esquejes del mismo campo","riesgo de Xanthomonas/Diplodia/ácaros vía material y secuencia de hospedantes","SENASA_YUCA",0.3,
      variable="cambio_riesgo_plaga",unidad="categoría",metodo="guía oficial",tipo_evidencia="regional",estado="desconocido",notas="guía pide esquejes sanos y secuencia de hospedantes; sin magnitud.")
# 11. Arroz (fangueo) -> secano
for s in ["maiz amarillo duro","algodon","frijol caupi","trigo"]:
    regla("arroz",s,"estructura_suelo","alternancia anaerobio/aerobio tras arroz inundado","cambia estructura, C y N del suelo para el cultivo de secano","ZHOU14",0.3,
          variable="cambio_rendimiento_cultivo_siguiente",unidad="% vs testigo",metodo="revisión narrativa",tipo_evidencia="analogo_externo",estado="desconocido",
          notas="revisión asiática sin magnitud en el resumen; dirección no cuantificada. Falta fuente sobre capa compactada por fangueo.")
# 12. Sorgo -> siguiente: alelopatía
for s in ["trigo","frijol caupi","maiz amarillo duro"]:
    regla("sorgo",s,"alelopatia","residuos/raíces de sorgo (sorgoleona y fenólicos)","puede reducir crecimiento del cultivo siguiente","SORGO21",0.3,
          variable="cambio_rendimiento_cultivo_siguiente",unidad="% vs testigo",metodo="revisión",tipo_evidencia="analogo_externo",estado="desconocido",
          notas="la revisión reporta reducción de plantas que crecen 'simultánea o posteriormente', sin magnitud general; especies concretas no confirmadas.")
# 13. Salinidad: cualquier previo -> X (Maas-Hoffman con datos de fichas)
fa=pd.read_csv(os.path.join(D,"fichas_anuales.csv"),dtype=str,keep_default_na=False)
for c in fa.cultivo.unique():
    a=fa[(fa.cultivo==c)&(fa.variable=="ece_umbral")&(fa.valor!="")]; b=fa[(fa.cultivo==c)&(fa.variable=="pendiente_salinidad_b")&(fa.valor!="")]
    if len(a) and len(b):
        a,b=a.iloc[0],b.iloc[0]
        r=row("F56T23",cultivo=c,variable="perdida_rendimiento_por_dS_sobre_umbral",valor=b.valor,unidad="%/(dS/m)",metodo="Maas-Hoffman Y=100-b(ECe-a)",
              tipo_evidencia="bibliografico",estado="estimado",
              notas=f"umbral a={a.valor} dS/m ({a.fuente}, {a.id}); b de {b.id}. Aplica si la ECe dejada por el cultivo previo supera a. Valores de tabla sin rango; FAO-29 y FAO-56 comparten linaje (Maas 1984).")
        r.update(cultivo_previo="cualquiera",cultivo_siguiente=c,tipo_efecto="sales",condicion=f"ECe medida > {a.valor} dS/m",efecto="reduce rendimiento",confianza=0.6); R.append(r)
rr=pd.DataFrame(R); rr["regla_id"]=[f"RR{i+1:03d}" for i in range(len(rr))]; rr["id"]=rr.regla_id
rr=rr[C+["cultivo_previo","cultivo_siguiente","tipo_efecto","condicion","efecto","confianza","regla_id","id"]]
rr.to_csv(os.path.join(D,"reglas_rotacion.csv"),index=False)

# ---------------- Recuperación de suelo ----------------
S=[]
def rec(manejo,prop,direc,src,conf,plazo="",**k):
    r=row(src,variable=prop,**k); r.update(manejo=manejo,propiedad=prop,direccion=direc,plazo=plazo or "desconocido",confianza=conf); S.append(r)
rec("retorno de paja/residuos","SOC_concentracion","aumenta","LIU14",0.6,valor=12.8,valor_min=12.4,valor_max=13.2,unidad="% vs sin paja",metodo="metaanálisis (176 estudios)",tipo_evidencia="analogo_externo",estado="estimado",notas="media ± error (12.8 ± 0.4%); min/max = ±1 error. Mayormente China; respuesta depende de dosis de C y arcilla.")
rec("retorno de paja/residuos","SOC_plazo_saturacion","se satura","LIU14",0.5,plazo="12 años",valor=12,unidad="años",metodo="regresión SOC anual vs duración",tipo_evidencia="analogo_externo",estado="estimado",notas="la fuente sugiere saturación de C tras 12 años; es una estimación sin rango.")
rec("retorno de paja/residuos","C_activo_fraccion","aumenta","LIU14",0.5,valor_min=27.4,valor_max=56.6,unidad="% vs sin paja",metodo="metaanálisis",tipo_evidencia="analogo_externo",estado="estimado",notas="rango entre fracciones activas reportadas; sin media única.")
rec("retorno de paja/residuos","emision_CH4_arrozal","aumenta","LIU14",0.5,valor=110.7,unidad="% vs sin paja",metodo="metaanálisis",tipo_evidencia="analogo_externo",estado="estimado",notas="solo arrozales (± 1.2%); relevante para arroz en Piura (riego por inundación).")
rec("retorno de paja/residuos","emision_N2O","disminuye en arrozal / aumenta en secano","LIU14",0.5,valor_min=-15.2,valor_max=8.3,unidad="% vs sin paja",metodo="metaanálisis",tipo_evidencia="analogo_externo",estado="estimado",notas="-15.2% arrozal, +8.3% secano; son dos sistemas, no un intervalo.")
rec("retorno de paja/residuos","macroagregados","aumenta (lineal con SOC)","LIU14",0.4,unidad="% vs sin paja",metodo="metaanálisis",tipo_evidencia="analogo_externo",estado="desconocido",notas="el resumen solo da la relación lineal positiva, sin magnitud.")
rec("cultivo de cobertura / abono verde","SOC_stock_tasa","aumenta","POEPLAU15",0.6,valor=0.32,valor_min=0.24,valor_max=0.40,unidad="Mg C/ha/año (0-22 cm)",metodo="metaanálisis (139 parcelas, 37 sitios)",tipo_evidencia="analogo_externo",estado="estimado",notas="0.32 ± 0.08 en hasta 54 años; min/max = ±0.08. Sitios mayormente templados, no áridos.")
rec("cultivo de cobertura / abono verde","SOC_stock_equilibrio","aumenta","POEPLAU15",0.4,plazo="155 años (modelado)",valor=16.7,valor_min=15.2,valor_max=18.2,unidad="Mg C/ha (0-22 cm)",metodo="modelo RothC",tipo_evidencia="prediccion",estado="estimado",notas="16.7 ± 1.5 Mg/ha al nuevo equilibrio, simulado, no medido.")
rec("lavado de recuperación (inundación continua)","sales_solubles_removidas","disminuye ECe","F29S2",0.5,valor_min=70,valor_max=80,unidad="% de sales por lámina = profundidad de suelo",metodo="guía técnica (Hoffman 1980)",tipo_evidencia="bibliografico",estado="estimado",notas="1 m de agua percolada lava 70-80% de sales de 1 m de suelo; depende del tipo de suelo. Plazo no dado.")
rec("lavado intermitente o por aspersión","sales_solubles_removidas","disminuye ECe","F29S2",0.5,valor_min=80,valor_max=90,unidad="% de sales por lámina = profundidad de suelo",metodo="guía técnica (Hoffman 1980)",tipo_evidencia="bibliografico",estado="estimado",notas="más eficiente en agua pero requiere más tiempo (no cuantificado).")
rec("riego de pre-siembra","lamina_suficiente_si_ECe<10-12","permite establecer cultivo tolerante","F29S2",0.5,valor_min=10,valor_max=20,unidad="cm de agua",metodo="guía técnica",tipo_evidencia="bibliografico",estado="estimado",notas="válido con ECe 0-0.3 m < ~10-12 dS/m para cultivo tolerante (cebada o algodón); por encima se requiere lavado de recuperación.")
rec("lavado de boro","lamina_relativa_vs_sales","más agua requerida","F29S4",0.5,valor=3,unidad="veces la lámina para sales",metodo="guía técnica",tipo_evidencia="bibliografico",estado="estimado",notas="'unas tres veces' más agua que para sales; aproximado, sin rango.")
rec("yeso + lavado (suelo sódico severo)","dosis_yeso_recuperacion_1_año","reduce PSI/sodio","F29S3",0.5,plazo="1 año",valor_max=40,unidad="t/ha",metodo="guía técnica",tipo_evidencia="bibliografico",estado="estimado",notas="'hasta 40 t/ha' más lavado extenso; dosis real requiere test de Schoonover / requerimiento de yeso.")
rec("cultivos tolerantes + Ca del agua (sin enmienda)","plazo_recuperacion_sodico","reduce PSI/sodio","F29S3",0.5,plazo="1 a 5 o más años",valor_min=1,valor_max=5,unidad="años",metodo="guía técnica",tipo_evidencia="bibliografico",estado="estimado",notas="requiere Ca en agua ≥2-3 me/l, labranza profunda y percolación; el máximo es abierto ('o más').")
rec("labranza profunda","infiltracion","aumenta","F29S3",0.4,unidad="mm/h",metodo="guía técnica",tipo_evidencia="bibliografico",estado="desconocido",notas="'mejora mucho la infiltración'; sin magnitud.")
rec("barbecho en verano con napa alta","ECe_superficial","aumenta (salinización secundaria)","F29S2",0.5,unidad="dS/m",metodo="guía técnica",tipo_evidencia="bibliografico",estado="desconocido",notas="FAO-29 recomienda evitar barbechos en veranos cálidos con napa alta; sin magnitud. Relevante para Bajo Piura (napa somera).")
rec("barbecho (general)","SOC / estructura","desconocido","F29S2",0.1,unidad="",metodo="sin fuente",tipo_evidencia="bibliografico",estado="desconocido",notas="no se halló fuente con magnitud ni plazo para recuperación por barbecho; fila marcador de vacío. Fuente apuntada solo por la advertencia de salinización.")
ss=pd.DataFrame(S); ss["id"]=[f"RS{i+1:03d}" for i in range(len(ss))]
ss=ss[C+["manejo","propiedad","direccion","plazo","confianza","id"]]
ss.to_csv(os.path.join(D,"recuperacion_suelo.csv"),index=False)
print(len(rr),"reglas;",len(ss),"filas recuperación")
