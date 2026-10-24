import json
from pathlib import Path
s=json.loads(Path('model_inputs.schema.json').read_text())
s['title']='Entradas de rotación Piura v2: parcela, horizontes, agua, riesgo y economía'
field=s['properties']['field']['properties']
field['soil_horizons']={'type':'array','description':'Muestras o calicatas por horizonte con método/fecha; no rellenar con promedios regionales','items':{'type':'object','required':['top_cm','bottom_cm','sample_date','method'],'properties':{
 'top_cm':{'type':'number','minimum':0},'bottom_cm':{'type':'number','exclusiveMinimum':0},'sample_date':{'type':'string','format':'date'},'method':{'type':'string'},
 'sand_pct':{'type':['number','null'],'minimum':0,'maximum':100},'silt_pct':{'type':['number','null'],'minimum':0,'maximum':100},'clay_pct':{'type':['number','null'],'minimum':0,'maximum':100},
 'bulk_density_g_cm3':{'type':['number','null'],'exclusiveMinimum':0},'field_capacity_m3_m3':{'type':['number','null'],'minimum':0,'maximum':1},'wilting_point_m3_m3':{'type':['number','null'],'minimum':0,'maximum':1},'Ksat_mm_h':{'type':['number','null'],'minimum':0},
 'pH':{'type':['number','null'],'minimum':0,'maximum':14},'ECe_dS_m':{'type':['number','null'],'minimum':0},'ESP_pct':{'type':['number','null'],'minimum':0,'maximum':100},'CEC_cmolc_kg':{'type':['number','null'],'minimum':0},'organic_carbon_g_kg':{'type':['number','null'],'minimum':0},
 'mineral_N_mg_kg':{'type':['number','null'],'minimum':0},'available_P_mg_kg':{'type':['number','null'],'minimum':0},'exchangeable_K_cmolc_kg':{'type':['number','null'],'minimum':0},'carbonates_pct':{'type':['number','null'],'minimum':0},'gypsum_pct':{'type':['number','null'],'minimum':0},'root_restricting_layer_cm':{'type':['number','null'],'minimum':0}
 }}}
field['groundwater_depth_cm']={'type':['number','null'],'minimum':0}
field['flood_duration_days_history']={'type':['number','null'],'minimum':0}
field['land_use_capability_verified']={'type':['string','null']}
field['hazard_layers']={'type':'array','description':'Intersección de polígono con capas oficiales, con fecha/escala, no solo distrito','items':{'type':'object','properties':{'hazard_type':{'enum':['flood','debris_flow','landslide','drought','heat','wind','erosion']},'exposure_fraction':{'type':['number','null'],'minimum':0,'maximum':1},'return_period_years':{'type':['number','null'],'exclusiveMinimum':0},'map_scale':{'type':['string','null']},'map_date':{'type':['string','null']},'source_url':{'type':'string'}}}}
irr=field['irrigation']['properties']
irr.update({'water_right_id':{'type':['string','null']},'conveyance_efficiency':{'type':['number','null'],'exclusiveMinimum':0,'maximum':1},'application_efficiency':{'type':['number','null'],'exclusiveMinimum':0,'maximum':1},'soil_infiltration_limit_mm_h':{'type':['number','null'],'minimum':0},'water_sodium_mg_L':{'type':['number','null'],'minimum':0},'water_chloride_mg_L':{'type':['number','null'],'minimum':0},'water_boron_mg_L':{'type':['number','null'],'minimum':0},'canal_turns_by_week':{'type':'object','additionalProperties':{'type':['number','null'],'minimum':0}}})
farmer=s['properties']['farmer']['properties']
farmer.update({'cash_available_pen_by_month':{'type':'object','additionalProperties':{'type':['number','null'],'minimum':0}},'credit_limit_pen':{'type':['number','null'],'minimum':0},'risk_tolerance':{'enum':['low','medium','high',None]},'buyer_contracts':{'type':'array','items':{'type':'object'}},'storage_capacity_t':{'type':['number','null'],'minimum':0}})
crop=s['properties']['candidate_crops']['items']['properties']
crop.update({'target_yield_t_ha':{'type':['number','null'],'minimum':0},'earliest_sowing_date':{'type':['string','null'],'format':'date'},'latest_sowing_date':{'type':['string','null'],'format':'date'},'seed_source':{'type':['string','null']},'existing_perennial_plantation':{'type':'boolean'},'residue_management':{'enum':['retained','removed','grazed','mixed',None]}})
hist=s['properties']['history']['items']['properties']
hist.update({'cultivar':{'type':['string','null']},'irrigation_m3_ha':{'type':['number','null'],'minimum':0},'fertilizer_N_kg_ha':{'type':['number','null'],'minimum':0},'fertilizer_P2O5_kg_ha':{'type':['number','null'],'minimum':0},'fertilizer_K2O_kg_ha':{'type':['number','null'],'minimum':0},'diagnosed_pests':{'type':'array','items':{'type':'object','properties':{'agent':{'type':'string'},'diagnosis_date':{'type':'string','format':'date'},'method':{'type':'string'}}}},'crop_failure_reason':{'type':['string','null']}})
s['properties']['required_confidence']={'enum':['observed_local_only','regional_plus_calibrated_analog','exploratory']}
s['$comment']='Inventario de 342 features complementario. Variables faltantes se conservan como null; validar suma de textura, horizontes, fechas, unidades y geometría. Huaico/inundación se modela como riesgo de daño/pérdida, no como ajuste arbitrario de días.'
Path('model_inputs_v2.schema.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print('schema bytes',Path('model_inputs_v2.schema.json').stat().st_size)
