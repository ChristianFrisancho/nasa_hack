"""Illustrative 2025 crop ETc scenarios; no field or soil-water calibration."""
import csv
import numpy as np
import pandas as pd

durations=pd.read_html('fao56_crop_coefficients.html')[0]
kc=list(csv.DictReader(open('fao56_kc_referencias.csv')))
specs=[
 ('arroz',141,'paddy rice'),('maiz amarillo duro',127,'grain maize'),('maiz choclo',133,'sweet maize'),
 ('frijol grano',76,'dry beans and pulses'),('arveja',89,'peas dry/seed'),
 ('algodon',100,'cotton'),('papa',59,'potato'),('yuca',56,'cassava year 1'),('zapallo',43,'pumpkin/winter squash'),
 ('cebolla',19,'dry onion'),('piquillo',32,'sweet bell pepper'),('banano',163,'banana second year'),
 ('uva',166,'table/raisin grapes'),('limon',172,'citrus no ground cover, 70% canopy'),
]
climate=pd.read_csv('clima_piura_1981_2025.csv.gz',parse_dates=['date'])
climate=climate[climate.year==2025]
out=[]
for crop,rowidx,subtype in specs:
 r=durations.iloc[rowidx]
 stages=[int(str(v).strip()) for v in r.iloc[2:6]]
 total=int(str(r.iloc[6]).strip())
 if sum(stages)!=total:raise RuntimeError(f'FAO duration inconsistent: {crop} {stages} {total}')
 candidates=[x for x in kc if x['crop']==crop and x['fao_crop_subtype']==subtype]
 if len(candidates)!=1:raise RuntimeError(f'Missing/multiple Kc for {crop}/{subtype}')
 k=candidates[0];ki=float(k['Kc_initial'])
 for band in ['min','max']:
  km=float(k['Kc_mid_'+band]);ke=float(k['Kc_end_'+band])
  k_curve=np.r_[np.repeat(ki,stages[0]),np.linspace(ki,km,stages[1]+1)[1:],np.repeat(km,stages[2]),np.linspace(km,ke,stages[3]+1)[1:]]
  assert len(k_curve)==total
  for zone,g in climate.groupby('zone'):
   g=g.set_index('date').sort_index()
   for start in ['2025-01-01','2025-07-01']:
    if pd.Timestamp(start)+pd.Timedelta(days=total-1)>pd.Timestamp('2025-12-31'):continue
    span=g.loc[start:pd.Timestamp(start)+pd.Timedelta(days=total-1)]
    if len(span)!=total or span.ET0_approx_mm_day.isna().any():continue
    et=(span.ET0_approx_mm_day.to_numpy()*k_curve).sum()
    rain=span.PRECTOTCORR.sum()
    out.append({'crop':crop,'subtype_analog':subtype,'reference_region':r.iloc[8],
     'start_date_hypothetical':start,'duration_days_external_analog':total,'zone_NASA':zone,
     'Kc_band':band,'ETc_reference_mm':round(et,1),'rain_modelled_mm':round(rain,1),
     'ETc_minus_total_rain_mm_diagnostic':round(et-rain,1),
     'days_Tmax_ge_35C':int((span.T2M_MAX>=35).sum()),
     'days_rain_ge_50mm':int((span.PRECTOTCORR>=50).sum()),
     'soil_hydraulic_properties':'unknown','effective_rainfall':'unknown','gross_irrigation_m3_ha':'unknown',
     'actual_duration_days_Piura':'unknown',
     'source_climate':'https://power.larc.nasa.gov/api/temporal/daily/point',
     'source_crop':'https://www.fao.org/4/x0490e/x0490e0b.htm',
     'interpretation':'Kc estándar x ET0 NASA regional; no es consumo total de arroz inundado ni recomendación de riego/cultivo'})
with open('escenarios_ETc_2025_referencia.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print('reference scenarios',len(out))
for x in out:
 if x['crop']=='arroz' and x['zone_NASA'].startswith('Bajo') and x['Kc_band']=='min':print('rice example',x)
