"""Pruebas de comportamiento observable del motor (v0 + ronda 2)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from motor_rotacion import Consulta, EstadoSuelo, comparar_secuencias, evaluar
from motor_rotacion.cifra import Cifra, operar
from motor_rotacion.motor import catalogo_por_defecto, evaluar_cultivo

BASE = Path(__file__).resolve().parents[1]
SENSIBLES = ("frijol grano", "frijol verde", "cebolla", "piquillo", "maiz amarillo duro", "papa")


def consulta(**cambios):
    d = {
        "parcela": {"punto": [-5.33, -80.68], "area_ha": 1.0, "provincia": "Piura"},
        "suelo": {"ece_ds_m": 1.0, "ph": 7.2, "profundidad_cm": 150, "drenaje": "bueno", "pendiente_pct": 1},
        "agua": {"m3_por_mes": 20000, "ecw_ds_m": 0.5, "eficiencia": [0.5, 0.7]},
        "presupuesto_pen": 50000, "cultivo_anterior": "arroz", "escenario": "sin_el_nino", "mes_siembra": 6,
        "horizonte_meses": 8,
    }
    for k, v in cambios.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            d[k] = {**d[k], **v}
        else:
            d[k] = v
    return Consulta.desde_dict(d)


def por_cultivo(r):
    return {e.cultivo: e for e in r.evaluaciones}


def test_rotacion_acepta_familia_botanica_para_anterior_fuera_del_catalogo():
    q_sin_familia = consulta(cultivo_anterior="maiz criollo", familia_anterior=None)
    q_con_familia = consulta(cultivo_anterior="maiz criollo", familia_anterior="Poaceae")
    assert q_con_familia.familia_anterior == "Poaceae"
    assert evaluar(q_sin_familia).ranking != evaluar(q_con_familia).ranking


def test_condicion_suelo_modifica_desempate_sin_ocultar_filtros_criticos():
    base = consulta(cultivo_anterior="mango", familia_anterior="Anacardiaceae",
                    suelo={"ece_ds_m": None}, agua={"m3_por_mes": 20000})
    normal = evaluar(base).ranking
    salino = evaluar(consulta(cultivo_anterior="mango", familia_anterior="Anacardiaceae",
                              suelo={"ece_ds_m": None}, agua={"m3_por_mes": 20000}, condicion_suelo="salino")).ranking
    arido = evaluar(consulta(cultivo_anterior="mango", familia_anterior="Anacardiaceae",
                             suelo={"ece_ds_m": None}, agua={"m3_por_mes": 20000}, condicion_suelo="arido")).ranking
    assert salino != normal
    assert arido != normal
    # La ECe sigue siendo no evaluable: el desempate no convierte una medición ausente en un pase.
    assert any(v.filtro == "salinidad" and v.resultado == "no_evaluable"
               for v in por_cultivo(evaluar(consulta(cultivo_anterior="mango", familia_anterior="Anacardiaceae",
                                                    suelo={"ece_ds_m": None}, agua={"m3_por_mes": 20000},
                                                    condicion_suelo="salino")))['arroz'].veredictos)


def test_salinidad_alta_descarta_cultivos_sensibles():
    # FAO-29 (R4A026): el umbral se aplica como exacto solo con ECe medida y napa ≥ 2 m; aquí la napa está medida a 2.5 m
    r = evaluar(consulta(suelo={"ece_ds_m": [9.0, 10.0], "napa_m": 2.5}))
    ev = por_cultivo(r)
    for c in SENSIBLES:
        assert ev[c].decision == "descartado", c
        assert any(v.filtro == "salinidad" and v.resultado == "descarta" for v in ev[c].veredictos), c
    # el algodón (ECe 100 % = 7.7 dS/m) tolera ese nivel: no lo descarta la salinidad
    sal_algodon = next(v for v in ev["algodon"].veredictos if v.filtro == "salinidad")
    assert sal_algodon.resultado in ("pasa", "advierte")


def test_salinidad_baja_no_descarta_por_sal():
    ev = por_cultivo(evaluar(consulta()))
    for c in SENSIBLES:
        sal = next(v for v in ev[c].veredictos if v.filtro == "salinidad")
        assert sal.resultado != "descarta", c


def test_sin_datos_de_suelo_devuelve_desconocido():
    r = evaluar(consulta(suelo={"ece_ds_m": None, "ph": None, "profundidad_cm": None, "drenaje": None,
                                "pendiente_pct": None}, agua={"ecw_ds_m": None}))
    d = r.a_dict()
    assert r.consulta.suelo.pendiente_pct.tipo_evidencia == "prediccion"
    assert "VALOR DE ZONA" in r.consulta.suelo.pendiente_pct.notas
    for e in r.evaluaciones:
        res = {v.filtro: v.resultado for v in e.veredictos}
        assert res["drenaje"] == res["pH"] == res["profundidad"] == "no_evaluable"
        assert res["pendiente"] != "no_evaluable"
        if e.cultivo in SENSIBLES:
            assert res["salinidad"] == "no_evaluable"
        # la ECe tras cosecha no se inventa
        assert e.estado_tras_cosecha.ece.estado == "desconocido"
        assert e.estado_tras_cosecha.ece.valor is None
    assert any("ECe del suelo" in f for f in r.faltantes_globales)
    texto = json.dumps(d, ensure_ascii=False)
    assert '"estado": "desconocido"' in texto


def test_cifra_desconocida_contamina_el_calculo():
    a = Cifra.rango(1, 2, "t/ha", "x", "regional", "observado")
    b = Cifra.desconocido("PEN/kg", "precio")
    c = operar("*", a, b, "PEN/ha", "ingreso", "a×b")
    assert c.estado == "desconocido" and c.valor is None and "precio" in c.notas
    with pytest.raises(ValueError):
        Cifra(1.0, None, None, "x", "y", "prediccion", "desconocido")


def test_reporta_cuando_no_hay_cultivo_viable():
    r = evaluar(consulta(suelo={"ece_ds_m": [14, 18], "drenaje": "pobre", "profundidad_cm": 40},
                         agua={"m3_por_mes": 300, "ecw_ds_m": 4.5}, presupuesto_pen=2000, horizonte_meses=4))
    assert r.ranking == []
    assert r.mensaje.startswith("Ningún cultivo anual evaluado es viable")
    assert "Restricciones a resolver" in r.mensaje
    assert "Ningún cultivo anual evaluado es viable" in r.a_texto()


def test_secuencia_actualiza_estado_del_suelo():
    c = consulta(suelo={"ece_ds_m": 1.0}, agua={"ecw_ds_m": 2.0}, candidatos=["maiz amarillo duro", "frijol grano",
                                                                          "algodon", "cebolla"],
                 fertilizacion_prevista={"N": 150})
    cat = catalogo_por_defecto()
    inicial = EstadoSuelo.desde_consulta(c)
    ev = evaluar_cultivo(cat.fichas["maiz amarillo duro"], c, inicial, evaluar(c, cat).clima, cat, "arroz")
    post = ev.estado_tras_cosecha
    assert post.historial == ("maiz amarillo duro",)
    # agua de ECw 2.0 lleva la ECe hacia 1.5·ECw = 3.0
    assert post.ece.hi == pytest.approx(3.0) and post.ece.lo == pytest.approx(1.0)
    # P y K solo salen (sin aporte): balance negativo; N con aporte de 150
    assert post.balance["P2O5"].hi < 0 and post.balance["K2O"].hi < 0
    assert post.agua_neta_m3_ha.lo > 0

    secs = comparar_secuencias(c, largo=2, catalogo=cat, horizonte_meses=18)
    assert secs, "debe comparar al menos una secuencia"
    s = next(s for s in secs if len(s.pasos) == 2)
    assert s.estado_final.historial == s.cultivos
    assert s.estado_final.ece.hi >= 3.0 - 1e-9
    # el segundo paso se evalúa con el primer cultivo como anterior y siembra después de la cosecha
    assert s.pasos[1].mes_siembra != s.pasos[0].mes_siembra
    if any(cat.fichas[x].leguminosa for x in s.cultivos):
        assert s.estado_final.balance["N"].estado == "desconocido"


def test_cada_cifra_lleva_fuente_y_tipo_evidencia():
    d = evaluar(consulta()).a_dict()
    tipos = {"medicion_local", "regional", "bibliografico", "analogo_externo", "prediccion"}

    def recorrer(x):
        if isinstance(x, dict):
            if {"valor", "unidad", "tipo_evidencia", "estado"} <= x.keys():
                assert x["tipo_evidencia"] in tipos
                assert x["fuente"]
                if x["estado"] == "desconocido":
                    assert x["valor"] is None
            for v in x.values():
                recorrer(v)
        elif isinstance(x, list):
            for v in x:
                recorrer(v)
    recorrer(d)


def test_cli_texto_y_json():
    for formato in ("texto", "json"):
        p = subprocess.run([sys.executable, "-m", "motor_rotacion", str(BASE / "ejemplos/bajo_piura_tras_arroz.json"),
                            "--formato", formato], cwd=BASE, capture_output=True, text=True, check=True)
        assert "zona" in p.stdout.lower()
        if formato == "json":
            assert json.loads(p.stdout)["zona_clima"]["zona"] == "Bajo Piura"


def test_integrar_csv_contrato_reemplaza_dato_desconocido():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()  # catálogo propio: no contamina el compartido de las otras pruebas
    assert not por_cultivo(evaluar(consulta(), cat))["caupi"].costo_ha.conocido
    # fila ficticia pero completa según CONTRATO.md (url en dominio .invalid reservado); vive en tests/, no en ejemplos/
    assert cat.integrar_csv_contrato(BASE / "tests/datos/integracion_ficticia.csv") == 1
    costo = por_cultivo(evaluar(consulta(), cat))["caupi"].costo_ha
    assert (costo.lo, costo.hi, costo.tipo_evidencia) == (1800, 2600, "regional")


# ------------------------------------------------------------------------------------------- ronda 2
from motor_rotacion.filtros import ADVIERTE, DESCARTA, PASA, APTO, MARGINAL, NO_APTO, profundidad_efectiva  # noqa: E402
from motor_rotacion.motor import Secuencia, clave_secuencia, clave_secuencia_v0, ordenar_secuencias  # noqa: E402
from motor_rotacion.estado_suelo import EstadoSuelo  # noqa: E402
from motor_rotacion.incertidumbre import muestras_uniformes, resumen  # noqa: E402


def veredicto(ev, filtro):
    return next(v for v in ev.veredictos if v.filtro == filtro)


def test_integrar_rechaza_fila_sin_url_y_lo_anota():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    assert cat.integrar_csv_contrato(BASE / "tests/datos/integracion_sin_fuente.csv") == 0
    assert not por_cultivo(evaluar(consulta(), cat))["caupi"].costo_ha.conocido
    reg = [r for r in cat.registro if r.archivo == "integracion_sin_fuente.csv"]
    assert reg and reg[-1].estado == "rechazada" and "url" in reg[-1].motivo


def test_integrar_motor_integracion_de_agronomia():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    assert cat.integrar_csv_contrato(BASE / "datos_agronomia/motor_integracion.csv") == 2
    assert cat.integrar_csv_contrato(BASE / "ejemplos/integracion_ejemplo.csv") == 2  # mismo dato con columna zona


def test_napa_desconocida_avisa_y_no_descarta_por_sal():
    ev = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": [9.0, 10.0]})))
    sal = veredicto(ev["frijol grano"], "salinidad")
    assert sal.resultado == ADVIERTE and "napa" in sal.motivo
    assert sal.grave  # probable no apto: va al final del orden
    assert ev["frijol grano"].decision == "aceptado"


def test_napa_somera_amplia_incertidumbre_del_rendimiento():
    exacto = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": 2.0, "napa_m": 3.0})))["frijol grano"]
    somera = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": 2.0, "napa_m": [0.8, 1.2]})))["frijol grano"]
    r_ex = veredicto(exacto, "salinidad").cifras["fraccion_rendimiento_salinidad"]
    r_so = veredicto(somera, "salinidad").cifras["fraccion_rendimiento_salinidad"]
    assert veredicto(somera, "salinidad").resultado == ADVIERTE
    assert r_so.lo < r_ex.lo and r_so.hi == pytest.approx(r_ex.hi)


def test_ece_estimada_desde_ecw_solo_con_napa_profunda():
    sin = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": None}, agua={"ecw_ds_m": 2.0})))["cebolla"]
    con = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": None, "napa_m": 2.5}, agua={"ecw_ds_m": 2.0})))["cebolla"]
    assert veredicto(sin, "salinidad").resultado == "no_evaluable"
    assert veredicto(con, "salinidad").resultado != "no_evaluable"


def test_rampa_ph_apto_marginal_no_apto():
    def clase(ph):
        ev = por_cultivo(evaluar(consulta(suelo={"ph": ph})))["arveja"]
        return veredicto(ev, "pH")
    assert clase(6.5).resultado == PASA and APTO in clase(6.5).motivo
    marg = clase(7.9)  # arveja EcoCrop: óptimo 5.5-7.0, absoluto 4.5-8.3 -> aptitud 0.31: penalización suave
    assert marg.resultado == PASA and "marginal" in marg.motivo
    borde = clase([7.8, 8.6])  # puede llegar al límite absoluto: avisa
    assert borde.resultado == ADVIERTE and "marginal" in borde.motivo
    malo = clase(9.5)
    assert malo.resultado == ADVIERTE and "no apto" in malo.motivo  # EcoCrop global: avisa, no descarta
    a = marg.cifras["aptitud_pH"]
    assert 0 < a.lo <= a.hi < 1


def test_rampa_profundidad_y_profundidad_efectiva_con_napa():
    # suelo físico profundo pero napa a 0.6-0.8 m: la profundidad útil es 0.1-0.5 m
    est = EstadoSuelo.desde_consulta(consulta(suelo={"profundidad_cm": 150, "napa_m": [0.6, 0.8]}))
    ef, _, _ = profundidad_efectiva(est)
    assert (ef.lo, ef.hi) == pytest.approx((0.1, 0.5))
    hondo = por_cultivo(evaluar(consulta(suelo={"profundidad_cm": 150, "napa_m": 4.0})))
    somero = por_cultivo(evaluar(consulta(suelo={"profundidad_cm": 150, "napa_m": [0.6, 0.8]})))
    assert veredicto(hondo["algodon"], "profundidad").resultado == PASA
    assert veredicto(somero["algodon"], "profundidad").resultado in (ADVIERTE, DESCARTA)
    muy = por_cultivo(evaluar(consulta(suelo={"profundidad_cm": 15})))
    assert veredicto(muy["algodon"], "profundidad").resultado == DESCARTA


def _sec(nombre, lo, hi):
    est = EstadoSuelo.desde_consulta(consulta())
    m = Cifra.rango(lo, hi, "PEN/ha", "prueba", "prediccion", "estimado", variable="margen")
    agua = Cifra.rango(8000, 9000, "m3/ha", "prueba", "prediccion", "estimado")
    mc = resumen(muestras_uniformes(lo, hi, nombre))
    return Secuencia((nombre,), True, [], est, Cifra(6.0, None, None, "meses", "prueba", "prediccion", "estimado"),
                     "si", m, agua, 0, margen_mc=mc)


def test_orden_robusto_no_premia_rangos_anchos():
    ancho = _sec("arveja→cebolla", -11026, 71201)  # el caso de v0
    estrecho = _sec("estrecha", 5000, 9000)
    assert ancho.margen_mc["prob_negativo"] > 0.1
    assert ordenar_secuencias([ancho, estrecho])[0] is estrecho
    # con el orden viejo (punto medio) el rango ancho quedaba primero: este test falla con v0
    assert sorted([ancho, estrecho], key=clave_secuencia_v0)[0] is ancho
    assert clave_secuencia(estrecho) < clave_secuencia(ancho)


def test_orden_desempata_por_agua():
    a, b = _sec("a", 5000, 9000), _sec("a", 5000, 9000)
    b.agua_neta_total_m3_ha = Cifra.rango(4000, 5000, "m3/ha", "prueba", "prediccion", "estimado")
    assert ordenar_secuencias([a, b])[0] is b


def test_calendario_observado_avisa_fuera_de_ventana_sin_descartar():
    # caupí en Bajo Piura: siembra observada mar; ago-set (DRAP 2016-2024)
    fuera = por_cultivo(evaluar(consulta(parcela={"punto": [-5.33, -80.68], "area_ha": 1.0, "provincia": "Piura",
                                                  "zona": "bajo_piura"}, mes_siembra=6)))["caupi"]
    dentro = por_cultivo(evaluar(consulta(parcela={"punto": [-5.33, -80.68], "area_ha": 1.0, "provincia": "Piura",
                                                   "zona": "bajo_piura"}, mes_siembra=8)))["caupi"]
    vf, vd = veredicto(fuera, "calendario"), veredicto(dentro, "calendario")
    assert vf.resultado == ADVIERTE and "FUERA de las ventanas observadas" in vf.motivo and "no es un descarte" in vf.motivo
    assert "dentro de lo observado" in vd.motivo and "no recomendación" in vd.motivo
    assert "DRAP" in vf.fuente


def test_reglas_de_agronomia_cargadas_y_aplicadas():
    ev = por_cultivo(evaluar(consulta(parcela={"punto": [-5.33, -80.68], "area_ha": 1.0, "provincia": "Piura",
                                               "zona": "bajo_piura"}, cultivo_anterior="algodon")))
    normas = veredicto(ev["algodon"], "normas")
    assert normas.resultado == ADVIERTE
    for rid in ("R4R004", "R4R006", "R4R005", "R4S001"):
        assert f"[{rid}]" in normas.motivo, rid


def test_zona_invalida_se_rechaza():
    with pytest.raises(ValueError):
        consulta(parcela={"punto": [-5.33, -80.68], "area_ha": 1.0, "zona": "lima"})


# ------------------------------------------------------------------- CONTRATO.md (zona agregada, métodos especiales)
CAB = ("variable,valor,valor_min,valor_max,unidad,cultivo,variedad,etapa,zona,lugar,lat,lon,fecha_o_periodo,fuente,"
       "url_o_doi,metodo,tipo_evidencia,estado,notas,fuente_primaria,subzona\n")


def _csv(nombre, filas):
    d = BASE / "tests" / "datos"
    p = d / nombre
    p.write_text(CAB + "".join(f + "\n" for f in filas), encoding="utf-8")
    return p


def test_contrato_zona_medio_bajo_piura_y_columnas_opcionales():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    p = _csv("contrato_mbp.csv", [
        "costo_produccion_ha,,1800,2600,PEN/ha,caupi,,,medio_bajo_piura,Medio y Bajo Piura,,,2026,FICTICIO prueba,"
        "https://example.invalid/mbp,,regional,estimado,fila de prueba,FICTICIO fuente citada,Sector Cumbibira"])
    assert cat.integrar_csv_contrato(p) == 1
    for zona in ("bajo_piura", "medio_piura"):
        assert cat.ficha("caupi", zona).costo.lo == 1800, zona
    assert not cat.ficha("caupi", "chira").costo  # no se extiende a otras zonas
    c = cat.ficha("caupi", "bajo_piura").costo
    assert "FICTICIO fuente citada" in c.fuente and "subzona=Sector Cumbibira" in c.notas


def test_contrato_unidad_fuera_de_lista_y_dotacion_asignada():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    p = _csv("contrato_unidades.csv", [
        "costo_produccion_ha,,1800,2600,soles,caupi,,,bajo_piura,x,,,2026,FICTICIO,https://example.invalid/u,,regional,estimado,x,,",
        "dotacion_agua,,9000,12000,m3/ha/año,todos,,,bajo_piura,x,,,2026,FICTICIO,https://example.invalid/d,"
        "dotacion_asignada,regional,observado,x,,",
        "dotacion_agua,,9000,12000,m3/ha/año,todos,,,bajo_piura,x,,,2026,FICTICIO,https://example.invalid/d,"
        "dotacion_asignada,regional,estimado,x,,"])
    assert cat.integrar_csv_contrato(p) == 0
    reg = {r.fila: r for r in cat.registro if r.archivo == "contrato_unidades.csv"}
    assert reg["línea 2"].estado == "rechazada" and "unidad" in reg["línea 2"].motivo
    assert reg["línea 3"].estado == "rechazada" and "dotacion_asignada" in reg["línea 3"].motivo
    assert reg["línea 4"].estado != "rechazada"  # cumple; el motor no modela dotaciones del catálogo


def test_contrato_ce_extracto_no_declarado():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    p = _csv("contrato_ce.csv", [
        "ce_suelo,,3.44,8.2,dS/m,todos,,,bajo_piura,Tablazo Sur,,,2024,Mendoza Flores 2025,"
        "https://hdl.handle.net/20.500.12692/170594,ce_extracto_no_declarado,medicion_local,observado,x,,Tablazo Sur",
        "ce_suelo,,3.44,8.2,dS/m,todos,,,bajo_piura,Tablazo Sur,,,2024,Mendoza Flores 2025,"
        "https://hdl.handle.net/20.500.12692/170594,ce_extracto_no_declarado,medicion_local,estimado,x,,"])
    cat.integrar_csv_contrato(p)
    reg = {r.fila: r for r in cat.registro if r.archivo == "contrato_ce.csv"}
    assert reg["línea 2"].estado == "ignorada" and "pasta saturada" in reg["línea 2"].motivo
    assert reg["línea 3"].estado == "rechazada"  # el contrato exige estado observado


def test_ce_extracto_no_declarado_avisa_y_amplia_incertidumbre():
    napa = {"napa_m": 3.0}
    pasta = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": [3.44, 8.2], **napa})))
    nd = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": [3.44, 8.2], "ce_metodo": "ce_extracto_no_declarado", **napa})))
    for c in ("arveja", "caupi"):
        sp, sn = veredicto(pasta[c], "salinidad"), veredicto(nd[c], "salinidad")
        assert sn.resultado == ADVIERTE and "extracto no declarado" in sn.motivo
        assert sn.cifras["fraccion_rendimiento_salinidad"].lo <= sp.cifras["fraccion_rendimiento_salinidad"].lo
    # con napa medida y ECe de pasta saturada ≥ ECe50, frijol grano se descarta; con extracto no declarado solo avisa
    pasta = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": [5.0, 8.2], **napa})))
    nd = por_cultivo(evaluar(consulta(suelo={"ece_ds_m": [5.0, 8.2], "ce_metodo": "ce_extracto_no_declarado", **napa})))
    assert pasta["frijol grano"].decision == "descartado"
    assert nd["frijol grano"].decision == "aceptado" and veredicto(nd["frijol grano"], "salinidad").grave
    assert any("método del extracto" in f for f in veredicto(nd["frijol grano"], "salinidad").faltantes)


def test_ejemplo_tablazo_sur():
    r = evaluar(Consulta.desde_dict(json.loads((BASE / "ejemplos/tablazo_sur_ce_medida.json").read_text())))
    sal = [v for e in r.evaluaciones for v in e.veredictos if v.filtro == "salinidad" and v.resultado != "no_evaluable"]
    assert sal and all("extracto no declarado" in v.motivo and "PSI" in v.motivo for v in sal)
    assert all(v.resultado != "descarta" for v in sal)


def test_ranking_pone_detras_la_perdida_casi_segura():
    for ej in ("tablazo_sur_ce_medida.json", "bajo_piura_tras_arroz.json"):
        r = evaluar(Consulta.desde_dict(json.loads((BASE / "ejemplos" / ej).read_text())))
        ev = {e.cultivo: e for e in r.evaluaciones}
        pierde = [bool(ev[c].margen_mc) and ev[c].margen_mc["p90"] < 0 for c in r.ranking
                  if ev[c].n_graves == 0]
        assert pierde == sorted(pierde), ej  # ningún 'pierde' antes de uno que puede ganar


# ------------------------------------------------------------------------------------------- ronda 3
from motor_rotacion.motor import ESCENARIOS_ECW, escenarios_ecw  # noqa: E402
from motor_rotacion.reporte import escenarios_a_dict, escenarios_a_texto  # noqa: E402


R5 = BASE / "datos_repo/evidencia_integrar_r5.csv"


def _cat_r5():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    cat.integrar_csv_contrato(R5)
    return cat


def test_ecw_desconocida_corre_tres_escenarios_etiquetados():
    # napa medida a 3 m: el filtro de salinidad sí usa 1,5·ECw, así que el escenario puede cambiar el orden
    c = consulta(agua={"ecw_ds_m": None}, suelo={"napa_m": 3.0})
    cat = catalogo_por_defecto()
    base = comparar_secuencias(c, 2, catalogo=cat)
    assert not base[0].estado_final.ece.conocido  # sin ECw la ECe proyectada tras la cosecha es desconocida
    escs = escenarios_ecw(c, cat, 2)
    assert [e.ecw for e in escs] == list(ESCENARIOS_ECW) == [0.5, 1.5, 3.0]
    for e in escs:
        ecw = e.resultado.consulta.agua.ecw
        assert "ESCENARIO" in e.etiqueta and "no es dato" in ecw.fuente and "falta la CE del agua" in ecw.notas
    d = escenarios_a_dict(escs)
    assert all(x["es_dato"] is False and "ECw" in x["dato_que_falta"] for x in d)
    bueno, salino = escs[0], escs[-1]
    assert any(s.viable for s in bueno.secuencias) and bueno.secuencias[0].estado_final.ece.conocido
    # el orden depende del agua: con ECw 3 salen del orden los sensibles a sal (desde la ronda 4 la regla térmica ya
    # manda al final a cebolla y frijol grano en junio, así que el cambio se ve en la cola y no en los 3 primeros)
    assert bueno.resultado.ranking != salino.resultado.ranking
    assert set(salino.resultado.ranking) < set(bueno.resultado.ranking)
    assert sum(s.viable for s in salino.secuencias) < sum(s.viable for s in bueno.secuencias)
    assert "frijol grano" in bueno.resultado.ranking and "frijol grano" not in salino.resultado.ranking
    txt = escenarios_a_texto(escs, base)
    assert "DATO QUE FALTA" in txt and "ESCENARIO ECw 3 dS/m" in txt


def test_ecw_conocida_no_genera_escenarios():
    assert escenarios_ecw(consulta(), catalogo_por_defecto(), 2) == []


def test_ecw_de_zona_no_pisa_la_de_la_parcela():
    # ronda 5: la ECw de zona de Chira pasó de la tesis de río (0.373–1.167) al reservorio (ver test de abajo)
    cat = _cat_r5()
    c_sin = consulta(parcela={"punto": [-4.9, -80.7], "area_ha": 1.0, "zona": "chira"}, agua={"ecw_ds_m": None})
    assert len(escenarios_ecw(c_sin, cat, 2)) == 3  # el valor de zona no es dato de la parcela: hay escenarios
    r2 = evaluar(consulta(parcela={"punto": [-4.9, -80.7], "area_ha": 1.0, "zona": "chira"}), cat)
    assert r2.consulta.agua.ecw.valor == 0.5  # la de la parcela


def test_pendiente_de_zona_es_prediccion_con_rango():
    cat = _cat_r5()
    c = Consulta.desde_dict(json.loads((BASE / "ejemplos/tablazo_sur_ce_medida.json").read_text()))
    p = evaluar(c, cat).consulta.suelo.pendiente_pct
    assert p.tipo_evidencia == "prediccion" and p.lo == 0.0 and p.hi == 2.6 and "VALOR DE ZONA" in p.notas


def test_catalogo_predeterminado_carga_pendiente_regional_sin_marcarla_como_medida():
    cat = catalogo_por_defecto()
    c = consulta(suelo={"pendiente_pct": None})
    resultado = evaluar(c, cat)
    pendiente = resultado.consulta.suelo.pendiente_pct
    assert pendiente is not None and pendiente.tipo_evidencia == "prediccion"
    assert pendiente.lo == 0.0 and pendiente.hi == 2.6
    assert "VALOR DE ZONA" in pendiente.notas and "no de su parcela" in pendiente.notas
    veredicto = next(v for v in por_cultivo(resultado)["caupi"].veredictos if v.filtro == "pendiente")
    assert veredicto.resultado != "no_evaluable"


def test_costo_analogo_externo_amplia_incertidumbre_y_avisa():
    # ronda 5: el análogo de caupí es Trujillo 3 248.66 (antes Phaseolus ENA 2018 con CONFIANZA BAJA)
    cat = _cat_r5()
    r = evaluar(consulta(), cat)
    costo = por_cultivo(r)["caupi"].costo_ha
    assert costo.tipo_evidencia == "analogo_externo"
    assert costo.lo <= 3248.66 / 2 + 0.01 and costo.hi >= 3248.66 * 2 - 0.01
    assert any("Costo análogo externo" in a and "caupi" in a for a in r.avisos)
    assert any("costo análogo externo" in f for f in por_cultivo(r)["caupi"].faltantes)
    reg = {x.fila: x for x in cat.registro if x.archivo == R5.name}
    assert reg["e6bc216fce1e"].estado == "ignorada" and "PEN/t" in reg["e6bc216fce1e"].motivo  # papaya PEN/t (era 5e0599d5cde9 en la r4)
    assert reg["1a6b5fe734ec"].estado == "ignorada"  # camote: fuera del catálogo


def test_hwsd_no_se_usa_para_ece(tmp_path):
    from motor_rotacion.catalogo import Catalogo
    cab = ("variable,valor,valor_min,valor_max,unidad,cultivo,variedad,etapa,zona,lugar,lat,lon,fecha_o_periodo,"
           "fuente,url_o_doi,metodo,tipo_evidencia,estado,notas\n")
    fila = ("ece_suelo,2.1,,,dS/m,,,,bajo_piura,Bajo Piura,,,2023,HWSD v2.0 (FAO/IIASA),https://x.invalid/hwsd,"
            "raster HWSD,prediccion,estimado,prueba\n")
    ruta = tmp_path / "hwsd.csv"
    ruta.write_text(cab + fila, encoding="utf-8")
    cat = Catalogo()
    assert cat.integrar_csv_contrato(ruta) == 0
    reg = [x for x in cat.registro if x.archivo == "hwsd.csv"]
    assert reg[-1].estado == "rechazada" and "HWSD" in reg[-1].motivo


def test_zonas_aplicables_integra_en_cada_zona(tmp_path):
    from motor_rotacion.catalogo import Catalogo
    cab = ("variable,valor,valor_min,valor_max,unidad,cultivo,variedad,etapa,zona,lugar,lat,lon,fecha_o_periodo,"
           "fuente,url_o_doi,metodo,tipo_evidencia,estado,notas,zonas_aplicables\n")
    fila = ("rendimiento,2.0,1.5,2.5,t/ha,caupi,,,alto_piura,Piura,,,2020,prueba,https://x.invalid/r,"
            "prueba,regional,estimado,prueba,alto_piura;chira\n")
    ruta = tmp_path / "multi.csv"
    ruta.write_text(cab + fila, encoding="utf-8")
    cat = Catalogo()
    assert cat.integrar_csv_contrato(ruta) == 1
    f = cat.fichas["caupi"]
    assert ("rendimiento", "alto_piura") in f.por_zona and ("rendimiento", "chira") in f.por_zona
    mal = tmp_path / "mal.csv"
    mal.write_text(cab + fila.replace("alto_piura;chira", "Alto Piura"), encoding="utf-8")
    assert cat.integrar_csv_contrato(mal) == 0


def test_perennes_ronda6_banano_chira_y_mango_kent():
    cat = catalogo_por_defecto()
    assert cat.fichas["banano"].primera_produccion["chira"].hi == 1.2
    assert cat.fichas["mango"].kc["mid_lo"] == 0.73  # Kc Kent análogo amplía la envolvente del agua anual
    assert "1.4" in cat.fichas["mango"].salinidad["notas"]
    assert cat.fichas["mango"].salinidad["ECe_100"] == 1.3  # inicio de síntomas no reemplaza el umbral


# ------------------------------------------------------------------------------------------- ronda 4
def _bajo_piura_tras_arroz(cat=None):
    c = Consulta.desde_dict(json.loads((BASE / "ejemplos/bajo_piura_tras_arroz.json").read_text()))
    return c, evaluar(c, cat or catalogo_por_defecto())


def test_arveja_en_junio_bajo_piura_no_es_grave_con_tmax_media_pisco():
    # ronda 5: la regla grave usa la media de las máximas diarias (PISCOt, Bajo Piura jun-set 25.5–29.3 °C) y no el
    # día más caluroso de POWER (32–37,5 °C), que hacía grave a la arveja contra su TMAX EcoCrop 30 °C
    _, r = _bajo_piura_tras_arroz()
    cal = next(v for v in por_cultivo(r)["arveja"].veredictos if v.filtro == "calendario")
    assert not cal.grave and "probable no apto" not in cal.motivo
    # el aviso por mes sigue con POWER, pero dice que es el día más caluroso y muestra la media PISCOt al lado
    assert "día más caluroso" in cal.motivo and "media de las máximas PISCOt 25.5–28.1" in cal.motivo


def test_tmax_sobre_tmax_en_pocos_meses_no_es_grave():
    # caupí (TMAX EcoCrop 40 °C) en el mismo ejemplo no pasa el límite en el 75 % del ciclo
    _, r = _bajo_piura_tras_arroz()
    cal = next(v for v in por_cultivo(r)["caupi"].veredictos if v.filtro == "calendario")
    assert not cal.grave


def _consulta_distrito(**parcela):
    d = json.loads((BASE / "ejemplos/bajo_piura_tras_arroz.json").read_text())
    d["parcela"] = {"punto": [-5.33, -80.68], "area_ha": 1.0, **parcela}
    return Consulta.desde_dict(d)


def test_zona_deducida_del_distrito_etiquetada():
    r = evaluar(_consulta_distrito(distrito="Cura Mori", provincia="Piura"), catalogo_por_defecto())
    assert r.zona == "bajo_piura"
    assert "deducida del distrito CURA MORI" in r.zona_origen and "distrito_zona.csv" in r.zona_origen
    assert "Zona CONTRATO: bajo_piura (deducida del distrito" in r.a_texto()


def test_zona_del_usuario_manda_sobre_el_distrito():
    r = evaluar(_consulta_distrito(distrito="Sullana", zona="bajo_piura"), catalogo_por_defecto())
    assert (r.zona, r.zona_origen) == ("bajo_piura", "dada por el usuario")


def test_distrito_repetido_sin_provincia_no_se_adivina():
    from motor_rotacion.motor import zona_de_distrito
    z, origen = zona_de_distrito("Salitral", None)
    assert z is None and "MORROPON" in origen and "SULLANA" in origen
    assert zona_de_distrito("Salitral", "Sullana")[0] == "chira"
    assert zona_de_distrito("Salitral", "Morropón")[0] == "alto_piura"


def test_distrito_ambiguo_avisa_la_alternativa_y_desconocido_no_inventa():
    from motor_rotacion.motor import zona_de_distrito
    z, origen = zona_de_distrito("Tambogrande", "Piura")
    assert z == "san_lorenzo" and "ambiguo" in origen
    z, origen = zona_de_distrito("Máncora", "Talara")
    assert z is None and "piura_region" in origen  # distrito sin zona de parcela del contrato
    z, origen = zona_de_distrito("Narnia", None)
    assert z is None and "no está en" in origen
    r = evaluar(_consulta_distrito(distrito="Narnia"), catalogo_por_defecto())
    assert "inferida de la zona climática" in r.zona_origen and "Narnia" in r.zona_origen


def test_cada_supuesto_del_motor_esta_en_la_tabla_del_readme():
    """Una constante marcada '# supuesto del motor' en motor_rotacion/ tiene que estar en la tabla 'Supuestos del
    motor' del README. Si falla: agregue la constante a esa tabla con su valor y por qué."""
    import re
    patron = re.compile(r"^([A-Z_]+)\s*(?::[^=]+)?=.*#\s*supuesto del motor", re.M)
    nombres = {n for f in (BASE / "motor_rotacion").glob("*.py") for n in patron.findall(f.read_text())}
    assert {"FRACCION_MESES_TERMICA", "VIGENCIA_PRONOSTICO_DIAS", "FACTOR_ANALOGO_COSTO", "ESCENARIOS_ECW"} <= nombres
    readme = (BASE / "README.md").read_text()
    tabla = readme[readme.index("## Supuestos del motor"):]
    faltan = sorted(n for n in nombres if f"`{n}`" not in tabla)
    assert not faltan, f"agregue a la tabla 'Supuestos del motor' de README.md: {faltan}"


# ------------------------------------------------------------------------------------------ ronda 5


def _reg(cat, archivo):
    return {x.fila: x for x in cat.registro if x.archivo == archivo}


def test_costo_caupi_vigna_de_piura_reemplaza_phaseolus():
    cat = _cat_r5()
    reg = _reg(cat, R5.name)
    assert "ddf95b71cd9e" not in reg  # el análogo de Phaseolus (ENA 2018) ya no entra
    alto = cat.ficha("caupi", "alto_piura").costo
    assert (alto.lo, alto.hi, alto.tipo_evidencia) == (2079.0, 3183.5, "regional")
    assert "PEIHAP" in alto.fuente or "PEIHAP" in alto.notas
    bajo = cat.ficha("caupi", "bajo_piura").costo  # sin dato de zona: análogo de Trujillo ampliado [v/2, 2v]
    assert bajo.tipo_evidencia == "analogo_externo" and "Trujillo" in (bajo.fuente + bajo.notas)
    assert bajo.lo == pytest.approx(3248.66 / 2, abs=0.01) and bajo.hi == pytest.approx(3248.66 * 2, abs=0.01)
    r = evaluar(consulta(), cat)
    costo = por_cultivo(r)["caupi"].costo_ha
    assert "CONFIANZA BAJA" not in costo.notas and "Phaseolus" not in costo.notas
    assert not any("confianza baja" in a for a in r.avisos)


def test_nombre_de_variable_desconocido_se_rechaza_con_mensaje_claro():
    # H05 de Agronomía sobre Territorio: CE_agua_riego_* no es el nombre del contrato; antes quedaba IGNORADA en silencio
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()
    assert cat.integrar_csv_contrato(BASE / "datos_repo/cew_por_zona.csv") == 0
    reg = [x for x in cat.registro if x.archivo == "cew_por_zona.csv" and x.variable.startswith("CE_agua")]
    con_valor = [x for x in reg if "desconocido" not in x.motivo]
    assert con_valor and all(x.estado == "rechazada" for x in con_valor)
    assert all("ce_agua_riego" in x.motivo and "no reconocida" in x.motivo for x in con_valor)
    assert not any(k[0] == "ecw" for k in cat.contexto_zona)
    otra = [x for x in cat.registro if x.archivo == "cew_por_zona.csv"]
    assert all(x.estado != "ignorada" or "variable" not in x.motivo for x in otra)


def test_variable_inventada_se_rechaza_y_lista_las_aceptadas(tmp_path):
    from motor_rotacion.catalogo import Catalogo
    ruta = tmp_path / "rara.csv"
    ruta.write_text(CAB + "humedad_rara,3,,,%,caupi,,,alto_piura,Piura,,,2020,prueba,https://x.invalid/a,m,"
                    "regional,estimado,prueba,,\n", encoding="utf-8")
    cat = Catalogo()
    assert cat.integrar_csv_contrato(ruta) == 0
    x = _reg(cat, "rara.csv")["línea 2"]
    assert x.estado == "rechazada" and "humedad_rara" in x.motivo and "costo" in x.motivo and "rendimiento" in x.motivo


def test_cew_de_canal_es_valor_de_zona_y_rios_solo_aviso():
    cat = _cat_r5()
    z = {k[1]: c for k, c in cat.contexto_zona.items() if k[0] == "ecw"}
    assert z["san_lorenzo"].valor == 0.47 and "reservorio" in z["san_lorenzo"].notas
    assert z["chira"].valor == 0.59 and "reservorio" in z["chira"].notas
    assert z["sierra_piura"].valor == 0.334 and "toma" in z["sierra_piura"].notas
    assert all("estiaje" in c.notas or "estación desconocida" in c.notas for c in z.values())
    assert not {"medio_piura", "bajo_piura", "alto_piura"} & set(z)  # sin CEw de canal: siguen los escenarios
    c = consulta(parcela={"punto": [-5.2, -80.6], "area_ha": 1.0, "zona": "medio_piura"}, agua={"ecw_ds_m": None})
    r = evaluar(c, cat)
    assert not r.consulta.agua.ecw.conocido and len(escenarios_ecw(c, cat, 2)) == 3
    aviso = [a for a in r.avisos if "puntos ANA" in a]
    # ronda 6: RPiur5 (9.92, estimada por Datos) entra como punto y sube el máximo del rango de 5.98 a 9.92
    assert aviso and "0.74" in aviso[0] and "9.92" in aviso[0] and "estiaje" in aviso[0]
    assert any("pozo" in a and "0.16" in a and "3.83" in a for a in r.avisos)  # tesis UNP: solo aviso


def test_cew_33_puntos_ana_aceptados_como_aviso_tras_resolucion_de_datos():
    """Ronda 6: el orquestador acepta la resolución de Datos de las 4 lecturas que antes se rechazaban (QCarn1,
    QSFran1, RPiur4, RPiur5): entran como puntos de río o quebrada (aviso), nunca como valor de zona."""
    cat = _cat_r5()
    import csv
    filas = list(csv.DictReader(open(R5, encoding="utf-8")))
    ana = {r["id_registro"] for r in filas if r["variable"] == "ce_agua_riego" and "-2024-ANA" in r["fuente"]
           and r["archivo_origen"] == "cew_ana_r4.csv"}  # puntos ANA 2024 (IT 0074 Chira, IT 0076 Piura) de Datos
    assert len(ana) == 33
    reg = [x for x in cat.registro if x.archivo == R5.name and x.variable == "ce_agua_riego"]
    acept = [x for x in reg if x.fila in ana and x.estado == "aceptada"]
    assert len(acept) == 33 and not [x for x in reg if x.estado == "rechazada"]
    for punto in ("QCarn1", "QSFran1", "RPiur4", "RPiur5"):
        x = [v for v in acept if f"({punto}," in v.motivo]
        assert x and "solo aviso" in x[0].motivo


def test_ecw_de_zona_chira_es_la_del_reservorio_etiquetada():
    cat = _cat_r5()
    r = evaluar(consulta(parcela={"punto": [-4.9, -80.7], "area_ha": 1.0, "zona": "chira"}, agua={"ecw_ds_m": None}), cat)
    ecw = r.consulta.agua.ecw
    assert ecw.valor == 0.59 and "VALOR DE ZONA chira" in ecw.notas
    assert any("valor de zona chira" in a and "reservorio" in a and "estiaje" in a for a in r.avisos)


def test_zona_vacia_exige_zonas_aplicables_como_validar_py(tmp_path):
    from motor_rotacion.catalogo import Catalogo
    cab = CAB.strip() + ",zonas_aplicables\n"
    filas = [
        # dato local (lugar concreto, regional) sin zona ni zonas_aplicables: rechazado
        "rendimiento,2.0,1.5,2.5,t/ha,caupi,,,,Sullana,,,2020,DRAP Piura,https://x.invalid/r,m,regional,estimado,prueba,,,",
        # tabla genérica de especie: pasa
        "rendimiento,2.0,1.5,2.5,t/ha,caupi,,,,,,,2020,Allen et al. 1998,https://x.invalid/g,m,bibliografico,estimado,prueba,,,",
        # zonas_aplicables con medio_bajo_piura: rechazado (validar.py R7)
        "rendimiento,2.0,1.5,2.5,t/ha,caupi,,,,Piura,,,2020,DRAP,https://x.invalid/m,m,regional,estimado,prueba,,,medio_bajo_piura",
    ]
    ruta = tmp_path / "za.csv"
    ruta.write_text(cab + "\n".join(filas) + "\n", encoding="utf-8")
    cat = Catalogo()
    cat.integrar_csv_contrato(ruta)
    reg = _reg(cat, "za.csv")
    assert reg["línea 2"].estado == "rechazada" and "zonas_aplicables" in reg["línea 2"].motivo
    assert reg["línea 3"].estado != "rechazada"  # pasa R7 (puede perder por prioridad de evidencia, eso es otra regla)
    assert reg["línea 4"].estado == "rechazada" and "medio_bajo_piura" in reg["línea 4"].motivo


def test_arveja_umbral_por_cultivar_y_alternativa_fao56_rotulada():
    cat = catalogo_por_defecto()
    s = cat.fichas["arveja"].salinidad
    assert (s["ECe_100"], round(50 / (s["ECe_50"] - s["ECe_100"]), 1)) == (3.4, 10.6)
    assert s["cultivares"] == {"SP-290": 2.5, "Durana": 4.5}
    # ECe medida 3.0 con napa profunda: bajo el umbral principal 3.4, pero SP-290 ya pierde desde 2.5
    c = consulta(suelo={"ece_ds_m": 3.0, "napa_m": 3.0}, candidatos=["arveja"])
    v = veredicto(por_cultivo(evaluar(c, cat))["arveja"], "salinidad")
    assert v.resultado == "advierte" and "SP-290" in v.motivo and "Durana" in v.motivo
    u = v.cifras["ECe_umbral_100"]
    assert (u.valor, u.lo, u.hi) == (3.4, 2.5, 4.5) and "cultivar" in u.notas
    assert "1.5" in u.notas and "14" in u.notas and "estimación" in u.notas and "FAO-48" in u.notas
    assert v.cifras["fraccion_rendimiento_salinidad"].lo < 1.0  # SP-290 a 3.0: 1 - 0.106·0.5 ≈ 0.95


def test_regla_termica_grave_usa_tmax_media_pisco_por_zona():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()  # copia propia: el test la modifica
    t = cat.tmax_pisco[("bajo_piura", 7)]
    assert (t.lo, t.hi, t.tipo_evidencia) == (25.48, 28.05, "prediccion") and "PISCOt" in t.fuente
    s = cat.tmax_pisco[("sierra_piura", 1)]  # dos celdas (Ayabaca, Huancabamba): envolvente
    assert (s.lo, s.hi) == (18.03, 21.49)
    # si la media de las máximas pasa el TMAX en todo el ciclo, es grave y lo dice; POWER no interviene
    for m in range(1, 13):
        cat.tmax_pisco[("bajo_piura", m)] = cat.tmax_pisco[("bajo_piura", m)].con(valor=36.0, valor_min=35.0, valor_max=37.0)
    c = Consulta.desde_dict(json.loads((BASE / "ejemplos/bajo_piura_tras_arroz.json").read_text()))
    cal = next(v for v in por_cultivo(evaluar(c, cat))["arveja"].veredictos if v.filtro == "calendario")
    assert cal.grave and "media de las máximas diarias" in cal.motivo and "PISCOt" in cal.motivo
    assert "NASA POWER" not in cal.motivo


def test_regla_termica_sin_pisco_de_la_zona_no_usa_el_dia_mas_caluroso():
    from motor_rotacion.catalogo import Catalogo
    cat = Catalogo()  # copia propia: el test la modifica
    cat.tmax_pisco.clear()
    _, r = _bajo_piura_tras_arroz(cat)
    cal = next(v for v in por_cultivo(r)["arveja"].veredictos if v.filtro == "calendario")
    assert not cal.grave
    assert any("Tmáx media PISCO" in f for f in por_cultivo(r)["arveja"].faltantes)


# ------------------------------------------------------------------------------------------- ronda 6
ICEN = ("sin_el_nino", "el_nino_moderado", "el_nino_fuerte_extraordinario")


def test_unidades_del_contrato_salen_de_contrato_md():
    # error repetido: la tupla escrita a mano en validacion.py se quedó atrás de CONTRATO.md (%/(dS/m), meses, años)
    from motor_rotacion import validacion
    texto = (BASE.parents[1] / "CONTRATO.md").read_text(encoding="utf-8")
    linea = next(x for x in texto.splitlines() if x.startswith("- Unidades"))
    for u in ("%/(dS/m)", "meses", "años", "categoría", "PEN/ha", "dS/m", "m3/ha/año"):
        assert u in linea and u in validacion.UNIDADES_CONTRATO, u
    assert not any("(" in u and u != "%/(dS/m)" for u in validacion.UNIDADES_CONTRATO)  # sin glosas entre paréntesis
    # consecuencia: la pendiente 14 de FAO-56 (AN0264) entra como alternativa rotulada, no como pendiente usada
    cat = catalogo_por_defecto()
    x = _reg(cat, "fichas_anuales.csv")["AN0264"]
    assert x.estado == "aceptada" and "alternativa rotulada" in x.motivo
    s = cat.fichas["arveja"].salinidad
    assert round(50 / (s["ECe_50"] - s["ECe_100"]), 1) == 10.6


def test_arveja_umbral_de_floracion_27_contra_tmax_media_pisco():
    cat = catalogo_por_defecto()
    x = [r for r in cat.registro if r.variable == "temperatura_umbral_estres_reproductivo"]
    assert x and x[0].estado == "aceptada"
    u = cat.fichas["arveja"].umbral_floracion
    assert (u.minimo, u.maximo, u.unidad) == (27.0, 32.0, "°C") and "10.1139/cjps-2022-0156" in u.url
    # junio en Bajo Piura: floración-llenado (etapa media FAO-56) en jul-set; set tiene mediana 27.82 > 27
    _, r = _bajo_piura_tras_arroz()
    cal = veredicto(por_cultivo(r)["arveja"], "calendario")
    assert cal.resultado == "advierte" and "floración" in cal.motivo and "27" in cal.motivo
    assert "27.82" in cal.motivo and not cal.grave  # P10 de jul-set (25.5-26.7) queda bajo 27: advertencia
    assert "TMAX absoluto EcoCrop" not in cal.motivo.split("floración")[0][-80:]  # no reutiliza el 30 de EcoCrop
    # si en casi todos los meses de floración hasta el año fresco (P10) pasa 27, es probable no apto
    from motor_rotacion.catalogo import Catalogo
    cat2 = Catalogo()
    for m in (7, 8, 9):
        cat2.tmax_pisco[("bajo_piura", m)] = cat2.tmax_pisco[("bajo_piura", m)].con(valor=28.5, valor_min=28.0,
                                                                                      valor_max=29.0)
    _, r2 = _bajo_piura_tras_arroz(cat2)
    cal2 = veredicto(por_cultivo(r2)["arveja"], "calendario")
    assert cal2.grave and "floración" in cal2.motivo


def test_arveja_sin_ventana_en_bajo_piura_por_ausencia_drap_es_alerta():
    cat = catalogo_por_defecto()
    assert "bajo_piura" not in cat.fichas["arveja"].calendario  # no hay ventana: 0 ha en la DRAP 2016-2024
    aus = [x for x in _reg(cat, "calendario_siembra_cosecha_piura.csv").values()
           if x.cultivo == "arveja" and "bajo_piura" in x.motivo]
    assert aus and aus[0].estado == "aceptada" and "ausencia" in aus[0].motivo
    _, r = _bajo_piura_tras_arroz()
    cal = veredicto(por_cultivo(r)["arveja"], "calendario")
    assert cal.resultado == "advierte"
    assert "sin ventana de siembra observada" in cal.motivo and "0 ha" in cal.motivo and "DRAP" in cal.motivo
    # en Medio Piura no hay fila de ausencia: solo la marca 'sin ventana', sin alerta inventada
    c = consulta(parcela={"punto": [-5.2, -80.6], "area_ha": 1.0, "zona": "medio_piura"}, candidatos=["arveja"])
    cal_m = veredicto(por_cultivo(evaluar(c, cat))["arveja"], "calendario")
    assert "sin ventana de siembra observada" in cal_m.motivo and "0 ha" not in cal_m.motivo


def test_lluvia_pisco_por_zona_y_escenario_icen():
    cat = catalogo_por_defecto()
    c = cat.lluvia_pisco[("bajo_piura", "el_nino_fuerte_extraordinario", 2)]
    assert c.conocido and c.unidad == "mm" and c.tipo_evidencia == "prediccion" and "PISCOp" in c.fuente
    s = cat.lluvia_pisco[("sierra_piura", "sin_el_nino", 2)]  # Ayabaca y Huancabamba: envolvente
    assert "envolvente" in s.notas
    assert set(cat.anios_icen) == set(ICEN) and cat.anios_icen["el_nino_fuerte_extraordinario"] == [1983, 1998, 2016]
    for esc in ICEN:
        r = evaluar(consulta(escenario=esc, parcela={"zona": "bajo_piura"}), cat)
        ll = r.clima.cifra(2, "lluvia")
        assert "PISCOp" in ll.fuente and ll.valor == cat.lluvia_pisco[("bajo_piura", esc, 2)].valor
        assert r.clima.anios == cat.anios_icen[esc]  # ET0 y temperatura de POWER con los mismos años ICEN


def test_escenario_viejo_se_rechaza_y_nombra_los_icen():
    with pytest.raises(ValueError) as e:
        consulta(escenario="normal")
    assert all(x in str(e.value) for x in ICEN)


def test_recomendacion_por_escenario_climatico_y_cambio_del_primer_lugar():
    from motor_rotacion.motor import evaluar_escenarios
    from motor_rotacion.reporte import escenarios_clima_a_dict, escenarios_clima_a_texto
    c, _ = _bajo_piura_tras_arroz()
    ec = evaluar_escenarios(c, catalogo_por_defecto())
    d = escenarios_clima_a_dict(ec)
    assert [x["escenario"] for x in d["escenarios"]] == list(ICEN)
    for x in d["escenarios"]:
        assert {"orden", "aceptados", "descartados", "primero"} <= set(x)
        assert all({"cultivo", "p10", "p50"} <= set(o) for o in x["orden"])
    primeros = {x["primero"] for x in d["escenarios"]}
    assert d["primer_lugar_cambia"] == (len(primeros) > 1)
    txt = escenarios_clima_a_texto(ec)
    assert "ESCENARIOS CLIMÁTICOS" in txt and ("cambia" in txt or "no cambia" in txt)
    assert "3,98" in txt and "met.igp.gob.pe" in txt  # contexto ICEN ago-2026, aviso con fuente


def test_el_nino_fuerte_marca_exceso_de_agua_y_lo_que_falta():
    cat = catalogo_por_defecto()
    base = dict(parcela={"zona": "bajo_piura"}, suelo={"drenaje": "moderado"}, mes_siembra=1, candidatos=["algodon", "caupi"])
    fuerte = evaluar(consulta(escenario="el_nino_fuerte_extraordinario", **base), cat)
    seco = evaluar(consulta(escenario="sin_el_nino", **base), cat)
    alg = veredicto(por_cultivo(fuerte)["algodon"], "calendario")
    assert alg.resultado == "advierte" and "exceso de agua" in alg.motivo and "PISCOp" in alg.motivo
    assert "59.95" in alg.motivo  # pérdida por anegamiento ≤15 d del algodón (Tian 2021, AN0458), solo como contexto
    cau = por_cultivo(fuerte)["caupi"]
    assert any("tolerancia al anegamiento de caupi" in f for f in cau.faltantes)
    assert any("duración del anegamiento" in f for f in por_cultivo(fuerte)["algodon"].faltantes)
    assert "exceso de agua" not in veredicto(por_cultivo(seco)["algodon"], "calendario").motivo


def test_lecturas_ana_resueltas_por_datos_son_aviso_de_punto():
    cat = _cat_r5()
    reg = [x for x in cat.registro if x.archivo == R5.name and x.variable == "ce_agua_riego"]
    assert not any("disputa" in x.motivo for x in reg)
    puntos = {p.punto: p for p in cat.contexto_agua}
    assert (puntos["RPiur4"].cifra.valor, puntos["RPiur4"].cifra.lo, puntos["RPiur4"].cifra.hi) == (7.86, 5.56, 9.03)
    assert (puntos["QCarn1"].cifra.lo, puntos["QCarn1"].cifra.hi) == (1.94, 3.23)
    assert puntos["RPiur5"].cifra.valor == 9.92 and puntos["QSFran1"].cifra.valor == 5.0
    assert all(puntos[p].cifra.estado == "estimado" for p in ("QCarn1", "QSFran1", "RPiur4", "RPiur5"))
    assert not any(k == ("ecw", "san_lorenzo") and c.valor != 0.47 for k, c in cat.contexto_zona.items())
    c = consulta(parcela={"punto": [-5.2, -80.6], "area_ha": 1.0, "zona": "medio_piura"}, agua={"ecw_ds_m": None})
    aviso = [a for a in evaluar(c, cat).avisos if "puntos ANA" in a][0]
    assert "9.92" in aviso and "estimad" in aviso and "RPiur5" in aviso


def test_advertencia_de_exceso_no_tapa_la_duracion_desconocida():
    """Frijol de palo no trae duración ni Kc: su calendario es no evaluable en todo escenario. La advertencia de
    exceso de agua de El Niño fuerte se reporta, pero no puede volverlo 'aceptado' (antes pasaba de sin_datos en
    sin_el_nino a aceptado en el_nino_fuerte_extraordinario solo por tener una advertencia más)."""
    cat = catalogo_por_defecto()
    base = dict(parcela={"zona": "bajo_piura"}, suelo={"drenaje": None}, mes_siembra=8, candidatos=["frijol de palo"])
    for esc in ("sin_el_nino", "el_nino_fuerte_extraordinario"):
        e = por_cultivo(evaluar(consulta(escenario=esc, **base), cat))["frijol de palo"]
        cal = veredicto(e, "calendario")
        assert cal.resultado == "no_evaluable" and e.decision == "sin_datos", esc
    cal = veredicto(por_cultivo(evaluar(consulta(escenario="el_nino_fuerte_extraordinario", **base), cat))
                    ["frijol de palo"], "calendario")
    assert "exceso de agua" in cal.motivo


def test_cli_da_la_recomendacion_por_escenario_climatico():
    """La pregunta del proyecto habla de escenarios climáticos: texto y JSON traen los 3 escenarios ICEN por parcela."""
    ej = str(BASE / "ejemplos/tablazo_sur_ce_medida.json")
    p = subprocess.run([sys.executable, "-m", "motor_rotacion", ej, "--formato", "json"], cwd=BASE, capture_output=True,
                       text=True, check=True)
    ec = json.loads(p.stdout)["escenarios_climaticos"]
    assert [e["escenario"] for e in ec["escenarios"]] == ["sin_el_nino", "el_nino_moderado",
                                                          "el_nino_fuerte_extraordinario"]
    assert all(e["fuente_lluvia"] == "PISCOp" and "orden" in e and "descartados" in e for e in ec["escenarios"])
    assert isinstance(ec["primer_lugar_cambia"], bool) and "3,98" in ec["contexto_icen"]
    t = subprocess.run([sys.executable, "-m", "motor_rotacion", ej], cwd=BASE, capture_output=True, text=True,
                       check=True).stdout
    assert "ESCENARIOS CLIMÁTICOS" in t and "El primer lugar" in t


# ---------------------------------------------------------------------------------------- ronda 7
def _tablazo(escenario, cat=None):
    c = Consulta.desde_dict(json.loads((BASE / "ejemplos/tablazo_sur_ce_medida.json").read_text()))
    from dataclasses import replace
    return evaluar(replace(c, escenario=escenario), cat or catalogo_por_defecto())


def test_dia_mas_caluroso_power_es_nota_sin_peso():
    """Datos marcó la Tmáx POWER 'no usar sin corregir' (>3 °C de diferencia con PISCO): solo nota, sin peso."""
    r = _tablazo("el_nino_fuerte_extraordinario")
    for cultivo in ("caupi", "zapallo"):
        cal = veredicto(por_cultivo(r)[cultivo], "calendario")
        assert "día más caluroso" in cal.motivo and "solo nota" in cal.motivo and "no usar sin corregir" in cal.motivo
        assert cal.resultado == "pasa", (cultivo, cal.resultado, cal.motivo)
    for e in r.evaluaciones:
        for v in e.veredictos:
            if v.resultado == "advierte" and v.filtro == "calendario":
                quitada = [m for m in v.motivo.split("; ") if "día más caluroso" not in m]
                assert quitada, (e.cultivo, v.motivo)


def test_lluvia_efectiva_usda_scs_mensual():
    from motor_rotacion.necesidad import lluvia_efectiva
    assert lluvia_efectiva(0.0) == 0.0
    assert lluvia_efectiva(100.0) == pytest.approx(84.0)  # P·(125 − 0,2·P)/125
    assert lluvia_efectiva(250.0) == pytest.approx(150.0)
    assert lluvia_efectiva(300.0) == pytest.approx(155.0)  # 125 + 0,1·P


def test_necesidad_de_riego_por_escenario_con_rango_entre_anios():
    from motor_rotacion.motor import evaluar_escenarios
    c, _ = _bajo_piura_tras_arroz()
    ec = evaluar_escenarios(c, catalogo_por_defecto())
    valores = {}
    for esc, r in ec.resultados.items():
        n = por_cultivo(r)["arveja"].necesidad
        assert n is not None and n.cifra.unidad == "m3/ha" and n.cifra.lo <= n.cifra.valor <= n.cifra.hi
        assert sorted({a for a, _, _ in n.por_anio}) == sorted(r.clima.anios)  # un valor por campaña del escenario
        assert "USDA-SCS" in n.metodo and "Kc" in n.metodo
        assert ("P10–P90" in n.rango) == (len(r.clima.anios) >= 5)
        valores[esc] = n.cifra.valor
    assert len(set(valores.values())) > 1  # el escenario mueve la necesidad
    # sin Kc o sin duración no se inventa la necesidad
    sin_kc = next(e for e in r.evaluaciones if not e.agua.disponible)
    assert sin_kc.necesidad is None


def test_tarifa_de_agua_entra_al_margen_solo_donde_hay_dato():
    from motor_rotacion.motor import evaluar_escenarios
    cat = catalogo_por_defecto()
    c, r = _bajo_piura_tras_arroz(cat)
    arv = por_cultivo(r)["arveja"]
    assert arv.costo_agua is None and any("tarifa de agua" in f and "bajo_piura" in f for f in arv.faltantes)
    d = json.loads((BASE / "ejemplos/bajo_piura_tras_arroz.json").read_text())
    d["parcela"] = {"punto": [-4.92, -80.35], "area_ha": 2.0, "provincia": "Piura", "zona": "san_lorenzo"}
    ec = evaluar_escenarios(Consulta.desde_dict(d), cat)
    p50, costos = {}, {}
    for esc, rr in ec.resultados.items():
        e = por_cultivo(rr)["arveja"]
        assert e.costo_agua is not None and e.costo_agua.unidad == "PEN/ha" and "c163a8cfff2f" in e.costo_agua.notas
        assert e.costo.lo > e.costo_agua.lo  # el costo de producción ya incluye el agua
        p50[esc], costos[esc] = e.margen_mc["p50"], (e.costo_agua.lo, e.costo_agua.hi)
    assert len(set(costos.values())) > 1 and len(set(p50.values())) > 1  # el margen varía por escenario


def test_deficit_contra_dotacion_asignada_con_ky():
    cat = catalogo_por_defecto()
    d = json.loads((BASE / "ejemplos/bajo_piura_tras_arroz.json").read_text())
    d["agua"]["eficiencia"] = [0.2, 0.25]  # con poca eficiencia la dotación del plan no alcanza
    r = evaluar(Consulta.desde_dict(d), cat)
    arv = por_cultivo(r)["arveja"]
    df = arv.deficit
    assert df is not None and "74fa4d33ef21" in df.fuente_dotacion  # medio_bajo_piura vale para bajo_piura
    assert df.deficit_m3_ha.hi > 0 and 0 <= df.caida_rendimiento.lo <= df.caida_rendimiento.hi <= 1
    assert "Ky" in df.caida_rendimiento.notas and "anual" in df.nota
    cau = por_cultivo(r)["caupi"].deficit  # caupí no tiene Ky en los datos
    assert cau is not None and (cau.deficit_m3_ha.hi == 0 or not cau.caida_rendimiento.conocido)


def test_tmax_media_por_escenario_icen():
    cat = catalogo_por_defecto()
    t = cat.tmax_pisco_enso[("bajo_piura", "el_nino_fuerte_extraordinario", 10)]
    assert "PISCOt" in t.fuente and t.tipo_evidencia == "prediccion"
    c, _ = _bajo_piura_tras_arroz(cat)
    from dataclasses import replace
    r = evaluar(replace(c, escenario="el_nino_fuerte_extraordinario"), cat)
    cal = veredicto(por_cultivo(r)["arveja"], "calendario")
    assert f"mes 10 {t.valor:g} [{t.lo:g}–{t.hi:g}]" in cal.motivo
    assert cat.tmax_pisco_enso[("bajo_piura", "sin_el_nino", 10)].valor != t.valor


def test_cli_muestra_necesidad_de_riego_por_escenario():
    ej = str(BASE / "ejemplos/bajo_piura_tras_arroz.json")
    p = subprocess.run([sys.executable, "-m", "motor_rotacion", ej, "--formato", "json"], cwd=BASE, capture_output=True,
                       text=True, check=True)
    for e in json.loads(p.stdout)["escenarios_climaticos"]["escenarios"]:
        o = e["orden"][0]
        n = o["necesidad_riego_m3_ha"]
        assert n["p10"] <= n["p50"] <= n["p90"] and "USDA-SCS" in n["metodo"] and n["n_anios"] == len(e["anios_campania"])
        assert "costo_agua_pen_ha" in o and "deficit_dotacion" in o
    t = subprocess.run([sys.executable, "-m", "motor_rotacion", ej], cwd=BASE, capture_output=True, text=True,
                       check=True).stdout
    esc = t.split("ESCENARIOS CLIMÁTICOS", 1)[1]
    assert "necesidad de riego neta" in esc and "m3/ha" in esc and "tarifa de agua" in esc
