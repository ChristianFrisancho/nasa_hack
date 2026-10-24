# Reglas del equipo Piura y qué las hace cumplir

| Regla | Qué la hace cumplir |
|---|---|
| Cada bot registra sus decisiones en `<su carpeta>/decisions.tsv` (show-me-your-work) | `tools/log.sh` escribe el formato; Grok Bot revisa que cada carpeta tenga filas antes de integrar |
| Todo dato lleva etiqueta `observado`, `estimado` o `desconocido`, con fuente y unidad | Grok Bot rechaza en la integración las filas sin etiqueta |
| Ningún resultado entra a `consolidado/` sin que otro bot lo haya interrogado | Revisión cruzada: Agronomía y Territorio se revisan entre sí, Datos y Modelos también; Grok Bot revisa al final |
| skills siempre activas: unslop, correct, show-me-your-work, interrogate, poteto-mode | Descripción de cada bot |
