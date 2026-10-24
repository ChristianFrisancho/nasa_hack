import csv

guides={
 'papaya':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-PAPAYA.pdf',
 'banano':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-PLATANO.pdf',
 'yuca':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-YUCA.pdf',
 'maiz':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-MAIZ-AMARILLO-DURO.pdf',
 'uva':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-UVA.pdf',
 'limon':'https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-LIMON.pdf',
 'mango':'https://repositorio.midagri.gob.pe/bitstream/20.500.13036/1443/1/Ficha%20de%20requerimientos%20agroecol%C3%B3gicos_%20Mango.pdf',
}
rows=[]
def add(crop,agent,category,status,trigger='',soil='',rotation='',source='',date='',note=''):
 rows.append({'crop':crop,'agent_as_source':agent,'category':category,'local_presence_status':status,'climate_trigger_from_source':trigger,'soil_or_water_trigger_from_source':soil,'rotation_or_management_relevance':rotation,'source_url':source,'source_date':date,'status_note':note})

# Documented Piura events, with dates. These do not establish current prevalence.
add('arroz','Pomacea canaliculata','molusco','Piura: intervención histórica 2021','','agua de arrozales','historial y agua; confirmar presencia actual','https://www.senasa.gob.pe/senasacontigo/piura-midagri-despliega-acciones-de-prevencion-y-control-contra-el-caracol-manzana-del-arroz/','2021-02-25')
add('banano','Fusarium oxysporum f. sp. cubense R4T','hongo','Piura: brote histórico confirmado 2021','','suelo/material vegetal','bioseguridad y reglamentos vigentes; no asumir que un año de rotación sanea el suelo','https://www.senasa.gob.pe/senasacontigo/midagri-senasa-confirma-brote-de-fusarium-raza-4-tropical-en-piura','2021')
add('mango','moscas de la fruta','insecto','Piura: vigilancia/erradicación histórica 2023','','','hospedantes frutales y calendario de cosecha','https://www.senasa.gob.pe/senasacontigo/senasa-piura-se-mantiene-en-etapa-de-erradicacion-de-mosca-de-la-fruta/','2023-10-18','especie y prevalencia por parcela desconocidas')
add('limon','Huanglongbing (HLB)','enfermedad','vigilancia; fuente histórica indicó ausencia en Perú 2021','','','no convertir vigilancia en detección','https://www.senasa.gob.pe/senasacontigo/productores-piuranos-enviaron-mas-de-17-mil-toneladas-de-limon-a-mercados-internacionales/','2021-12-22','verificar estatus oficial actual')
add('papa','Tecia solanivora','insecto','vigilancia preventiva en Piura 2021, no detección','','','material de siembra y reglamentos','https://www.senasa.gob.pe/senasacontigo/piura-refuerzan-acciones-fitosanitarias-para-evitar-ingreso-de-la-polilla-de-la-papa/','2021-02-10')

# Guides identify potential host/pest interactions, NOT detections in Piura.
general='plaga/enfermedad de guía nacional; presencia en parcela/Piura no demostrada'
for agent,cat,trig,soil,rot in [
 ('Aphis spiraecola / Myzus persicae','insecto vector','','','hospedantes y transmisión viral'),
 ('Prodiplosis longifila','insecto','','','etapa inicial de papaya; también hospedantes en otros cultivos'),
 ('Tetranychus spp.','ácaro','época seca','','vigilar brotes/hojas'),
 ('Polyphagotarsonemus latus','ácaro','','','vigilar brotes/hojas'),
 ('Meloidogyne spp.','nematodo','','suelo infestado','rotación según rango de hospedantes y diagnóstico'),
 ('Phytophthora palmivora / P. parasitica','oomiceto','lluvia/humedad','drenaje deficiente','no elegir en sitio que se encharca sin mitigación'),
 ('Colletotrichum gloeosporioides','hongo','humedad','','riesgo en flor/fruto y poscosecha'),
]:add('papaya',agent,cat,general,trig,soil,rot,guides['papaya'],'2020')
for agent,cat,trig,soil,rot in [
 ('Fusarium oxysporum f. sp. cubense, otras razas','hongo','','mal drenaje / suelo contaminado','distinguir de R4T confirmada localmente'),
 ('Pseudocercospora fijiensis / Sigatoka negra','hongo','24-30°C, humedad alta','','pérdida de área foliar'),
 ('Cosmopolites sordidus','insecto','','cormos infestados','material propagativo y remanentes'),
 ('Castniomera humboldti','insecto','','','material propagativo y remanentes'),
 ('nematodos de Musa, grupo no resuelto','nematodo','','suelo/raíces','diagnosticar especie y hospedantes'),
]:add('banano',agent,cat,general,trig,soil,rot,guides['banano'],'2020')
for agent,cat,trig,soil in [
 ('Erinnyis ello','insecto','',''),('Lonchaea pendula','insecto','',''),
 ('Mononychellus spp.','ácaro','estación seca',''),
 ('Cercospora caribae','hongo','húmedo/fresco',''),
 ('Diplodia manihotis','hongo','humedad alta','raíces/tallo'),
 ('Xanthomonas manihotis, nombre según guía','bacteria','','esquejes'),
]:add('yuca',agent,cat,general,trig,soil,'esquejes sanos y secuencia de hospedantes',guides['yuca'],'2020','taxonomía histórica de la guía; verificar nomenclatura')
for agent,cat,trig,soil,rot in [
 ('Spodoptera frugiperda','insecto','poblaciones mayores en siembras de verano','','hospedantes compartidos con algodón, zapallo y leguminosas'),
 ('Elasmopalpus lignosellus','insecto','','mejor establecimiento en suelos arenosos','hospeda frijol/arveja/pallar'),
 ('Diatraea saccharalis','insecto','','','residuos/tallos hospederos'),
 ('Puccinia sorghi','hongo','lluvia y alta temperatura','','vigilar hojas'),
 ('Fusarium spp. / Gibberella spp.','hongo','','suelo/semilla','pudrición de granos y tallos'),
]:add('maiz amarillo duro',agent,cat,general,trig,soil,rot,guides['maiz'],'2020')
for agent,cat,trig,soil in [
 ('Phylloxera vitifoliae','insecto','','raíces/porta injerto'),
 ('Tetranychus spp. / Panonychus ulmi','ácaro','poca humedad',''),
 ('Erysiphe necator / oídio','hongo','',''),
 ('Botrytis cinerea','hongo','humedad alta',''),
 ('Agrobacterium vitis','bacteria','','herramientas/agua de riego'),
]:add('uva',agent,cat,general,trig,soil,'historial de hospedante y material sano',guides['uva'],'2020')
for agent,cat,trig,soil in [
 ('moscas de la fruta, grupo','insecto','','fruto remanente'),
 ('Prodiplosis longifila','insecto','','brotes'),
 ('Thrips tabaci','insecto','','flores/frutos'),
 ('Phytophthora citrophthora / P. parasitica','oomiceto','lluvia','drenaje deficiente'),
 ('Colletotrichum gloeosporioides','hongo','lluvia','herramientas'),
 ('Citrus tristeza virus','virus','','material propagativo / áfidos'),
]:add('limon',agent,cat,general,trig,soil,'material sano, drenaje y hospedantes',guides['limon'],'2020')
for agent,cat,trig in [('Ceratitis capitata','insecto','22-30°C, HR>75%'),('Colletotrichum gloeosporioides','hongo','25-30°C, HR95-100%'),('Oidium mangiferae','hongo','10-31°C, HR60-90%')]:add('mango',agent,cat,general,trig,'','fenología y humedad',guides['mango'],'2023','clima favorable según ficha, no incidencia observada')

fields=list(rows[0])
with open('plagas_hospedantes_condiciones_v2.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print('pest-host-condition records',len(rows))
