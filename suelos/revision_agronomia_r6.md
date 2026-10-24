# Revisión cruzada de Agronomía, ronda 6 (Territorio)

Fecha: 2026-10-24. Alcance: respuesta_revision_r5.csv, filas R6S001-006, R6P001-008, R6A001-003, la columna zona/zonas_aplicables y R5S009. No modifiqué cultivos/: el md5 de todos sus CSV es igual al inicio y al final de la ronda. Detalle fila a fila en `revision_agronomia_r6.csv` (18 hallazgos: 0 alta, 9 media, 9 baja). Gasté 4 créditos de Tavily de 40.

## 0. Respuesta r5 y columnas zona / zonas_aplicables

Comprobé cada afirmación que se podía comprobar y todas se cumplen:
- H01: arroz de sierra marcado MARGINAL con 2.3 %.
- H02: para_motor con 126 filas.
- H03: PE0015 y PE0031 con 1.0 (0.85-1.2) y zona chira.
- H05: R5P004 con 8 (4-12).
- H18: existe R5R001b.
- H19: R5R004 está borrada.

Acepto el rechazo de H12: consulta_parcela.py es código nuestro.

Revisé con un script todos los CSV de cultivos/ y para_motor/. Todos los valores de zona y de zonas_aplicables son códigos válidos del CONTRATO. Hay 17 filas con zonas_aplicables (Olmos, Mochumí, Lambayeque, uva) y **ninguna incluye sierra_piura**. No hay análogos de costa extendidos a la sierra.

Problemas:
- **zonas_aplicables no está en CONTRATO.md** (solo fuente_primaria y subzona), aunque validar.py y el motor ya la leen. Propongo un texto en el CSV.
- **R6P001-008 y R6A001-003 no tienen zona ni zonas_aplicables.** El motor las aplica a todas las zonas, sierra incluida, y el calendario oficial registra mango y banano en sierra_piura.
- R5S001-009 llevan zona bajo_piura con lugar Mochumí. Lo pedí yo en r5, pero no es coherente con Olmos (zona vacía + zonas_aplicables). Corrijo esa petición.
- El aviso de H15 ya no aplica: el calendario_obs.py consolidado lee códigos y zonas_aplicables.

## 1. R5S009: 5.9 o 6.4 (error nuestro)

El 5.9 de r5 es Ozcan 2006, ECe = 1.93·EC1:1 − 0.57, que a 3.36 da 5.91. Ozcan está en la Tabla 4 de Spiteri y Sacco 2024, pero nuestra tabla de r5 solo listaba Zhang, las tres de Sonmez y USDA. Con esas cinco, el mínimo es 6.4, como recalculó el agrónomo. **El error es nuestro**: dimos un mínimo con una ecuación que no documentamos y mezclamos ecuaciones sin elegir por textura.

Verifiqué los coeficientes en el original. Para la textura probable del bajo valle, arcillosa o franco-arcillosa (la fila no la reporta), la ecuación es **Sonmez et al. 2008, arcilla: ECe = 2.03·EC1:1 − 0.41**. Con CE 1:1 de 3.36-3.71, da **ECe 6.4-7.1 dS/m**, valor central 6.8. Las tres ecuaciones con menor error en la validación de Spiteri y Sacco dan 5.9-7.1: Kargas (RMSE 0.86), Sonmez arcilla (0.92) y Ozcan (1.00). La envolvente de las 9 ecuaciones es 5.9-11.1. La conclusión no cambia: el suelo "recuperado" sigue salino.

## 2. Umbral ECw del mango (DZ_EJA04)

No es una cita de segunda mano: es la fuente primaria. Durán Zuazo, Martínez Raya y Aguilar Ruiz, *Eur. J. Agron.* 21(3):323-334, 2004 (en línea 2003), doi 10.1016/j.eja.2003.10.004, con cv. Osteen en Almuñécar, España. El artículo es de acceso cerrado; solo leí el resumen. Según el resumen, los tratamientos son agua de riego con CE de 1.02, 1.50, 2.00 y 2.50 dS/m. Por tanto **los umbrales 0.88 y 1.81 y las pendientes 17.1 y 12.5 %/(dS/m) están en base ECw**. El 0.88 queda por debajo del tratamiento más bajo, así que es una extrapolación de la recta.

En ECe (≈1.5·ECw, FAO-29, LF 15-20 %) equivalen a unos 1.3-2.7 dS/m. Encaja con R6P001: el umbral ECe de 1.4 de Embleton y Jones 1966, citado en la p.72 de Durán Zuazo 2003 (SJAR), es ECe y está verificado. Propuesta para R6P002/003: cambiar "probablemente ECw" por "ECw", citar el resumen de ScienceDirect en vez de "citado por Territorio" y usar el año 2004.

## 3. Tesis UNITRU (Peña Serrano 2013)

Leí el PDF completo. El ensayo se hizo en la **EEA Vista Florida (INIA), Chiclayo, Lambayeque**: p.21 (resumen), p.25 §3.2.7 ("Las parcelas experimentales correspondieron a la estación experimental Vista Florida de Chiclayo (1008 m2)") y p.96 (Anexo 37, análisis de suelo). No es de Piura. Que en r3 escribiéramos "en Piura" **fue un error nuestro**.

Según el CONTRATO cuenta como "regional" (costa norte), pero no como dato de Piura. Debe llevar zona vacía y zonas_aplicables solo costeras. Los rendimientos de las conclusiones (71 753 y 79 335 kg/ha) son inverosímiles; usar solo el resultado cualitativo sobre las cepas. Extracto con páginas en `suelos/fuentes/PenaSerrano_2013_UNT_caupi_extracto.md`.

## 4. FAO/UNALM 1990 y ANA ERH Piura

**No pude leer el FAO/UNALM 1990.** repositorio.ana.gob.pe corta la conexión desde nuestra red: TLS cerrado (curl exit 35) y ERR_CONNECTION_CLOSED en Chrome. Wayback no tiene copia accesible (CDX 429). Tampoco hay copia en suelos/fuentes/, solo el extracto OCR. **No puedo citar sección, tabla ni página.**

Qué se puede decir de cada fila:
- **R6S001-002** coinciden con los fragmentos OCR. R6S001 interpreta mal la cita: dice que las mayores áreas están en dos clases, "< 4 y 4-12 mmhos/cm", no que 4-12 sea la dominante.
- **R6S003** (450 km de drenes abiertos, sistema principal terminado en 1977) está corroborada solo por una presentación estudiantil secundaria. Esa misma presentación menciona una II etapa con drenes parcelarios y entubados, así que "sin drenes parcelarios" vale para 1977-1990, no para hoy.

ANA 2015, verificado en el texto:
- **R6S004** (p.102): "fluctúa entre 0,04 (IRHS-46 – Piura) y 16.83 mmhos/cm (IRHS-68 – Catacaos)". Es CE de agua de pozo y está bien etiquetada como ECw.
- **R6S005** (p.110, §10.3.4): nivel estático de 15-30 m, y más de 30 m en Piura, Castilla y Catacaos. Está bien separada de la napa somera.
- **R6S006** (Cuadros 7.6-7.18): lo recalculé y coincide: n=41, mediana 2.3 m, p25-p75 0.6-6.0 m, 20 de 41 bajo 2 m. Esto es coherente con la napa somera que describe FAO 1990, aunque con 25 años de diferencia y sin ubicación de cada SEV.

## Kc de mango Kent y banano

- **FAO-56 Tabla 12 no incluye mango** (verificado en x0490e0b). Los Kc de Kent 0.88/0.84/0.81/0.73 (R6P004-007) coinciden con Cavalcante 2022, Tabla 9, p.23 (Silva 2019, semiárido brasileño). Son coherentes con Paredes et al. 2024, ya presente en el repositorio con el método FAO-56 (Kc mid 0.85-0.95). Detalle menor: en la misma tabla 4.27/4.98 = 0.86, no 0.88.
- **Banano 1.12** (R6P008, Quevedo, lisímetros; el resumen coincide) es **menor** que FAO-56 año 2 (Kc mid 1.20), que es lo comparable para la soca perenne del Chira. La nota "mayor que FAO-56 1.1 del año 1" engaña. Al venir de clima húmedo, no debe reemplazar PE0017-19.
- No encontré una fuente peruana de Kc para mango ni para banano. Una búsqueda solo devolvió Kc de arroz en La Molina y de cultivos andinos.

Además, R6A001/002 (frijol de palo) coinciden con el PDF completo: Tayyab et al. 2016, Pak. J. Bot. 48(4):1353-1360, p.1354.

## ¿Queda cerrado H02?

**Parcialmente.** Lo que depende de ANA 2015 (R6S004-006) está cerrado y verificado con página. Lo que depende de FAO/UNALM 1990 (R6S001-003) sigue sin poder verificarse contra el original. Esas filas deben quedar con conf ≤0.3 y marca de no verificadas, y R6S001 debe corregirse a "dos clases <4 y 4-12". Cerrarlo del todo requiere que alguien con acceso desde Perú, o el usuario desde su navegador, descargue hdl 20.500.12543/1535.
