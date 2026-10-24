"""Curate FAO-56 Table 11 and Table 12 as transferable references, not Piura measurements."""
import csv,re
import pandas as pd

SOURCE='https://www.fao.org/4/x0490e/x0490e0b.htm'
# Table 12: Kc from standard, non-stressed crop conditions. Ranges retain source variability.
kc=[
 ('arroz','paddy rice',1.05,1.20,1.20,.60,.90,'inundación y manejo de agua condicionan interpretación'),
 ('maiz amarillo duro','grain maize',.30,1.20,1.20,.35,.60,'semilla y fecha cambian desarrollo; Kc es referencia'),
 ('maiz choclo','sweet maize',.30,1.15,1.15,1.05,1.05,'cosecha verde, no equiparar al grano'),
 ('frijol grano','dry beans and pulses',.40,1.15,1.15,.35,.35,'proxy de grupo; validar especie/caupí'),
 ('frijol verde','green beans',.50,1.05,1.05,.90,.90,'cosecha verde'),
 ('caupi','green gram and cowpeas',.40,1.05,1.05,.35,.60,'caupí; Kc final varía según cosecha y secado'),
 ('arveja','peas dry/seed',.40,1.15,1.15,.30,.30,'arveja grano seco, proxy FAO'),
 ('algodon','cotton',.35,1.15,1.20,.50,.70,'Pima local puede diferir'),
 ('papa','potato',.50,1.15,1.15,.75,.75,'fecha y variedad alteran calendario'),
 ('yuca','cassava year 1',.30,.80,.80,.30,.30,'año 1; año 2 tiene otros Kc'),
 ('yuca','cassava year 2',.30,1.10,1.10,.50,.50,'año 2; no asumir ciclo anual'),
 ('zapallo','pumpkin/winter squash',.50,1.00,1.00,.80,.80,'proxy por tipo de Cucurbita'),
 ('cebolla','dry onion',.70,1.05,1.05,.75,.75,'bulbo seco'),
 ('piquillo','sweet bell pepper',.60,1.05,1.05,.90,.90,'proxy de pimiento tipo bell; NO validado para piquillo'),
 ('banano','banana first year',.50,1.10,1.10,1.00,1.00,'planta de primer año'),
 ('banano','banana second year',1.00,1.20,1.20,1.10,1.10,'plantación establecida'),
 ('cacao','cacao',1.00,1.05,1.05,1.05,1.05,'plantación perenne'),
 ('cafe','coffee bare ground',.90,.95,.95,.95,.95,'sin cobertura activa'),
 ('cafe','coffee with weeds',1.05,1.10,1.10,1.10,1.10,'con vegetación activa; no implica manejo recomendable'),
 ('uva','table/raisin grapes',.30,.85,.85,.45,.45,'uva de mesa o pasas'),
 ('uva','wine grapes',.30,.70,.70,.45,.45,'uva vinífera distinta a uva de mesa'),
 ('limon','citrus no ground cover, 70% canopy',.70,.65,.65,.70,.70,'proxy de cítricos, depende de cobertura'),
 ('limon','citrus no ground cover, 50% canopy',.65,.60,.60,.65,.65,'proxy de cítricos, depende de cobertura'),
 ('limon','citrus no ground cover, 20% canopy',.50,.45,.45,.55,.55,'proxy de cítricos, depende de cobertura'),
]
fields=['crop','fao_crop_subtype','Kc_initial','Kc_mid_min','Kc_mid_max','Kc_end_min','Kc_end_max','locality_match','soil_match','stage_match','water_requirement_mm','source_url','source_table','source_scope','applicability_note']
with open('fao56_kc_referencias.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for crop,sub,ki,kml,kmh,kel,keh,note in kc:
  w.writerow({'crop':crop,'fao_crop_subtype':sub,'Kc_initial':ki,'Kc_mid_min':kml,'Kc_mid_max':kmh,'Kc_end_min':kel,'Kc_end_max':keh,'locality_match':'sin comprobar','soil_match':'sin comprobar','stage_match':'tipo general','water_requirement_mm':'','source_url':SOURCE,'source_table':'FAO-56, Tabla 12, capítulo 6','source_scope':'Kc estándar sin estrés hídrico/salino/nutricional ni plagas','applicability_note':note})

t=pd.read_html('fao56_crop_coefficients.html')[0]
terms=[('arroz',r'^Rice$'),('maiz amarillo duro',r'^Maize \(grain\)$'),('maiz choclo',r'^Maize \(sweet\)$'),('frijol grano',r'^Beans \(dry\)$'),('frijol verde',r'^Beans \(green\)$'),('caupi',r'^Green gram, cowpeas$'),('arveja',r'^Peas$'),('algodon',r'^Cotton$'),('papa',r'^Potato$'),('yuca',r'^Cassava: year'),('zapallo',r'^Pumpkin, Winter squash$'),('cebolla',r'^Onion \(dry\)$'),('piquillo',r'^Sweet peppers'),('banano',r'^Banana,'),('uva',r'^Grapes$'),('limon',r'^Citrus$')]
f2=['crop','fao_label','L_initial_days_as_printed','L_development_days_as_printed','L_mid_days_as_printed','L_late_days_as_printed','total_days_as_printed','planting_date_reference','analogue_region','soil_match','climate_match','Piura_days_predicted','source_url','source_table','validation_status']
count=0
with open('fao56_duracion_analogos.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=f2);w.writeheader()
 for _,r in t.iloc[1:].iterrows():
  label=str(r.iloc[0]).strip()
  matched=[crop for crop,pattern in terms if re.search(pattern,label,re.I)]
  if not matched:continue
  for crop in matched:
   w.writerow({'crop':crop,'fao_label':label,'L_initial_days_as_printed':r.iloc[2],'L_development_days_as_printed':r.iloc[3],'L_mid_days_as_printed':r.iloc[4],'L_late_days_as_printed':r.iloc[5],'total_days_as_printed':r.iloc[6],'planting_date_reference':r.iloc[7],'analogue_region':r.iloc[8],'soil_match':'desconocido','climate_match':'no calculado','Piura_days_predicted':'','source_url':SOURCE,'source_table':'FAO-56 Tabla 11, capítulo 6','validation_status':'análogo externo, no predicción de Piura'})
   count+=1
print('Kc references',len(kc),'duration analog records',count)
