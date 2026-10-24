"""Join documented crop thresholds with historical soil map classes, preserving unknowns."""
import csv,json

crops=[r['crop'] for r in csv.DictReader(open('cobertura_datos_por_cultivo_v2.csv'))]
params=list(csv.DictReader(open('parametros_cultivo_v2.csv')))
coastal=list(csv.DictReader(open('suelos_bajo_piura_unidades_v2.csv')))
montero=list(csv.DictReader(open('suelos_montero_ayabaca_cum_v2.csv')))
perennial={'mango','limon','banano','uva','cacao','cafe','papaya'}
output=[]
for crop in crops:
    cp=[r for r in params if r['crop']==crop]
    ph=[r for r in cp if ('pH_suelo' in r['parameter']) and r['parameter_kind'] in ('soil_threshold','direct_source')]
    depth=[r for r in cp if ('profundidad' in r['parameter']) and r['parameter_kind'] in ('soil_threshold','direct_source')]
    phs='; '.join(f"{r['min_value'] or '?'}–{r['max_value'] or '?'} pH [{r['source_url']}]" for r in ph)
    deps='; '.join(f"{r['min_value'] or '?'} m [{r['source_url']}]" for r in depth)
    for s in coastal:
        unit=s['soil_unit'];risks=s['known_constraints']
        extra={'Pajarito':'priorizar ECe, ESP/SAR, napa y drenaje','Ramón':'priorizar ECe, ESP/SAR, napa y drenaje','Cerezal':'priorizar capacidad de agua utilizable, materia orgánica, CIC e infiltración','Curumuy':'priorizar yeso, carbonatos, ECe y agua disponible'}.get(unit,'medir textura, profundidad, pH, ECe, N/P/K, infiltración')
        output.append({'crop':crop,'crop_system':'perenne' if crop in perennial else 'anual/estacional','soil_scope':'Bajo Piura','soil_map_unit_or_CUM':unit,'soil_information':s['texture_evidence']+'; '+risks,'crop_pH_reference':phs,'crop_depth_reference':deps,'crop_salinity_threshold':'no verificado para cultivar','actual_profile_pH':'','actual_profile_ECe_dS_m':'','actual_effective_depth_m':'','actual_soil_water_capacity_mm':'','field_geometry_match':'no, ubicación de parcela desconocida','prescreen_status':'indeterminado hasta análisis de parcela','priority_measurements':extra,'source_soil':s['source_url']})
    for s in montero:
        c=s['cum_class'];is_excl=c.startswith('X') or c.startswith('F')
        status='capacidad de protección/forestal: excluir cultivo intensivo salvo evaluación legal/técnica' if is_excl else 'indeterminado hasta ubicación y análisis de parcela'
        if c.startswith('C') and crop not in perennial:status='clase orientada a perennes; revisar antes de labranza anual'
        output.append({'crop':crop,'crop_system':'perenne' if crop in perennial else 'anual/estacional','soil_scope':'Montero-Ayabaca','soil_map_unit_or_CUM':c,'soil_information':s['texture']+'; '+s['limitations'],'crop_pH_reference':phs,'crop_depth_reference':deps,'crop_salinity_threshold':'no verificado para cultivar','actual_profile_pH':'','actual_profile_ECe_dS_m':'','actual_effective_depth_m':'','actual_soil_water_capacity_mm':'','field_geometry_match':'no, ubicación de parcela desconocida','prescreen_status':status,'priority_measurements':'pendiente, profundidad a roca, textura, pH, riego, erosión y CUM del polígono','source_soil':s['source_url']})
with open('matriz_cultivo_suelo_regional_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
print('crop-soil prescreen rows',len(output))
