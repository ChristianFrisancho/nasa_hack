import csv,hashlib

rows=[]
for r in csv.DictReader(open('fao56_duracion_analogos.csv')):
    key='duration|'+r['crop']+'|'+r['analogue_region']+'|'+r['total_days_as_printed']
    rows.append({'analog_id':hashlib.sha1(key.encode()).hexdigest()[:12],'crop':r['crop'],'trait':'duration_days','donor_value':r['total_days_as_printed'],'donor_region':r['analogue_region'],'donor_source_url':r['source_url'],'Piura_target_zone':'','Piura_soil_class':'','donor_soil_class':'','Piura_climate_vector':'','donor_climate_vector':'','cultivar_match':'unknown','management_match':'unknown','soil_match':'unknown','climate_match':'unknown','match_status':'not_mergeable_missing_covariates','Piura_observed_value':'','donor_minus_Piura':'','validation_action':'obtain coordinates, comparable season, soil profile, cultivar/use and management; then compare holdout outcome'})
for r in csv.DictReader(open('nutrientes_cultivo_fao.csv')):
    key='nutrient|'+r['crop']+'|'+r['main_product_or_part']+'|'+r['measurement_type']
    rows.append({'analog_id':hashlib.sha1(key.encode()).hexdigest()[:12],'crop':r['crop'],'trait':r['measurement_type']+' N/P2O5/K2O kg/t','donor_value':r['N_kg_per_t']+'/'+r['P2O5_kg_per_t']+'/'+r['K2O_kg_per_t'],'donor_region':r['source_region'],'donor_source_url':r['source_url'],'Piura_target_zone':'','Piura_soil_class':'','donor_soil_class':'','Piura_climate_vector':'','donor_climate_vector':'','cultivar_match':'unknown','management_match':'unknown','soil_match':'unknown','climate_match':'unknown','match_status':'not_mergeable_missing_covariates','Piura_observed_value':'','donor_minus_Piura':'','validation_action':'compare dry-matter basis, removed plant parts, yield, soil and cultivar before borrowing coefficient'})
with open('analogos_comparacion_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rules=[
 ('crop_taxon','categorical','same species or documented biological proxy','hard'),
 ('harvest_use','categorical','same harvested part and moisture basis','hard'),
 ('cultivar_or_maturity_group','categorical','same or locally calibrated maturity group','hard'),
 ('planting_date','days','within seasonal window after local phenology review','hard'),
 ('irrigation_method','categorical','same method and comparable efficiency','hard'),
 ('soil_sand_clay_silt','percentage points','each fraction difference <=5 if lab methods comparable','soft'),
 ('soil_pH','pH','difference <=0.3, same extraction method','soft'),
 ('soil_ECe','dS/m','difference <=1, same saturation extract method','soft'),
 ('effective_root_depth','m','difference <=0.2 after field pit','soft'),
 ('soil_available_water','mm/root_zone','difference <=15%','soft'),
 ('monthly_precipitation','mm','difference <=10% or 20mm, whichever greater; distribution also compare','soft'),
 ('monthly_Tmean','°C','difference <=1; count heat/cold extremes separately','soft'),
 ('ET0_and_radiation','mm and MJ/m²','ET0 difference <=10%; same calculation method','soft'),
 ('pest_status','categorical','same diagnosed pathogen/host pressure','hard'),
 ('yield_or_consumption_measure','categorical','same measurement protocol, yield target and crop phase','hard'),
]
with open('reglas_analogos_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['feature','unit','candidate_rule_for_review','rule_type']);w.writeheader()
 for a in rules:w.writerow(dict(zip(w.fieldnames,a)))
print('analog candidates',len(rows),'confirmed exact matches',0,'rules',len(rules))
