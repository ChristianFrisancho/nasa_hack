# Revisión cruzada ronda 5 (Territorio: clima/suelos/zonas) de la ronda 5 de Agronomía

Revisé las filas R5* de calendario_drap_piura.csv (R5C, 2718 filas), para_motor/calendario_siembra_cosecha_piura.csv, perennes R5P, fichas_anuales R5A, recuperacion_suelo R5S y reglas_rotacion R5R. También comprobé por muestreo respuesta_revision_r1.csv y respuesta_revision_r3.csv. No modifiqué cultivos/. Tavily: 0 créditos.

Hay **23 hallazgos: 3 altos, 10 medios y 10 bajos.** El detalle está en `revision_agronomia_r5.csv`.

## 1. Zonas (distrito → zona)

La tabla de referencia está en `suelos/datos/distrito_zona.csv`. Tiene 65 distritos con columnas ubigeo, distrito, provincia, zona, criterio, fuente, ambiguo, zona_alternativa, zona_agronomo, discrepancia, zona_cajas_suelos, elev_mediana_m, pct_area_lt600m y con_filas_drap.

Método:
- Límites INEI tomados de INGEMMET GEOCATMIN (capa de demarcación).
- Solape con las cajas de suelos.
- Altitud de 14 puntos SRTM90m por distrito (OpenTopoData).
- Ámbito de las juntas de usuarios: JU San Lorenzo, ALA/JU Chira, JU Alto Piura (10 comisiones) y la delimitación ANA del sector Medio y Bajo Piura (RD 1882-2015).

Resultado:
- **9 discrepancias con el agrónomo.** Paimas y Suyo (sierra_piura → san_lorenzo), Veintiséis de Octubre (sin zona → medio_piura) y los 6 distritos de Talara (sin zona → piura_region).
- **Solo Paimas y Suyo afectan datos.** Aportan 65 % de las ha de arroz de la "Sierra" (2016-2024), 15 % del maíz amarillo duro y 19 % del maní. La ventana de arroz de Sierra (ene-feb; ago) es la del valle Quiroz.
- **24 distritos son ambiguos.** Ejemplos: Tambogrande, Bellavista (Sullana), Lancones, Paita, Santa Catalina de Mossa, Yamango, Canchaque, San Miguel de El Faique, Frías y Sapillica. Cada uno lleva su zona_alternativa.
- **Ningún archivo del agrónomo tiene la columna `zona`.** El motor los carga con zona vacía, así que todas las filas valen para toda la región. El calendario para_motor usa texto libre, que el motor traduce por prefijo; funciona, pero es frágil.
- **Autocrítica del lado de suelos.** `consulta_parcela.zona_de` (cajas más la caja más cercana) discrepa de la tabla en 14 distritos: Paimas y Suyo caen en sierra, Santa Catalina y Santo Domingo en alto_piura, y Talara en chira. Conviene asignar la zona por punto en polígono más distrito_zona.csv.

## 2. Pasache: CE 1:1 → ECe

No hay un factor universal; depende de la textura, que el ensayo no reporta en la fila. Ecuaciones publicadas (Spiteri y Sacco 2024, Tabla 4):

| Fuente | Ecuación |
|---|---|
| Zhang et al. 2005 | ECe = 1.79·EC1:1 + 1.46 |
| Sonmez et al. 2008, arena | ECe = 2.72·EC1:1 − 1.27 |
| Sonmez et al. 2008, franco | ECe = 2.15·EC1:1 − 0.44 |
| Sonmez et al. 2008, arcilla | ECe = 2.03·EC1:1 − 0.41 |
| USDA 1954 | ECe = 3.0·EC1:1 |

- **CE final 3.36-3.71 → ECe ≈ 5.9-11.1 dS/m.** Según estas ecuaciones, el suelo "recuperado" seguiría salino para el maíz.
- **La CE inicial (26-42) queda fuera del rango calibrado.** Se mantiene como "no comparable", con el rango anterior solo como orden de magnitud.

## 3. Análogos de Lambayeque

**Mochumí (bajo Chancay, salino-sódico).** Es un análogo válido para bajo_piura, y quizá para el bajo Chira, si el drenaje funciona. No lo es para medio/alto Piura ni para la sierra.

**Olmos (palta).**
- Es desierto arenoso con riego nuevo y gestión empresarial, comparable a la agroexportación de chira, san_lorenzo y medio_piura.
- Los 12 t/ha a 18 meses son el "récord" de un solo fundo. En el mismo artículo, otra empresa proyecta 4-8 t/ha.
- Debe tratarse como techo y nunca aplicarse a sierra_piura.

**Tipo de evidencia.** "regional" es admisible por el CONTRATO (costa norte), siempre que la fila lleve zona y nota de comparabilidad.

## 4. Banano: primera cosecha

PE0015 (9-11 meses) es la edad promedio de las parcelas demostrativas, no la edad a la primera cosecha. La guía de banano orgánico del valle del Chira (Swisscontact 2012, p.23) ubica:
- la cosecha para exportación hacia la semana 48-53 (~11-12 meses);
- la segunda cosecha hacia la semana ~72.

Valor propuesto: 1.0 año (0.85-1.2), regional, zona chira.

## 5. Yuca 0.7 dS/m

Traza: SG99 p.29 cita "Anon. 1976, cited in Hawker and Smith 1982" (Colombia, campo).
- "Anon. 1976" no figura en la bibliografía de SG99 y no pude verificar el original.
- No se sabe si el valor es ECe o ECw.
- Hawker y Smith (invernadero) dan −50 % a 30-50 mM NaCl (≈3-5 dS/m en el agua), lo que contradice 0.7.

Decisión: R5A007 queda solo como alerta (conf 0.2). El umbral central sigue siendo MS 3.0 / 7.7, que ya está en R4N001/R4N002 y en para_motor/umbrales_salinidad_defecto_clase.csv.

## 6. Fidelidad de las respuestas r1/r3

Son fieles en lo sustantivo. Verifiqué:
- AN0018;
- RS001;
- RR001-006;
- R3A0137/0139 y R3A0155/0159;
- los renombres de pH (pH_suelo_absoluto_ecocrop) y de profundidad (profundidad_suelo_favorable_minima) en para_motor;
- los defectos MS de yuca y papaya;
- el filtro continuo de aptitud en catalogo.py.

Excepciones:
- r1 L32 dice que "dos fuentes coinciden" (18 meses frente a 2-3 años), y no coincide.
- r3 H06 da 31/3 corregidos/pendientes; en realidad son 33/1.
- r1 H03 cita un nombre de variable que no existe; los reales son napa_freatica_*.
- r1 M24 llama "datos peruanos" a datos de Lambayeque.
