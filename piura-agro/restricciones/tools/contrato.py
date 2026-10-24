"""Reglas del CONTRATO (versión 06:41 del 24-oct) que los generadores de insumos aplican antes de escribir.
limpiar.py no corrige nada: sólo valida. Este módulo deja cada fila en la forma que limpiar.py exige.
  - Dotaciones o módulos de riego (no son entregas medidas): estado 'estimado', metodo 'dotacion_asignada'.
  - CE de suelo sin extracto declarado: estado 'observado', metodo 'ce_extracto_no_declarado'.
El texto de método de la fuente no se pierde: pasa a notas como 'Método de la fuente: ...'."""
import re
DOTACION = re.compile(r"^(dotacion|modulo_riego|volumen_asignado|volumen_licencia)")
CE_SUELO = re.compile(r"^(ce_suelo|ece)", re.I)
EXTRACTO = re.compile(r"pasta saturada|extracto de saturaci|1:1|1:2[.,]5|1:5", re.I)
NO_DECLARA = re.compile(r"no declar|sin declarar|extracto desconocido", re.I)
def declara_extracto(metodo):
    """True si el método nombra el extracto; 'la tesis no declara el extracto (pasta saturada u otro)' no cuenta."""
    return bool(EXTRACTO.search(metodo)) and not NO_DECLARA.search(metodo)
M_DOT, M_CE = "dotacion_asignada", "ce_extracto_no_declarado"

def _mueve_metodo(r, nuevo):
    if r["metodo"] != nuevo:
        r["notas"] = (r["notas"] + f" Método de la fuente: {r['metodo'].rstrip('.')}.").strip()
        r["metodo"] = nuevo

def normalizar(r):
    if DOTACION.match(r["variable"]):
        _mueve_metodo(r, M_DOT)
        if r["estado"] != "desconocido": r["estado"] = "estimado"
    if CE_SUELO.match(r["variable"]) and not declara_extracto(r["metodo"]):
        _mueve_metodo(r, M_CE)
    return r
