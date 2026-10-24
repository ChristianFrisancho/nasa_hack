# PROGRESO, Piura Datos (restricciones/)

## Ronda 1 (cerrada 2026-10-24)
- [x] Copié `evidencia_n8n.csv` a `insumos/`. No toqué n8n: solo lo leí.
- [x] `evidencia_observada.csv`: 11134 registros, generado con `tools/limpiar.py`. `tools/test_limpiar.py` pasa 11/11.
- [x] DRAP 2015-24 por distrito y año (`tools/extraer_drap.py`): 9514 registros. Corregí el error de agregación (la producción solo se sumaba en meses con cosecha).
- [x] Curado manual (`tools/insumos_curados.py`, `tools/insumos_curados_r1b.py`):
  - agua: ANA PGRH, PADH 2025-26, PCR 2025-26, tesina de San Lorenzo, agraria.pe;
  - costos ENA 2018;
  - drenaje y sales: Santayana 2012;
  - CE: Jequetepeque.
- [x] `cobertura.csv` y `cobertura.md` (`tools/cobertura.py`, `tools/cobertura_md.py`).
- [x] `respuestas_a_modelos.md`: 9 preguntas más las 4 anteriores.
- [x] `revision_de_modelos.md`: 6 objeciones.
- [x] `decisions.tsv` al día.
- [x] Tavily: 137 créditos de Piura Datos en total (`../creditos_tavily.tsv`).

## Para reproducir
```
python3 tools/extraer_drap.py && python3 tools/extraer_pdfs.py && python3 tools/insumos_curados.py && python3 tools/insumos_curados_r1b.py && python3 tools/insumos_curados_r2.py && python3 tools/insumos_curados_r3.py && python3 tools/insumos_curados_r4.py && python3 tools/cew_ana_puntos.py && python3 tools/insumo_pendiente.py
python3 tools/limpiar.py && python3 tools/test_limpiar.py
python3 tools/cobertura.py && python3 tools/cobertura_md.py
# aparte, con rasterio:
../suelos/.venv/bin/python tools/temperatura_power.py && ../suelos/.venv/bin/python tools/test_temperatura_power.py
../suelos/.venv/bin/python tools/pisco_vs_chirps.py
```

## Pendiente al cerrar la ronda 1
- ECe agrícola de Piura (tesis UNP Rabanal Yocya 2025, PECHP, INIA).
- Fracción con mal drenaje por zona (PECHP, 7980 ha sin verificar; JUMBP).
- Volumen entregado por campaña y junta (PADH de la ANA).
- Columna `zona` en el contrato.
- Costos por ha en Piura.

## Ronda 2 (cerrada 2026-10-24)
- [x] `evidencia_observada.csv`: 11180 registros, 22 columnas (nueva `zona` con los 7 códigos del CONTRATO). `tools/test_limpiar.py` pasa 35/35. 0 claves con cifras distintas, 0 duplicados fundidos.
  - estado: observado 10989, estimado 110, desconocido 81.
  - zona: sierra_piura 5240, bajo_piura 1624, chira 1515, alto_piura 964, piura_region 964, san_lorenzo 421, medio_piura 357, vacía 95.
  - De las 95 vacías, 79 son "Medio y Bajo Piura" en conflicto (no asignadas, por instrucción) y 16 están fuera de Piura.
  - Unidades fuera del CONTRATO (pasan con aviso, fallan con `--estricto`): PEN/kg 5219, ha 21, m3/ha/año 15, PEN/t 6, m3/ha 5, hm3 5, USD/ha 2, PEN/m3 1.
- [x] `tools/insumos_curados_r2.py` → `insumos/curado_r2.csv`, 47 filas (11 medicion_local, 36 regional):
  - CE de suelo en chacra: Alto (El Huaro, 0,46-0,6 dS/m), Medio (UNP, 0,95), Bajo (Tablazo Sur, 3,44-8,2; PSI 7,3-17,7 %);
  - napa y sales: Bajo Piura 1978 y Alto Piura 1987 (Castillo Albines); cuenca 32000 ha (PGRH);
  - agua en San Lorenzo: módulos, volumen distribuido, pérdidas, tarifa (García Samamé 2024);
  - costos: MAD Bajo Piura 2021 (tesis y artículo), algodón Pima DRA 2022;
  - algodón Bajo Piura 2016-2023: 3,09 t/ha ponderado.
- [x] Fuentes con copia local en `fuentes/`: Mendoza 2025, tesis Rodríguez Valdez, García Samamé 2024 (PDF y texto); PGRH 2015, Castillo Albines, artículo LATAM (texto). Sin copia local: El Huaro, UNP y DRA (solo resumen o web).
- [x] `tools/zonas.py` y la columna `zona`; prueba de los 7 códigos y del conflicto Medio-Bajo.
- [x] `propuesta_contrato_zona.md`: unidades nuevas, `medio_bajo_piura`, estado `asignada`, `fuente_primaria` y `subzona`. No toqué CONTRATO.md.
- [x] `respuestas_a_modelos.md`, sección "Ronda 2": desacuerdos, pedidos 12-16, puntos 1-11 y P1-P18.
- [x] `cobertura.csv` (155 celdas) y `cobertura.md` (ronda 2).
- [x] Tavily: 23 créditos en la ronda 2; 160 en total de Piura Datos. Nada pago. No toqué flujos n8n.
- Incidente: a las 06:30 la caja se restauró y perdí el script y el CSV de la ronda 2 y los PDF de `/tmp`. Los rehíce y gasté 1 crédito en volver a extraer textos (ver `decisions.tsv`, r2-incidente).

## Pendiente al cerrar la ronda 2
- CE de suelo en Chira y San Lorenzo; método de extracto (pasta saturada o 1:1) de las CE ya cargadas.
- Napa o drenaje en Chira, San Lorenzo, Medio y Alto Piura; PECHP 7980 ha sigue sin verificar.
- Pendiente de las áreas bajo riego (probar un DEM público).
- Agua por campaña en Chira, Medio y Bajo Piura (solo hay San Lorenzo).
- Costos de frijol, caupí y camote en Piura.
- Kc del mango y validación de CHIRPS contra estaciones SENAMHI.

## Ronda 3 (cerrada 2026-10-24)
- [x] CONTRATO de las 06:41 aplicado con `tools/contrato.py`: `medio_bajo_piura` (79 filas), dotaciones `estimado` con método `dotacion_asignada` (16), CE de suelo sin extracto con método `ce_extracto_no_declarado` (4), columnas opcionales `fuente_primaria` y `subzona`. No toqué CONTRATO.md.
- [x] Pendiente de Piura Territorio: 42 filas `prediccion`/`estimado` (`tools/insumo_pendiente.py`). No la recalculé.
- [x] `tools/insumos_curados_r3.py` → `insumos/curado_r3.csv`, 16 filas (steering 3 primero):
  - costos, todos `analogo_externo` con "Comparabilidad:": papaya 3940,3 PEN/ha (ENA 2018, selva); vainita 10327,07 PEN/ha (DRA Tacna 2014 vía Paxi 2022); caupí 1531,01 PEN/ha (proxy de frijol grano seco de costa); camote 16340 PEN/ha (MIDAGRI 2026, Cañete). Frijol de palo: desconocido;
  - CE del agua de riego: Chira 0,373-1,167 dS/m (río Chira en Sullana, Coronel 2021). Medio, Bajo, Tablazo Sur y San Lorenzo quedan `desconocido`, con la fuente que no se pudo leer;
  - CE de suelo en Chira: 0,103 dS/m (Atoche 2025, Sullana). Ninguna tesis declara el extracto.
- [x] `cobertura.md` (ronda 3), 185 celdas, con una tabla nueva que compara HWSD con las mediciones de chacra. Cultivos nuevos en la cobertura: frijol verde, frijol de palo, papaya y quinua.
- [x] `evidencia_observada.csv`: 11238 registros. `tools/test_limpiar.py`: 57/57 (2 casos nuevos de `ce_agua_riego`).
- [x] Copias locales en `fuentes_r3/`: Paxi 2022, Atoche 2025, La Rosa 2021 (PDF y texto).
- [x] Respaldo en `respaldo/r3a`, `r3c` y `r3d`.
- [x] Tavily: unos 36 créditos en la ronda 3; unos 196 en total de Piura Datos. Nada pago. No toqué flujos n8n.

## Pendiente al cerrar la ronda 3
- ECe con extracto declarado (pasta saturada) en cualquier zona; CE de suelo en San Lorenzo.
- CE del agua de riego en Medio, Bajo, Tablazo Sur y San Lorenzo: las fuentes son de la ANA, la UNP o CORE, y no pude abrir esos repositorios.
- PECHP 7980 ha sin fuente. Napa en Chira, San Lorenzo, Medio y Alto: sin dato.
- Agua por campaña en Chira y en el Medio y Bajo Piura: sin dato por campaña. Pista: el PADH 2022-2023 da una demanda bruta de 1779,66 hm3/año para todo el sistema Chira-Piura (IRAGER 2023). Es demanda, no entrega, así que no la cargué.
- Costos de Piura para caupí, frijol, camote y papaya: hoy sólo hay análogos externos.
- Kc del mango y CHIRPS contra SENAMHI: sin hacer.

## Ronda 4 (cerrada 2026-10-24, 07:35 UTC)
- [x] Costo de producción de caupí (Vigna) por ha: `insumos/curado_r4.csv`.
- [x] Temperatura NASA POWER diaria 2001-2025 (T2M_MAX y T2M_MIN), 6 zonas × 12 meses: 168 filas en `temperatura_media_max_min_zona.csv`, con `tools/temperatura_power.py`. Cada fila trae en `notas` el contraste con PISCO-SENAMHI 1981-2010. 52 filas difieren en más de 3 °C y llevan "no usar esta fila sin corregir": Ayabaca entera y las Tmax de julio de la costa. `tools/test_temperatura_power.py` PASA.
- [x] CE del agua, puntos ANA 2024 (`tools/cew_ana_puntos.py`): 29 con cifra y 4 con unidad ambigua (`desconocido`). La unidad se verificó contra los PDF de `fuentes_r4/`.
- [x] Suelos del EIA Olmos-Sechura: zona vacía, subzona `eia_olmos_sechura_no_agricola`, "Zona no aplica".
- [x] `limpiar.py`:
  - convierte kg/ha a t/ha;
  - exige una unidad por variable, con una lista de excepciones justificadas;
  - falla con CEw fuera de [0,01; 30] dS/m, salvo pozo.
  `test_limpiar.py` PASA 69/69.
- [x] `evidencia_observada.csv`: 11286 registros. 51 sin zona, todos con "Zona no aplica". 91 sin cifra, todos `desconocido`.
- [x] Lluvia: `tools/pisco_vs_chirps.py` compara PISCOp, CHIRPS y las normales SENAMHI por estación, zona y temporada, con y sin FEN (salidas en `clima/`). Recomiendo PISCOp para la costa, con la mediana sin FEN y el escenario FEN aparte.
- [x] `respuestas_a_modelos.md`, sección Ronda 4: R4-1 a R4-11.
- [x] Tavily: unos 35 créditos en la ronda 4. Acumulado de Piura Datos: unos 231 de 1200.

## Pendiente al cerrar la ronda 4
- Puntos ANA 2015 (hdl 20.500.12543/2890): el repositorio no respondió.
- Los 4 puntos ANA con unidad ambigua: Territorio los usa como dS/m en `suelos/datos/cew_por_zona.csv`.
- ~~Serie ICEN: met.igp.gob.pe no respondió. Los años FEN se fijaron en 1983 y 1998.~~ Resuelto en la ronda 5: se usa la clasificación ICEN oficial de Territorio (`tools/icen_campanias.py`). El ajuste de periodo de PISCOp en la costa pasa de 1,05 a 1,06-1,48.
- PISCOp de Chusis en marzo de 2017 (886,7 mm), sin contrastar.

## Ronda 5 (cerrada 08:03 UTC)
- temperatura_pisco_zona.csv lista 07:39 UTC (168 filas, PISCOt v1.2 diaria 1981-2020, mismos 7 puntos que POWER; `tools/test_temperatura_pisco.py` PASA). El motor usa esta y no la de POWER. 20 filas de sierra (Ayabaca 7, Huancabamba 13) discrepan con la climatología PISCO 0,05° y lo dicen en notas.
- lluvia_zona_pisco.csv lista 07:43 UTC: 294 filas, PISCOp v2.1 1981-2019, cajas de Territorio, mediana sin El Niño más escenarios moderado y fuerte/extraordinario; `tools/test_lluvia_zona_pisco.py` PASA. ICEN de agosto de 2026 = 3,98 confirmado en la serie oficial del IGP.
- CEw, balance iónico (08:00): QSFran1 5, RPiur4 9,03 y RPiur5 9,92 dS/m como estimado/balance_ionico; QCarn1 sigue desconocido. Se confirma que dividir por 1000 es imposible. Aviso en `aviso_territorio_cew.md`.
- ANA 2015 (hdl 2890): sin acceso por ninguna vía (repositorio con TLS eof y 504, API del handle, Wayback, Tavily). El texto ERH 2015 de Territorio es otro documento. No cargué cifras.
- Rendimientos desconocidos: 75 explicados fila por fila en `anexos/rendimiento_desconocido_explicado.csv` (18 error probable, 17 dudosos, 40 posibles reales). El estado no cambia.
- Pipeline completo reejecutado: `evidencia_observada.csv` 11286 filas (11023 observado, 175 estimado, 88 desconocido). `test_limpiar` 69/69; los tests de temperatura POWER, temperatura PISCOt y lluvia PISCOp PASAN.
- Tavily en la ronda 5: 7 créditos; acumulado 238 de 1200.

## Pendiente al cerrar la ronda 5
- Puntos ANA nov-2015 (hdl 20.500.12543/2890): reintentarlo si el repositorio vuelve.
- QCarn1: no hay cifra fiable; haría falta otro monitoreo del mismo punto.
- Regla de serie para atípicos A4 (40 filas posibles reales), a decidir con Piura Modelos.
- Cloruro impreso como 0,21 y 0,09 mg/L en el cuadro ANA, inverosímil con 2068-6806 mg/L de sales: probable errata del informe. Sin la fuente no se corrige; por eso el balance usa sólo cationes y STD.

## Ronda 6 (cerrada 08:10 UTC)
- CEw reconciliada 08:09 UTC. Con la revisión de Agronomía (H01, H02, H03, H06): QCarn1 3,23 [1,94-3,23] (el 10,4 no tiene respaldo); RPiur4 7,86 [5,56-9,03]; QSFran1 5 y RPiur5 9,92 sin cambio, los dos con error de balance >10 % avisado. Nota H03 en los 4 puntos. Anexo nuevo `anexos/cew_resumen_zona.csv` por zona y tipo de fuente (H06). Aviso reescrito en `aviso_territorio_cew.md`.
- A4: en `modelo/` no hay criterio de atípicos. Propuse la regla de serie en `respuestas_a_modelos.md` (R6-1). Va sólo como marca `posible_real_por_serie` en `anexos/rendimiento_desconocido_explicado.csv`: con √10 da si 30, no 11, no_aplica 34; con factor 1,5 da 19 (la recomendada). El estado no cambia (40/18/17).
- PISCOp validado (`anexos/validacion_pisco_2017.md/.csv`):
  - Marzo 2017 con ±15 % frente a Piura ciudad (481 mm) y Chulucanas (1130 mm), según Rollenbeck et al. 2022. Febrero −52 %.
  - Chusis 886,7 mm: sin cifra pública que lo contraste. Queda desconocido; el orden de magnitud es plausible.
  - Sep-nov: costa casi cero (1-2 mm de diferencia); en la sierra, PISCOp da un 15-35 % menos que la normal.
- ANA nov-2015: un solo reintento, fallido (TLS eof; el handle da 500). No hay segundo monitoreo público de QCarn1.
- Pipeline completo con `cew_resumen_zona`: 72 PASA y 0 FALLA (`test_limpiar` 69/69; los tests de temperatura POWER, temperatura PISCOt y lluvia PISCOp PASAN). `evidencia_observada.csv` tiene 11286 filas: 11023 observado, 176 estimado y 87 desconocido. Log en `/tmp/pipe_r6.log`. Cobertura, fila 2, actualizada.
- Tavily en la ronda 6: 5 créditos. Acumulado 243 de 1200.

## Pendiente al cerrar la ronda 6
- Que Modelos acepte o rechace A4 (recomiendo la variante 1,5); revisar a mano la uva de Las Lomas 2016.
- Que Territorio cargue las cifras finales de CEw en `cew_por_zona.csv`.
- QSFran1 y RPiur5 tienen error de balance >10 % y no tienen rango; decidir si se les da rango (3,97-5,34 y 9,73-12,32).
- Chusis, marzo de 2017: no verificado. ANA 2015: sin acceso.
