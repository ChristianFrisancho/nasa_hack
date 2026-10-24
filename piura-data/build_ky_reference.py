"""Seasonal FAO Ky values for broad yield response to water deficits."""
import csv
values=[('banano',1.20,1.35,'Banana'),('frijol grano',1.15,1.15,'Beans'),('algodon',.85,.85,'Cotton'),('maiz amarillo duro',1.25,1.25,'Maize'),('cebolla',1.1,1.1,'Onion'),('arveja',1.15,1.15,'Peas'),('piquillo',1.1,1.1,'Pepper proxy'),('papa',1.1,1.1,'Potato')]
source='https://www.fao.org/4/i2800e/i2800e.pdf'
fields=['crop','Ky_seasonal_min','Ky_seasonal_max','FAO_crop_label','source_url','source_table','model_equation','regional_calibration','limitation']
with open('fao_ky_respuesta_agua.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for crop,lo,hi,label in values:w.writerow(dict(zip(fields,[crop,lo,hi,label,source,'FAO 2012 Crop Yield Response to Water Table 1, copied from FAO 33','1-Ya/Ym = Ky*(1-ETa/ETm)','pendiente en Piura','Ky estacional general: no representa daño por inundación/huaico/plagas; las fases tienen sensibilidades distintas'])))
print('Ky records',len(values))
