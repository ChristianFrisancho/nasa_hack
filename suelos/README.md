# Suelos y territorio – Piura (NASA Space Apps 2026)

Carpeta del investigador de suelos y territorio. Todas las tablas usan el formato de `../CONTRATO.md`. Las columnas extra (`resolucion`, `subzona`, `tabla_origen`, `zona_contrato`) van al final.

## Entregables

| Archivo | Qué es |
|---|---|
| `suelos_piura.csv` | Tablas por zona consolidadas (593 filas). Se genera con `scripts/consolidar.py`. |
| `datos/zonas_ece_drenaje_fen.csv` | ECe, drenaje, napa e inundación por Niño (FEN) por zona (92 filas). HWSD queda solo como contexto (`*_HWSD2_contexto`); la ECe preferente es la CE medida en chacra de Piura Datos (`ECe_medida_local`). |
| `datos/cew_por_zona.csv` | CE del agua de riego y de la napa por zona y fuente (río, quebrada, reservorio, toma, pozo; canal y dren sin dato), con columnas `fuente_agua` y `estacion` (estiaje/avenida/desconocida) y filas `punto`, `resumen` y `sin_dato` (66 filas). |
| `datos/profundidad_ph_por_zona.csv` | Profundidad efectiva, napa (FAO 29) y pH por zona (62 filas). |
| `datos/pendiente_por_zona.csv` | Pendiente en tierras de cultivo (GLO-30 × WorldCover) (42 filas). |
| `datos/clima_por_zona.csv` | Lluvia y temperatura PISCO, CHIRPS y POWER, con sesgos en años normales y en los Niño 1998, 2017 y 2023 (336 filas). |
| `datos/clima/clima_por_zona_series.csv` | Serie anual por zona, producto y temporada. |
| `datos/distrito_zona.csv` | Tabla de 65 distritos → zona, con `zona_alternativa` para los ambiguos. |
| `datos/limites/distritos_piura_inei.geojson` | Límites INEI 2024 obtenidos de GEOCATMIN (65 distritos). |
| `datos/peligros/cenepred_riesgo_inundacion_piura.csv` | Riesgo de inundación CENEPRED por distrito, con zona. |
| `fuentes_datos.md` | Fuentes con resolución, acceso, tipo de evidencia e incertidumbre. |
| `notas_pendiente.md` | Método y advertencias de pendiente. |
| `decisions.tsv` | Registro de decisiones. |
| `creditos_tavily.tsv` | Gastos de Tavily. |

## Consulta por parcela

```bash
.venv/bin/python scripts/consulta_parcela.py --nombre sullana --lat -4.90 --lon -80.68
.venv/bin/python scripts/consulta_parcela.py --nombre mi_parcela --poligono ejemplos/parcela_bajo_piura.geojson
```

Genera `ejemplos/<nombre>.csv` en formato contrato y `ejemplos/<nombre>.json`. Cada fila indica si el valor es de la parcela (SoilGrids, HWSD, GLO-30 o POWER en el punto) o de la zona (`zona:*`, tomado de las tablas de arriba). El módulo `agua` trae la CEw de la zona (`zona:CE_agua_riego_*`, `zona:CE_agua_napa_pozo`). La ECe de HWSD sale como `ECe_0_20cm_HWSD2_contexto` con el aviso de que contradice la CE medida en chacra.

La zona se asigna por punto en polígono de distrito (INEI), cruzado con `distrito_zona.csv`. Si el distrito es ambiguo, se devuelve también `zona_alternativa`. Fuera de los polígonos se usa la caja más cercana y se marca `dentro=False`.

## Regenerar

Cada script se puede volver a correr sin dañar los resultados anteriores:

1. `scripts/chirps_cajas_zona.py` (con caché)
2. `scripts/clima_por_zona.py`
3. `scripts/pendiente_por_zona.py`
4. `scripts/profundidad_ph_zona.py`
5. `scripts/zonas_ece_drenaje_fen.py`
6. `scripts/ece_preferir_medida.py` (siempre después del 5: degrada HWSD a contexto y carga la CE de Piura Datos)
7. `scripts/armonizar_zonas.py`
8. `scripts/cew_por_zona.py` (usa `consulta_parcela.zona_de`; correr con `.venv/bin/python`)
9. `scripts/consolidar.py`

Los datos crudos grandes están en `datos/*/raw/` y `datos/hwsd2/`.
