# Revisión de Piura Datos al modelo (ronda 2 de Modelos)

Revisé `modelo/resultados.md` (ronda 2), `scripts/validacion.py`, `scripts/rendimientos_observados.py`, `params/rend_zona.csv` y `params/escenario_rangos.csv`. Solo leí; no cambié nada. Las objeciones van de mayor a menor efecto en el ranking.

## 1. El +37 % (camote) y el +22 % (arroz) de GroupKFold miden la diferencia entre zonas, no el clima

En `validacion.py` (GroupKFold por distrito):
- la **referencia** es la media de los otros distritos en el mismo año, sin zona;
- el **modelo** es un Ridge con el clima POWER y ANO.

POWER tiene una serie por zona, así que dentro de un año las variables de clima solo toman 5 valores. Eso equivale a codificar la zona.

El camote de sierra rinde unas 3 t/ha y el del Chira unas 16 t/ha (pregunta 7 de `respuestas_a_modelos.md`). Cualquier variable que separe zonas le gana a una media sin zona. El arroz pasa lo mismo: sierra 5,0 frente a costa 7,9-9,2 t/ha de mediana.

El LOYO, que sí compara contra el propio distrito, da negativo en los 6 anuales salvo algodón (+4,5 %). Además la referencia de GroupKFold usa rendimientos del mismo año. Eso no es fuga hacia el modelo, pero vuelve injusta la comparación en las dos direcciones.

**Propuesta:** usar como referencia la media de la zona en ese año (o en los otros años) y no reportar el +37 % como habilidad del clima.

## 2. Se omite "ALGODON" (genérico) del DRAP

`rendimientos_observados.py` solo mapea "ALGODON PIMA". El DRAP tiene además "ALGODON": 242 filas, 3404 ha cosechadas y 8841 t en 2015-24, sobre todo en las provincias de Piura (2920 ha) y Sechura (421 ha). En mis datos los dos van juntos, con una nota.

El algodón de la validación (n = 89, 18 distritos) y el de `rend_zona.csv` quedan cortos.

Aparte, la cosecha de algodón cruza el cambio de año y el DRAP se agrega por año calendario. Algunos distrito-año dan valores raros, como Catacaos 2015 con 0,58 t/ha. El ratio de 0,26 de 2023 puede estar exagerado por ese corte. No lo verifiqué; merece revisarse antes de usarlo como castigo de evento.

## 3. El camote del Medio y Bajo Piura y de San Lorenzo hereda 14,17 t/ha del Chira

En `rend_zona.csv`, bajo_piura, medio_piura y san_lorenzo caen al regional ponderado de 14,17 porque tienen menos de 5 distrito-año o menos de 200 ha. Ese regional lo domina el Chira, con el 73 % del área cosechada de camote.

En San Lorenzo, el dato de la zona (n = 4, 65 ha) es 7,75 t/ha, la mitad del valor que usa el modelo. La regla de respaldo infla el camote unas 1,8 veces en San Lorenzo.

**Propuesta:** como respaldo, usar el regional de costa sin Chira, o el dato de la zona marcado como "n bajo", en vez del regional completo.

## 4. Rangos atribuidos a fuentes que no los respaldan

- `escenario_rangos.csv`, fila `agua_extra_arroz_mm`, dice "~12000 m3/ha (Agraria.pe 22-dic-2016, dato DRA)". No es dato de la DRA: es una declaración del presidente de APEAR recogida por la prensa. Además es ambiguo si "anuales" significa por año o por campaña. Si es anual con dos campañas, el mínimo del rango de agua extra baja.
- La dotación ANA es **asignada**, no entregada.
  - En San Lorenzo choca con otra fuente: el PGRH da 9528 m3/ha/año y la tesina de Castillo Mimbela (2007) da 15191, con 578,4 hm3 para 38550 ha.
  - La tesina dice que esa dotación "en la práctica no es utilizada".
  - "Dato de zona + hipótesis" es una etiqueta generosa para el agua.
- `bajo_piura` y `medio_piura` usan la misma dotación (11472) y la misma eficiencia (0,57) porque el PGRH no los separa. Separarlos en el modelo no agrega información de agua: solo cambia el rendimiento de referencia.

## 5. Etiquetas "medido" en variables que no se midieron

En la tabla 1 de `resultados.md`, `mes_siembra`, `anio (clima)` y `cultivo_previo` figuran como "medido":
- `mes_siembra` y `cultivo_previo` son opciones de escenario, no mediciones;
- solo el clima POWER es un dato, y es un reanálisis satelital por zona (prediccion o regional en nuestra escala), no una medición local.

Propongo la etiqueta "variable de decisión" para las dos primeras y "reanálisis" para el clima. El `taw_mm_m` ya está bien etiquetado como bibliográfico.

## 6. Muestras chicas y costos de otro año

- Frijol: n = 37 con 5 distritos; en los datos DRAP casi todo el frijol es de sierra (Huancabamba, Ayabaca y Morropón). Camote: n = 52 con 12 distritos. Algodón: 89 con 18. Con 10 años y 2 eventos (2017 y 2023), cualquier modelo anual se sobreajusta, como ya dice la sección 5. El intervalo P10-P90 debería reflejar ese n.
- Los costos son de la ENA 2018. Para caupí no hay costo, y MAD, algodón, frijol y camote son de costa, de Perú o de Lambayeque, no de Piura. Se combinan con precios DRAP de 2015-24 sin deflactar. 2021-22 tiene precios de algodón de 5,6-6,0 PEN/kg frente a 2,5-3,9 en otros años. Un costo fijo de 2018 contra esos precios infla el margen de 2021-22.

**Propuesta:** comparar en soles constantes (IPC) o limitarse a márgenes del mismo año.
