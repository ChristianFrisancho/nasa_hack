"""CLI: python -m motor_rotacion consulta.json [--formato texto|json] [--secuencias 2|3] [--integrar archivo.csv ...]
[--estricto] [--registro registro.tsv]"""
import argparse
import json
import sys

from .catalogo import Catalogo
from .entradas import Consulta
from .motor import comparar_secuencias, escenarios_ecw, evaluar, evaluar_escenarios
from .reporte import (escenarios_a_dict, escenarios_a_texto, escenarios_clima_a_dict, escenarios_clima_a_texto,
                      secuencia_a_dict, secuencias_a_texto)


def main(argv=None):
    p = argparse.ArgumentParser(prog="motor_rotacion", description="Motor de rotación de cultivos v1 (Piura)")
    p.add_argument("consulta", help="archivo JSON con la consulta")
    p.add_argument("--formato", choices=("texto", "json"), default="texto")
    p.add_argument("--secuencias", type=int, choices=(2, 3), help="comparar secuencias de 2 o 3 anuales")
    p.add_argument("--integrar", nargs="*", default=[], help="CSV con formato CONTRATO.md para integrar")
    p.add_argument("--estricto", action="store_true", help="rechaza CSV sin la columna zona de CONTRATO.md")
    p.add_argument("--registro", help="escribe el registro de integración (aceptado/rechazado/ignorado) en este TSV")
    a = p.parse_args(argv)
    with open(a.consulta, encoding="utf-8") as f:
        consulta = Consulta.desde_dict(json.load(f))
    cat = Catalogo()
    for ruta in a.integrar:
        print(f"integradas {cat.integrar_csv_contrato(ruta, estricto=a.estricto)} filas de {ruta}", file=sys.stderr)
    if a.registro:
        cat.escribir_registro(a.registro)
    r = evaluar(consulta, cat)
    secs = comparar_secuencias(consulta, a.secuencias, catalogo=cat) if a.secuencias else None
    escs = escenarios_ecw(consulta, cat, a.secuencias) if a.secuencias else []
    clima_escs = evaluar_escenarios(consulta, cat)  # la misma parcela en los 3 escenarios climáticos ICEN
    if a.formato == "json":
        d = r.a_dict()
        d["escenarios_climaticos"] = escenarios_clima_a_dict(clima_escs)
        if secs is not None:
            d["secuencias"] = [secuencia_a_dict(s) for s in secs]
        if escs:
            d["escenarios_agua"] = escenarios_a_dict(escs)
        json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
        print()
    else:
        print(r.a_texto())
        print()
        print(escenarios_clima_a_texto(clima_escs))
        if secs is not None:
            print()
            print(secuencias_a_texto(secs))
            if escs and not any(s.viable for s in secs):
                print("   Ninguna secuencia es viable con la ECw desconocida: vea ESCENARIOS DE AGUA abajo. "
                      "Dato que falta: CE del agua de riego.")
        if escs:
            print()
            print(escenarios_a_texto(escs, secs))


if __name__ == "__main__":
    main()
