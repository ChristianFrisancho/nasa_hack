# Piura: datos para decisiones de rotación de cultivos

Este repositorio contiene la investigación y los datos de referencia para evaluar cultivos según clima, suelo, agua, nutrientes, plagas, restricciones de la parcela y prioridades del agricultor. Empieza por el [informe agronómico](piura-data/informe_piura_v2.md) y las [reglas del modelo](piura-data/criterios_modelo.md). El [inventario de factores](piura-data/inventario_features.csv) y el [esquema de entradas](piura-data/model_inputs_v2.schema.json) muestran qué debe medir o proporcionar el agricultor.

Los datos incluyen 82 180 registros climáticos diarios NASA POWER de cinco puntos de referencia en Piura (1981–2025), 186 parámetros de cultivo, 42 relaciones de plagas, unidades cartográficas de suelo, 210 escenarios ilustrativos de ETc y 3 232 registros de evidencia recolectada. La [guía del paquete](piura-data/README_PAQUETE.md) explica cada capa y sus límites. Los coeficientes de nutrientes y agua no sustituyen un análisis de suelo, un derecho de riego ni un ensayo en la parcela.

Los flujos activos de n8n son [investigación Tavily semanal](https://moraprix.app.n8n.cloud/workflow/4TeSMeSTACXljaBk) y [fuentes oficiales más NASA diarios](https://moraprix.app.n8n.cloud/workflow/FZuImrDNKPsFj306). Sus exportaciones están en `piura-data/`; para importarlas en otra instancia hay que vincular su propia credencial Tavily y configurar las tablas de datos. No se incluye ninguna clave API. La [guía de operación](piura-data/operacion_v2.md) registra los horarios y los controles de calidad.

Para comprobar los archivos:

```bash
python -m pip install -r requirements.txt
python piura-data/verify_v2.py
```

Los scripts `build_*.py` dentro de `piura-data/` documentan cómo se generaron las tablas de referencia a partir de las fuentes guardadas o citadas. Los CSV distinguen observaciones regionales, parámetros de otras regiones y valores desconocidos; las comparaciones externas aún no están validadas como equivalentes a Piura.
