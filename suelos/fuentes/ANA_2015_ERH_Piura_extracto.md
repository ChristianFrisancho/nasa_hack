# Extracto: ANA 2015, Evaluación de Recursos Hídricos Superficiales en la Cuenca del Río Piura (Tomo I)

- **Cita:** Autoridad Nacional del Agua (ANA), AAA Jequetepeque-Zarumilla. *Evaluación de Recursos Hídricos Superficiales en la Cuenca del Río Piura*, Tomos I y II. Piura, octubre de 2015.
- **URL:** https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf
- **Cómo lo obtuve:** ana.gob.pe corta el TLS desde nuestra caja (curl exit 35). Extraje el texto completo del PDF con Tavily extract (1 crédito) el 2026-10-24. Está en `ANA_2015_ERH_Piura_tomos_I_II_texto_tavily.txt`, en esta misma carpeta. Ese archivo no es el PDF: es texto con errores de OCR (por ejemplo "M edio"). Las páginas salen del texto del propio documento, donde aparecen como "P á g i n a - N -".

## CE del agua subterránea: 16.83 dS/m (pág. 102; repetido en las conclusiones, pág. 118)
> "La conductividad eléctrica en el área de estudio fluctúa entre 0,04 (IRHS-46 – Piura) y 16.83 mmhos/cm (IRHS-68 – Catacaos)"

- 1 mmhos/cm = 1 dS/m.
- El dato corresponde al **agua subterránea** de pozos IRHS del Valle Medio y Bajo Piura. No es la ECe del suelo.
- En el mismo capítulo: las aguas para riego van de la clase C3S1 a la C3S4. El pH del agua va de 3.20 (IRHS 26, La Arena) a 10.42 (IRHS-52, Sechura) y el boro de 0.24 a 2.68 ppm.

## Profundidad del techo de la napa: niveles estáticos en pozos (sección 10.3.4, pág. 110, Figura N° 27)
> "De modo general, se tiene valores de profundidad mayores a los 30 metros en pozos de los Distritos de Piura, Castilla y Catacaos. Para el resto de zonas investigadas, los valores de profundidad del nivel estático están entre los 15 hasta los 30 metros."

- Base del dato: inventario de pozos de 2014 y red piezométrica de la ANA (ex INRENA), con 80 piezómetros entre 2004 y 2014 (sección 10.3.2, pág. 109).
- La pág. 110 menciona conos de descenso por bombeo en Cura Mori y en el oeste de Piura.
- **Interpretación (mía):** los pozos de bombeo miden el acuífero explotado. No miden la napa colgada bajo las parcelas regadas, así que esta cifra no contradice la napa somera que muestran los SEV.

## Nivel freático por sondeos eléctricos verticales (SEV/TDEM), Cuadros 7.6 a 7.18 (págs. 75–83)
- Las tablas traen la columna "Nivel Freático" por SEV.
- Secciones 1 a 7, 12 y 13 (41 SEV con dato), en metros:
  - Valores: 0.60, 4.68, 0.55, 0.078, 6.44, 6, 3.30, 38.59, 1.05, 1.26, 0.60, 0.5, 0.52, 0.57, 34.73, 5.95, 3.50, 0.062, 1.34, 2.49, 1.62, 1.29, 58.70, 0.00, 19.05, 25.38, 7.28, 6.13, 159.50, 0.00, 1.00, 0.00, 1.32, 7.03, 1.31, 1.32, 5.50, 5.0, 4.56, 4.27, 2.30.
  - Mediana 2.3 m y p25–p75 de 0.6 a 6.0 m. 20 de 41 SEV quedan por debajo de 2 m y 11 por debajo de 1 m.
- Las secciones 8 a 11 (31 SEV) dan niveles de 114 a 285 m. Las excluí porque probablemente son bordes desérticos.
- Limitaciones:
  - La ubicación de cada SEV está en el "Anexo 4: Mapas", que no tengo, así que no se puede separar el Medio del Bajo Piura.
  - Es una medición indirecta (geofísica) y no indica la estación del año.
- Ejemplo de cita, Cuadro 7.6 (pág. 75): "SEV 12 0.60 … 0 - 0.60".
