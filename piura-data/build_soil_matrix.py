import csv

SOURCE='https://siar.regionpiura.gob.pe/documentos/normativa/584.pdf'
units=[
 ('Palo Verde','Entisol','Torrifluvents','Fluvisol','aluvial','media a fina en sectores cultivados','baja a media','Poca evidencia de limitación específica de la unidad; verificar salinidad, drenaje y fertilidad de cada perfil','70; cuadro 14 y pp. 66-70'),
 ('Piura','Entisol','Torrifluvents','Fluvisol','aluvial','media a fina en sectores cultivados','baja a media','El riego y el drenaje pueden alterar salinidad; verificar perfil por parcela','66-70; cuadro 14'),
 ('Cerezal','Entisol','Torripsamments','Regosol','eólico o aluvial arenoso','gruesa; arena/arena franca','muy baja','Baja materia orgánica y CIC; poca retención de agua y nutrientes','66-70; cuadro 14'),
 ('Pajarito','Aridisol','Aquisalids','Regosol en tabla histórica','depresión','heterogénea, no cuantificada por unidad','no cuantificada','Salinidad y mal drenaje documentados; comprobar ECe, ESP/SAR y napa','66-70; cuadro 14'),
 ('Ramón','Aridisol','Haplosalids','Regosol en tabla histórica','depresión y cobertura eólica','heterogénea, no cuantificada por unidad','no cuantificada','Salinidad y mal drenaje documentados; comprobar ECe, ESP/SAR y napa','66-70; cuadro 14'),
 ('Curumuy','Aridisol','Gypsiorthids','sin equivalencia FAO inequívoca en tabla','terraza marina','heterogénea, no cuantificada por unidad','no cuantificada','Yeso y carbonatos posibles; déficit hídrico y acceso a riego limitantes','66-70; cuadro 14'),
]
fields=['soil_unit','soil_taxonomy_order_1999','soil_taxonomy_group_1999','fao_1990_map_label','geomorphic_setting','texture_evidence','fertility_evidence','known_constraints','profile_depth_cm','ECe_dS_m','pH','available_N_mg_kg','available_P_mg_kg','exchangeable_K_cmol_kg','historical_reference_year','scope','source_url','source_pages','observation_status']
with open('suelos_bajo_piura_unidades_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for name,order,group,fao,setting,texture,fertility,constraints,pages in units:
  w.writerow({'soil_unit':name,'soil_taxonomy_order_1999':order,'soil_taxonomy_group_1999':group,'fao_1990_map_label':fao,'geomorphic_setting':setting,'texture_evidence':texture,'fertility_evidence':fertility,'known_constraints':constraints,'profile_depth_cm':'','ECe_dS_m':'','pH':'','available_N_mg_kg':'','available_P_mg_kg':'','exchangeable_K_cmol_kg':'','historical_reference_year':'circa 2005','scope':'Área de interés Bajo Piura; mapa 1:50 000, no parcela','source_url':SOURCE,'source_pages':pages,'observation_status':'clasificación/cartografía histórica; medición de campo pendiente'})

# Table 16 in the source lists consociations and associations separately.
map_units=[
 ('Cerezal','A',405.04),('Cerezal','B',3951.91),('Cerezal','C',4011.40),('Cerezal','D',1067.91),('Cerezal','E',1328.75),
 ('Pajarito','A',4370.19),('Pajarito','B',597.67),('Piura','A',7219.46),('Piura','B',9138.78),
 ('Curumuy-Cerezal','A',787.38),('Curumuy-Cerezal','B',424.11),('Curumuy-Cerezal','C',225.35),
 ('Palo Verde-Cerezal','B',142.99),('Palo Verde-Cerezal','C',43.36),('Palo Verde-Cerezal','D',411.73),
 ('Pajarito-Palo Verde','B',597.67),('Pajarito-Piura','A',4370.19),('Piura-Cerezal','B',4743.83),
 ('Pajarito-Ramón','A',2372.36),('Pajarito-Ramón','B',1118.15),
 ('Piura-Pajarito','A',2047.54),('Piura-Pajarito','B',3181.80),
 ('Piura-Ramón','A',1469.70),('Piura-Ramón','B',5738.71),
 ('Cerezal-Curumuy','D',1138.65),('Cerezal-Palo Verde','D',204.33),('Otros','',7678.53),
]
slope={'A':'0-2%','B':'2-4%','C':'4-8%','D':'8-15%','E':'15-25%','F':'25-50%','G':'50-75%','H':'>75%'}
with open('suelos_bajo_piura_mapunits_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['map_unit','slope_class','slope_range','area_ha','source_url','source_table','status']);w.writeheader()
 for name,cls,area in map_units:w.writerow({'map_unit':name,'slope_class':cls,'slope_range':slope.get(cls,''),'area_ha':area,'source_url':SOURCE,'source_table':'Cuadro 16, área de interés Bajo Piura, circa 2005','status':'área cartográfica histórica, asociaciones no son parcelas homogéneas'})
reported_total=67421.33
row_sum=round(sum(x[2] for x in map_units),2)
print('soil units',len(units),'map units',len(map_units),'reported_total_ha',reported_total,'row_sum_ha',row_sum,'discrepancy_ha',round(row_sum-reported_total,2))

MONTERO='https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca/9281_micro-zonificacion-ecologica-y-economoca-provincia-ayabaca-distrito-montero-solo-memoria-descriptiva.pdf'
classes=[
 ('A3s(r)','anuales de ciclo corto','0-4','arcillosa o arenosa, extremos','no especificado','no especificado','riego requerido; impermeabilidad o infiltración excesiva','uso agrícola condicionado'),
 ('C2s(r)','cultivos permanentes','4-8','media a moderadamente fina','ligeramente superficial a moderadamente profundo','fuertemente ácido a ligeramente alcalino','riego requerido; drenaje bueno a moderado; fertilidad baja a media','uso agrícola condicionado'),
 ('C3s(r)','cultivos permanentes','8-15','media a moderadamente gruesa','superficial a moderadamente profundo, limitado por gravas','ligeramente ácido a ligeramente alcalino','riego requerido; fertilidad baja y pendiente; serie Montero','uso agrícola condicionado'),
 ('P3se(t)','pastos','8-25','media a moderadamente fina','superficial a moderadamente profundo','moderado a ligeramente ácido','fertilidad baja; serie Charán','no clasificar como cultivo intensivo'),
 ('F3se','forestal','15-50','media a fina','superficial a moderadamente profundo','fuertemente ácido a ácido','pendiente, erosión; series Los Horcones, Pite, Los Molinos','excluir cultivo intensivo'),
 ('Xse','protección','variable, a menudo muy empinada','pedregosa/rocosa','limitada por contacto lítico','variable','erosión severa y poca cobertura; no agricultura','excluir cultivo'),
]
with open('suelos_montero_ayabaca_cum_v2.csv','w',newline='') as f:
 names=['cum_class','land_use_capability','slope_pct_as_documented','texture','effective_depth','pH_description','limitations','decision_constraint','geographic_scope','source_url','reference_period','source_pages','quality_status']
 w=csv.DictWriter(f,fieldnames=names);w.writeheader()
 for c,usage,slope,texture,depth,ph,limits,decision in classes:
  w.writerow(dict(zip(names,[c,usage,slope,texture,depth,ph,limits,decision,'Distrito de Montero, provincia Ayabaca; no extrapolar a toda la sierra de Piura',MONTERO,'circa 2016','37-39','zonificación histórica; verificar polígono y licencia de uso'])))
