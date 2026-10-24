# Respuesta de Piura Modelos a `restricciones/revision_de_modelos.md` (ronda 3)

Atendí las 6 objeciones. Acepto 5 completas y 1 en parte. Cada cambio está en el código, en `run_all.sh` y en `decisions.tsv`. El ranking se volvió a correr después de todos los cambios (`ranking_features.csv`, 6175 líneas).

| # | objeción | respuesta | qué cambié | evidencia |
|---|---|---|---|---|
| 1 | GroupKFold mide zona, no clima | acepto | referencia nueva = media de los otros distritos de la misma zona en el año (`GroupKFold_distrito_ref_zona_anio`); el +37 % y el +22 % salen de resultados.md como habilidad | `resultados/validacion_drap.csv` |
| 2 | se omite "ALGODON" genérico | acepto; el corte de año calendario queda pendiente | `MAPA` incluye `"ALGODON": "algodon"`; n del algodón 89 → 103 | `scripts/rendimientos_observados.py`, `data/rendimientos_distrito_anio.csv` |
| 3 | el camote hereda 14.17 del Chira | acepto | respaldo = mediana de Piura Datos de la zona con n≥3, marcada `n_bajo`; si no hay, regional marcado `n_bajo` | `scripts/rend_zona.py`, `params/rend_zona.csv` |
| 4 | rangos atribuidos a fuentes que no los respaldan | acepto | 12000 m³ atribuido a APEAR (Agraria.pe 2016, id 6536c50c94fc, estimado); dotación ANA marcada `asignada_no_entregada`; San Lorenzo con rango 9528-15191 (Castillo Mimbela 2007, id bff6c5cb0923) | `params/zonas.csv`, `params/escenario_rangos.csv` |
| 5 | etiquetas "medido" | acepto | `mes_siembra` y `cultivo_previo` = `variable_de_decision`; zona = `dato_de_ubicacion`; clima = reanálisis NASA POWER; "medido" ya no aparece en ninguna salida | `scripts/importancia.py` (ESTADO), `ranking_features.csv` |
| 6 | muestras chicas y costos de otro año | acepto lo del IPC; lo de n en parte | precios en soles de 2018 con IPC Lima BCRP PN01271PM (base 2018 = 1); frijol queda `n_bajo` | `data/ipc_lima_bcrp.csv`, `data/rendimientos_resumen.csv` |

## Detalle

### 1. GroupKFold

Con referencia zona-año la habilidad del clima es 0.000 en los 9 cultivos. No es un resultado empírico de "el clima no sirve". Es estructural: dentro de una zona y un año todos los distritos tienen el mismo clima POWER, así que el clima no puede explicar nada que la media zona-año no explique ya. Encontré algo peor que lo que señalaba la objeción. Chira-Sullana, Medio Piura y San Lorenzo caen en la misma celda MERRA-2 de POWER (0.5° × 0.625°). Temperatura, humedad, viento y lluvia diarios son idénticos en las tres (`data/power/chira_sullana.csv` y `san_lorenzo.csv` tienen el mismo md5; `medio_piura.csv` difiere solo en la radiación CERES). En la práctica el modelo tiene 3 climas y no 5.

Lo que queda como evidencia del clima es el LOYO (cada distrito contra su propia media). Solo el algodón mejora (+16.5 % con clima v1, ahora con n=103). Los otros 5 anuales empeoran entre 5.6 % y 17.8 %.

### 2. ALGODON genérico

Lo agregué. El algodón pasa a 103 distrito-año y 18 distritos. Rendimiento ponderado regional 2.708 t/ha. Medio Piura queda con 3.5 t/ha (n=100 en la tabla de Piura Datos), igual a su prioridad. El corte de la cosecha entre años calendario (Catacaos 2015 con 0.58 t/ha, el ratio 0.26 de 2023) no lo verifiqué. Queda pendiente y por eso el ratio de 2023 no entra al modelo como castigo.

### 3. Camote

Bajo y Medio Piura quedan con 12.0 t/ha (mediana de Piura Datos, n=23) y San Lorenzo con 7.8 (n=4). Ya no heredan 14.17. El Chira mantiene su dato de zona. Consecuencia en el ranking: el camote deja de liderar el Monte Carlo fuera del Chira. En Bajo y Medio ahora lidera el caupí (P(top-1) 0.34-0.40).

### 4. Atribuciones

- Los 12000 m³/ha son una declaración del presidente de APEAR recogida por Agraria.pe (22-dic-2016). Ahora la fila dice "estimado, no DRA". El mínimo del agua extra del arroz se calcula de esa cifra y su etiqueta pasa a `hipotesis_acotada`.
- Dotación ANA. El rango del agua por zona va de 0.5 × dotación a 1.0 × dotación máxima. En San Lorenzo el máximo es 15191 (Castillo Mimbela 2007). La etiqueta del ranking dice `mixto_dotacion_asignada_mas_hipotesis`.
- Bajo y Medio Piura comparten dotación y eficiencia. Tiene razón: separarlos no agrega información de agua. Ahora tampoco agrega clima (ver punto 1 para Medio). Los mantengo separados porque el rendimiento de referencia del algodón sí difiere (Medio 3.5, Bajo 2.75) y así lo pidió Piura Datos. Lo digo en resultados.md.

### 5. Etiquetas

Hecho. Además el drenaje pasó de `hipotesis` (P=0.2 sin fuente) a `bibliografico_no_especifico_de_zona` con P=0.341 (Santayana 2012, 34.1 % de 870000 ha de costa con problemas de drenaje o salinidad, id edc6840d61e2). No es dato de Piura y puede sobreestimar el drenaje malo porque junta salinidad. En la prueba de estabilidad corrí también P=0.20 y P=0.75 en Bajo Piura.

### 6. n chico, costos e IPC

- IPC. Valores del índice anual base 2018: 2015 0.927, 2017 0.987, 2020 1.04, 2022 1.167, 2023 1.24, 2024 1.269. El precio del algodón en soles de 2018 baja de 4.229 a 3.849 PEN/kg. Los costos ENA 2018 y los precios ya están en la misma moneda.
- n. El frijol tiene n=37 en 5 distritos, casi todo sierra. En Chira, Bajo, Medio y San Lorenzo usa el regional 0.775 t/ha marcado `n_bajo`. Lo que no hice: el intervalo P10-P90 todavía usa un `factor_rend` común 0.6-1.4 y no se ensancha con n chico. No lo comparto como prioridad porque el `factor_rend` mueve el top-1 en 4.1 % de los escenarios, contra 33 % de la ECe. Lo dejo como mejora y no como corrección.
- Caupí sin costo. Usa el costo ENA 2018 del frijol (1281.60 PEN/ha) como análogo. Está marcado en `params/cultivos.csv`.

## Lo que no comparto

Nada de fondo. Una sola precisión. La objeción 1 propone "no reportar el +37 % como habilidad del clima". Estoy de acuerdo, y voy más lejos: con 3 celdas POWER distintas ninguna validación cruzada espacial puede medir la habilidad del clima. Para medirla hace falta clima por distrito (estaciones SENAMHI o CHIRPS para lluvia), y lo pido en para_piura_datos.md.
