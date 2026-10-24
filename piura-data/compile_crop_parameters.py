"""Unify sourced crop parameters without conflating Kc, uptake, export and fertilizer."""
import csv,math,re

rows=[]
def add(crop,param,lo,hi,unit,stage,source,scope,kind,status,note='',cultivar='',use=''):
    crop={'maíz amarillo duro':'maiz amarillo duro','maíz choclo':'maiz choclo','plátano':'banano'}.get(crop,crop)
    lo=None if lo in ('',None) else float(lo)
    hi=None if hi in ('',None) else float(hi)
    rows.append({'parameter_key':f'{crop}|{cultivar}|{use}|{param}|{stage}|{len(rows)}','crop':crop,'cultivar':cultivar,'harvest_use':use,'parameter':param,'min_value':lo,'max_value':hi,'unit':unit,'stage':stage,'parameter_kind':kind,'geographic_scope':scope,'source_url':source,'validation_status':status,'applicability_note':note})

for r in csv.DictReader(open('requisitos_cultivo_verificados.csv')):
    add(r['crop'],r['parameter'],r['min_value'],r['max_value'],r['unit'],r['stage'],r['source_url'],r['geographic_scope'],'direct_source',r['validation_status'],r['method'],r['cultivar'],r['harvest_use'])

for r in csv.DictReader(open('fao56_kc_referencias.csv')):
    for stage,lo,hi in [('initial',r['Kc_initial'],r['Kc_initial']),('mid',r['Kc_mid_min'],r['Kc_mid_max']),('end',r['Kc_end_min'],r['Kc_end_max'])]:
        add(r['crop'],'Kc_standard',lo,hi,'dimensionless',stage,r['source_url'],'FAO-56, estándar no estresado; no medido en Piura','crop_coefficient','reference_needs_local_calibration',r['fao_crop_subtype']+'; '+r['applicability_note'],use=r['fao_crop_subtype'])

for r in csv.DictReader(open('nutrientes_cultivo_fao.csv')):
    for elem,col in [('N','N_kg_per_t'),('P2O5','P2O5_kg_per_t'),('K2O','K2O_kg_per_t')]:
        add(r['crop'],('total_uptake_' if r['measurement_type'].startswith('absorción') else 'harvest_export_')+elem,r[col],r[col],'kg '+elem+'/t principal' if r['measurement_type'].startswith('absorción') else 'kg '+elem+'/t retirada','seasonal',r['source_url'],r['source_region'],'nutrient_uptake' if r['measurement_type'].startswith('absorción') else 'harvest_export','reference_needs_local_calibration',r['main_product_or_part']+'; '+r['note'],use=r['main_product_or_part'])

for r in csv.DictReader(open('fao_ky_respuesta_agua.csv')):
    add(r['crop'],'Ky_seasonal',r['Ky_seasonal_min'],r['Ky_seasonal_max'],'dimensionless','seasonal',r['source_url'],'FAO multi-region','water_stress_response','reference_needs_local_calibration',r['limitation'])

PAPAYA='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-PAPAYA.pdf'
BANANA='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-PLATANO.pdf'
YUCA='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-YUCA.pdf'
LIMON='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-LIMON.pdf'
MAIZ='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-MAIZ-AMARILLO-DURO.pdf'
UVA='https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-UVA.pdf'
guide=[
 ('papaya','profundidad_suelo_minima',.50,None,'m','establishment',PAPAYA,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement','aproximado, no garantizado por mapa'),
 ('papaya','pH_suelo_recomendado',6,7,'pH','all',PAPAYA,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement',''),
 ('papaya','temperatura_adaptacion',17,38,'°C','all',PAPAYA,'guía SENASA Perú p.4','climate_threshold','reference_needs_local_calibration','rango amplio, NO óptimo de crecimiento'),
 ('papaya','humedad_relativa_adaptacion',50,95,'%','all',PAPAYA,'guía SENASA Perú p.4','climate_threshold','reference_needs_local_calibration','rango amplio, exceso de humedad favorece hongos'),
 ('banano','pH_suelo_favorable',6,7.5,'pH','all',BANANA,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement',''),
 ('banano','temperatura_floracion_optima',27,27,'°C','flowering',BANANA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration','no es temperatura base para grados-día'),
 ('banano','temperatura_dano_calor_umbral',37,None,'°C','all',BANANA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration','fuente indica quemaduras y deformación >37°C'),
 ('banano','temperatura_crecimiento_lento_umbral',None,16,'°C','all',BANANA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration','fuente indica crecimiento más lento <16°C'),
 ('yuca','pH_suelo_favorable',5.5,7,'pH','all',YUCA,'guía SENASA Perú p.3','soil_threshold','reference_needs_field_measurement','suelo suelto y bien drenado'),
 ('yuca','temperatura_optima',25,29,'°C','all',YUCA,'guía SENASA Perú p.3','climate_threshold','reference_needs_local_calibration','mayores rendimientos en esta banda según guía'),
 ('yuca','temperatura_adaptacion',16,38,'°C','all',YUCA,'guía SENASA Perú p.3','climate_threshold','reference_needs_local_calibration','no confundir con óptimo'),
 ('yuca','fotoperiodo_favorable',10,12,'h/día','all',YUCA,'guía SENASA Perú p.3','climate_threshold','reference_needs_local_calibration',''),
 ('limon','temperatura_adaptacion',23,30,'°C','all',LIMON,'guía SENASA Perú p.4','climate_threshold','reference_needs_local_calibration',''),
 ('limon','temperatura_dano_calor_umbral',36,None,'°C','fruit',LIMON,'guía SENASA Perú p.4','climate_threshold','reference_needs_local_calibration','fuente indica daño de calidad >36°C'),
 ('limon','profundidad_suelo_minima',1,None,'m','establishment',LIMON,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement',''),
 ('limon','pH_suelo_favorable',6,7,'pH','all',LIMON,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement','fuente cita tolerancia 5-8,5, favorable más estrecho'),
 ('maiz amarillo duro','profundidad_efectiva_favorable',.5,None,'m','establishment',MAIZ,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement',''),
 ('maiz amarillo duro','pH_suelo_favorable',5.5,6,'pH','all',MAIZ,'guía SENASA Perú p.4','soil_threshold','reference_needs_field_measurement','intervalo indicado por la guía; consultar ensayo local'),
 ('maiz amarillo duro','temperatura_crecimiento_ideal',24,30,'°C','vegetative',MAIZ,'guía SENASA Perú p.4','climate_threshold','reference_needs_local_calibration',''),
 ('uva','pH_suelo_adaptacion',5.6,7.7,'pH','all',UVA,'guía SENASA Perú p.5','soil_threshold','reference_needs_field_measurement',''),
 ('uva','temperatura_optima_apertura_yemas',9,10,'°C','budbreak',UVA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration','vid; variedad y manejo de dormancia importan'),
 ('uva','temperatura_optima_floracion',18,22,'°C','flowering',UVA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration',''),
 ('uva','temperatura_optima_crecimiento_fruto',22,26,'°C','fruit_growth',UVA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration',''),
 ('uva','temperatura_optima_maduracion',20,24,'°C','ripening',UVA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration',''),
 ('uva','temperatura_optima_vendimia',18,22,'°C','harvest',UVA,'guía SENASA Perú p.5','climate_threshold','reference_needs_local_calibration',''),
 ('papaya','riego_total_anual_reportado',2000,2000,'m³/ha/año','productive',PAPAYA,'guía SENASA Perú p.13','irrigation_reference','hold_due_source_conflict','riego aplicado en guía vs agua total de revisión Ecuador son métricas distintas y magnitudes difíciles de conciliar; no usar en modelo'),
]
for a in guide:add(*a)
add('papaya','agua_anual_reportada',1500,2000,'mm/año','productive','https://agris.fao.org/search/en/providers/124888/records/674896267625988a371e1ed2','Ecuador; revisión de tesis 2020','water_reference','analog_unmatched','revisión cita varios autores; método y densidad no comparables con guía SENASA')

fields=list(rows[0])
with open('parametros_cultivo_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

crops=['arroz','maiz amarillo duro','maiz choclo','frijol grano','frijol de palo','caupi','mango','limon','banano','algodon','uva','cacao','papa','yuca','cafe','zapallo','papaya','cebolla','piquillo','arveja']
with open('cobertura_datos_por_cultivo_v2.csv','w',newline='') as f:
 names=['crop','Kc_records','nutrient_uptake_records','nutrient_export_records','Ky_records','soil_or_climate_threshold_records','external_duration_analog_records','Piura_specific_nutrient_coefficients','Piura_specific_soil_profile','status']
 w=csv.DictWriter(f,fieldnames=names);w.writeheader()
 analog=list(csv.DictReader(open('fao56_duracion_analogos.csv')))
 for crop in crops:
  rr=[r for r in rows if r['crop']==crop]
  count=lambda kind:sum(r['parameter_kind']==kind for r in rr)
  w.writerow({'crop':crop,'Kc_records':count('crop_coefficient'),'nutrient_uptake_records':count('nutrient_uptake'),'nutrient_export_records':count('harvest_export'),'Ky_records':count('water_stress_response'),'soil_or_climate_threshold_records':sum(r['parameter_kind'] in ('soil_threshold','climate_threshold','direct_source') for r in rr),'external_duration_analog_records':sum(x['crop']==crop for x in analog),'Piura_specific_nutrient_coefficients':0,'Piura_specific_soil_profile':0,'status':'fuentes externas pendientes de calibración; perfil local faltante'})
print('parameters',len(rows),'crops',len(crops))
