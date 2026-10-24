"""Build a regional NASA POWER climate panel; values are modeled grid estimates."""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd

locations={
 'Bajo_Piura':'Bajo Piura - referencia regional',
 'Chira_Sullana':'Chira Sullana - referencia regional',
 'San_Lorenzo':'San Lorenzo - referencia regional',
 'Ayabaca':'Ayabaca - referencia regional',
 'Huancabamba':'Huancabamba - referencia regional',
}
rows=[]
for slug,label in locations.items():
    p=json.loads(Path(f'power_{slug}_1981_2025.json').read_text())
    lon,lat,elev=p['geometry']['coordinates']
    series=p['properties']['parameter']
    fill=p['header']['fill_value']
    for day in series['T2M']:
        a={key:(None if vals[day]==fill else vals[day]) for key,vals in series.items()}
        rows.append({'zone':label,'lat':lat,'lon':lon,'model_elevation_m':elev,'date':pd.Timestamp(day),**a})
df=pd.DataFrame(rows).sort_values(['zone','date'])

# Approximate FAO-56 Penman-Monteith reference ET from POWER daily means.
# RH2M is a mean, so ea and ET0 are approximate; no field-scale calibration.
T=df.T2M.to_numpy();tx=df.T2M_MAX.to_numpy();tn=df.T2M_MIN.to_numpy()
RH=df.RH2M.to_numpy();u=df.WS2M.to_numpy();P=df.PS.to_numpy();Rs=df.ALLSKY_SFC_SW_DWN.to_numpy()
lat=np.radians(df.lat.to_numpy());z=df.model_elevation_m.to_numpy();J=df.date.dt.dayofyear.to_numpy()
es_tx=.6108*np.exp(17.27*tx/(tx+237.3));es_tn=.6108*np.exp(17.27*tn/(tn+237.3));es=(es_tx+es_tn)/2
ea=es*RH/100
dr=1+.033*np.cos(2*np.pi*J/365)
delta_s=.409*np.sin(2*np.pi*J/365-1.39)
ws=np.arccos(np.clip(-np.tan(lat)*np.tan(delta_s),-1,1))
Ra=(24*60/np.pi)*.0820*dr*(ws*np.sin(lat)*np.sin(delta_s)+np.cos(lat)*np.cos(delta_s)*np.sin(ws))
Rso=(.75+2e-5*z)*Ra
Rns=.77*Rs
Rnl=4.903e-9*((tx+273.16)**4+(tn+273.16)**4)/2*(.34-.14*np.sqrt(np.maximum(ea,0)))*(1.35*np.clip(Rs/Rso,0,1.5)-.35)
Rn=Rns-Rnl
delta=4098*(.6108*np.exp(17.27*T/(T+237.3)))/(T+237.3)**2
gamma=.000665*P
et0=(.408*delta*Rn+gamma*(900/(T+273))*u*(es-ea))/(delta+gamma*(1+.34*u))
df['ET0_approx_mm_day']=np.where(np.isfinite(et0)&np.isfinite(Rs),np.maximum(et0,0),np.nan)
df['year']=df.date.dt.year
df['month']=df.date.dt.month
df['heavy_rain_20mm']=df.PRECTOTCORR>=20
df['very_heavy_rain_50mm']=df.PRECTOTCORR>=50
df['extreme_rain_100mm']=df.PRECTOTCORR>=100
df['hot_day_35C']=df.T2M_MAX>=35
df['date']=df.date.dt.strftime('%Y-%m-%d')
df.to_csv('clima_piura_1981_2025.csv.gz',index=False,compression='gzip')

def longest_run(x):
    top=cur=0
    for v in x:
        if v:cur+=1;top=max(top,cur)
        else:cur=0
    return top

annual=[]
for (zone,year),g in df.groupby(['zone','year'],sort=True):
    rain=g.PRECTOTCORR
    annual.append({'zone':zone,'year':year,'days':len(g),
      'rain_mm':round(rain.sum(),2),'rain_max_1d_mm':round(rain.max(),2),
      'rain_max_5d_mm':round(rain.rolling(5,min_periods=5).sum().max(),2),
      'days_rain_ge_20mm':int(g.heavy_rain_20mm.sum()),
      'days_rain_ge_50mm':int(g.very_heavy_rain_50mm.sum()),
      'days_rain_ge_100mm':int(g.extreme_rain_100mm.sum()),
      'longest_dry_spell_days_under_1mm':longest_run(rain.fillna(0)<1),
      'Tmean_C':round(g.T2M.mean(),2),'Tmax_annual_C':round(g.T2M_MAX.max(),2),
      'days_Tmax_ge_35C':int(g.hot_day_35C.sum()),
      'ET0_approx_mm':round(g.ET0_approx_mm_day.sum(),2) if g.ET0_approx_mm_day.notna().all() else None,
      'source':'NASA POWER daily point, regional modeled climate',
      'ET0_method':'FAO-56 PM approximation using mean RH2M; missing before 1984 solar',
    })
annual=pd.DataFrame(annual)
annual.to_csv('clima_piura_anual_1981_2025.csv',index=False)
monthly=df.groupby(['zone','year','month'],as_index=False).agg(rain_mm=('PRECTOTCORR','sum'),Tmean_C=('T2M','mean'),Tmax_max_C=('T2M_MAX','max'),ET0_approx_mm=('ET0_approx_mm_day',lambda x:x.sum(min_count=1)),days_rain_ge_20mm=('heavy_rain_20mm','sum'))
monthly.to_csv('clima_piura_mensual_1981_2025.csv',index=False)
baseline=annual[(annual.year>=1991)&(annual.year<=2020)].groupby('zone').agg(rain_mm_1991_2020=('rain_mm','mean'),Tmean_C_1991_2020=('Tmean_C','mean'),ET0_approx_mm_1991_2020=('ET0_approx_mm','mean'),rain_95pct_year=('rain_mm',lambda x:x.quantile(.95))).reset_index()
baseline.round(2).to_csv('clima_piura_baseline_1991_2020.csv',index=False)
print('daily',len(df),'annual',len(annual),'monthly',len(monthly))
print(baseline.round(1).to_string(index=False))
