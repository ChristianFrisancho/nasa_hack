"""Genera fichas_anuales.csv y perennes.csv en formato del CONTRATO (+confianza, id).
Todos los valores están transcritos a mano de las tablas citadas en fuentes.py; nada se interpola."""
import csv, os
from fuentes import F

COLS = ["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","lugar","lat","lon",
        "fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas","confianza","id"]
OUT = os.path.dirname(os.path.abspath(__file__))

def mk(rows, prefix):
    def r(variable, valor, unidad, cultivo, etapa, src, tipo, estado, notas, conf, vmin="", vmax="",
          variedad="", lugar="", fecha="", metodo="", url=None, fuente=None):
        cita, u = F[src] if src else ("", "")
        rows.append(dict(variable=variable, valor=valor, valor_min=vmin, valor_max=vmax, unidad=unidad,
            cultivo=cultivo, variedad=variedad, etapa=etapa, lugar=lugar, lat="", lon="", fecha_o_periodo=fecha,
            fuente=fuente or cita, url_o_doi=url or u, metodo=metodo or "transcripción de tabla publicada",
            tipo_evidencia=tipo, estado=estado, notas=notas, confianza=conf, id=f"{prefix}{len(rows)+1:04d}"))
    return r

NO_RANGO = "sin rango: la fuente da un solo valor"
ANALOGO = ("análogo FAO-56 de otra región; Piura costa es árida cálida (ETo alta), por eso se eligió el caso árido/tropical "
           "más cercano; min/max = rango entre todos los casos FAO-56 del cultivo")

# ---------- 1. Duración de etapas (FAO-56 T11): cultivo -> (elegido, región, fecha, [(ini,dev,mid,late,total) todos los casos])
DUR = {
 "arroz": ((30,30,60,30,150),"Tropics; Mediterranean","Dec; May",[(30,30,60,30,150),(30,30,80,40,180)]),
 "maiz amarillo duro": ((25,40,45,30,140),"Arid Climate","Dec/Jan",[(30,50,60,40,180),(25,40,45,30,140),(20,35,40,30,125),(30,40,50,30,150),(30,40,50,50,170)]),
 "maiz amilaceo": ((30,50,60,40,180),"East Africa (alt.)","April",[(30,50,60,40,180),(25,40,45,30,140),(20,35,40,30,125),(30,40,50,30,150),(30,40,50,50,170)]),
 "algodon": ((30,50,60,55,195),"Egypt; Pakistan; Calif.","Mar-May",[(30,50,60,55,195),(45,90,45,45,225),(30,50,60,55,195),(30,50,55,45,180)]),
 "frijol castilla/grano seco": ((15,25,35,20,95),"Pakistan, Calif.","June",[(20,30,40,20,110),(15,25,35,20,95),(25,25,30,20,100)]),
 "frijol caupi": ((20,30,30,20,110),"Mediterranean","March",[(20,30,30,20,110)]),
 "camote": ((15,30,50,30,125),"Tropical regions","Rainy seas.",[(20,30,60,40,150),(15,30,50,30,125)]),
 "yuca": ((20,40,90,60,210),"Tropical regions","Rainy",[(20,40,90,60,210)]),
 "pimiento/paprika": ((30,40,110,30,210),"Arid Region","October",[(25,35,40,20,125),(30,40,110,30,210)]),
 "papa": ((25,30,45,30,130),"(Semi) Arid Climate","Jan/Nov",[(25,30,30,30,115),(25,30,45,30,130),(30,35,50,30,145),(45,30,70,20,165),(30,35,50,25,140)]),
 "trigo": ((15,30,65,40,150),"East Africa","July",[(15,25,50,30,120),(20,25,60,30,135),(15,30,65,40,150),(40,30,40,20,130),(40,60,60,40,200),(20,50,60,30,160)]),
 "arveja": ((20,30,35,15,100),"Mediterranean","Mar/Apr",[(15,25,35,15,90),(20,30,35,15,100),(35,25,30,20,110)]),
 "haba": ((20,30,35,15,100),"Mediterranean","Mar/Apr",[(15,25,35,15,90),(20,30,35,15,100)]),
 "sorgo": ((20,35,45,30,140),"Arid Region","Mar/April",[(20,35,40,30,130),(20,35,45,30,140)]),
 "mani": ((25,35,45,25,130),"West Africa","Dry season",[(25,35,45,25,130),(35,35,35,35,140),(35,45,35,25,140)]),
 "soya": ((15,15,40,15,85),"Tropics","Dec",[(15,15,40,15,85),(20,30,60,25,140),(20,25,75,30,150)]),
 "cana de azucar (planta)": ((35,60,190,120,405),"Low Latitudes","",[(35,60,190,120,405),(50,70,220,140,480),(75,105,330,210,720)]),
 "cana de azucar (soca)": ((25,70,135,50,280),"Low Latitudes","",[(25,70,135,50,280),(30,50,180,60,320),(35,105,210,70,420)]),
}
ETAPAS = ["inicial","desarrollo","media","final","ciclo_total"]
FAO_LABEL = {"frijol castilla/grano seco":"Beans (dry)","frijol caupi":"Green gram, cowpeas","camote":"Sweet potato",
  "yuca":"Cassava year 1","pimiento/paprika":"Sweet peppers (bell)","papa":"Potato","trigo":"Barley/Oats/Wheat","arveja":"Peas",
  "haba":"Faba bean","sorgo":"Sorghum","mani":"Groundnut","soya":"Soybeans","arroz":"Rice","maiz amarillo duro":"Maize (grain)",
  "maiz amilaceo":"Maize (grain)","algodon":"Cotton","cana de azucar (planta)":"Sugarcane, virgin","cana de azucar (soca)":"Sugarcane, ratoon"}

# ---------- 2. Kc FAO-56 T12: (ini, mid, end, nota)
KC = {
 "arroz":(1.05,1.20,"0.90-0.60",""), "maiz amarillo duro":(0.30,1.20,"0.60-0.35","Kc_end 0.60 si se cosecha con grano húmedo, 0.35 si seca en campo"),
 "maiz amilaceo":(0.30,1.20,"0.60-0.35","se usa la fila maize field (grain); no hay fila específica para amiláceo"),
 "algodon":(0.35,"1.15-1.20","0.70-0.50",""), "frijol castilla/grano seco":(0.4,1.15,0.35,"beans dry"),
 "frijol caupi":(0.4,1.05,"0.60-0.35","fila green gram and cowpeas; Kc_ini heredado del grupo leguminosas"),
 "camote":(0.5,1.15,0.65,"Kc_ini heredado del grupo raíces y tubérculos"), "yuca":(0.3,0.80,0.30,"año 1"),
 "pimiento/paprika":(0.6,1.05,0.90,"fila sweet peppers (bell); Kc_ini heredado del grupo solanáceas"),
 "papa":(0.5,1.15,0.75,"Kc_ini heredado del grupo raíces y tubérculos"), "trigo":(0.3,1.15,"0.25-0.4","spring wheat"),
 "arveja":(0.4,1.15,0.30,"peas dry"), "haba":(0.5,1.15,0.30,"faba bean dry"), "sorgo":(0.3,"1.00-1.10",0.55,"grain"),
 "mani":(0.4,1.15,0.60,""), "soya":(0.4,1.15,0.50,""), "cana de azucar (planta)":(0.40,1.25,0.75,""),
 "cana de azucar (soca)":(0.40,1.25,0.75,"FAO-56 da una sola fila de Kc para caña"),
}
# ---------- 3. Raíz y p (T22): (raíz m min,max ; p)
ROOT = {"arroz":(0.5,1.0,0.20),"maiz amarillo duro":(1.0,1.7,0.55),"maiz amilaceo":(1.0,1.7,0.55),"algodon":(1.0,1.7,0.65),
 "frijol castilla/grano seco":(0.6,0.9,0.45),"frijol caupi":(0.6,1.0,0.45),"camote":(1.0,1.5,0.65),"yuca":(0.5,0.8,0.35),
 "pimiento/paprika":(0.5,1.0,0.30),"papa":(0.4,0.6,0.35),"trigo":(1.0,1.5,0.55),"arveja":(0.6,1.0,0.40),"haba":(0.5,0.7,0.45),
 "sorgo":(1.0,2.0,0.55),"mani":(0.5,1.0,0.50),"soya":(0.6,1.3,0.50),"cana de azucar (planta)":(1.2,2.0,0.65),"cana de azucar (soca)":(1.2,2.0,0.65)}
# ---------- 4. Salinidad: FAO-29 T4 (ECe a 100/90/75/50/0 %) y FAO-56 T23 (a, b, clase)
SAL29 = {"arroz":(3.0,3.8,5.1,7.2,11),"maiz amarillo duro":(1.7,2.5,3.8,5.9,10),"maiz amilaceo":(1.7,2.5,3.8,5.9,10),
 "algodon":(7.7,9.6,13,17,27),"frijol castilla/grano seco":(1.0,1.5,2.3,3.6,6.3),"frijol caupi":(4.9,5.7,7.0,9.1,13),
 "camote":(1.5,2.4,3.8,6.0,11),"pimiento/paprika":(1.5,2.2,3.3,5.1,8.6),"papa":(1.7,2.5,3.8,5.9,10),"trigo":(6.0,7.4,9.5,13,20),
 "haba":(1.5,2.6,4.2,6.8,12),"sorgo":(6.8,7.4,8.4,9.9,13),"mani":(3.2,3.5,4.1,4.9,6.6),"soya":(5.0,5.5,6.3,7.5,10),
 "cana de azucar (planta)":(1.7,3.4,5.9,10,19),"cana de azucar (soca)":(1.7,3.4,5.9,10,19)}
SAL56 = {"arroz":("3.0","12","S"),"maiz amarillo duro":("1.7","12","MS"),"maiz amilaceo":("1.7","12","MS"),"algodon":("7.7","5.2","T"),
 "frijol castilla/grano seco":("1.0","19","S"),"frijol caupi":("4.9","12","MT"),"camote":("1.5-2.5","10","MS"),
 "pimiento/paprika":("1.5-1.7","12.0-14.0","MS"),"papa":("1.7","12","MS"),"trigo":("6.0","7.1","MT"),"arveja":("1.5","14","S"),
 "haba":("1.5-1.6","9.6","MS"),"sorgo":("6.8","16","MT"),"mani":("3.2","29","MS"),"soya":("5.0","20","MT"),
 "cana de azucar (planta)":("1.7","5.9","MS"),"cana de azucar (soca)":("1.7","5.9","MS")}
CLASE29 = {"arroz":"MS","maiz amarillo duro":"MS","maiz amilaceo":"MS","algodon":"T","frijol castilla/grano seco":"S","frijol caupi":"MT",
 "camote":"MS","pimiento/paprika":"MS","papa":"MS","trigo":"MT","haba":"MS","sorgo":"MT","mani":"MS","soya":"MT",
 "cana de azucar (planta)":"MS","cana de azucar (soca)":"MS"}
# ---------- 5. Nutrientes PNB16 T29 absorción total kg por t de producto principal (N, P2O5, K2O)
UPT = {"arroz":(20,11,30),"trigo":(25,9,33),"maiz amarillo duro":(29.9,13.5,32.8),"maiz amilaceo":(29.9,13.5,32.8),
 "sorgo":(16.4,7.7,25.5),"mani":(58.1,19.6,30.1),"soya":(70.7,30.9,57.7),"papa":(3.3,0.9,6.2),"yuca":(5.0,2.3,6.8),
 "cana de azucar (planta)":(2.1,1.2,3.4),"cana de azucar (soca)":(2.1,1.2,3.4),"algodon":(43.2,29.3,53.3)}
# PNB16 T28 contenido en lo cosechado (exportación) kg/t: cultivo -> [(organo, N, P2O5, K2O, etiqueta tabla)]
EXP = {"maiz amarillo duro":[("grano",16.1,6.3,4.8,"Corn grain"),("rastrojo",9.9,3.7,14.4,"Corn stover")],
 "maiz amilaceo":[("grano",16.1,6.3,4.8,"Corn grain"),("rastrojo",9.9,3.7,14.4,"Corn stover")],
 "sorgo":[("grano",14.9,7.4,4.5,"Sorghum grain"),("rastrojo",9.7,3.0,14.2,"Sorghum stover")],
 "trigo":[("grano",20.8,10.4,6.3,"Wheat grain"),("paja",6.0,1.5,10.4,"Wheat straw")],
 "frijol castilla/grano seco":[("grano",41.7,13.9,13.9,"Bean dry")], "frijol caupi":[("heno",26.8,5.6,17.9,"Cowpea hay")],
 "pimiento/paprika":[("fruto fresco",6.8,2.6,10.8,"Bell peppers")], "arveja":[("grano",58.6,12.5,37.5,"Peas")],
 "papa":[("tubérculo",3.0,1.6,5.3,"Potatoes")], "camote":[("raíz",2.4,1.1,5.8,"Sweet potatoes")],
 "algodon":[("semilla+fibra",24.2,9.6,11.9,"Cotton seed and lint"),("residuo (trash)",19.0,5.3,24.0,"Cotton trash")],
 "mani":[("vaina",35.0,5.5,8.8,"Peanuts nuts"),("follaje",20.0,3.4,30.0,"Peanut vines")],
 "soya":[("grano",95.6,20.8,37.6,"Soybeans"),("residuo",14.6,2.6,12.1,"Soybean residue")]}

def build_anuales():
    rows=[]; r=mk(rows,"AN")
    for c,(sel,reg,fecha,cases) in DUR.items():
        for i,et in enumerate(ETAPAS):
            vals=[k[i] for k in cases]
            note=f"{ANALOGO}. Caso elegido: {FAO_LABEL[c]}, {reg}, siembra {fecha}."
            if c=="frijol caupi" and et=="ciclo_total": note+=" OJO: la suma de etapas impresa (20+30+30+20=100) no coincide con el total impreso 110."
            if c=="maiz amilaceo": note+=" Para maíz amiláceo (sierra) se eligió el caso de altura de África del Este."
            if c=="trigo": note+=" Trigo de sierra: caso East Africa (altura)."
            r("duracion_etapa",sel[i],"días",c,et,"F56T11","analogo_externo","estimado",note,0.4,
              vmin=min(vals) if len(set(vals))>1 else "",vmax=max(vals) if len(set(vals))>1 else "",lugar=reg,fecha=fecha)
        if c in KC:
            ini,mid,end,n=KC[c]
            for et,v in (("inicial",ini),("media",mid),("final",end)):
                s=str(v); lo=hi=""; val=v
                if "-" in s: a,b=sorted(float(x) for x in s.split("-")); lo,hi,val=a,b,""
                r("kc",val,"adimensional",c,et,"F56T12","bibliografico","estimado",
                  (n+"; " if n else "")+("rango de la tabla; valor central no dado" if val=="" else NO_RANGO)+
                  ". Kc estándar (subhúmedo, HRmin 45 %, u2 2 m/s); en Piura árida Kc_mid/end deben ajustarse con ec. 62 de FAO-56",0.6,vmin=lo,vmax=hi)
            r("kc","","adimensional",c,"desarrollo","","bibliografico","desconocido",
              "FAO-56 no tabula Kc para la etapa de desarrollo: se interpola linealmente entre Kc_ini y Kc_mid (no se rellena aquí)",0,fuente="",url="")
        if c in ROOT:
            a,b,p=ROOT[c]
            r("profundidad_raiz_max",(a+b)/2 if False else "","m",c,"media","F56T22","bibliografico","estimado",
              "rango de la tabla; valor central no dado",0.6,vmin=a,vmax=b)
            r("fraccion_agotamiento_p",p,"fracción",c,"ciclo","F56T22","bibliografico","estimado",
              NO_RANGO+"; válido para ETc≈5 mm/día; FAO-56 ajusta p=p_tabla+0.04(5−ETc)"+("; para arroz p se expresa respecto a saturación" if c=="arroz" else ""),0.6)
        if c in SAL29:
            vals=SAL29[c]
            for pct,v in zip((100,90,75,50,0),vals):
                var="ece_umbral" if pct==100 else f"ece_rend_{pct}pct"
                r(var,v,"dS/m",c,"ciclo","F29T4","bibliografico","estimado",
                  NO_RANGO+"; ECe de extracto saturado; datos de ensayos de Maas y Hoffman (EE.UU.), no de Piura; FAO-56 T23 copia el umbral del mismo linaje (no es fuente independiente)",0.6)
        if c in SAL56:
            a,b,cl=SAL56[c]
            if c not in SAL29:
                lo=hi=""; val=a
                if "-" in a: lo,hi=a.split("-"); val=""
                r("ece_umbral",val,"dS/m",c,"ciclo","F56T23","bibliografico","estimado","Maas-Hoffman; "+(NO_RANGO if val!="" else "rango de la tabla"),0.6,vmin=lo,vmax=hi)
            lo=hi=""; val=b
            if "-" in b: lo,hi=b.split("-"); val=""
            r("pendiente_salinidad_b",val,"%/(dS/m)",c,"ciclo","F56T23","bibliografico","estimado",
              "Y(%)=100−b(ECe−a) (Maas-Hoffman); "+(NO_RANGO if val!="" else "rango de la tabla"),0.6,vmin=lo,vmax=hi)
            cl29=CLASE29.get(c,"")
            note="clases: S <1.3, MS 1.3-3, MT 3-6, T 6-10 dS/m (FAO-29)"
            if cl29 and cl29!=cl: note+=f"; DISCREPANCIA: FAO-29 Tabla 5 la clasifica {cl29}"
            r("clase_tolerancia_salinidad",cl,"categoría",c,"ciclo","F56T23","bibliografico","estimado",note,0.5 if cl29 and cl29!=cl else 0.6)
        if c in UPT:
            for nut,v in zip(("N","P2O5","K2O"),UPT[c]):
                r(f"absorcion_total_{nut}",v,"kg/t producto",c,"ciclo","PNB16T29","analogo_externo","estimado",
                  NO_RANGO+"; datos de India (Tandon 2004) por t de producto principal incluyendo residuos; comparables solo como orden de magnitud, la absorción depende del rendimiento y manejo de Piura",0.4)
        for org,n,p,k,lab in EXP.get(c,[]):
            for nut,v in zip(("N","P2O5","K2O"),(n,p,k)):
                conf=0.4; note=f"{NO_RANGO}; fila '{lab}'; datos de Carolina del Norte, EE.UU. (Zublena); exportación por t de órgano cosechado"
                if c=="soya" and org=="grano": conf=0.2; note+="; DUDOSO: N=95.6 kg/t supera la absorción total de PNB16 T29 (70.7), posible error de unidad en la tabla original"
                r(f"exportacion_{nut}",v,"kg/t órgano",c,"cosecha","PNB16T28","analogo_externo","estimado",note,conf,variedad="",metodo=f"transcripción de tabla publicada; órgano: {org}")
    # cultivos sin datos en las tablas
    # Páprika, manual peruano MIDAGRI (ronda 2): etapas tipo FAO y profundidad radicular por etapa
    NP="manual peruano; leído en extracto de búsqueda, PDF no descargado desde el box; complementa el análogo FAO-56"
    for et,v in zip(ETAPAS,(25,60,45,45,175)):
        r("duracion_etapa",v,"días","pimiento/paprika",et,"MIDAGRI_PAPRIKA","regional","estimado",NP,0.45,variedad="páprika",lugar="Perú (costa)")
    for et,v in zip(("inicial","desarrollo","media","final"),(0.15,0.25,0.35,0.45)):
        r("profundidad_raiz_etapa",v,"m","pimiento/paprika",et,"MIDAGRI_PAPRIKA","regional","estimado",NP,0.45,variedad="páprika",lugar="Perú (costa)")
    r("ece_umbral",1.5,"dS/m","pimiento/paprika","ciclo","MIDAGRI_PAPRIKA","regional","estimado",NP+"; coincide con FAO-29 para pimiento (1.5), misma línea Maas, no cuenta como fuente independiente",0.5,variedad="páprika")
    # Variedades peruanas (ronda 2): ciclo total por variedad; contrasta con el análogo FAO-56
    SN="leído en extracto de búsqueda; el PDF de INIA no descarga desde el box ni con tavily_extract"
    r("duracion_etapa","","días","frijol caupi","ciclo_total","INIA432","regional","estimado",
      "periodo vegetativo de la variedad; liberada para Piura, Lambayeque, La Libertad y norte chico de Lima (Agraria.pe); más corto que el análogo FAO-56 de 110 d; "+SN,0.5,
      vmin=80,vmax=100,variedad="INIA 432 Vaina Verde",lugar="costa norte del Perú")
    r("rendimiento_comercial","","kg/ha","frijol caupi","cosecha","INIA432","regional","estimado","rendimiento potencial 3000 kg/ha; Agraria.pe cita 3.5 t/ha; "+SN,0.45,
      vmin=2000,vmax=2500,variedad="INIA 432 Vaina Verde",lugar="costa norte del Perú")
    r("tolerancia_salinidad_cualitativa","resistente (sin cifra)","categoría","frijol caupi","ciclo","AGRARIA432","regional","estimado",
      "nota de prensa; sin ECe umbral; no reemplaza FAO-29 (umbral 4.9 dS/m) ni FAO-56 (clase MT)",0.3,variedad="INIA 432 Vaina Verde")
    r("duracion_etapa",148,"días","arroz","ciclo_total","INIA510","regional","estimado",
      "'ciclo intermedio, en promedio madura en 148 días, igual que IR 43'; variedad de Mallares (valle del Chira, Piura); "+SN,0.45,variedad="INIA 510 Mallares",lugar="Piura (Chira)")
    r("duracion_etapa","","días","arroz","ciclo_total","INIA502","regional","estimado","periodo vegetativo 150 a 155 días; variedad de costa norte (Lambayeque); "+SN,0.45,
      vmin=150,vmax=155,variedad="INIA 502 Pitipo",lugar="costa norte del Perú")
    for c,a,b in (("arroz",4,6),("maiz amilaceo",4,7),("maiz amarillo duro",4,6),("trigo",5,8),("yuca",7,10),("haba",4,6)):
        r("periodo_vegetativo","","meses",c,"ciclo_total","INEI_ENA24","regional","estimado",
          "tabla operativa nacional del censo/encuesta agropecuaria, no por región ni variedad"+("; haba = grano seco" if c=="haba" else ""),0.5,vmin=a,vmax=b,lugar="Perú")
    r("temperatura_optima","","°C","frijol caupi","ciclo","MIDAGRI_CAUPI","analogo_externo","estimado","manual de Loreto que cita EMBRAPA 2002; no es dato de Piura",0.4,vmin=18,vmax=34)
    r("ph_tolerado","","pH","frijol caupi","ciclo","MIDAGRI_CAUPI","analogo_externo","estimado","'puede tolerar la acidez del suelo (pH 5.5 a 6.6)', cita EMBRAPA 2002; Piura costa tiene suelos neutros a alcalinos",0.4,vmin=5.5,vmax=6.6)
    r("periodo_vegetativo","","meses","zarandaja","ciclo_total","RG_ZARANDAJA","regional","estimado",
      "'periodo vegetativo 3 a 6 meses dependiendo variedad'; densidad 20 000 plantas/ha; fuente única no revisada; etapas FAO siguen desconocidas",0.35,vmin=3,vmax=6,lugar="Piura")
    for c,var,why in [("zarandaja","duracion_etapa","Lablab purpureus no figura en FAO-56 T11; falta ficha INIA/DRA de Piura"),
                      ("zarandaja","kc","no figura en FAO-56 T12"),("zarandaja","ece_umbral","no figura en FAO-29 ni FAO-56"),
                      ("arveja","ece_rend_50pct","FAO-29 Tabla 4 no incluye arveja; solo FAO-56 T23 da umbral"),
                      ("yuca","ece_umbral","yuca no figura en FAO-29 T4 ni FAO-56 T23"),
                      ("frijol caupi","absorcion_total_N","PNB16 T29 no lista caupí (sí green gram 106 kg/t, especie distinta)")]:
        r(var,"","",c,"ciclo","","bibliografico","desconocido",why,0,fuente="",url="")
    # ---- Fuentes peruanas: duraciones
    r("periodo_vegetativo",145,"días","maiz amarillo duro","ciclo_total","INIA619","regional","observado",
      "siembra de verano en costa; ensayos INIA Vista Florida (Chiclayo, costa norte)",0.6,vmin=140,vmax=150,variedad="INIA 619 Megahíbrido",lugar="costa norte (Lambayeque)",fecha="verano",metodo="ensayos de adaptación y parcelas de comprobación INIA")
    r("periodo_vegetativo",165,"días","maiz amarillo duro","ciclo_total","INIA619","regional","observado",
      "siembra de invierno en costa",0.6,vmin=160,vmax=170,variedad="INIA 619 Megahíbrido",lugar="costa norte (Lambayeque)",fecha="invierno",metodo="ensayos INIA")
    r("dias_a_floracion",65,"días","maiz amarillo duro","media","INIA619","regional","observado","verano",0.6,vmin=60,vmax=70,variedad="INIA 619 Megahíbrido",lugar="costa norte (Lambayeque)",fecha="verano",metodo="ensayos INIA")
    r("dias_a_floracion","","días","maiz amarillo duro","media","INIA619","regional","observado","invierno; rango sin valor central",0.6,vmin=75,vmax=90,variedad="INIA 619 Megahíbrido",lugar="costa norte (Lambayeque)",fecha="invierno",metodo="ensayos INIA")
    r("dias_a_floracion","","días después de germinación","arroz","media","MIDAGRI_ARROZ","bibliografico","estimado",
      "fenología nacional SENAMHI; el texto extraído del PDF está desordenado y la asignación del rango 72-95 a floración es una lectura nuestra; verificar en el PDF",0.4,vmin=72,vmax=95,lugar="Perú (nacional)",metodo="lectura de tabla de fenología")
    r("dias_a_madurez_cornea","","días después de germinación","arroz","final","MIDAGRI_ARROZ","bibliografico","estimado",
      "misma advertencia de lectura que floración; la ficha da periodo vegetativo '4 meses según variedad', variedades no piuranas (NIR, BG 90, Tacuari)",0.4,vmin=110,vmax=130,lugar="Perú (nacional)",metodo="lectura de tabla de fenología")
    for et,lo,hi,val in (("inicial","","",7),("desarrollo","","",70),("media",70,90,""),("final",120,150,"")):
        r("dias_desde_siembra_a_fase",val,"días","pimiento/paprika",et,"MIDAGRI_PAPRIKA","bibliografico","estimado",
          {"inicial":"germinación","desarrollo":"fin de fase vegetativa (lectura nuestra: la tabla dice 'Tiempo (días) 7 70 70-90 120-150')","media":"floración y cuajado","final":"cosecha"}[et]+
          "; manual nacional, no específico de Piura; interpretamos los tiempos como acumulados desde siembra",0.4,vmin=lo,vmax=hi,lugar="Perú (nacional)")
    r("ventana_siembra","15 dic - 30 ene","fecha","arroz","siembra","DRA_CAL","regional","observado","almácigo y siembra directa; campaña grande 2025-26; texto, no cifra",0.6,lugar="Piura",fecha="2025-2026")
    r("ventana_siembra","10 ene - 28 feb","fecha","arroz","trasplante","DRA_CAL","regional","observado","trasplante; campaña grande 2025-26",0.6,lugar="Piura",fecha="2025-2026")
    r("ventana_siembra","15 mar - 30 abr","fecha","algodon","siembra","DRA_CAL","regional","observado","campaña grande 2025-26",0.6,lugar="Piura",fecha="2025-2026")
    # ---- Anegamiento
    r("tolerancia_anegamiento","alta (cultivo inundado)","categoría","arroz","ciclo","FAO62","bibliografico","estimado","FAO-62 trata el arroz bajo inundación como excepción a los criterios de drenaje de cultivos de secano",0.5)
    for d,(lo,hi,v) in {"0-3":(0,3,22.43),"3-6":(3,6,39.77),"6-9":(6,9,52.72),"9-15":(9,15,76.33)}.items():
        r("perdida_rendimiento_anegamiento",v,"%","maiz amarillo duro","ciclo","TIAN21","analogo_externo","estimado",
          f"metaanálisis global, ensayos de campo, duración {d} días; reducción media; sin IC transcrito; no hay datos de Piura",0.5,metodo=f"metaanálisis; duración {d} d")
    r("perdida_rendimiento_anegamiento",59.95,"%","algodon","ciclo","TIAN21","analogo_externo","estimado","metaanálisis global, ensayos de campo, promedio de duraciones; reducción media",0.5,metodo="metaanálisis")
    r("perdida_rendimiento_anegamiento",25.32,"%","trigo","ciclo","TIAN21","analogo_externo","estimado","metaanálisis global, ensayos de campo, promedio de duraciones",0.5,metodo="metaanálisis")
    r("tiempo_max_evacuar_encharcamiento",24,"horas","maiz amarillo duro","ciclo","FAO62","bibliografico","estimado","criterio de diseño de drenaje superficial (clima templado húmedo); no es umbral fisiológico medido",0.5)
    r("tiempo_max_evacuar_encharcamiento",24,"horas","papa","ciclo","FAO62","bibliografico","estimado","criterio de diseño de drenaje (clima templado húmedo)",0.5)
    r("tolerancia_encharcamiento","tolera 'un par de días'","texto","cana de azucar (planta)","ciclo","FAO62","bibliografico","estimado","expresión cualitativa de la fuente",0.5)
    r("napa_freatica_profundidad_diseno","","m","algodon","ciclo","FAO62","bibliografico","estimado","diseño de drenaje en riego, cultivos de campo en general (no específico de algodón)",0.5,vmin=0.8,vmax=0.9)
    r("napa_freatica_media_critica",0.85,"m","maiz amarillo duro","ciclo","FAO62","bibliografico","estimado","Martínez Beltrán 1978 citado en FAO-62; se tolera napa temporal a 0.30 m por un día",0.5)
    return rows

# ================= PERENNES
PER = {
 # cultivo: dict con kc(ini,mid,end,nota), dur(ini,dev,mid,late,total,region), root(min,max,p), sal29 tuple|None, clase29, upt
 "banano (año 1)":dict(kc=(0.50,1.10,1.00,""),dur=(120,90,120,60,390,"Mediterranean"),root=(0.5,0.9,0.35),upt=(5.6,1.3,20.3),clase56="MS"),
 "banano (año 2)":dict(kc=(1.00,1.20,1.10,""),dur=(120,60,180,5,365,"Mediterranean"),root=(0.5,0.9,0.35),upt=(5.6,1.3,20.3),clase56="MS"),
 "uva de mesa":dict(kc=(0.30,0.85,0.45,"table grapes"),dur=(20,40,120,60,240,"Low Latitudes"),root=(1.0,2.0,0.35),sal29=(1.5,2.5,4.1,6.7,12),clase29="MS",upt=(3.9,0.6,6.2),b56=9.6),
 "limon":dict(kc=(0.70,0.65,0.70,"citrus sin cobertura, 70 % dosel"),dur=(60,90,120,95,365,"Mediterranean"),root=(1.2,1.5,0.50),clase29="S",upt=(9.0,2.0,11.7)),
 "mango":dict(clase29="S",upt=(6.7,1.7,6.7)),
 "palta":dict(kc=(0.60,0.85,0.75,"sin cobertura"),root=(0.5,1.0,0.70),clase29="S"),
 "cacao":dict(kc=(1.00,1.05,1.05,""),root=(0.7,1.0,0.30),upt=(22.7,10.2,53.3)),
 "cafe":dict(kc=(0.90,0.95,0.95,"suelo desnudo"),root=(0.9,1.5,0.40),upt=(129,27,174)),
 "papaya":dict(clase29="MT",upt=(2.8,0.8,2.2)),
 "maracuya":dict(clase29="S"),
 "pina":dict(kc=(0.50,0.30,0.30,"suelo desnudo"),dur=(60,120,600,10,790,"Hawaii, USA"),root=(0.3,0.6,0.50),clase29="MT",upt=(1.8,0.5,6.2)),
 "naranja (referencia citricos)":dict(sal29=(1.7,2.3,3.3,4.8,8.0),clase29="S",b56=16),
}

# Ciclo de vida de perennes (ronda 2). (valor, min, max, fuente, tipo, confianza, variedad, nota). Solo cifras textuales.
LIFE = {
 "mango": {"anos_a_primera_produccion":[("",3,4,"MIDAGRI_MANGO","regional",0.55,"","MIDAGRI: 'empieza a producir frutos a los 3 o 4 años aproximadamente'; Morton 1987 da 2-3 años (árbol injertado, Florida), coincide en orden de magnitud")],
           "vida_util_productiva":[(30,"","","MIDAGRI_MANGO","regional",0.5,"","MIDAGRI: 'vive 30 años en promedio' (vida del árbol, no necesariamente vida comercial); Morton cita árboles de 100-300 años aún fructificando")]},
 "palta": {"anos_a_primera_produccion":[(2,"","","MIDAGRI_PALTA","regional",0.45,"Hass","MIDAGRI: produce a los 2 años (Hass); rendimiento progresivo 0,5 a 12 t/ha hasta los 10 años; leído en extracto, PDF no descargó"),
                                       (3,"","","MIDAGRI_PALTA","regional",0.45,"Fuerte","MIDAGRI: produce a los 3 años (Fuerte); leído en extracto, PDF no descargó")],
           "vida_util_productiva":[("",25,"","MIDAGRI_PALTA","regional",0.45,"","MIDAGRI: 'vive más de 25 años' (cota inferior, sin máximo)")]},
 "cacao": {"vida_util_productiva":[(20,"","","MIDAGRI_CACAO","regional",0.5,"","MIDAGRI manual cacao: 'vida útil de producción promedio de 20 años'; cacao no es cultivo de la costa de Piura, se mantiene como referencia")]},
 "papaya": {"vida_util_productiva":[("",3,4,"MORTON_PAPAYA","analogo_externo",0.4,"","Morton: produce bien 2 años, luego baja; las plantaciones comerciales se renuevan a los 3-4 años (Hawái/Florida)")]},
 "maracuya": {"anos_a_primera_produccion":[("",1,3,"MORTON_PASSION","analogo_externo",0.4,"amarilla (flavicarpa)","Morton: la planta, sobre todo la amarilla, empieza a producir en 1 a 3 años")],
              "vida_util_productiva":[("",5,6,"MORTON_PASSION","analogo_externo",0.4,"","Morton: la poda de laterales puede extender la vida de la plantación a 5 o 6 años (sin poda, menor; no cuantificado)")]},
 "limon": {"anos_a_primera_produccion":[("",3,6,"MORTON_LIME","analogo_externo",0.4,"sutil (Citrus aurantifolia), planta de semilla","Morton: plantas de semilla fructifican a los 3-6 años y llegan a plena producción a los 8-10 años; injertos no cuantificados")]},
}
def build_perennes():
    rows=[]; r=mk(rows,"PE")
    for c,d in PER.items():
        if "kc" in d:
            ini,mid,end,n=d["kc"]
            for et,v in (("inicial",ini),("media",mid),("final",end)):
                r("kc",v,"adimensional",c,et,"F56T12","bibliografico","estimado",(n+"; " if n else "")+NO_RANGO+"; en frutales 'etapa' = fase del ciclo anual de FAO-56",0.6)
        if "dur" in d:
            *v,reg=d["dur"]
            for et,x in zip(ETAPAS,v):
                r("duracion_etapa_ciclo_anual",x,"días",c,et,"F56T11","analogo_externo","estimado",f"caso FAO-56 {reg}; {NO_RANGO}; no calibrado para Piura",0.4,lugar=reg)
        if "root" in d:
            a,b,p=d["root"]
            r("profundidad_raiz_max","","m",c,"adulto","F56T22","bibliografico","estimado","rango de la tabla",0.6,vmin=a,vmax=b)
            r("fraccion_agotamiento_p",p,"fracción",c,"adulto","F56T22","bibliografico","estimado",NO_RANGO,0.6)
        if "sal29" in d:
            for pct,v in zip((100,90,75,50,0),d["sal29"]):
                r("ece_umbral" if pct==100 else f"ece_rend_{pct}pct",v,"dS/m",c,"adulto","F29T4","bibliografico","estimado",NO_RANGO+"; ensayos Maas-Hoffman EE.UU.",0.6)
        if "b56" in d:
            r("pendiente_salinidad_b",d["b56"],"%/(dS/m)",c,"adulto","F56T23","bibliografico","estimado",NO_RANGO,0.6)
        if "clase29" in d:
            r("clase_tolerancia_salinidad",d["clase29"],"categoría",c,"adulto","F29T5","bibliografico","estimado","FAO-29 Tabla 5; para limón la fila es Citrus limon; maracuyá = passion fruit",0.6)
        elif "clase56" in d:
            r("clase_tolerancia_salinidad",d["clase56"],"categoría",c,"adulto","F56T23","bibliografico","estimado","FAO-56 T23",0.6)
        if "upt" in d:
            for nut,v in zip(("N","P2O5","K2O"),d["upt"]):
                r(f"absorcion_total_{nut}",v,"kg/t producto",c,"ciclo anual","PNB16T29","analogo_externo","estimado",NO_RANGO+"; datos de India (Tandon 2004)",0.4)
        for var,u in (("anos_a_primera_produccion","años"),("vida_util_productiva","años")):
            ents=LIFE.get(c,{}).get(var)
            if not ents:
                r(var,"",u,c,"","","bibliografico","desconocido","sin fuente encontrada (ronda 2: serie MIDAGRI de fichas agroecológicas solo cubre mango y palta); no se rellena",0,fuente="",url="")
                continue
            for val,vmin,vmax,src,tipo,conf,varied,nota in ents:
                r(var,val,u,c,"",src,tipo,"estimado",nota,conf,vmin=vmin,vmax=vmax,variedad=varied,metodo="transcripción de texto publicado")
    # plagas (piura-data, SENASA BPA) para perennes y anuales
    return rows

def pests(rows_an, rows_pe):
    import pandas as pd
    d=pd.read_csv(os.path.join(OUT,"raw/piura-data-clean/plagas_hospedantes_condiciones_v2.csv"))
    ra=mk(rows_an,"AN"); rp=mk(rows_pe,"PE")
    m={"banano":"banano (año 2)","limon":"limon","mango":"mango","uva":"uva de mesa","papaya":"papaya"}
    for x in d.itertuples(index=False):
        local="Piura" in str(x.local_presence_status)
        f=rp if x.crop in m else ra; c=m.get(x.crop,x.crop)
        f("plaga_clave",x.agent_as_source,"taxón",c,"ciclo","","regional" if local else "bibliografico","observado" if local else "estimado",
          f"categoría: {x.category}; presencia: {x.local_presence_status}; relevancia rotación: {x.rotation_or_management_relevance}; reutilizado de piura-data",
          0.6 if local else 0.5, fuente="SENASA (vía piura-data/plagas_hospedantes_condiciones_v2.csv)", url=x.source_url, fecha=str(x.source_date))

def write(rows,name):
    p=os.path.join(OUT,name)
    with open(p,"w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(name,len(rows))

if __name__=="__main__":
    a=build_anuales(); p=build_perennes(); pests(a,p)
    write(a,"fichas_anuales.csv"); write(p,"perennes.csv")
