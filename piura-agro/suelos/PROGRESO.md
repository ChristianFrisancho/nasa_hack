# Progreso: suelos y territorio (24 de octubre de 2026, ~07:10 UTC)

## Ronda 1
No hubo entregables (ver `decisions.tsv`, ronda1). Todo lo que sigue es de la ronda 2 en adelante.

## Hecho

### Zonas
`consulta_parcela.zona_de` asigna la zona por punto en polígono de distrito (INEI 2024, obtenido de GEOCATMIN) y la cruza con `datos/distrito_zona.csv`.
- Los 65 distritos coinciden con la tabla.
- Para los 24 distritos ambiguos devuelve también `zona_alternativa`.
- Las 7 cajas de datos coinciden con su zona entre 80 y 97 % del área.
- Todas las tablas por zona usan los códigos del contrato: columna `zona` o `zona_contrato`, más `subzona`.

### ECe, drenaje y Niño 2017
`datos/zonas_ece_drenaje_fen.csv`
- HWSD v2 por zona.
- Rango local del Bajo Piura: 1.2–12 dS/m, sin valor central.
- Áreas inundadas en 2017 (Copernicus EMSR199).
- HWSD ya no es fuente de ECe (pedido de las 07:04): 21 filas pasan a `*_HWSD2_contexto` con el aviso "HWSD contradice CE medida en chacra (fuente: Piura Datos)". `ECe_medida_local` usa la CE de Piura Datos: Chira 0.103 (Sullana 2024), Medio 0.95 (UNP 2013-14), Bajo 3.44–8.2 (Tablazo Sur 2024, 40 predios), Alto 0.46–0.6 dS/m (El Huaro 2021). El extracto no está declarado; si fuera 1:1, la ECe sería 1.8–3 veces mayor. San Lorenzo y la sierra quedan como `desconocido`.

### CEw (agua de riego y napa)
`datos/cew_por_zona.csv` (`scripts/cew_por_zona.py`), con informes ANA de oct-2024 (Piura y Chira) bajados del SIAR Piura a `fuentes/cew/`:
- Poechos, en la salida: 0.59 dS/m. El Chira hasta Sullana: 0.51–0.85. Más abajo (Sojo, El Arenal, Miramar): 1.7–4.98.
- El río Piura en Medio Piura (oct-2024): 0.74–9.92 dS/m. En nov-2015: 1.98–3.32. Cuatro lecturas de 2024 vienen con la unidad mal puesta y se corrigieron (estado `estimado`).
- Alto Piura: 0.35–0.74. Sierra: < 0.45.
- Pozos del Medio y Bajo Piura (ERH ANA, 2014): 0.04–16.83, la mayoría C3, y solo 1 de 18 es apto.
- Reservorio San Lorenzo (agua que entra a los canales Yuscay/Tablazo): 0.47 dS/m, C2S1, RAS 1.9 (lab. UNP, perfil PSI nov-2011; una muestra, fecha exacta no indicada).
- Toma del canal Macará (sierra Ayabaca): 0.334 dS/m (oct-2024), ahora con `fuente_agua=toma`.
- Pozos por tesis UNP (solo resumen; el repositorio UNP no respondió): Cura Mori 0.13–1.12 dS/m (Bajo); Castilla, Progreso Bajo 0.16–3.83 dS/m (Medio).
- Columna `estacion`: 40 puntos en estiaje (oct-nov 2024/2015, sep 2014); 3 sin fecha de mes (desconocida). No hay ninguna medición en avenida.
- Sin cifra: muestras dentro de canal (Biaggio Arbulú, Miguel Checa, Daniel Escobar, Yuscay/Tablazo, Quiroz), drenes, río en el Bajo Piura y pozos del Tablazo Sur, uno por uno.

### Profundidad, napa y pH
`datos/profundidad_ph_por_zona.csv`
- Profundidad física del suelo (HWSD2).
- Napa del Bajo y Medio Piura según sondeos eléctricos verticales (SEV) de ANA 2015: mediana 2.3 m; 20 de 41 SEV con menos de 2 m.
- Criterio FAO 29 de napa (2 m) y franja capilar.
- pH de SoilGrids y HWSD2.

### Pendiente bajo cultivo
`datos/pendiente_por_zona.csv`, con GLO-30 y WorldCover. Método y advertencias en `notas_pendiente.md`.
- Pendiente media: valles costeros 1.2–2.7 %; sierra 17–19 %.

### Clima por zona
`datos/clima_por_zona.csv`
- Fuentes: PISCOp/PISCOt de SENAMHI como referencia, CHIRPS y NASA POWER.
- Periodos: años neutros según ICEN y Niños 1998, 2017 y 2023.
- Hallazgos:
  - POWER sobreestima la lluvia de años normales en Chira, Medio y Bajo Piura entre +93 y +135 %.
  - En el Alto Piura y la sierra, POWER falla en temperatura entre −3.6 y +4.1 °C.
  - CHIRPS subestima la lluvia de los Niño costeros entre −59 y −90 %.

### Consulta por parcela
`scripts/consulta_parcela.py` acepta un punto o un polígono. Las filas de parcela y las filas `zona:*` (ECe, profundidad, pendiente y clima de referencia con el sesgo de POWER) van en formato contrato.

### Consolidado
`suelos_piura.csv` reúne 630 filas validadas contra el contrato (incluye `cew_por_zona.csv` y, desde la ronda 8, `fen_por_zona.csv`). Tiene dos columnas nuevas: `representatividad` (punto, zona o regional) y `campos_faltantes`. Las filas incompletas se listan en `filas_incompletas.csv`.

### Ronda 7: correcciones del coordinador
1. `cumple_napa_2m_FAO29` ahora es categórico: `si`, `no` o `parcial`, con unidad `categoría`, y el texto libre pasa a notas. Medio y Bajo quedan como `parcial`, la sierra como `si`, y Chira, San Lorenzo y Alto vacíos (`desconocido`). Lo corregí en `scripts/profundidad_ph_zona.py`.
2. En `/workspace/piura-agro/creditos_tavily.tsv`, las 12 filas con "Piura Suelos" o "territorio_r6" pasan a "Piura Territorio". Solo cambió esa columna. Este agente suma 228 créditos (el coordinador contaba 227).
3. Las cuatro lecturas ANA 2024 (QCarn1, QSFran1, RPiur4 y RPiur5) **no** se dividieron por 1000. Con los aniones del mismo informe, divididas darían 0.005–0.010 dS/m, lo cual es imposible. El balance de aniones da 3.0, 4.0, 5.6 y 12.3 dS/m, y el mismo control reproduce bien RPiur13 y RPiur6. Ningún CE o CEw del set de suelos pasa de 20 dS/m, y el script ahora lo comprueba.

### Ronda 8 (24-oct)
1. **CEw de las 4 lecturas ambiguas (IT 0076-2024).** Cifras de Piura Datos (precisión de las 08:12, que reemplaza el cierre de las 08:04). Todas `estimado`, `metodo = balance_ionico`, dS/m:
   - QSFran1: 5.0 [3.97–5.34] (error de balance +14,7 %).
   - RPiur4: 7.86 [5.56–9.03].
   - RPiur5: 9.92 [9.73–12.32] (error de balance −11,7 %).
   - QCarn1: 3.23 [1.94–3.23]. El 10,4 impreso no tiene respaldo (harían falta ~104 meq/L de cationes y el cuadro da 19,4); se retiró de todos mis archivos y del ejemplo de Tambogrande.

   Nota común en las 4: el Gráfico 6.7 del informe ANA está en µS/cm y no sostiene el cambio de unidad; lo sostiene el balance iónico (`restricciones/aviso_territorio_cew.md`). `datos/balance_ionico_ana2024.csv` queda como evidencia (`nota_final`: la cifra adoptada es la de Datos). La diferencia entre Agronomía y Datos en RPiur4 no viene del cloruro impreso (0.09 mg/L), sino de usar la suma de aniones (5.56) o la de cationes (9.03).

   **Cruce con `restricciones/anexos/cew_resumen_zona.csv`:** alineado. Los resúmenes de agua superficial usan ahora solo la campaña ANA oct-2024 (2015, Coronel 2021 y PSI2011 quedan como filas `nivel=punto`), la mediana se da con ≥ 2 puntos y RMaca1 (bocatoma en el río Macará) y RChir3 (río Chira bajo Poechos) pasan a `rio`. Resultado: alto río 0.51 (0.345–0.741); chira río 0.868 (0.514–4.98); medio río 5.98 (0.74–9.92); san_lorenzo río 0.449 (0.417–**7.86**); san_lorenzo quebrada 4.115 (3.23–5.0); sierra río 0.280 y quebrada 0.259. **Bajo Piura sin cifra de río.** Diferencias que se mantienen (registradas): san_lorenzo/reservorio 0.47 de PSI2011 (Datos no lo usa) y la napa por pozos en Medio y Bajo (0.04–16.83, de ERH 2014 y tesis UNP), que Datos no resume.
2. **Formato del motor.** Todas las filas de `cew_por_zona.csv` usan `variable = ce_agua_riego`, con el origen en `fuente_agua` y el nivel en `nivel`. En PSI2011 la estación sigue `desconocida`, porque la fuente no da el mes.
3. **Napa del Bajo Piura como distribución.** Mediana 2.3 m, p25–p75 0.6–6.0 m; el 48.8 % de los sondeos queda por debajo de 2 m. El tope de 0–2.0 m ahora solo aplica al sector somero que describe FAO 1990.
4. **Franja capilar con fuente primaria.** Va de 0.25 a 1.06 m (Lohman 1972, USGS PP 708, Tabla 1) y sustituye al 0.3–0.5 m, que no tenía fuente.
5. **Respuesta a Agronomía.** Está en `respuesta_revision_agronomia_sobre_territorio_r1.csv`: 7 hallazgos aceptados, 5 parciales y 2 rechazados.
6. **P3: FEN por zona.** Está en `datos/fen_por_zona.csv` (37 filas; script `scripts/fen_por_zona.py`). Incluye:
   - INDECI: ha afectadas y perdidas por zona en 2017 (IE 607) y 2023 (IE 2186), con cruce por distrito.
   - UNOSAT 2023: área inundada por provincia.
   - INGEMMET: huaicos inventariados por zona.
   - Consistencia con el ICEN: `parcial`.

   Las provincias que figuran en 0 (Piura en 2017, Sechura en 2023) se tratan como falta de registro, no como cero: la zona queda como cota inferior o como desconocida.
7. **P4: incertidumbre.** Se añadió la columna `representatividad`. `filas_incompletas.csv` lista las 145 filas a las que les falta rango, resolución o fecha.
8. **P1, P2 y P5.** No hay cifras nuevas de CEw en avenida, en drenes ni en canales del Medio y Bajo Piura o del Tablazo. Los repositorios ANA y UNP siguen caídos.
9. **Pedido de las 08:20: ce_agua_subterranea.** No queda en ningún archivo de datos de `suelos/`. `cew_por_zona.csv` usa solo `ce_agua_riego` (64 filas; `fuente_agua` ∈ rio, pozo, quebrada, reservorio, canal, dren). Las únicas menciones están en `decisions.tsv`, que es historial de solo añadir.
10. **Pedido de las 08:20: Tablazo Sur, arveja frente a caupí** (`tablazo_sur_ce_orden.md`). La sal solo mueve el orden hacia el caupí (a = 4.9, b = 12). Si el criterio es que la arveja baje del 90 %, el orden se invierte desde:
    - FAO-61: ECe 4.34 (CEw 2.89).
    - FAO-56: ECe 2.21 (CEw 1.47).

    De las 8 ECe de Mendoza 2025 (3.44–8.2; extracto no declarado), se invierten 8 con FAO-56 y 5 con FAO-61. El escenario sí importa para ECe entre 2.2 y 4.3. Hay que medir la ECe en pasta saturada a 0–30 y 30–60 cm, en abril–mayo antes de sembrar, en los 8 sectores de La Unión, con 1 compuesta por predio, más la CEw de la fuente y la napa.
11. **Diferencias que siguen abiertas con `cew_resumen_zona.csv`:**

    | Diferencia | Motivo |
    |---|---|
    | san_lorenzo/reservorio 0.47 (PSI2011) | Datos no lo usa; lo mantengo como `nivel=punto`, con la estación `desconocida`. |
    | Pozos de Medio y Bajo 0.04–16.83 (ERH 2014 y tesis UNP) | Datos no resume los pozos. Se mantiene porque es la única CEw de la napa. |
    | Redondeo: 4.115 frente a 4.12 (san_lorenzo quebrada) y 0.280 frente a 0.281 (sierra río) | Es aritmética, no una diferencia de datos. |

    El resto está alineado: los 4 valores ANA, la campaña oct-2024, RMaca1/RChir3 como `rio` y Bajo Piura sin cifra de río.

## Falla o falta

| Qué | Por qué |
|---|---|
| Recortes de r8 (pedido de las 08:20) | Prioricé la respuesta a Agronomía, Tablazo y PROGRESO. Quedan pendientes: P1/P2, sin cifras nuevas y sin más búsquedas; la regeneración de 6 ejemplos (`/tmp/regen5.log`), que estaba en curso al cerrar; y el reintento de SoilGrids. |
| Extracto de la ECe del Tablazo (Mendoza 2025) | No está declarado. Si fuera 1:1, el orden se invierte hacia el caupí con los dos umbrales. |
| SoilGrids en los ejemplos (24-oct, r8) | rest.isric.org da timeout; la fila `SoilGrids_0_30cm` y sus derivados quedan `desconocido` en los 10 ejemplos. No se rellenan con otra fuente. |
| CEw de dren con cifra (quebrada Sofía, ene-2024) | ANA solo dice que supera el ECA por drenaje agrícola; sin cifra pública. |
| Napa en Chira, San Lorenzo y Alto Piura | Está como `desconocido`: no encontré datos públicos. |
| ECe medida en San Lorenzo y la sierra | Está como `desconocido`. Las otras 4 zonas usan la CE de Piura Datos (extracto no declarado). |
| CEw de canales, drenes y pozos del Tablazo Sur | No hay cifra pública verificable. La tesis del canal Biaggio no se puede descargar, CORE (pozos Sechura-Parachique) pide pasar Cloudflare y el repositorio ANA da error TLS. Sin CEw del Tablazo no se puede proyectar su salinidad. |
| Hosts .gob.pe de ANA, SENAMHI, CENEPRED e IGP | No se alcanzan desde la caja. Usé figshare (PISCO), GEOCATMIN y WebFetch. |
| PISCO en 2023 | Termina en 2019 (lluvia) y 2020 (temperatura). Para 2023 solo hay POWER frente a CHIRPS. |
| SoilGrids REST | Da timeouts intermitentes. Uso el COG y, si falla, la fila queda como `desconocido`. |
| piura_region (Talara) | No tiene caja de datos, así que no hay filas `zona:*`. |
| CEw en avenida (dic–abr) y CEw de drenes | No se encontró ninguna cifra. Ninguna fuente cuantifica el sesgo entre estiaje y avenida (PSI 2011 B.4 solo lo describe). Pistas: ANA/SENAMHI feb-2005 (hdl 20.500.12542/4179) y tesis UNP Barranzuela 2023, ambas en repositorios caídos. |
| FEN 2023 en Sechura | El IE 2186 reporta la provincia en 0 y omite 5 distritos, así que el Bajo Piura de 2023 es solo una cota inferior. UNOSAT da 56 600–60 400 ha inundadas en Sechura. |
| FEN 2017 en el Medio Piura | El IE 607 reporta en 0 la provincia de Piura, así que queda como `desconocido`. Para el área inundada está EMSR199: 1 325 ha. |

## Créditos de Tavily
Se han gastado 229 de 600: 228 hasta la ronda 7 y 1 en la ronda 8 (una búsqueda básica; los 2 extract fallaron y no se cobraron). Todo está anotado como "Piura Territorio" en los dos TSV.
