"""FAO nutrient coefficients: uptake and exported product are distinct quantities."""
import csv

SOURCE='https://www.fao.org/4/a0443e/a0443e.pdf'
# Table 29: kg total above-ground uptake per tonne of principal product,
# including nutrients in by-products. Compiled mainly from Indian conditions.
uptake=[
 ('arroz','arroz cáscara',20,11,30,'exacto a nivel especie; variedad y manejo por validar'),
 ('maiz amarillo duro','grano',29.9,13.5,32.8,'exacto a nivel especie; híbrido por validar'),
 ('papa','tubérculo',3.3,.9,6.2,'exacto a nivel especie'),
 ('yuca','raíz tuberosa',5,2.3,6.8,'exacto a nivel especie'),
 ('algodon','algodón en rama',43.2,29.3,53.3,'especie/grupo; Pima por validar'),
 ('mango','fruta',6.7,1.7,6.7,'exacto a nivel especie'),
 ('banano','fruta',5.6,1.3,20.3,'banano/plátano de consumo; cultivar por validar'),
 ('limon','fruta',9,2,11.7,'proxy de cítricos, no limón sutil específico'),
 ('papaya','fruta',2.8,.8,2.2,'exacto a nivel especie'),
 ('uva','fruta',3.9,.6,6.2,'exacto a nivel especie; uso por validar'),
 ('cebolla','bulbo',2.7,1.3,3.9,'exacto a nivel especie'),
 ('cacao','grano seco',22.7,10.2,53.3,'cocoa, probablemente grano seco'),
 ('cafe','grano verde',129,27,174,'café verde; no confundir con cereza'),
 ('frijol de palo','grano',70.8,15.3,16,'pigeon pea Cajanus cajan; confirmar especie local'),
]
# Table 28: nutrients in exported harvested product, assuming this part leaves the field.
export=[
 ('maiz amarillo duro','grano',16.1,6.3,4.8,'grano seco; residuo no incluido'),
 ('maiz amarillo duro','rastrojo',9.9,3.7,14.4,'por tonelada de rastrojo retirado'),
 ('frijol grano','grano seco',41.7,13.9,13.9,'Phaseolus dry bean proxy; no usar para caupí sin validar'),
 ('arveja','grano',58.6,12.5,37.5,'peas genérico; uso y especie por validar'),
 ('piquillo','fruto',6.8,2.6,10.8,'proxy bell pepper, NO específico de piquillo'),
 ('cebolla','bulbo',2.7,1.2,2.4,'cebolla cosechada'),
 ('papa','tubérculo',3.0,1.6,5.3,'tubérculo; fuente usa white potato'),
 ('algodon','semilla y fibra',24.2,9.6,11.9,'semilla y fibra exportadas'),
 ('algodon','restos vegetales',19.0,5.3,24.0,'por tonelada de restos retirados'),
]
fields=['crop','main_product_or_part','measurement_type','N_kg_per_t','P2O5_kg_per_t','K2O_kg_per_t','base_unit','residue_management','source_region','source_year','source_url','source_table','Piura_calibration','note']
with open('nutrientes_cultivo_fao.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for crop,product,n,p,k,note in uptake:
  w.writerow(dict(zip(fields,[crop,product,'absorción total por biomasa por t de producto principal',n,p,k,'kg nutriente/t producto','incluye subproductos en biomasa; exportación depende de residuos','principalmente India',2004,SOURCE,'Tabla 29 FAO Plant Nutrition Bulletin 16','pendiente',note])))
 for crop,product,n,p,k,note in export:
  w.writerow(dict(zip(fields,[crop,product,'exportación potencial del producto retirado',n,p,k,'kg nutriente/t parte retirada','multiplicar solo por masa realmente retirada','principalmente Norteamérica',1997,SOURCE,'Tabla 28 FAO Plant Nutrition Bulletin 16','pendiente',note])))
print('uptake',len(uptake),'export',len(export))
