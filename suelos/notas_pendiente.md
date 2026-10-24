# Notas sobre la pendiente

**Datos:** `datos/pendiente_por_zona.csv` (42 filas; script `scripts/pendiente_por_zona.py`) y la pendiente de punto o polígono en `scripts/consulta_parcela.py`.

## Método
- DEM Copernicus GLO-30 (1″, ~30 m; adquisición 2011-2015) leído desde el S3 público. La pendiente se calcula con el método de Horn (3×3) en %.
- Máscara: píxeles de cultivo de ESA WorldCover 2021 (clase 40), remuestreados a la malla del DEM por moda, dentro de cada caja de zona.
- `valor` = DEM sin suavizar. `valor_min`/`valor_max` = rango entre ese valor y el del DEM suavizado 5×5. El suavizado es un análisis de sensibilidad al ruido, no un intervalo de confianza.

## Resultados (cultivo WorldCover dentro de cada caja)
| Zona (caja) | Media % | p90 % | % área >2 % (suavizado) | % >5 % | % >15 % |
|---|---|---|---|---|---|
| chira (Valle del Chira) | 1.5 | 3.0 | 20.7 (12.1) | 2.9 | 0.2 |
| san_lorenzo | 2.7 | 5.1 | 52.2 (35.6) | 10.4 | 0.2 |
| medio_piura | 1.8 | 3.8 | 33.7 (22.4) | 4.7 | 0.0 |
| bajo_piura | 1.2 | 2.6 | 15.9 (4.5) | 2.8 | 0.1 |
| alto_piura | 1.8 | 3.9 | 27.8 (16.1) | 5.7 | 0.3 |
| sierra_piura (Ayabaca) | 16.7 | 30.3 | 98.6 | 89.6 | 51.2 |
| sierra_piura (Huancabamba) | 19.0 | 33.1 | 99.1 | 95.1 | 60.3 |

## Advertencias
1. **El ruido del DEM en terreno plano infla la pendiente.** GLO-30 tiene ~1-2 m de ruido vertical. Con 30 m de paso, 0.5 m de ruido ya equivale a ~1.7 % de pendiente aparente. En los valles costeros, los % de área >2 % son una cota superior; la versión suavizada se acerca más a la realidad (el Bajo Piura pasa de 15.9 % a 4.5 %).
2. **GLO-30 es un modelo de superficie (DSM), no de terreno.** Frutales, bordos, canales y edificios suman relieve.
3. **WorldCover clase 40 no capta bien los frutales ni la sierra.** El mango y el limón pueden figurar como árboles (clase 10), y en la caja Sierra Ayabaca solo hay ~614 ha clasificadas como cultivo, así que la muestra de sierra es pequeña.
4. **Las cajas no coinciden con los distritos.** Entre el 80 y el 97 % del área de cada caja cae en distritos de su misma zona (`datos/distrito_zona.csv`).
5. **Pendiente de parcela.** Para una parcela, usar la de `consulta_parcela.py`. La de zona es contexto.
