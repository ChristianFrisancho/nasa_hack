"""Valida todos los CSV de cultivos/: lectura pandas, columnas del contrato (con zona), fuente en cada valor numérico, estado/tipo válidos."""
import glob, os, sys, pandas as pd
C=["variable","valor","valor_min","valor_max","unidad","cultivo","variedad","etapa","zona","lugar","lat","lon","fecha_o_periodo","fuente","url_o_doi","metodo","tipo_evidencia","estado","notas"]
ZV={"alto_piura","medio_piura","bajo_piura","chira","san_lorenzo","sierra_piura","medio_bajo_piura","piura_region",""}
TIPOS={"medicion_local","regional","bibliografico","analogo_externo","prediccion"}; EST={"observado","estimado","desconocido"}
D=os.path.dirname(os.path.abspath(__file__)); bad=0
GEN=("Allen et al. 1998","FAO EcoCrop","Tanji & Kielen","Tanji y Kielen","Ayers","Crop Salt Tolerance","Steduto","Rhoades","Grieve")
RC=["id_hallazgo","severidad","filas_afectadas","accion","justificacion","fuente"]
for f in sorted(glob.glob(os.path.join(D,"respuesta_revision_*.csv"))):
    d=pd.read_csv(f,dtype=str,keep_default_na=False); e=[]
    if list(d.columns)!=RC: e.append(f"columnas: {list(d.columns)}")
    if not d.accion.isin({"corregido","rechazado","pendiente"}).all(): e.append("accion inválida")
    if (d.justificacion=="").any() or (d.fuente=="").any(): e.append("justificación/fuente vacía")
    if d.id_hallazgo.duplicated().any(): e.append("ids duplicados")
    print(("OK  " if not e else "FALLA ")+os.path.basename(f), len(d), "; ".join(e)); bad+=bool(e)
for f in sorted(glob.glob(os.path.join(D,"*.csv"))):
    if os.path.basename(f).startswith("respuesta_revision_"): continue
    d=pd.read_csv(f,dtype=str,keep_default_na=False); e=[]
    if list(d.columns[:19])!=C: e.append(f"columnas: {list(d.columns[:19])}")
    num=lambda s: s.apply(lambda v: v!="" and v.replace(".","",1).replace("-","",1).isdigit())
    hasnum=num(d.valor)|num(d.valor_min)|num(d.valor_max)
    nosrc=d[hasnum&((d.fuente=="")|(d.url_o_doi==""))]
    if len(nosrc): e.append(f"{len(nosrc)} filas numéricas sin fuente/url: {nosrc.id.tolist()[:5] if 'id' in d else ''}")
    if not d.tipo_evidencia.isin(TIPOS).all(): e.append(f"tipo inválido: {set(d.tipo_evidencia)-TIPOS}")
    if not d.estado.isin(EST).all(): e.append(f"estado inválido: {set(d.estado)-EST}")
    des=d[(d.estado=="desconocido")&(d.valor!="")]
    if len(des): e.append(f"{len(des)} filas desconocido con valor")
    sinrango=d[(d.valor_min=="")&(d.valor_max=="")&(d.notas=="")]
    if len(sinrango): e.append(f"{len(sinrango)} filas sin rango y sin notas")
    ana=d[(d.tipo_evidencia=="analogo_externo")&(d.notas.str.len()<20)]
    if len(ana): e.append(f"{len(ana)} análogos sin nota de comparabilidad")
    if "zona" in d and not d.zona.isin(ZV).all(): e.append(f"zona inválida: {set(d.zona)-ZV}")
    if "zonas_aplicables" in d:
        za={z for v in d.zonas_aplicables for z in v.split(";") if v}
        if za-ZV: e.append(f"zonas_aplicables inválidas: {za-ZV}")
        if za&{"piura_region","medio_bajo_piura"}: e.append("zonas_aplicables con piura_region/medio_bajo_piura")
        # [R7] dato NO genérico con zona vacía debe declarar zonas_aplicables. Genérico = tabla de especie sin sitio
        # (FAO-56/29/61/48, EcoCrop, CPIC, ASCE: el 'lugar' es una clase climática de la tabla) o fila sin lugar de tipo
        # bibliografico/analogo_externo. No genérico = cualquier otra fila con lugar concreto, o regional/medicion_local.
        gen=d.fuente.str.startswith(GEN)|((d.lugar=="")&d.tipo_evidencia.isin({"bibliografico","analogo_externo","prediccion"}))
        sinza=d[(d.zona=="")&(d.zonas_aplicables=="")&~gen]
        if len(sinza): e.append(f"{len(sinza)} filas no genéricas con zona vacía y sin zonas_aplicables: {sinza.id.tolist()[:6] if 'id' in d else ''}")
    if "id" in d and d.id.duplicated().any(): e.append("ids duplicados")
    if "confianza" in d:
        cf=pd.to_numeric(d.confianza,errors="coerce")
        if cf.isna().any() or (cf>1).any(): e.append("confianza fuera de 0-1")
    print(("OK  " if not e else "FALLA ")+os.path.basename(f), len(d), "; ".join(e)); bad+=bool(e)
for f in sorted(glob.glob(os.path.join(D,"para_motor","*.csv"))):
    d=pd.read_csv(f,dtype=str,keep_default_na=False); e=[]
    if "zona" not in d: e.append("falta columna zona")
    elif not d.zona.isin(ZV).all(): e.append(f"zona inválida: {set(d.zona)-ZV}")
    print(("OK  " if not e else "FALLA ")+"para_motor/"+os.path.basename(f), len(d), "; ".join(e)); bad+=bool(e)
sys.exit(bad)
