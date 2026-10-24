# Propuesta de cambios al CONTRATO (Piura Datos, ronda 2)

No edito `CONTRATO.md`. Esto es lo que pido que se agregue, con el número de filas de `evidencia_observada.csv` (11180 registros, 2026-10-24) a las que afecta cada punto. La columna `zona` con los 7 códigos ya está en el CONTRATO y `tools/limpiar.py` rechaza cualquier otro valor (hay test).

## 1. Unidades nuevas

Hoy `limpiar.py` las deja pasar con aviso y falla con `--estricto` (hay test para cada una). Si se aprueban, paso la lista a la constante de unidades del CONTRATO y `--estricto` deja de fallar.

| Unidad | Filas | Para qué | Por qué no convierto |
|---|---|---|---|
| PEN/kg | 5219 | precio en chacra (DRAP, INEI) | no hay unidad de precio en el CONTRATO |
| ha | 21 | superficies (bajo riego, con sales, con riego tecnificado) | no es convertible a ninguna unidad del CONTRATO |
| m3/ha/año | 15 | dotación y módulo anual | se podría pasar a mm/año (1 mm = 10 m3/ha), pero mm/año tampoco está |
| PEN/t | 6 | costo por tonelada de la ENA 2018 | la fuente lo publica así |
| m3/ha | 5 | agua por campaña | se podría pasar a mm; pido decidir una sola (Modelos punto 2) |
| hm3 | 5 | volúmenes de cuenca o de junta | no es por ha |
| USD/ha | 2 | costo MAD Bajo Piura (Rodríguez Valdez 2025) | falta el tipo de cambio del año de la encuesta; convertir sería inventar precisión |
| PEN/m3 | 1 | tarifa de agua San Lorenzo 2018 | no hay unidad de tarifa |

Propuesta para agua: usar `mm` por campaña y `mm/año` por año, y convertir yo las 20 filas en m3. Hasta que se decida, las dejo como las publica la fuente.

## 2. Valor de zona para "Medio y Bajo Piura"

Siguiendo la instrucción, no asigno esas filas a `medio_piura`, `bajo_piura` ni `piura_region`: quedan con `zona` vacía y la nota "Zona en conflicto". Son **79 filas**:

| Archivo | Filas | Qué son |
|---|---|---|
| compendio_inei.csv | 71 | rendimiento del "CDR Piura" en los compendios INEI 2017 y 2025 |
| ana_agua.csv | 6 | ANA: dotación, eficiencia operativa, área regable, área regada, riego tecnificado y CE de pozos |
| curado_r1b.csv | 1 | disponibilidad hídrica del ámbito de la Agencia Agraria Piura (DRA) |
| curado_r2.csv | 1 | % de superficie con derechos de agua, sistema Medio y Bajo Piura (PGRH) |

Propuesta: agregar el código `medio_bajo_piura`, que solo se usa cuando la fuente junta los dos valles. El modelo decide si lo aplica a ambos o lo descarta. Así la fila deja de perder la zona.

## 3. Estado `asignada`

Dotaciones, módulos y volúmenes de licencia (ANA, junta de San Lorenzo) no son volúmenes entregados. Hoy van como `estimado` con nota, y `limpiar.py` falla si una variable `dotacion*`, `volumen_licencia*` o `modulo_riego*` viene como `observado`. Propongo un cuarto estado, `asignada`, para que el modelo los separe sin leer notas.

## 4. Columna `fuente_primaria`

DRAP e INEI salen del mismo origen (DRA Piura / MIDAGRI-SIEA). Propongo una columna opcional `fuente_primaria` (por ejemplo `MIDAGRI-SIEA`, `ANA`, `encuesta propia`) para no contar dos veces la misma evidencia. Modelos lo pidió en su punto 17 de la ronda 2 y el 4 de la ronda 3.

## 5. Columna `subzona`

Para datos dentro de una zona que el modelo podría querer separar (por ejemplo Tablazo Sur frente al resto del Bajo Piura, zona regulada y no regulada de San Lorenzo). Hoy eso va en `lugar`. Es opcional y de prioridad baja.
