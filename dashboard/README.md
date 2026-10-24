# Dashboard interactivo «Raíz»

El tablero usa **D3.js 7.9** para comparar márgenes P10–P50, demanda de agua por etapa y exportación estimada de nutrientes. Está escrito en HTML, CSS y JavaScript estáticos: no requiere cuentas, API ni compilación.

**Sin instalar nada:** descarga [`standalone.html`](standalone.html) desde GitHub (botón «Download raw file») y ábrelo con doble clic. Incluye D3, estilos, los seis ejemplos y el CSV completo comprimido dentro del mismo archivo. La fuente GitHub debe descargarse: la página `blob` muestra el código, no ejecuta HTML.

Para usar la versión modular desde la **raíz del repositorio**:

```bash
python -m http.server 8000
```

Abre `http://localhost:8000/dashboard/`. Debe servirse desde la raíz porque la sección «Datos y fuentes» lee `piura-agro/consolidado/piura_super_dataset.csv` bajo demanda. Abrir `index.html` directamente con `file://` no permite cargar los datos en la mayoría de los navegadores.

## Qué muestra

- Seis parcelas **de ejemplo**, 84 alternativas evaluadas y 36 fichas resumen de cultivos. Cada perfil despliega además sus registros agronómicos con variedad, etapa, lugar, valores/rangos, tipo de evidencia, estado, confianza, método, fecha y fuente. Las fichas originales incluyen datos estimados, observados y desconocidos; no se mezclan especies solo por parecerse de nombre.
- El catálogo DRAP muestra 80 etiquetas de cultivos con cosecha registrada durante 2015–2024, rendimiento, área cosechada, producción y precio en chacra cuando están disponibles. Son etiquetas literales del registro, no 80 especies únicas: las filas se mantienen separadas y solo se enlazan con perfiles cuando el nombre común identifica el cultivo con suficiente certeza. De los cultivos del motor, 14 se comparan como rotaciones anuales y 7 como sistemas perennes; los demás registros DRAP se presentan como producción local y no como recomendaciones automáticas.
- La sección **Suelos** lista las seis unidades del mapa histórico de Bajo Piura (Entisoles y Aridisoles), las 27 asociaciones cartográficas unidad-pendiente, seis clases de capacidad de uso de Montero y datos regionales disponibles por zona. Añade 22 combinaciones CUM de tres mapas de cuenca (Chira, Piura y Huancabamba, 2008). La CUM describe usos y limitaciones; no es una clase taxonómica ni un análisis de parcela. Las clases de Montero tampoco son tipos taxonómicos ni cubren toda la sierra. El cruce con cultivos muestra límites y vacíos de evidencia; no declara aptitud cuando falta medición de campo.
- “Árido” describe el clima; “arenoso”, “salino”, “mal drenado” o “agrietado” describen propiedades distintas del suelo. El tablero separa estas condiciones de los nombres taxonómicos. Las grietas no se atribuyen a una parcela sin identificar arcillas expansivas y observar el perfil en campo.
- El primer puesto del motor y los diez filtros separados en **pasa, alerta, sin evaluar y descarta**. El detalle técnico y la fuente están dentro de cada filtro.
- Margen P10 y P50, agua, duración, rendimiento, exportación de N/P₂O₅/K₂O, balance posterior modelado, escenarios El Niño y secuencias.
- El CSV completo de 17 150 filas se carga solo si la persona abre «Datos y fuentes». Puede buscar y filtrar sin confundir un resultado estimado con una medición.

La arveja tras arroz en Bajo Piura aparece con sus alertas térmicas y su ausencia en las siembras DRAP del llano. El primer caupí del Tablazo muestra margen P50 negativo y una advertencia explícita. Un ejemplo sin opciones viables muestra «ninguno viable».

`data/dashboard.json` es una instantánea derivada de las tablas del motor, registros DRAP, `piura-agro/cultivos/fichas_anuales.csv`, `piura-agro/cultivos/perennes.csv`, cartografía del SIAR Piura y la microzonificación de Montero. `piura-data/suelos_cum_cuencas_v1.csv` conserva la transcripción de leyendas y áreas de los mapas CUM de 2008, con URL y alcance de clasificación por fila. Tras actualizar esas fuentes, regenera la instantánea con:

```bash
python dashboard/build_data.py
```

El script falla si las 84 alternativas del CSV dejan de coincidir con las salidas del motor. D3 se guarda localmente en `vendor/` bajo licencia ISC (véase `vendor/LICENSE`).

Tras modificar el dashboard o actualizar las tablas, regenera el archivo autónomo con `python dashboard/build_standalone.py`. Este archivo no pide recursos locales ni acceso a los CSV externos cuando se abre; las fuentes web enlazadas solo se consultan si la persona hace clic en ellas.

Las pruebas de navegador comprueban arveja tras arroz, margen negativo en Tablazo, ausencia de cultivo viable, carga de evidencia y ancho móvil. Para ejecutarlas instala `dashboard/requirements-test.txt`, ejecuta `python -m playwright install chromium` si falta el navegador y corre `python -m unittest discover -s dashboard/tests`.
