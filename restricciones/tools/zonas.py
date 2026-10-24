"""Zonas del CONTRATO (columna `zona`) y reglas para asignarlas. Lo usan los generadores de insumos.
Una fila sin zona lleva en notas 'Zona no aplica: ...'. limpiar.py lo exige. Medio y Bajo juntos = medio_bajo_piura."""
import re
ZONAS = ["alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura", "medio_bajo_piura", "piura_region"]
MEDIO_BAJO = "medio_bajo_piura"  # CONTRATO 24-oct 06:41: la fuente reporta Medio y Bajo Piura juntos
NO_APLICA = "Zona no aplica: lugar fuera de Piura."
# Distritos (DRAP, provincia Piura y Sechura). Igual que modelo/scripts/validacion.py.
BAJO = {"CATACAOS", "CURA MORI", "EL TALLAN", "LA ARENA", "LA UNION"}
MEDIO = {"PIURA", "CASTILLA", "VEINTISEIS DE OCTUBRE"}
SANL = {"TAMBO GRANDE", "LAS LOMAS"}
SIERRA = {"AYABACA", "HUANCABAMBA"}
MORR_SIERRA = {"CHALACO", "SANTO DOMINGO", "SANTA CATALINA DE MOSSA", "YAMANGO"}

def zona_distrito(prov, dist):
    if prov in SIERRA or (prov == "MORROPON" and dist in MORR_SIERRA): return "sierra_piura"
    if prov == "MORROPON": return "alto_piura"
    if prov in ("SULLANA", "PAITA"): return "chira"
    if prov == "SECHURA": return "bajo_piura"
    if prov == "PIURA" and dist in SANL: return "san_lorenzo"
    if prov == "PIURA" and dist in BAJO: return "bajo_piura"
    if prov == "PIURA" and dist in MEDIO: return "medio_piura"
    raise ValueError(f"distrito sin zona: {prov}/{dist}")

FUERA = re.compile(r"La Libertad|Jequetepeque|Virú|San Pedro de Lloc|\bIca\b|\bLima\b|Arequipa|Tacna|Chile|\bPerú\b|Costa peruana|Región natural costa|San Martín|Lambayeque")

def zona_lugar(lugar):
    """(zona, nota) para un lugar escrito a mano. Si no se reconoce, error: el generador debe dar zona explícita."""
    l = lugar
    if FUERA.search(l) and "Piura" not in l: return "", NO_APLICA
    if "valles con arroz" in l: return "piura_region", ""
    if "Medio y Bajo" in l or l.startswith("CDR Piura"): return MEDIO_BAJO, ""
    for k, z in (("CDR Chira", "chira"), ("CDR Chulucanas", "alto_piura"), ("CDR San Lorenzo", "san_lorenzo"), ("CDR Ayabaca", "sierra_piura"),
                 ("CDR Huancabamba", "sierra_piura"), ("CDR Huarmaca", "sierra_piura")):
        if l.startswith(k): return z, ""
    if any(k in l for k in ("Chira-Piura", "promedio", "región", "departamento", "valles", "Poechos", "zona productora", "eriazas", "Olmos-Sechura")):
        return "piura_region", ""
    for k, z in (("Alto Piura", "alto_piura"), ("San Lorenzo", "san_lorenzo"), ("Bajo Piura", "bajo_piura"), ("Sechura", "bajo_piura"),
                 ("Tablazo", "bajo_piura"), ("Chira", "chira")):
        if k in l: return z, ""
    raise ValueError(f"lugar sin zona reconocible: {lugar}")
