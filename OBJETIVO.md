# Objetivo de la noche (24 oct 2026, dado por Christian)

Construir y validar un sistema de apoyo a la rotación de cultivos en Piura. No detenerse en un plan: entregar datos trazables, flujos automatizados, un modelo ejecutable y experimentos que permitan comprobar sus recomendaciones.

## Qué debe hacer el sistema
- Para cada parcela y cultivo candidato, explicar cómo influyen: tipo y profundidad del suelo, textura, drenaje, salinidad, pH, nutrientes disponibles, cultivo anterior, variedad, etapa de crecimiento, agua de riego, lluvias, temperatura, plagas, enfermedades, pendiente y riesgo de inundación o huaico.
- Estimar, con unidades y rangos de incertidumbre, duración del ciclo, demanda de agua por etapa, absorción y exportación de nutrientes, rendimiento y costos cuando existan datos suficientes.
- Después de cada cosecha, actualizar el estado estimado del suelo y del agua. Evaluar cuánto y bajo qué manejo podrían recuperarse sus propiedades (residuos, cultivos de cobertura, enmiendas, descanso), sin inventar un número fijo de días de "recuperación".
- Comparar secuencias de cultivos viables respetando presupuesto, turnos de riego, restricciones sanitarias, calendario, mercado y salud del suelo a largo plazo.
- Tratar los perennes como un problema distinto de la rotación de anuales.
- Validar contra datos observados y modelos de referencia, separando fincas y años entre entrenamiento y prueba. Reportar errores, incertidumbre, cobertura de datos y casos donde ningún cultivo candidato es viable.

## Pregunta que debe poder responder
"En esta parcela, después de este cultivo y bajo estos escenarios climáticos, ¿cuál es la mejor siguiente opción, por qué, qué recursos requiere, qué le deja al suelo y qué datos podrían cambiar la recomendación?"

## Si queda tiempo
Dashboard interactivo con D3.js, muy entendible para gente no técnica. Usar arena para comparar diseños y create-verification-skill para crear una skill que pruebe la app como lo haría un usuario.

## Presupuestos (estrictos)
- Tavily: 3000 créditos en total para todo el equipo. Reparto: Piura Datos 1200, Piura Agronomía 700, Piura Territorio 600, Piura Modelos 100, reserva de Grok Bot 400. Cada bot anota lo que gasta en `creditos_tavily.tsv` (fecha, bot, herramienta, créditos aprox). `tavily_research` (investigación profunda) está permitido, Christian lo autorizó; úsalo para preguntas amplias y anota su gasto, que es alto.
- n8n (moraprix.app.n8n.cloud, plan Pro): usar lo que el plan incluye. Prohibido cualquier cosa que cobre a la tarjeta de Christian: cambiar de plan, comprar ejecuciones extra, nodos o APIs de pago, o credenciales de servicios que facturen.
- Nada de compras, registros con tarjeta ni servicios de pago.

## Reparto
- Piura Agronomía: fichas por cultivo y etapa, reglas de rotación, recuperación de suelo por manejo, perennes aparte.
- Piura Territorio: variables por parcela y campaña (clima histórico y escenarios, suelo, pendiente, inundación, huaico) con incertidumbre espacial.
- Piura Datos: n8n + Tavily, tabla limpia con procedencia, cobertura cultivo × suelo × zona, resultados observados (rendimientos, costos, agua).
- Piura Modelos: pruebas de modelos e importancia de features; balances de agua y nutrientes, filtros duros, validación por finca y año.
- Grok Bot: contrato de datos, integración, motor ejecutable que recibe una parcela y explica, validación final.
