# Esquema del modelo de rotación (Piura Modelos, ronda 2)

Versión 2 (v2b), 24-oct-2026. La sección "Cambios de la ronda 2" manda sobre el texto de la versión 1 donde choquen. Código en `scripts/`, parámetros en `params/`, todo se reproduce con `bash run_all.sh` (semilla 42).

## Tipos

| objeto | dónde | contenido |
|---|---|---|
| Cultivo | `params/cultivos.csv` | fenología FAO-56 (L, Kc), Zr y p (T22), Ky (T24), umbral ECe y pendiente b (T23), NPK kg/t (FAO PNB16 T29), rendimiento y precio regional (DRAP 2015-2024), costo por ha (ENA 2018), tolerancia a mal drenaje, pendiente máxima. Cada grupo de columnas trae su fuente y su estado |
| Escenario de parcela | `params/escenario_rangos.csv` | lo que se le pide al usuario o se deduce del lugar, con rango y estado |
| Clima | `data/power/<zona>.csv` | NASA POWER diario 2000-2025 (T, Tmax, Tmin, RH, u2, Rs, lluvia, elevación) |
| Demanda de agua | `data/demanda_agua.csv` | ETc, Peff y riego neto por zona × cultivo × año × mes de siembra |

## Funciones

- `agua.et0_pm(df, lat)` ET0 Penman-Monteith FAO-56 diaria.
- `agua.curva_kc(cultivo)` Kc diario por etapas (ini, desarrollo, media, final).
- `agua.p_efectiva(lluvia)` lluvia confiable FAO/AGLW por bloques de 30 días.
- `modelo.evaluar(escenarios)` devuelve rendimiento, margen, viabilidad y el filtro que falla, por cultivo.
- `modelo.ranking(res)` ordena solo los viables. Si ninguno pasa, el top-1 es "ningún cultivo evaluado es viable" (código -1).

## Cálculo por cultivo

1. Agua. Oferta = Peff + riego bruto × eficiencia + 0.5 × TAW × Zr − agua extra (solo arroz, 600 mm, hipótesis por inundación y percolación). ETa = min(oferta, ETc). Yw = 1 − Ky (1 − ETa/ETc) (FAO-33).
2. Sal. Ys = 1 − b/100 × (ECe − umbral) (Maas-Hoffman, FAO-56 T23).
3. Sanidad. Repetir familia botánica resta 10 % al rendimiento (hipótesis; ronda 2 usa `plagas_hospedantes_condiciones_v2.csv`).
4. Rendimiento = rendimiento regional DRAP × factor_rend × Yw × Ys × Ysanidad.
5. NPK. Demanda = rendimiento × kg/t. Oferta N = N mineral del suelo + crédito si el previo es leguminosa. Las leguminosas no piden N. El déficit se divide por la eficiencia de recuperación (N 0.5, P 0.25, K 0.6, hipótesis) y se valoriza con el precio del fertilizante. Como el costo ENA ya incluye la fertilización típica, al margen solo entra la diferencia frente al suelo central.
6. Margen (PEN/ha) = rendimiento × precio en chacra × factor_precio − costo ENA × factor_costo − delta de fertilizante.

## Filtros duros (van antes del margen)

| filtro | regla | estado del umbral |
|---|---|---|
| salinidad | Ys < 0.5 (pérdida > 50 %) | umbral y pendiente medidos (FAO-56 T23); el corte en 50 % es hipótesis |
| agua | Yw < 0.5 | Ky de FAO-56 T24; el corte es hipótesis |
| drenaje | drenaje malo y cultivo que no lo tolera (solo arroz lo tolera) | hipótesis |
| pendiente | pendiente > máximo del cultivo (arroz 1 %, resto 8 %) | hipótesis |

Un cultivo que no pasa un filtro no se rankea aunque su precio sea alto. La sal y el agua no se compensan con precio, como pide `criterios_modelo.md`. Un dato faltante no se trata como cero. Hoy el modelo usa el valor central del rango y lo marca. En la ronda 2 debe propagar el rango completo y reportar el intervalo del margen.

## Cambios de la ronda 2

| pieza | dónde | qué hace | fuente o estado |
|---|---|---|---|
| zonas | `params/zonas.csv` | 5 zonas (Chira-Sullana, Bajo, Medio y Alto Piura, San Lorenzo) con dotación ANA m³/ha y eficiencia operativa | ANA PGRH Chira-Piura p.155 |
| agua de riego | `modelo.rango()` | agua_riego_mm = dotación × fracción U(0.5, 1.0); eficiencia U(0.6·ef, ef) | dato de zona + hipótesis de fracción |
| agua del arroz | `modelo.evaluar()` | riego en parcela = agua_arroz_m3_ha / 10, sin eficiencia; extra 150-780 mm | ESCO arroz Piura 2024 (10000-18000 m³); FAO Irrigation Water Needs |
| rendimiento por zona | `params/rend_zona.csv`, `scripts/rend_zona.py` | producción/cosecha DRAP por zona; regional si hay < 5 distrito-año o < 200 ha | DRAP 2015-2024 |
| sanidad | `modelo.evaluar()` | castigo pen_sanidad U(0.05, 0.20) solo si previo y candidato comparten agente | `plagas_hospedantes_condiciones_v2.csv`; magnitud hipótesis |
| costos | `params/escenario_rangos.csv` | factor_costo U(1.0, 2.11) sobre ENA 2018 | ESCO 1.67×, LATAM maíz 2.11× |
| intervalo | `scripts/intervalo.py` | 20000 sorteos por zona y mes; P10/P50/P90, P(viable), P(top-1), P(ninguno) | semilla 42 |
| escenario central | `scripts/central.py` | top-3 con valores centrales por zona y mes | prueba del motor |
| adversarial | `scripts/adversarial.py` | fija un supuesto a la vez y mide el cambio de ganador | `resultados/adversarial.csv` |
| perennes | `scripts/perennes_agua.py` | riego neto FAO-56 de banano, limón y uva contra la dotación; fuera del ranking | mango sin Kc |
| eventos | `scripts/validacion.py` | ICEN, lluvia dic-abr y días cálidos feb-abr en la validación | empeoran LOYO, no entran al modelo |

En el paso 1 del cálculo, para el arroz la oferta es Peff + agua_arroz_m3_ha/10 + 0.5·TAW·Zr − agua_extra_arroz_mm. Para el resto es Peff + agua_riego_mm × eficiencia + 0.5·TAW·Zr. El castigo por familia de la versión 1 ya no existe.

## Qué se le pide al usuario y qué sale de la ubicación

| feature | origen | permutación v2 (v1) | ablación v2 (v1) |
|---|---|---|---|
| CE del suelo (ECe) | usuario (análisis) o mapa | 43.0 % (33.1) | 39.2 % (34.4) |
| drenaje / napa freática | usuario | 29.8 % (25.5) | 18.5 % (15.9) |
| agua de riego por campaña | usuario, junta de usuarios o dotación ANA de la zona | 15.4 % (35.2) | 11.3 % (25.8) |
| eficiencia de riego | usuario o ANA por zona | 11.0 % (10.0) | 8.4 % (8.4) |
| mes de siembra | usuario | 8.9 % (6.9) | 9.6 % (7.7) |
| año climático | ubicación (POWER) | 7.5 % (6.0) | 5.6 % (4.5) |
| costo de producción | usuario o ENA/ESCO | 6.8 % (4.0) | 11.4 % (3.4) |
| rendimiento esperado | historial del usuario o DRAP por zona | 6.8 % (3.6) | 5.0 % (2.7) |
| textura del suelo (TAW) | usuario o mapa | 5.9 % (3.9) | 4.6 % (3.0) |
| precio esperado | DRAP o mercado | 5.2 % (2.7) | 3.9 % (2.0) |
| pendiente | usuario o DEM | 5.1 % (0.3) | 13.2 % (0.8) |
| cultivo previo | usuario | 0.5 % (2.5) | 0.7 % (1.6) |
| P, N, K del suelo | análisis de suelo | 1.5, 0.9, 0.3 % | 1.4, 0.9, 0.2 % |

Las ETc y la lluvia efectiva salen de la ubicación (POWER + FAO-56). Lo demás debe pedirse.
