# Motor de rotación de cultivos · Piura · v1

Herramienta de apoyo a la decisión (NASA Space Apps 2026, «Field Shift»). Recibe una parcela y devuelve qué cultivos anuales y perennes son viables, con motivos y cifras. Cada cifra trae rango, fuente y tipo de evidencia en el formato de `CONTRATO.md`. También compara secuencias de 2 o 3 cultivos.

**Regla central:** si falta un dato, el motor lo marca `desconocido` (valor vacío) y lo propaga o lo usa como rango amplio. Nunca lo cambia por una cifra que parezca exacta. Si ningún cultivo es viable, lo dice.

## Cómo ejecutarlo

Requiere Python 3.10 o superior y `numpy` (Monte Carlo del margen). pytest solo hace falta para las pruebas.

```bash
cd consolidado/motor
python3 -m motor_rotacion ejemplos/bajo_piura_tras_arroz.json                       # texto
python3 -m motor_rotacion ejemplos/bajo_piura_tras_arroz.json --formato json        # JSON completo
python3 -m motor_rotacion ejemplos/bajo_piura_tras_arroz.json --secuencias 3        # compara secuencias de 3
python3 -m motor_rotacion consulta.json --integrar datos_agronomia/motor_integracion.csv --registro registro.tsv
python3 -m pytest -v tests
```

Las salidas de `salidas/` se regeneran con `./scripts/regenerar_salidas.sh` (`--integrar datos_agronomia/motor_integracion.csv datos_repo/evidencia_integrar_r5.csv --secuencias 2 --registro salidas/integracion_registro.tsv`; cada salida trae la sección ESCENARIOS CLIMÁTICOS). `salidas/v0/` guarda las salidas de la v0 para comparar.

Desde Python:

```python
from motor_rotacion import Consulta, evaluar, comparar_secuencias
r = evaluar(Consulta.desde_dict({...}))
print(r.a_texto()); r.a_dict()
secs = comparar_secuencias(consulta, largo=2)
```

## Entrada (JSON)

| campo | qué es | si falta |
|---|---|---|
| `parcela.punto` [lat, lon] o `parcela.poligono` [[lat, lon], …] | ubicación; con polígono se usa el centroide para elegir la zona NASA POWER | obligatorio |
| `parcela.area_ha`, `parcela.provincia` | la provincia elige el rendimiento DRAP de esa provincia; si no hay, usa el del departamento | departamento |
| `suelo.ece_ds_m`, `ph`, `profundidad_cm`, `pendiente_pct` | número = medido; [mín, máx] = estimado; `null` = desconocido | filtro `no_evaluable` |
| `suelo.napa_m` | profundidad de la napa freática en m (número o rango) | desconocida: los umbrales de ECe se aplican como aproximados (FAO-29) |
| `suelo.ece_ds_m` como `{"valor_min", "valor_max", "metodo", "fuente"}` | `metodo`: `pasta_saturada` (por defecto) o `ce_extracto_no_declarado` (CONTRATO.md) | |
| `suelo.psi_pct` | porcentaje de sodio intercambiable | no se evalúa sodicidad |
| `parcela.zona` | alto_piura, medio_piura, bajo_piura, chira, san_lorenzo, sierra_piura | se deduce del distrito; si no, del punto |
| `parcela.distrito` | nombre del distrito, sin importar tildes, mayúsculas ni espacios. Si no hay `parcela.zona`, la zona se saca de `datos_repo/distrito_zona.csv` (copia de `suelos/datos/` de Piura Territorio) y la salida la marca como «deducida del distrito» con su criterio | se usa la zona climática más cercana |
| `suelo.drenaje` | `bueno` / `moderado` / `pobre` | `no_evaluable` |
| `agua.m3_por_mes` | número o {mes: m3} (agua de turno disponible para la parcela) | `no_evaluable` |
| `agua.ecw_ds_m`, `agua.eficiencia`, `agua.intervalo_turno_dias` | salinidad del agua, eficiencia de riego (0–1) | sin eficiencia se compara con riego neto y se advierte |
| `presupuesto_pen`, `cultivo_anterior`, `plagas_presentes` | | `no_evaluable` |
| `escenario` | `sin_el_nino`, `el_nino_moderado`, `el_nino_fuerte_extraordinario` (clasificación ICEN de la campaña). Otro nombre da error con la lista | sin_el_nino. La salida trae además los 3 escenarios (ESCENARIOS CLIMÁTICOS) |
| `mes_siembra`, `horizonte_meses`, `candidatos`, `incorporar_residuos`, `fertilizacion_prevista` {N, P2O5, K2O kg/ha} | | |

Hay ejemplos en `ejemplos/` y sus salidas reales en `salidas/`:
- `bajo_piura_tras_arroz.json`
- `inviable.json` (ningún cultivo viable)
- `salino_sin_datos.json` y `salino_napa_medida.json` (la misma parcela salina sin napa y con napa de 3 m)
- `sin_datos_suelo.json`
- `tablazo_sur_ce_medida.json` (primera CE medida en chacra, ver abajo)

## Qué hace

1. **Clima.** Busca la zona NASA POWER más cercana y toma las campañas del escenario ICEN (ronda 6). Para cada mes saca la mediana y el rango p10–p90 de ET0 y temperatura (POWER) y de la lluvia (PISCOp de la zona; POWER solo si la zona no tiene PISCOp, con aviso). El clima del repo no trae Tmín, así que el límite inferior de EcoCrop se compara con Tmedia y queda anotado.
2. **Filtros.** Corren todos, aunque alguno ya haya descartado el cultivo. Son salinidad, drenaje, pendiente, agua por mes, sanidad, calendario y temperatura, pH, profundidad, presupuesto y normas. Cada uno devuelve `pasa`, `advierte`, `descarta` o `no_evaluable`. Después cada cultivo queda en uno de tres estados:
   - `descartado`: algún filtro lo descarta;
   - `sin_datos`: 2 o más filtros críticos (salinidad, agua, calendario) no se pueden evaluar;
   - `aceptado`: el resto.
3. **Salinidad (regla FAO-29, R4A026).** El umbral de ECe de un cultivo se aplica como exacto solo si se cumplen las cuatro condiciones:
   - la ECe es medida en pasta saturada;
   - la napa está a 2 m o más;
   - el extracto está declarado;
   - el umbral no es un valor por defecto de su clase.
   Si falta alguna, el filtro avisa en vez de descartar y el límite inferior del rendimiento relativo baja un tramo. Si además ECe mín ≥ ECe 50 %, el cultivo queda marcado **«probable no apto»**: se reporta aparte y va al final del orden.
   - Con napa medida a 2 m o más y sin ECe, se estima ECe ≈ 1,5·ECw. Con napa somera o desconocida, esa estimación no se hace.
   - **CE con `ce_extracto_no_declarado`** (CONTRATO.md): no se trata como ECe de pasta saturada. Se toma como cota inferior de la ECe, porque un extracto más diluido da una cifra menor. Nunca descarta, baja otro tramo el rendimiento y pide el método del extracto.
   - **PSI ≥ 15 %** (límite de suelo sódico, USDA Handbook 60): agrega un aviso de sodicidad que no entra en el rendimiento.
4. **pH y profundidad: rampa apto / marginal / no apto** con los rangos óptimo y absoluto de EcoCrop.
   - En la zona marginal la aptitud baja de forma lineal de 1 a 0.
   - Si el pH puede llegar al límite absoluto, avisa. Fuera del absoluto: «probable no apto». Descarta solo con pH medido y umbral local o regional, porque EcoCrop es un rango global de especie.
   - La profundidad del cultivo se compara con la **profundidad efectiva** de la parcela: mín(profundidad física, napa − franja capilar de 0,3 a 0,5 m).
   - Para los parámetros EcoCrop, `DEPR` (profundidad mínima apta) puede descartar y `DEP` (favorable) solo avisa.
5. **Calendario.** Usa la duración y la temperatura de cada mes del ciclo. Además compara el mes de siembra con las **ventanas observadas DRAP 2016-2024** por cultivo y zona (`calendario_siembra_cosecha_piura.csv`). Son ventanas observadas, no recomendaciones:
   - mes fuera de la ventana: aviso «poca experiencia local», no descarte;
   - a un mes del borde: nota;
   - zona sin ventana para ese cultivo: nota.
   Los perennes y los nombres ambiguos («frijol caupi (vaina verde)», «frijol castilla/grano seco») no se asignan.
6. **Normas (reglas de Piura Agronomía):**
   - arroz y drenaje (R4R001/R4R002);
   - Niño costero + parcela inundable + cultivo en campo entre enero y abril (R4R003, cifras FEN 2017 R4A021/R4A022);
   - algodón: campo limpio, socas y chupadera (R4R004–R4R006), ventanas legales por valle (R4A002…R4A015);
   - prohibición de incorporar rastrojo de algodón (R4S001, RM 0251-94-AG Art. 12). El balance de nutrientes lo trata como retirado.
7. **Por cultivo aceptado:**
   - agua por etapa (FAO-56);
   - nutrientes por absorción y exportación;
   - rendimiento DRAP × fracción por salinidad × fracción por agua;
   - margen;
   - qué deja en el suelo y estado del suelo tras la cosecha.
   El margen también se simula con **Monte Carlo** (4000 muestras, factores uniformes e independientes dentro de su rango, semilla fija, no calibrado). Da P10, P50, P90 y P(margen < 0).
8. **Orden de cultivos:**
   1. sin «probable no apto»;
   2. sin pérdida casi segura (P90 < 0);
   3. menos alertas;
   4. cambio de familia;
   5. mayor P10;
   6. aptitud de suelo;
   7. menos agua.
9. **Secuencias.** Cada paso se reevalúa con el suelo actualizado, el cultivo anterior real y el mes siguiente a la cosecha. El orden es:
   1. viables y que caben en el horizonte;
   2. sin pasos «probable no apto»;
   3. **mayor P10 del margen total** (redondeado a 100 PEN);
   4. menos agua;
   5. menor ECe final;
   6. mejor balance P2O5 + K2O;
   7. menos alertas.
   Antes se ordenaban por el punto medio del margen, que premiaba los rangos muy anchos. `clave_secuencia_v0` sigue en el código solo para el test que lo demuestra.
10. **Perennes** (módulo aparte): se evalúa un año en producción.

## Ejemplo real (`ejemplos/bajo_piura_tras_arroz.json`, extracto; salida completa en `salidas/`)

```
MOTOR DE ROTACIÓN v1 · zona climática Bajo Piura (12.0 km) · escenario sin_el_nino (29 años: 1981, 1982, 1984, 1985, 1986, 1988, 1989, 1990…)
Parcela -5.330, -80.680 · área 2.00 ha · ECe 2.00–3.50 dS/m · ECw 0.80 dS/m · pH 7.6 pH · drenaje moderado · anterior arroz · siembra mes 6
Zona CONTRATO: bajo_piura (dada por el usuario) · pendiente usada 1.0 %

12 de 14 cultivos anuales pasan los filtros duros. Primero en el orden: arveja. 1 de los aceptados son PROBABLEMENTE NO APTOS (no se descartan porque el umbral no se puede aplicar como exacto; van al final del orden): piquillo. Sin datos suficientes para decidir (no se recomiendan): frijol de palo.
[…]
3. CAUPI (Fabaceae) · advertencias 2 · no evaluables 0
   Duración: 80–100 días [regional]
   Riego neto por etapa: inicial 30–43 mm | desarrollo 83–116 mm | media 118–172 mm | final 55–94 mm
   Riego neto ciclo: 2 869–4 244 m3/ha · bruto: 4 781–9 431 m3/ha
   Absorción N/P2O5/K2O: 112–291 kg/ha / 21–54 kg/ha / 94–244 kg/ha
   Exportación N/P2O5/K2O: 36–349 kg/ha / 10–70 kg/ha / 21–278 kg/ha
   Rendimiento: 1.10–2.85 t/ha [prediccion] · precio 1.73–3.71 PEN/kg · costo 1 624–6 497 PEN/ha [analogo_externo] · margen -4 601–8 964 PEN/ha [P10 -1 619 · P50 1 100 · P90 4 246 PEN/ha · P(margen<0) 30 %]
   Deja en el suelo: residuo N 17.4–254.4 kg/ha; residuo P2O5 0.0–44.5 kg/ha; residuo K2O 39.0–223.3 kg/ha; leguminosa: posible aporte de N por fijación, cantidad desconocida; no reemplaza N mineral; puede dejar inóculo/plaga para hospedantes: spodoptera; ECe tras cosecha 1.2–3.5 dS/m; balance P2O5 acumulado -69.9–-9.8 kg/ha; balance K2O acumulado -278.1–-21.0 kg/ha
   [!] salinidad: ECe medida 2.0-3.5 dS/m ≤ umbral 4.9 dS/m, pero el umbral no se aplica como exacto (napa freática desconocida); rendimiento relativo 0.90–1.00 fracción con incertidumbre ampliada
   [!] calendario: siembra en mes 6 FUERA de las ventanas observadas en bajo_piura (siembra observada mar; ago-set; cosecha observada jun; nov-dic (frijol caupi; 2016-2024 (9 campañas calendario); confianza 0.6)): poca experiencia local en ese mes; no es un descarte ni una recomendación; Tmedia fuera del óptimo EcoCrop 25.0–35.0 °C en meses [6, 7, 8, 9] (solo nota: sin peso en la decisión)
[…]
Otros aceptados: maiz amarillo duro, algodon, frijol verde, arroz, maiz choclo, zapallo, piquillo
[…]
SECUENCIAS (30 comparadas; se muestran 5)
   orden: viables y que caben → sin pasos 'probable no apto' → mayor P10 del margen (Monte Carlo, redondeado a 100 PEN) → menos agua → menor ECe final → mejor balance P+K → menos alertas
 - arveja → frijol grano: viable · meses 5.8–7.7 meses (cabe: si) · margen -611–5 683 PEN/ha [P10 887 · P50 1 750 · P90 2 752 PEN/ha · P(margen<0) <1 %] · agua neta 7 584–11 278 m3/ha · ECe final 1.20–3.50 dS/m · balance P2O5 -26–-10 kg/ha · K2O -51–-21 kg/ha · N desconocido (kg/ha)
 - frijol grano → arveja: viable · meses 5.8–7.7 meses (cabe: si) · margen -611–4 992 PEN/ha [P10 774 · P50 1 548 · P90 2 414 PEN/ha · P(margen<0) <1 %] · agua neta 7 571–11 215 m3/ha · ECe final 1.20–3.50 dS/m · balance P2O5 -24–-10 kg/ha · K2O -49–-21 kg/ha · N desconocido (kg/ha)
 - arveja → maiz amarillo duro: viable · meses 7.4–9.6 meses (cabe: si) · margen -2 613–9 275 PEN/ha [P10 506 · P50 2 243 · P90 4 199 PEN/ha · P(margen<0) 5 %] · agua neta 9 630–14 833 m3/ha · ECe final 1.20–3.50 dS/m · balance P2O5 -66–-20 kg/ha · K2O -139–-28 kg/ha · N desconocido (kg/ha)
```

**Ronda 4.** La arveja sembrada en junio tiene una Tmáx de 32–37,5 °C en los 4 meses del ciclo. Su TMAX absoluto EcoCrop es 30 °C, así que ahora es «probable no apto» y va al final del orden. El motivo en el JSON:

```
probable no apto: Tmáx (máxima diaria del mes, NASA POWER) sobre el TMAX absoluto EcoCrop 30.0 °C en 4 de 4 meses del ciclo [6, 7, 8, 9] (umbral: al menos el 75 % de los meses, supuesto del motor; EcoCrop es rango de especie, no de variedad local)
```

En la ronda 4 la misma regla mandaba al final a frijol grano, cebolla y piquillo. La primera secuencia pasaba de arveja → caupí a caupí → algodón (P10 3 098 PEN/ha, P(margen<0) 1 %). Entre los cultivos, caupí era primero desde la ronda 3, cuando recibió un costo análogo. Ese costo era de *Phaseolus* (confianza baja), y sembrar caupí en junio queda fuera de las ventanas observadas en Bajo Piura (mar; ago-set). Las dos cosas salen como aviso.

Ojo con la cifra de temperatura. `Tmax_max_C` del repo es la máxima diaria más alta del mes, es decir, el día más caluroso, no la media de las máximas. En julio en Bajo Piura la Tmedia es de unos 22 °C y la `Tmax_max_C` de unos 33 °C. Comparar el día más caluroso contra el TMAX de EcoCrop era una prueba estricta. Desde la ronda 5 la regla grave usa la media de las máximas diarias de PISCOt (ver «Ronda 5»).

**Ronda 5.** Dos cambios mueven este ejemplo:
- La media de las máximas PISCOt de Bajo Piura en junio-setiembre es 25,5–29,3 °C (P10–P90 entre años), bajo el TMAX 30 °C de la arveja. La arveja deja de ser «probable no apto» y pasa al primer lugar (P10 441 PEN/ha). Frijol grano, cebolla y piquillo también salen de la regla térmica. Piquillo sigue «probable no apto», pero por el pH 7,6 (límite absoluto 7,0).
- El costo del caupí fuera de Alto Piura ahora es el análogo de Trujillo (3 249 PEN/ha, ampliado a 1 624–6 497). Su P10 baja a −1 619 PEN/ha y queda tercero, detrás de arveja y frijol grano (P10 11). La caída viene del costo, no de la temperatura: frijol grano le gana por P10 con cualquiera de las dos reglas térmicas.

**Cambio respecto a v0.** En v0 la primera secuencia era arveja → cebolla, con margen −11 026 a 71 201 PEN/ha. Ganaba solo por tener el punto medio más alto. En la v1 pasó a quinta (P10 303 PEN/ha) y desde la ronda 4 ni aparece entre las cinco primeras.

## Caso imposible (`ejemplos/inviable.json`: ECe 14–18 dS/m, napa 0,8–1,2 m, 500 m3/mes, presupuesto 3000 PEN)

```
MOTOR DE ROTACIÓN v1 · zona climática Bajo Piura (3.5 km) · escenario sin_el_nino (29 años: 1981, 1982, 1984, 1985, 1986, 1988, 1989, 1990…)
Parcela -5.450, -80.750 · área 3.00 ha · ECe 14.00–18.00 dS/m · ECw 4.50 dS/m · pH 8.6 pH · drenaje pobre · anterior algodon · siembra mes 9

Ningún cultivo anual evaluado es viable con estos datos. Restricciones a resolver: agua descarta 13 (arroz, maiz amarillo duro, maiz choclo, frijol grano, frijol verde…); presupuesto descarta 9 (arroz, maiz amarillo duro, maiz choclo, frijol grano, algodon…); profundidad descarta 4 (frijol de palo, algodon, piquillo, yuca); calendario descarta 2 (algodon, yuca).
```

Con napa somera la sal ya no descarta, porque el umbral no se puede aplicar como exacto. La marca «probable no apto» queda igual. El caso sigue siendo inviable por agua, presupuesto, profundidad efectiva y calendario.

## Tablazo Sur, Bajo Piura: primera CE medida en chacra (`ejemplos/tablazo_sur_ce_medida.json`)

Fuente: Piura Datos, `restricciones/evidencia_observada.csv`. CE 3,44–8,2 dS/m y PSI 7,3–17,7 % (Mendoza Flores 2025, tesis UCV, hdl 20.500.12692/170594). El método del extracto no está declarado. El punto es aproximado y el resto de datos de la parcela queda desconocido.

```
MOTOR DE ROTACIÓN v1 · zona climática Bajo Piura (2.2 km) · escenario sin_el_nino (29 años: 1981, 1982, 1984, 1985, 1986, 1988, 1989, 1990…)
Parcela -5.400, -80.740 · área 1.00 ha · ECe 3.44–8.20 dS/m · ECw desconocido (dS/m) · pH desconocido (pH) · drenaje desconocido · anterior desconocido · siembra mes 8

12 de 14 cultivos anuales pasan los filtros duros. Primero en el orden: caupi. Sin datos suficientes para decidir (no se recomiendan): frijol de palo.
   [!] salinidad: CE medida (extracto no declarado, tratada como cota inferior de la ECe) 3.4-8.2 dS/m supera el umbral sin pérdida (4.9 dS/m); umbral no exacto (napa freática desconocida; CE de suelo con extracto no declarado: no es ECe de pasta saturada (si el extracto fue más diluido, 1:1 a 1:5, la ECe real es mayor que la cifra)); rendimiento relativo 0.00–1.00 fracción con incertidumbre ampliada; PSI 7.3–17.7 % puede superar 15 % (límite de suelo sódico, USDA Handbook 60): riesgo de sodicidad y mala estructura no incluido en el rendimiento
```

Sin ECw ninguna secuencia de 2 cultivos es viable: no se puede proyectar la ECe después de la primera campaña, y además faltan agua y presupuesto, así que el segundo paso queda `sin_datos`. Desde la ronda 3 el motor no se queda ahí: corre tres **escenarios de agua** explícitos (ECw 0,5 / 1,5 / 3,0 dS/m, etiquetados ESCENARIO, no dato) y dice cuál es el dato que falta:

```
ESCENARIOS DE AGUA abajo. Dato que falta: CE del agua de riego.

ESCENARIOS DE AGUA (la ECw de la parcela es DESCONOCIDA; estos valores son ESCENARIOS, no datos)
   DATO QUE FALTA: CE del agua de riego (ECw, dS/m) de su canal o pozo. Con ese dato el motor usa uno solo.
   Proyección de ECe tras cada cosecha: envolvente entre la ECe previa y 1,5·ECw (FAO-29, régimen permanente).
   Sin escenario (ECw desconocida o solo valor de zona): 0 de 30 secuencias viables
 [ESCENARIO ECw 0.5 dS/m] anuales aceptados 12 · orden: caupi, arveja, frijol grano, frijol verde, algodon, maiz choclo · secuencias viables 29 de 30
     - algodon → caupi: P10 1 641 PEN/ha · P(margen<0) 3 % · ECe final 0.75–8.20 dS/m
     - caupi → algodon: P10 381 PEN/ha · P(margen<0) 8 % · ECe final 0.75–8.20 dS/m
     - arveja → caupi: P10 208 PEN/ha · P(margen<0) 8 % · ECe final 0.75–8.20 dS/m
 [ESCENARIO ECw 1.5 dS/m] anuales aceptados 12 · orden: caupi, arveja, frijol grano, frijol verde, algodon, maiz choclo · secuencias viables 29 de 30
     - algodon → caupi: P10 1 641 PEN/ha · P(margen<0) 3 % · ECe final 2.25–8.20 dS/m
     - caupi → algodon: P10 381 PEN/ha · P(margen<0) 8 % · ECe final 2.25–8.20 dS/m
     - arveja → caupi: P10 208 PEN/ha · P(margen<0) 8 % · ECe final 2.25–8.20 dS/m
 [ESCENARIO ECw 3 dS/m] anuales aceptados 12 · orden: caupi, arveja, frijol grano, frijol verde, algodon, maiz choclo · secuencias viables 29 de 30
     - algodon → caupi: P10 1 641 PEN/ha · P(margen<0) 3 % · ECe final 3.44–8.20 dS/m
     - caupi → algodon: P10 381 PEN/ha · P(margen<0) 8 % · ECe final 3.44–8.20 dS/m
     - arveja → caupi: P10 208 PEN/ha · P(margen<0) 8 % · ECe final 3.44–8.20 dS/m
   El orden de los 3 primeros NO cambia entre escenarios; la viabilidad de las secuencias: 0.5→29 / 1.5→29 / 3→29
```

En Tablazo el valor de la ECw no cambia ni el orden ni la viabilidad: la CE medida (3,44–8,2) domina la envolvente de la ECe proyectada y, con la napa desconocida, los umbrales FAO-29 no se aplican como exactos (R4A026). Lo que bloquea es que falte el dato, no su valor. Con napa medida ≥ 2 m sí cambia (prueba `test_ecw_desconocida_corre_tres_escenarios_etiquetados`).

## Integrar datos de los otros bots

`Catalogo.integrar_csv_contrato(ruta)` (en la CLI: `--integrar archivo.csv`, con `--registro` para guardar qué entró). Lee filas con las columnas de `CONTRATO.md`.
- **Validación por fila** (`validacion.validar_fila_contrato`). Una fila que no cumple no entra y queda en el registro con su motivo. Se exige:
  - columnas obligatorias, incluida `zona`;
  - `fuente` y `url_o_doi`;
  - `tipo_evidencia` y `estado` válidos;
  - mín ≤ valor ≤ máx;
  - unidad dentro de la lista de CONTRATO.md;
  - `dotacion_asignada` solo con `estado=estimado`;
  - `ce_extracto_no_declarado` solo con `estado=observado` y dS/m.
- **Zonas:** alto_piura, medio_piura, bajo_piura, chira, san_lorenzo, sierra_piura, `medio_bajo_piura` (se usa para parcelas de medio o bajo Piura cuando no hay dato de su zona; queda anotado), `piura_region` o vacío (regional).
- **Columnas opcionales** `fuente_primaria` (se suma a la fuente) y `subzona` (va a las notas).
- **Variables que usa el catálogo:** `rendimiento`, `precio_chacra`, `costo_produccion_ha`, `duracion_ciclo`. Una fila reemplaza el dato vigente solo si su `tipo_evidencia` es igual o mejor.
- **Filas de CE de suelo** (por ejemplo `ce_extracto_no_declarado`): son datos de una parcela, no del catálogo. Se ignoran con aviso y se pasan en la consulta (`suelo.ece_ds_m` con `metodo`).
- **Ejemplo:** `ejemplos/integracion_ejemplo.csv` trae filas reales (duración de arroz y caupí INIA). Las filas ficticias de las pruebas están en `tests/datos/`, marcadas FICTICIO y con URL `.invalid`.

Datos de Piura Agronomía (copias con SHA256 en `datos_agronomia/`). Se revisan fila por fila al cargar y el resultado está en `salidas/integracion_registro.tsv`:
- parámetros EcoCrop: 114 aceptados, 24 ignorados por ser cultivos fuera del catálogo;
- costos: 17 aceptados, 4 rechazados por no tener fuente;
- umbrales de salinidad: arveja 3,4 / 10,6 dS/m, y los valores por defecto de clase marcados de menor confianza, que nunca descartan;
- nutrientes de caupí, zapallo y papa, calculados con exportación;
- Kc de mango y papaya (Paredes 2024), marcados «no FAO-56»;
- 19 reglas;
- 43 ventanas de calendario.
- Las reglas categóricas no pasan por la lista de unidades, que es para cifras.

## Ronda 3 (escenarios de agua, evidencia observada, perennes de Agronomía r6)

- **Escenarios de ECw** (`motor.escenarios_ecw`, `reporte.escenarios_a_texto/escenarios_a_dict`). Solo si la parcela no trae ECw; si la trae, se usa la suya y no hay escenarios. Un valor de zona no cuenta como dato de la parcela. En JSON: `escenarios_agua` con `es_dato: false` y `dato_que_falta`.
- **Valores de zona** (`motor.completar_con_zona`). Si falta el dato de la parcela, se usa el de la zona como rango etiquetado «VALOR DE ZONA», con aviso:
  - ECw del río Chira en Sullana 0,373–1,167 dS/m (Coronel Chávez 2021, `medicion_local`; es agua de río, no de canal);
  - pendiente 0–p90 % (mediana p50) de Piura Territorio (Copernicus DEM 30 m, `prediccion`).
- **Contexto regional, solo como aviso:** ECe 4–12 dS/m de la clase dominante del Bajo Piura (FAO/UNALM 1990), napa por SEV mediana 2,3 m [0,6–6] y CE del agua subterránea 0,04–16,8 dS/m (ANA ERH 2015). Nunca reemplazan un dato de la parcela.
- **Costos análogos externos** (`analogo_externo`). El rango se amplía a la envolvente del de la fuente y ×½–×2 (supuesto del motor). El aviso y los faltantes lo dicen. (Hasta la ronda 4 el caupí usaba un costo de *Phaseolus* con aviso de confianza baja; la ronda 5 lo reemplazó por costos de *Vigna*.)
- **HWSD:** el motor no lo usa para ECe. Toda fila de ECe cuya fuente o método mencione HWSD se rechaza al integrar.
- **Zonas:** en todo el motor se usan los códigos de CONTRATO.md. `zonas_aplicables` (separadas por `;`) se acepta en `integrar_csv_contrato`, el calendario y las reglas.
- **Perennes** (`perennes.csv`):
  - Kc de mango Kent (Brasil) amplía la envolvente a 0,73–0,95;
  - Kc 1,12 de banano (Ecuador) cae dentro de FAO-56 y queda como contraste;
  - mango ECe 1,4 = inicio de síntomas, no umbral (el 1,3 por defecto se mantiene);
  - primera producción de banano 0,85–1,2 años en chira.
- Unidad `años` agregada a las extra del motor, igual que `meses`.

## Ronda 4 (regla térmica y zona por distrito)

- **Regla térmica grave** (`filtros.termica_grave`, dentro del filtro calendario). El cultivo es «probable no apto» si la Tmáx pasa el TMAX absoluto EcoCrop, o la Tmín baja del TMIN absoluto, en al menos el 75 % de los meses del ciclo (`FRACCION_MESES_TERMICA`, supuesto del motor). Un mes cuenta solo si todo su rango del escenario queda fuera. Un mes sin dato no cuenta. No descarta; manda el cultivo y sus secuencias al final del orden.
- **Tmín.** El clima del repo no trae Tmín. Como la Tmín nunca supera la Tmedia, un mes con toda la Tmedia bajo TMIN cuenta como frío. Fuera de ese caso, la Tmín sigue en «datos que faltan».
- **Zona por distrito** (`motor.zona_de_distrito`). El orden es: zona del usuario, zona deducida del distrito, zona climática más cercana. El motor no deduce la zona en estos casos y lo dice en el origen:
  - un distrito repetido sin provincia (Salitral está en Morropón y en Sullana);
  - un distrito en `piura_region` (Talara: no es zona de parcela);
  - un distrito que no está en la tabla.
  - Si la tabla marca el distrito como ambiguo, el origen nombra la zona alternativa (Tambo Grande: san_lorenzo, alternativa medio_piura).
- **Comprobación de supuestos.** `test_cada_supuesto_del_motor_esta_en_la_tabla_del_readme` falla si una constante marcada `# supuesto del motor` no está en la tabla de abajo.

## Ronda 5 (costo del caupí, CEw por zona, nombres de variable, arveja, temperatura PISCOt)

Datos de entrada: `datos_repo/evidencia_integrar_r5.csv`, armado por `scripts/extraer_evidencia_r5.py` (93 filas; reemplaza a `evidencia_observada_r3.csv`). Las copias y sus SHA256 están en `datos_repo/SHA256SUMS`.

- **Costo del caupí.** El análogo de *Phaseolus* (ENA 2018) se retiró. En Alto Piura se usa el PEIHAP del GORE Piura: 2 079 PEN/ha (actual) y 3 181–3 184 (optimizada), `regional`/`estimado`. Dos filas de la misma zona y la misma prioridad de evidencia ya no se pisan: el motor arma la envolvente 2 079–3 184 (solo para costos). En las demás zonas se usa el análogo de Trujillo, 3 249 PEN/ha, ampliado a 1 624–6 497 por la regla de `FACTOR_ANALOGO_COSTO`. El aviso de confianza baja ya no existe.
- **CEw.** El agua de canal, reservorio o toma entra como VALOR DE ZONA: San Lorenzo 0,47 (reservorio a canales, UNP c. 2011, estación desconocida), Chira 0,59 (Poechos, ANA octubre 2024, estiaje), Sierra 0,334 (toma de Macará, estiaje). Los 29 puntos de río y quebrada de ANA 2024 (IT 0076-2024 Piura, IT 0074-2024 Chira) y los pozos de tesis UNP (0,13–3,83) solo salen como aviso: no son el agua que llega a la parcela. Medio y Bajo Piura no tienen CEw de canal y siguen con los tres escenarios. QCarn1, QSFran1, RPiur4 y RPiur5 se rechazan al integrar: su unidad está en disputa entre Datos y Territorio, y las estimaciones por balance iónico de Agronomía y de Datos no coinciden. *Ronda 6: ya no se rechazan; ver abajo.*
- **Nombres de variable.** El motor tiene un registro de nombres (`catalogo.variables_conocidas`): los de CONTRATO.md que usa, los de zona, los de CE de suelo y los conocidos que no usa (`dotacion_agua`, `costo_produccion_por_t`). Un nombre fuera del registro se rechaza con un motivo que lista los aceptados. Si empieza por `CE_agua`, `cew` o `ecw`, el motivo pide `ce_agua_riego` con la columna `fuente_agua`. Antes quedaba «ignorada» y la integración fallaba sin decir por qué.
- **Regla R7 de `validar.py`.** Si un archivo trae la columna `zonas_aplicables`, una fila con `zona` vacía la exige, salvo que sea genérica (misma lista de fuentes que `validar.py`, o sin lugar y de tipo bibliográfico, análogo externo o predicción). `medio_bajo_piura` y `piura_region` no valen en `zonas_aplicables`.
- **Arveja.** El umbral sin pérdida es ECe 3,4 dS/m con pendiente de 10,6 %/dS/m (FAO-61). Los cultivares acotan el umbral: SP-290 2,5 y Durana 4,5. Hay advertencia desde que la ECe pasa el umbral de SP-290. El «probable no apto» y el descarte exigen pasar el ECe 50 % del cultivar más tolerante. La alternativa 1,5 / 14 de FAO-56 solo va en las notas, rotulada como estimación (probable corrimiento de fila de FAO-48 T13). La fila de Agronomía con la pendiente 14 (AN0264) se rechaza por su unidad `%/(dS/m)`, que no está en CONTRATO.md. *Ronda 6: CONTRATO.md ya la tiene y AN0264 entra como alternativa rotulada.*
- **Temperatura.** La regla térmica grave usa la media mensual de las máximas diarias de PISCOt 1981-2020 por zona (`datos_repo/temperatura_pisco_zona.csv`, `prediccion`), con su rango P10–P90 entre años. Ya no usa el día más caluroso de POWER. Si la zona trae dos celdas (sierra: Ayabaca y Huancabamba), se usa la envolvente. Sin PISCOt para la zona, el calor no cuenta para la regla grave y queda en «datos que faltan»: no se vuelve al día más caluroso. El aviso por mes con POWER sigue, rotulado «día más caluroso» y con la media PISCOt al lado.

- **Tests.** `conftest.py` manda los `tmp_path` de pytest a `.pytest_tmp/` dentro de `consolidado/motor/`; antes iban a `/tmp/pytest-of-box`.

## Ronda 6 (escenarios climáticos ICEN, lluvia PISCOp, lecturas ANA resueltas, arveja)

Datos nuevos: `datos_repo/lluvia_zona_pisco.csv` (copia de `restricciones/`, 294 filas, Piura Datos) y `datos_repo/evidencia_observada.csv` refrescada. Los SHA256 están en `datos_repo/SHA256SUMS`.

- **Escenarios climáticos ICEN.** Los escenarios `normal`, `el_nino`, `la_nina` y `seco` ya no existen. También se borró `datos_motor/escenarios_enso.csv`, una lista provisional que ya nadie usaba. Ahora hay tres escenarios: `sin_el_nino` (29 campañas), `el_nino_moderado` (1987, 1992, 2017) y `el_nino_fuerte_extraordinario` (1983, 1998, 2016). Las campañas salen de las filas de enero de `lluvia_zona_pisco.csv`. Una campaña va de agosto del año Y-1 a julio del año Y y lleva el nombre Y. Por eso el motor toma el año Y para enero–julio y el año Y-1 para agosto–diciembre (`catalogo.anios_del_mes`). La ET0 y la temperatura de NASA POWER usan esos mismos años, mes por mes.
- **Lluvia.** La costa usa la lluvia de PISCOp por zona; CHIRPS no se usa. En la sierra se toma la envolvente de las subzonas Ayabaca y Huancabamba. Las filas de temporada quedan ignoradas porque el motor trabaja por mes. Resultado: 252 filas aceptadas, 42 ignoradas y 0 rechazadas. Hay un caso de borde en la serie: agosto–diciembre de 2019 entra sin su mitad de enero–julio de 2020. Se tolera porque son años de borde, no un error de la fila.
- **Recomendación por escenario** (`motor.evaluar_escenarios`, `reporte.escenarios_clima_a_texto` y `escenarios_clima_a_dict`, clave JSON `escenarios_climaticos`). Corre la misma parcela en los tres escenarios. Para cada uno da el orden con P10/P50, los aceptados, los descartados con sus motivos, los que quedan sin datos y los cultivos con exceso de agua. Al final dice si el primer lugar cambia entre escenarios.
  - P10 y P50 no cambian entre escenarios. El margen sale de rendimientos y precios DRAP, y el clima no entra en él. Lo que sí cambia entre escenarios son los filtros: calendario, temperatura y exceso de agua.
  - La Tmáx media de PISCOt tampoco depende del escenario: es la serie 1981-2020 completa.
- **Exceso de agua** (`filtros.exceso_agua`, dentro del filtro calendario). Hay exceso cuando la lluvia mediana de PISCOp supera a la ET0 mediana en un mes del ciclo.
  - Con exceso y drenaje que no es `bueno`, el calendario recibe una advertencia por riesgo de anegamiento.
  - Si solo el año más lluvioso supera a la ET0, es «posible exceso»: sale como nota y no pesa.
  - La pérdida por anegamiento citada en `fichas_anuales.csv` va como contexto. Ejemplo: algodón, 59,95 % con hasta 15 días de anegamiento (Tian et al. 2021, `analogo_externo`). Esa pérdida no entra al margen porque la duración del anegamiento en El Niño es desconocida (R4A024).
  - Entre los datos que faltan quedan esa duración y la tolerancia al anegamiento de los cultivos que no la traen. AN0453 y AN0462 se rechazan porque su valor no es numérico (unidad `texto`).
  - Una advertencia no vuelve evaluable un ciclo sin duración. Antes el frijol de palo pasaba de «sin datos» a «aceptado» solo con El Niño fuerte.
- **Aviso ICEN** (contexto, no regla). Cita la nota del escenario fuerte en `lluvia_zona_pisco.csv`: ICEN de agosto de 2026 = 3,98 (serie IGP). El aviso R4A025 de ENFEN, cuando el escenario elegido no es de Niño, pide comparar con `el_nino_fuerte_extraordinario`.
- **Lecturas ANA.** QCarn1 3,23 [1,94–3,23], QSFran1 5,0, RPiur4 7,86 [5,56–9,03] y RPiur5 9,92 dS/m ya no se rechazan. Son estimaciones de Piura Datos (`balance_ionico`, `estimado`) porque la química del informe no cierra. Entran solo como aviso de punto de río o quebrada, nunca como valor de zona. El aviso las nombra con su rango. El máximo del aviso de Medio Piura sube de 5,98 a 9,92.
- **Arveja.**
  - El umbral de estrés reproductivo en floración, 27–32 °C (Osorio et al. 2023, confianza 0,3), se compara con la Tmáx media de PISCOt en los meses de floración, usando el umbral inferior de 27 °C. No se usa el TMAX absoluto de EcoCrop, que es 30. Por defecto da una advertencia. Pasa a regla grave solo si hasta el año fresco (P10) supera 27 °C en el 75 % de los meses de floración.
  - En Bajo Piura la arveja no tiene ventana de siembra observada: la DRAP 2016–2024 registra 0 ha. Sale como alerta, con un test que la fija.
  - La lista de unidades de `validacion.py` se lee de CONTRATO.md, y un test falla si las dos listas se separan. Con eso, AN0264 (pendiente 14 %/(dS/m)) entra como alternativa rotulada, solo en las notas.

Primer lugar por ejemplo y escenario (salidas reales de `salidas/`):

| ejemplo | sin_el_nino | el_nino_moderado | el_nino_fuerte_extraordinario | ¿cambia? |
|---|---|---|---|---|
| bajo_piura_tras_arroz | arveja | arveja | arveja | no |
| inviable | ninguno viable | ninguno viable | ninguno viable | no |
| salino_napa_medida | algodón | algodón | algodón | no |
| salino_sin_datos | algodón | algodón | algodón | no |
| sin_datos_suelo | caupí | caupí | caupí | no |
| tablazo_sur_ce_medida | caupí | caupí | arveja | sí |

En Tablazo el cambio viene de la temperatura, no de la lluvia. En las campañas fuertes, el día más caluroso de agosto según POWER (33,8–40,8 °C) llega al TMAX 40 de EcoCrop, y el caupí recibe una advertencia más en el calendario.

## Supuestos del motor

Cifras que eligió el motor, no un dato con fuente. Cada una sale marcada en la salida donde se usa.

| constante | valor | dónde | por qué |
|---|---|---|---|
| `FRACCION_MESES_TERMICA` | 0,75 | `filtros.py` | «todos o casi todos los meses del ciclo» de la regla térmica grave |
| `VIGENCIA_PRONOSTICO_DIAS` | 60 días | `reglas.py` | tiempo que un comunicado ENFEN cuenta como vigente (R4A025) |
| `FACTOR_ANALOGO_COSTO` | 2 | `catalogo.py` | un costo `analogo_externo` se amplía a [v/2, 2v] |
| `ESCENARIOS_ECW` | 0,5 / 1,5 / 3,0 dS/m | `motor.py` | agua buena, media y salina cuando falta la ECw de la parcela (clases FAO-29) |

## Archivos

- `motor_rotacion/`: el paquete.
  - `cifra.py`: Cifra e intervalos.
  - `catalogo.py`: carga de datos e `integrar_csv_contrato`.
  - `validacion.py`: reglas de CONTRATO.md.
  - `reglas.py`: reglas de Agronomía.
  - `calendario_obs.py`: ventanas DRAP.
  - `incertidumbre.py`: Monte Carlo.
  - `clima.py`, `entradas.py`, `agua.py`, `nutrientes.py`, `estado_suelo.py`, `filtros.py`, `motor.py`, `perennes.py`, `reporte.py`.
- `datos_repo/`: copias de datos del repo nasa_hack.
- `datos_agronomia/`: copias de `cultivos/` (Piura Agronomía), con `SHA256SUMS` y `COPIADO_EN`.
- `datos_motor/`: tablas preparadas para el motor.
- `tests/`: 62 pruebas; `tests/datos/` tiene los CSV ficticios de prueba.
- `ARQUITECTURA.md`: diseño y decisiones.

## Límites conocidos de la v1

- **Monte Carlo:** supone factores independientes y uniformes, así que P(margen<0) es indicativa y no está calibrada.
- **Clima:** no hay Tmín.
- **Costos que faltan:** caupí, frijol verde, frijol de palo y papaya no tienen costo con fuente.
- **Secuencias:** sin ECw no se puede proyectar la ECe entre campañas.
- **Calendario:** las ventanas DRAP son observadas, no recomendaciones, y tienen confianza 0,5–0,6.
- **Tablazo Sur:** el punto es aproximado y la conversión de la CE de extracto no declarado a ECe es desconocida.
