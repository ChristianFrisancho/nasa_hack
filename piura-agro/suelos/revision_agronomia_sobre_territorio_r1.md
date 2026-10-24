# Revisión de Agronomía (Agente 1) sobre Territorio — Ronda 7 (r1)

Revisión cruzada de `suelos/` hecha sobre una copia congelada de las 07:17 UTC
(`cultivos/_scratch/suelos_r7/`), porque Territorio editaba en vivo. Método
tipo *interrogate* adaptado: por lentes (química iónica, semántica de rangos,
integración con el motor, cobertura por zona), de forma manual.

**No edité ningún archivo de Territorio.** Esto es solo una lista de hallazgos
con corrección propuesta. Detalle en
`revision_agronomia_sobre_territorio_r1.csv` (columnas: id, severidad, archivo,
fila_o_variable, problema, evidencia, fuente_url, correccion_propuesta).

## Conteo: 14 hallazgos — 4 altos, 6 medios, 4 bajos

### Altos
- **H01 — QCarn1 = 10.4 dS/m**: incompatible con el balance iónico del punto
  (≈3.0–3.3 dS/m ≈ 3000–3300 µS/cm). Infla la mediana (5.0) y el máximo (10.4)
  de san_lorenzo quebrada.
- **H02 — RPiur4 = 9.03 dS/m**: el balance da ≈5.1–5.8 dS/m (≈5100–5800 µS/cm);
  el HCO3 de 2377 mg/L a pH 8.05 es anómalo.
- **H03 — justificación de unidades**: la nota dice que QCarn1, QSFran1, RPiur4 y
  RPiur5 se leen como mS/cm «igual que el Gráfico 6.7»; pero ese gráfico, en
  µS/cm, los muestra casi en cero. El orden mS/cm es plausible, pero la
  justificación correcta es el balance iónico, no el gráfico.
- **H04 — napa Bajo Piura tope 2.0 m**: contradice los SEV 2015 (p75 = 6.0 m,
  51% de puntos > 2 m; n=41, mediana 2.3). Un tope fijo descarta de más en el
  caso insignia.

### Medios
- **H05** — nombres de variable de Territorio (CE_agua_riego_rio) no coinciden
  con los del motor (ce_agua_riego): el contexto ECw por zona nunca llega al
  motor (integración efectiva = 0, confirmado en sandbox).
- **H06** — el rango 0.42–9.03 es dispersión entre puntos, no incertidumbre de
  parcela; el motor lo trata como rango de parcela. Además el 9.03 es RPiur4
  (H02).
- **H07** — C orgánico ≈18.55 g/kg para Bajo Piura árido arenoso: SoilGrids
  sobreestima SOC; marcar SOC y N como baja confianza.
- **H08** — profundidad de Chira toma el borde inferior (0.1 m, 27% del área)
  cuando el 73% supera 1 m; 0.1 m es limitante, no típico.
- **H09** — Sullana: profundidad efectiva de punto (HWSD) 1.0 m vs zona 0.1 m;
  prevalece de más el valor de zona.
- **H10** — salida de consulta_parcela con CE_agua_napa_pozo duplicada y estados
  en conflicto (napa puntual «desconocido» junto a napa_estacional «observado»).

### Bajos
- **H11** — puntos de Sechura sin CE_suelo (nunca se sirve).
- **H12** — una textura geográficamente atípica para su zona (posible cruce de
  celda).
- **H13** — misma mediana de napa (2.3) reportada como min-max (0.0–159.5) por
  Territorio y como IQR (0.6–6.0) por Agronomía: inconsistencia semántica.
- **H14** — la pendiente de zona usa el máximo (ruido DEM), no la suavizada.

## µS/cm corregidos (estimación por balance iónico)
- QCarn1: ~3.0–3.3 dS/m (reportado 10.4) → ~3000–3300 µS/cm.
- RPiur4: ~5.1–5.8 dS/m (reportado 9.03) → ~5100–5800 µS/cm.
- QSFran1: ~4.0–4.6 dS/m (reportado 5.0) → internamente coherente.
- RPiur5: ~11–12 dS/m (reportado 9.92) → coherente (Cl 3288 mg/L).
