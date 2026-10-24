# Piura: factores determinantes y reglas del modelo

Este documento especifica la lógica del modelo; no convierte noticias, datos regionales ni fragmentos web en mediciones de una parcela.

## 1. Filtros duros antes de puntuar

1. **Lista permitida por el agricultor:** recomendar solo especies/cultivares/usos autorizados. Barbecho o cobertura fuera de esa lista requiere una política explícita, no una inclusión silenciosa.
2. **Naturaleza de la decisión:** rotación entre anuales, manejo de cobertura en plantación y reconversión de perennes son problemas diferentes. No recomendar reemplazar una plantación establecida como si fuera un cereal cosechado.
3. **Sanidad y restricciones vigentes:** historial de hospedantes, cuarentenas aplicables a la ubicación, material vegetal y bioseguridad. Conservar fecha/versión de norma; una noticia de 2021 no demuestra vigencia en 2026.
4. **Ventana de cultivo:** fechas de siembra, duración varietal, tiempo de preparación y riesgo térmico/hídrico por fase. La altitud o el nombre de distrito no bastan.
5. **Agua:** oferta legal y físicamente disponible por mes/turno, calidad y capacidad de riego. No basta el total anual de lluvia.
6. **Limitaciones del perfil:** profundidad efectiva y compactación, drenaje, pH, salinidad y sodicidad frente a tolerancias por cultivo y etapa.
7. **Recursos:** presupuesto disponible en cada fecha, mano de obra, maquinaria, semilla, acceso a insumos y comprador. Un margen positivo al final no resuelve falta de caja al inicio.

Si todos los candidatos fallan, el resultado correcto es **ningún cultivo evaluado es viable bajo estas condiciones**, con explicación de qué restricciones habría que resolver. No devolver el menos malo como si fuera apto.

## 2. Comparar entre opciones viables

No hay un ranking universal ni pesos transferibles desde India. En general, las variables que primero cambian la decisión son:

| Variable o conjunto | Por qué determina el siguiente cultivo | Evidencia necesaria |
|---|---|---|
| Agua disponible y calidad por fase | Puede hacer físicamente inviable la campaña | Cuota/turno + clima + balance + EC/SAR del agua |
| Cultivo precedente e historial sanitario | El beneficio de rotar depende de hospedantes y tiempo desde el último hospedante | Registro multianual + diagnóstico local |
| Profundidad efectiva y reserva de agua | Determina el volumen de raíces y amortiguación de periodos secos | Calicata/medición por horizonte, θFC/θWP o estimación calibrada |
| EC, sodicidad, drenaje, pH | Controla establecimiento, absorción y necesidad de correcciones | Análisis de suelo y agua, método y fecha |
| Temperatura, calendario y eventos extremos | El estrés durante floración o establecimiento puede dominar el resultado | Series diarias + fenología varietal + escenarios |
| N/P/K disponible, residuos y fijación | Afecta rendimiento, costo de fertilización y estado que hereda el sucesor | Analítica con método + extracción por uso cosechado + manejo |
| Presupuesto, costos, trabajo y mercado | Decide si la opción es realizable y económicamente sostenible | Datos del agricultor y precios/costos con fecha |
| Erosión y cobertura | Puede excluir cultivos con suelo desnudo en pendientes vulnerables | DEM, pendiente, lluvia, estabilidad y manejo |

No convertir la salinidad o el presupuesto en un término compensable con alto precio si existe una prohibición o imposibilidad real.

## 3. Balances que deben conservarse

- Agua: W_siguiente = W_actual + lluvia + riego neto + capilaridad − ET − escorrentía − drenaje.
- Demanda climática de un cultivo por etapa: ETc_t = Kc_{cultivo,etapa,t} × ET0_t; la necesidad neta de riego depende además de lluvia efectiva, agua utilizable del suelo, ascenso capilar y objetivo de humedad. NASA POWER aporta clima regional para estimar ET0 con un método declarado y altitud contrastada; no proporciona por sí solo Kc, cuota de canal ni lluvia efectiva de la parcela.
- Exportación de nutriente: rendimiento (t/ha) × coeficiente de extracción (kg de elemento/t) + residuos/forraje retirados.
- N total: entradas de fertilizante/estiércol/riego/deposición/fijación − exportaciones − pérdidas. Mineralización es transferencia interna.
- N mineral: aportes disponibles + mineralización − absorción del suelo − inmovilización − pérdidas.
- Fijación de una leguminosa no equivale a N mineral que deja al siguiente cultivo; la cosecha puede exportar gran parte del N.
- P y K no se crean por rotación: se redistribuyen, movilizan o reponen mediante entradas.
- Riego bruto (m³) = riego neto (mm) / eficiencia × área (ha) × 10.
- P ≈ 0,4364 × P2O5; K ≈ 0,8301 × K2O. Identificar unidades de las fuentes.

Una tabla de dosis de fertilización no puede cargarse automáticamente como tabla de extracción. Tampoco una necesidad anual de una rotación como necesidad de cada especie.

## 4. Presupuesto y restricciones temporales

Para cada periodo t: gasto acumulado_t ≤ caja inicial + ingresos acumulados_t + crédito autorizado_t. Además: agua usada_t ≤ agua disponible_t; horas requeridas_t ≤ horas disponibles_t; maquinaria usada_t ≤ capacidad_t.

La lista de cultivos del usuario reduce el universo de búsqueda, pero cada opción todavía debe superar clima, suelo, agua, sanidad y recursos. Preservar estados finales de agua, nutrientes, sales y carbono para no elegir una secuencia rentable que degrade la capacidad de la siguiente campaña.

## 5. Campos que la web no puede inventar

- Presupuesto y acceso real a crédito del agricultor.
- Polígono exacto y área útil del campo.
- Turnos y cuota real de riego, pérdidas y capacidad instalada.
- Historial de tratamientos y residuos de herbicidas.
- Análisis actual de N mineral, P/K disponibles, pH y EC.
- Profundidad efectiva observada, capa compactada y diagnóstico sanitario.

`model_inputs.schema.json` deja explícitos los desconocidos. `null` no equivale a cero ni a ausencia de una restricción.

## 6. Fuentes de suelo y topografía

SoilGrids puede aportar propiedades modeladas por capas e incertidumbre. Su API REST agotó el tiempo de espera en la prueba de esta sesión: no se cargaron valores no obtenidos. Sus profundidades estándar NO son la profundidad efectiva de suelo ni de roca. N total NO es N mineral disponible; no asumir mapas de P y K disponibles.

La pendiente se deriva de un DEM y depende de resolución, proyección y método. Una elevación puntual no proporciona pendiente de parcela. Un raster regional no debe considerarse una calicata. La pendiente y profundidad concreta del campo quedan desconocidas hasta recibir su geometría y fuentes apropiadas.

## 7. Confianza y trazabilidad

Separar:

- documento oficial publicado en una fecha;
- mención de cultivo/plaga en un documento;
- evidencia de presencia local en esa fecha;
- alerta o restricción actualmente vigente;
- observación de la parcela;
- parámetro agronómico transferible después de calibración.

Guardar URL, fecha de publicación y extracción, localidad, cultivar, uso cosechado, etapa, unidad, método y fragmento/página. Un puntaje Tavily mide relevancia de recuperación, no certeza agronómica. Duplicados temáticos no representan experimentos independientes.
