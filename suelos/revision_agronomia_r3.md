# Revisión cruzada de la ronda 3 del agrónomo (rol Piura Territorio)

Fecha: 2026-10-24. Alcance: filas R3A* de `cultivos/fichas_anuales.csv` (169), R3P* de `cultivos/perennes.csv` (97), todo `cultivos/para_motor/` (5 archivos) y `cultivos/motor_integracion.csv` (2 filas). No se modificó nada en `cultivos/`. Tavily: 0 créditos. El detalle está en `revision_agronomia_r3.csv` (mismas columnas que r1).

**27 hallazgos: 6 alta, 11 media, 10 baja.**

## Método
- Comparé cada umbral de salinidad con FAO-29 T5, FAO-56 T23, FAO-61 Anexo 1 y CPIC Appendix I, y busqué ensayos primarios de rendimiento para los cultivos con defecto de clase.
- Recalculé Maas-Hoffman: los ECe_90..0 del agrónomo están bien calculados.
- Contrasté los rangos EcoCrop con el pH de HWSD2 (capas D1/D3 de las SMU de Piura) y con la temperatura mensual del repo, siguiendo la lógica del motor (`catalogo.py:178`, `filtros.py:304-333`).
- Verifiqué Paredes et al. 2024 T6 contra la tabla publicada y FAO-56 T12.
- Rehíce el 25 kg N/ha de caupí desde Herridge 2008 T4.

## 1. Umbrales por defecto de clase
En CPIC, mango, arveja, frijol de palo (forraje), limón, palta y manzana comparten el mismo 1.3/17.5. Papaya, olivo y pallar comparten 6.0/5.6. Son defectos de clase (S, MS, MT), no mediciones. Lo infiero porque cultivos no emparentados tienen valores idénticos; el PDF no lo dice.

| Cultivo | Defecto usado | Evidencia específica | Consecuencia | Veredicto |
|---|---|---|---|---|
| Mango | S 1.3/17.5 | Durán Zuazo 2003: campo, 4 años, umbral 0.88–1.81, pendiente 12.5–17.1 (probablemente ECw) | Rinde 53 % con ECe 4 y 0 % con ECe ≥7: excluye Bajo Piura salino. Es coherente con un mango concentrado en Chira/San Lorenzo. | Aceptable. Falta citar el ensayo y anotar la dependencia del portainjerto. |
| Frijol de palo | S 1.3/17.5 | Keating & Fisher 1985: ECe50 4.9–5.4 (macetas, vegetativo) | ECe50 4.16, algo conservador | Aceptable. No hay datos de grano. |
| Papaya | MT 6.0/5.6 | Subhas Chander 2007: −10 % y −24 % de rendimiento con ECw 4 (ECe ≈6) | MT predice 0 % de pérdida y MS predice −23 % | **Cambiar a MS 3.0/7.7** (alta). |

La política de defectos no es coherente:
- Mango y frijol de palo reciben defecto.
- Banano (S) y yuca no lo reciben.
- La nota de yuca dice que CPIC no tiene umbral, pero CPIC lista "Casava 3.0/7.7".

Hay que decidir una sola regla. Además, los defectos deberían marcarse `analogo_externo`/`es_defecto_clase`, no `bibliografico`.

## 2. Clases en conflicto
- **Banano:** S. Tiene apoyo primario (FAO-61: rendimiento de fruto, Israeli 1986). El MS de FAO-56 no trae umbral ni referencia.
- **Papaya:** MS. Tiene apoyo primario en FAO-61 (Kottenmeier 1983; Makhija & Jindal 1983) y lo confirma el único ensayo de rendimiento encontrado. El MT de FAO-29 es anterior.
- **Arveja:** 3.4/10.6. Tiene apoyo primario en FAO-61 (Cerda 1982). El 1.5 de FAO-56 no tiene referencia y el 1.3 es defecto S. El agrónomo eligió bien.

## 3. Café 1.1 dS/m
No encontré un umbral para café adulto en campo. Solo hay:
- almácigo de Caturra (1.1);
- plántulas de Catuaí de 5 meses en macetas (daño desde ECw 1.2, RBEAA 2006);
- la recomendación comercial de Netafim de no regar con agua de más de 1.5 dS/m (sin revisión por pares).

Debe quedar como advertencia, nunca como descarte. En Piura el café es de sierra con lluvia, así que el impacto es bajo.

## 4. Profundidad: EcoCrop frente a medida
- **Lo que hay hoy:** solo se transcribe DEPR (mínimo absoluto) y el motor lo aplica como descarte duro. DEP (óptimo) se pierde.
- **Datos locales:** no hay ninguna profundidad numérica local. SIAR 584 y la matriz regional tienen el campo vacío, y Montero (Ayabaca) solo da clases cualitativas.
- **HWSD2 ROOT_DEPTH:** es una clase derivada de la unidad de suelo, no una medida. Casi todo Piura queda en clase 1 (>100 cm) salvo LPeu (clase 3). No considera la napa, que en Bajo Piura llega a 2 m o menos.

**Propuesta:** primero la medida local, luego el estudio regional y por último el intervalo HWSD. El requisito EcoCrop nunca reemplaza el estado del suelo.

profundidad_efectiva = min(profundidad física, napa estacional − franja capilar)

Se compara como intervalo [lo, hi] con incertidumbre:

| Caso | Resultado |
|---|---|
| hi < DEPR | Descarta |
| DEPR ≤ profundidad < DEP | Rampa lineal de aptitud |
| lo ≥ DEP | Apto |
| El intervalo cruza un corte | Advierte, con la fracción del intervalo que cumple |

## 5. Caupí ≈25 kg N/ha
Herridge 2008 T4: 0.23 Tg N fijado / 9.2 Mha = 25 kg N/ha.
- Ese valor es 63 % Ndfa × N total del cultivo, que ya incluye la raíz (N aéreo × 1.4).
- Corresponde a rendimientos de unos 0.5 t/ha.
- **Es N fijado total, no N neto que queda en el suelo.**

Con los coeficientes de Embrapa de la propia ronda (101.8 kg N/t absorbido en la parte aérea y 33 kg N/t exportado en grano), a 1 t/ha el balance neto es:

| Manejo del rastrojo | Balance neto |
|---|---|
| Rastrojo retenido | ≈ +31 kg N/ha |
| Parte aérea retirada | ≈ −38 kg N/ha |

Los ensayos de balance en semiárido dan entre +1 y +18 kg N/ha (Namibia, Nigeria).

Correcciones:
- La unidad "/año" es incorrecta: es por campaña (igual en R3A0155-0158).
- Peoples 2009 (30–40 kg N/t MS aérea) da 43–58 kg N/ha con la biomasa de Herridge. Hay que documentar el rango 25–58 según el método.
- No hay medición en Piura. Hay una tesis UNITRU sobre efectividad de rizobios nativos en caupí en Piura; es cualitativa y solo la vi en el buscador.

## Otros puntos
- **pH duro de EcoCrop:**
  - El pH de HWSD2 en la costa es 7.5–8.3. El máximo de adaptación de piquillo (7.0) lo descartaría en todo el valle, aunque Piura produce cerca del 45 % del piquillo nacional (alta).
  - Papaya, cacao y sorgo (máximo 8.0) se cruzan con CMca a pH 8.2–8.3 en San Lorenzo.
  - Los óptimos de limón, papa, maní, soya y cacao quedan fuera en toda la costa. Sirven como penalización suave, no como discriminante.
- **Kc:**
  - La transcripción de Paredes 2024 es correcta.
  - No es un Kc FAO-56: FAO-56 T12 no tiene mango ni papaya.
  - La misma tabla tiene valores "previamente tabulados" para mango que son la mitad.
  - Falta ajustar con la ec. 62, y el clima del repo no trae HR ni viento. Faltan además las etapas.
  - No hay fuente peruana.
- **Unidades:**
  - R3A0137-0139 son heno de caupí etiquetados como exportación de cosecha. No deben mezclarse con el grano.
  - ECw = ECe/1.5 asume una fracción de lavado de 15–20 %.
- **Faltantes:**
  - Nutrientes de papa (pedidos y ausentes).
  - Absorción de zapallo.
  - Ventanas de siembra peruanas.
- **motor_integracion:** R3M0001 sigue en 0.45 aunque el PDF INIA 510 ya se leyó completo por Wayback (148 d).

## Estado de los altos de la r1
`cultivos/respuesta_revision_r1.csv` no existe. Ninguna fila R3 corrige napa/ECe, HWSD frente a FAO/UNALM, AN0460-0464, curvas de Tian, regla de napa en arroz, reglas FEN ni residuos de algodón. Solo el etiquetado de los ECe por defecto avanza en parte sobre el alta 1. Los 8 siguen abiertos.
