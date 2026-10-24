/* Raíz: an explanatory view over published, precomputed Piura examples. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const nf = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 1 });
  const names = { arroz:'Arroz', arveja:'Arveja', caupi:'Caupí', algodon:'Algodón',
    'maiz amarillo duro':'Maíz amarillo duro', 'maiz choclo':'Maíz choclo',
    limon:'Limón', platano:'Plátano', papaya:'Papaya', yuca:'Yuca',
    'frijol grano':'Frijol grano', 'frijol verde':'Frijol verde',
    'frijol de palo':'Frijol de palo', cebolla:'Cebolla', papa:'Papa', piquillo:'Piquillo', zapallo:'Zapallo' };
  const zones = {bajo_piura:'Bajo Piura', medio_piura:'Medio Piura', alto_piura:'Alto Piura',
    chira:'Chira', san_lorenzo:'San Lorenzo', sierra_piura:'Sierra de Piura', piura_region:'Región Piura'};
  const filterNames = {salinidad:'Sales en el suelo', drenaje:'Drenaje', pendiente:'Pendiente', agua:'Agua disponible',
    sanidad:'Plagas y sanidad', calendario:'Clima y calendario', pH:'Acidez del suelo',
    profundidad:'Profundidad del suelo', presupuesto:'Presupuesto', normas:'Normas'};
  const scenarioNames = {sin_el_nino:'Sin El Niño', el_nino_moderado:'El Niño moderado',
    el_nino_fuerte_extraordinario:'El Niño fuerte / extraordinario'};
  const resultNames = {pasa:'Pasa', advierte:'Alerta', no_evaluable:'Sin evaluar', descarta:'Descarta'};
  const state = {data:null, example:null, crop:null, evidence:null, evidenceFiltered:[], evidenceLimit:12};

  function elem(tag, cls, value) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  }
  function clear(node) { node.replaceChildren(); return node; }
  function pretty(value) { return names[value] || (value ? value[0].toUpperCase() + value.slice(1).replaceAll('_',' ') : 'No registrado'); }
  function num(value, decimals) {
    if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return 'Sin dato';
    return new Intl.NumberFormat('es-PE', {maximumFractionDigits: decimals ?? 1}).format(Number(value));
  }
  function val(measure) { return measure && measure.value !== null && measure.value !== undefined ? Number(measure.value) : null; }
  function fmt(measure, unitOverride) {
    if (val(measure) === null) return 'Sin dato';
    const unit = unitOverride === undefined ? (measure.unit || '') : unitOverride;
    return num(measure.value) + (unit ? ' ' + unit : '');
  }
  function fmtRange(measure) {
    if (!measure || (measure.min == null && measure.max == null)) return 'Rango no disponible';
    return num(measure.min) + '–' + num(measure.max) + (measure.unit ? ' ' + measure.unit : '');
  }
  function sole(value) { return value == null ? 'Sin dato' : 'S/ ' + num(value, 0); }
  function safeUrl(url) {
    try { const u = new URL(url); return ['https:', 'http:'].includes(u.protocol) ? u.href : null; }
    catch { return null; }
  }
  function addLink(parent, text, url) {
    const good = safeUrl(url);
    if (good) { const a = elem('a', '', text); a.href=good; a.target='_blank'; a.rel='noopener noreferrer'; parent.append(a); }
    else parent.append(elem('span','',text));
  }
  function currentCandidate() { return state.example?.candidates.find(c => c.crop === state.crop) || null; }
  function topCandidate() { return state.example?.candidates.find(c => c.rank === 1) || null; }
  function counts(candidate) {
    const tally = {pasa:0, advierte:0, no_evaluable:0, descarta:0};
    for (const v of candidate?.verdicts || []) if (v.result in tally) tally[v.result]++;
    return tally;
  }
  function getProfile(crop) { return state.data?.profiles.find(p => p.cultivo === crop); }
  function option(select, value, label) { const o = elem('option','',label); o.value=value; select.append(o); }

  function populateControls() {
    const prior = clear(byId('previous-select'));
    const values = [...new Set(state.data.examples.map(e => e.previousCrop))];
    for (const crop of values) option(prior, crop, crop ? pretty(crop) : 'No registrado en el ejemplo');
    const parcels = clear(byId('parcel-select'));
    for (const e of state.data.examples) option(parcels,e.id,e.label);
    const profiles = clear(byId('profile-select'));
    for (const p of state.data.profiles) option(profiles,p.cultivo,pretty(p.cultivo));
    prior.addEventListener('change', () => {
      const example = state.data.examples.find(e => e.previousCrop === prior.value);
      if (example) chooseExample(example.id);
    });
    parcels.addEventListener('change', () => chooseExample(parcels.value));
    profiles.addEventListener('change', renderProfiles);
    byId('data-stamp').textContent = `${state.data.counts.examples} parcelas · ${state.data.counts.candidates} alternativas · ${nf.format(state.data.counts.evidence)} datos`;
  }

  function chooseExample(id, crop) {
    state.example = state.data.examples.find(e => e.id === id) || state.data.examples[0];
    state.crop = crop && state.example.candidates.some(c => c.crop === crop) ? crop :
      (state.example.candidates.find(c => c.rank === 1) || state.example.candidates[0]).crop;
    byId('parcel-select').value = state.example.id;
    byId('previous-select').value = state.example.previousCrop;
    byId('parcel-zone').textContent = zones[state.example.zone] || 'Zona sin identificar';
    byId('parcel-coords').textContent = state.example.lat != null && state.example.lon != null ?
      `${num(state.example.lat, 2)}, ${num(state.example.lon, 2)}` : 'No precisada';
    render();
    updateUrl();
  }
  function chooseCrop(crop) {
    if (!state.example.candidates.some(c => c.crop === crop)) return;
    state.crop = crop;
    render(); updateUrl();
  }
  function updateUrl() {
    const url = new URL(location.href);
    url.searchParams.set('parcela',state.example.id);
    url.searchParams.set('cultivo',state.crop);
    history.replaceState(null,'',url);
  }
  function recommendationLevel(candidate, top) {
    if (!top) return {label:'Ninguna opción viable', css:'danger'};
    if (candidate.decision === 'descartado') return {label:'Cultivo descartado', css:'danger'};
    if (candidate.decision === 'sin datos') return {label:'Faltan datos esenciales', css:'unknown'};
    if (candidate.p50 != null && candidate.p50 < 0) return {label:'Pérdida estimada', css:'danger'};
    const tally = counts(candidate);
    if (tally.advierte || tally.no_evaluable || (candidate.p10 != null && candidate.p10 < 0)) return {label:'Opción con reservas',css:'warning'};
    return {label:'Opción evaluada',css:'good'};
  }
  function editorialMessage(example, candidate, top) {
    if (!top) return 'Con el agua, presupuesto y suelo de este ejemplo, ninguna alternativa evaluada supera los filtros. La siguiente decisión es corregir esas restricciones o buscar otro escenario.';
    if (candidate.decision === 'descartado') return `${pretty(candidate.crop)} quedó fuera por una o más restricciones que no se deben compensar con un margen alto.`;
    if (candidate.decision === 'sin datos') return `Faltan mediciones esenciales antes de evaluar ${pretty(candidate.crop)} en esta parcela.`;
    if (candidate.p50 != null && candidate.p50 < 0) return `Es la primera opción del ranking, pero su margen mediano es negativo (${sole(candidate.p50)}/ha). No conviene sembrarla sin revisar agua y costos.`;
    if (example.id === 'bajo_piura_tras_arroz' && candidate.crop === 'arveja') return 'Arveja ocupa el primer lugar, pero el calor durante la floración y la ausencia de siembras registradas en el llano de Bajo Piura hacen que sea una opción exploratoria.';
    if (counts(candidate).no_evaluable > 0) return 'Esta opción supera los filtros que pudieron evaluarse. Faltan datos de campo que todavía podrían cambiar la decisión.';
    return 'Esta opción encabeza el ranking del ejemplo. Compara los riesgos y verifica las mediciones de tu campo antes de sembrar.';
  }
  function renderRecommendation(candidate) {
    const box = clear(byId('recommendation-card'));
    const top = topCandidate();
    const level = recommendationLevel(candidate,top);
    const head = elem('div','rec-topline');
    head.append(elem('span','',top && top.crop === candidate.crop ? 'LA PRIMERA EN EL RANKING' : 'OPCIÓN QUE ESTÁS EXPLORANDO'));
    head.append(elem('span','pill '+level.css,level.label)); box.append(head);
    const journey = elem('div','crop-journey');
    const previous = elem('div','crop-node'); previous.append(elem('span','','Venimos de'),elem('strong','',pretty(state.example.previousCrop)));
    const arrow = elem('span','journey-arrow','→'); arrow.setAttribute('aria-hidden','true');
    const next = elem('div','crop-node next'); next.append(elem('span','',top ? 'Podría seguir' : 'Por ahora'),elem('strong','',top ? pretty(candidate.crop) : 'Ninguno viable'));
    journey.append(previous,arrow,next); box.append(journey);
    box.append(elem('p','rec-message',editorialMessage(state.example,candidate,top)));
    if (top || candidate.decision === 'descartado') {
      const tally = counts(candidate);
      const chips = elem('div','rec-bottom');
      for (const [n,label,cls] of [[tally.pasa,'Pasan',''],[tally.advierte,'Alertas','alert'],[tally.no_evaluable,'Sin evaluar','missing'],[tally.descarta,'Descartan','alert']])
        chips.append(elem('span','count-chip '+cls,`${n} ${label.toLowerCase()}`));
      box.append(chips);
      let caution = '';
      if (candidate.p10 != null && candidate.p10 < 0 && candidate.p50 != null && candidate.p50 >= 0) caution = `En un escenario conservador (P10), el margen baja a ${sole(candidate.p10)}/ha.`;
      if (candidate.p50 != null && candidate.p50 < 0) caution = 'El orden prioriza filtros agronómicos: ser primero no elimina una pérdida económica estimada.';
      if (candidate.decision === 'descartado') caution = 'Esta alternativa incumple una o más restricciones del ejemplo. Revisa los filtros de abajo para conocerlas.';
      if (caution) box.append(elem('p','rec-alert '+(candidate.p50 < 0 || candidate.decision === 'descartado'?'danger':''),caution));
    }
  }
  function renderMetrics(candidate) {
    const grid = clear(byId('metric-grid'));
    const metrics = [
      {label:'Margen P50 · sin El Niño',value:sole(candidate.p50),note:candidate.p10 == null?'P10 sin dato':`P10 conservador: ${sole(candidate.p10)}`,icon:'S/',negative:candidate.p50 != null && candidate.p50 < 0},
      {label:'Riego bruto estimado',value:fmt(candidate.grossWater,'m³/ha'),note:'Agua que habría que entregar al sistema de riego',icon:'≈'},
      {label:'Duración del ciclo',value:fmt(candidate.duration,'días'),note:fmtRange(candidate.duration),icon:'◷'},
      {label:'Cosecha estimada',value:fmt(candidate.yield,'t/ha'),note:fmtRange(candidate.yield),icon:'↗'},
    ];
    for (const m of metrics) {
      const card = elem('article','metric-card'+(m.negative?' negative':''));
      const top = elem('div','metric-top'); top.append(elem('span','',m.label),elem('span','metric-icon',m.icon));
      card.append(top,elem('strong','',m.value),elem('small','',m.note));grid.append(card);
    }
  }
  function renderAlternatives() {
    const list = clear(byId('alternatives-list'));
    for (const c of state.example.candidates) {
      const b = elem('button','alternative'+(state.crop===c.crop?' active':''));b.type='button';b.setAttribute('aria-pressed',String(state.crop===c.crop));
      b.append(elem('span',c.rank?'rank-bubble':'status-dot '+c.decision.replace(' ','-'),c.rank?String(c.rank):''),elem('strong','',pretty(c.crop)));
      b.append(elem('small','',c.decision==='aceptado' ? (c.p50==null?'Sin margen':sole(c.p50)) : c.decision));
      b.addEventListener('click',()=>chooseCrop(c.crop));list.append(b);
    }
  }
  function renderMarginChart() {
    const holder = clear(byId('margin-chart'));
    const crops = state.example.candidates.filter(c => c.decision==='aceptado' && c.rank != null).sort((a,b)=>a.rank-b.rank);
    if (!crops.length) { holder.append(elem('div','empty-state','Ningún cultivo pasó los filtros. Consulta los motivos de descarte en la lista.')); return; }
    const width=700,left=175,right=90,row=34,top=25,bottom=34,height=top+crops.length*row+bottom;
    const vals=crops.flatMap(c=>[c.p10,c.p50]).filter(x=>x!=null);
    if (!vals.length) { holder.append(elem('div','empty-state','No hay márgenes suficientes para dibujar una comparación.'));return; }
    const min=Math.min(0,...vals),max=Math.max(0,...vals),pad=Math.max(300,(max-min)*.07);
    const x=d3.scaleLinear().domain([min-pad,max+pad]).range([left,width-right]);
    const svg=d3.select(holder).append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','img').attr('aria-label','Comparación de márgenes P10 y P50 por cultivo, en soles por hectárea');
    svg.append('line').attr('class','zero-line').attr('x1',x(0)).attr('x2',x(0)).attr('y1',top-5).attr('y2',height-bottom+2);
    const rows=svg.selectAll('g.crop-row').data(crops).join('g').attr('class','crop-row').attr('transform',(_,i)=>`translate(0,${top+i*row})`).attr('role','button').attr('tabindex',0).attr('aria-label',c=>`${pretty(c.crop)}: P10 ${sole(c.p10)}, P50 ${sole(c.p50)}`)
      .style('cursor','pointer').on('click',(_,c)=>chooseCrop(c.crop)).on('keydown',(event,c)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();chooseCrop(c.crop);}});
    rows.append('rect').attr('x',0).attr('y',0).attr('width',width).attr('height',row-2).attr('fill',c=>state.crop===c.crop?'#e9f3e8':'transparent').attr('rx',6);
    rows.append('text').attr('class','crop-label').attr('x',8).attr('y',21).text(c=>`${c.rank}. ${pretty(c.crop)}`);
    rows.filter(c=>c.p10!=null&&c.p50!=null).append('line').attr('x1',c=>x(c.p10)).attr('x2',c=>x(c.p50)).attr('y1',17).attr('y2',17).attr('stroke',c=>c.p50<0?'#b65d43':(state.crop===c.crop?'#143d37':'#85aa8e')).attr('stroke-width',5).attr('stroke-linecap','round');
    rows.filter(c=>c.p10!=null).append('circle').attr('cx',c=>x(c.p10)).attr('cy',17).attr('r',3).attr('fill','#a3b2a2');
    rows.filter(c=>c.p50!=null).append('circle').attr('cx',c=>x(c.p50)).attr('cy',17).attr('r',6).attr('fill',c=>c.p50<0?'#b65d43':(state.crop===c.crop?'#143d37':'#4b8a62'));
    rows.filter(c=>c.p50==null).append('text').attr('class','bar-label').attr('x',left+5).attr('y',21).text('Sin margen');
    svg.append('g').attr('class','axis').attr('transform',`translate(0,${height-bottom})`).call(d3.axisBottom(x).ticks(5).tickFormat(v=>v===0?'S/ 0':`S/ ${Math.round(v/1000)} mil`));
  }
  function shortReason(verdict, candidate) {
    if (verdict.result === 'no_evaluable') return verdict.missing?.length ?
      `Todavía falta medir ${verdict.missing.slice(0,2).join(' y ')}.` : 'No hay datos suficientes para evaluar este punto.';
    if (verdict.result === 'pasa') return verdict.reason.length <= 130 ? verdict.reason : 'No se detectó una restricción decisiva con los datos disponibles.';
    if (verdict.result === 'descarta') return 'Esta condición incumple un límite del ejemplo. Consulta el detalle antes de considerar este cultivo.';
    const messages = {
      salinidad:'La salinidad podría reducir la cosecha. Conviene confirmar la ECe y la profundidad de la napa.',
      drenaje:'El drenaje puede limitar las raíces o elevar el riesgo de enfermedad.',
      pendiente:'La pendiente exige controlar erosión y manejo del terreno.',
      agua:'La cantidad o calidad de agua podría no cubrir el ciclo completo.',
      sanidad:'Hay un riesgo sanitario relacionado con el cultivo anterior o esta parcela.',
      calendario:'La ventana de siembra o el calor pueden afectar etapas sensibles.',
      pH:'El pH está fuera del rango preferido o es incierto.',
      profundidad:'La profundidad efectiva puede limitar las raíces.',
      presupuesto:'Los costos podrían superar el presupuesto disponible.',
      normas:'Hay una restricción normativa o de manejo que requiere revisión.',
    };
    if (verdict.filter === 'calendario' && candidate.crop === 'arveja' && state.example.id === 'bajo_piura_tras_arroz')
      return 'El calor coincide con la floración y la DRAP no registra siembras de arveja en el llano de Bajo Piura.';
    return messages[verdict.filter] || 'Este punto requiere atención antes de sembrar.';
  }
  function renderFilters(candidate) {
    const tally=counts(candidate);
    const summary=clear(byId('verdict-summary'));
    for(const [key,label,css] of [['pasa','Pasan','good'],['advierte','Alertas','warning'],['no_evaluable','Sin evaluar','unknown'],['descarta','Descartan','danger']])
      summary.append(elem('span','pill '+css,`${tally[key]} ${label.toLowerCase()}`));
    const list=clear(byId('filter-list'));
    const columns=[elem('div','filter-column'),elem('div','filter-column')];list.append(...columns);
    const split=Math.ceil(candidate.verdicts.length/2);
    for(const [index,v] of candidate.verdicts.entries()) {
      const d=elem('details','filter-item');
      if(['advierte','descarta'].includes(v.result)) d.open=true;
      const s=elem('summary','');s.append(elem('span','status-ico '+v.result,({pasa:'✓',advierte:'!',no_evaluable:'?',descarta:'×'})[v.result]||'?'),elem('span','filter-name',filterNames[v.filter]||pretty(v.filter)),elem('span','pill '+({pasa:'good',advierte:'warning',no_evaluable:'unknown',descarta:'danger'})[v.result],resultNames[v.result]||v.result));
      const body=elem('div','filter-detail');body.append(elem('p','',shortReason(v,candidate)));
      if(v.reason||v.source){
        const technical=elem('details','technical-details');technical.append(elem('summary','','Ver explicación técnica y fuente'));
        if(v.reason)technical.append(elem('p','',v.reason));
        if(v.source){const source=elem('div','source');source.append(elem('strong','','Fuente: '),elem('span','',v.source));if(v.url){source.append(document.createTextNode(' · '));addLink(source,'Abrir fuente ↗',v.url);}technical.append(source);}
        body.append(technical);
      }
      d.append(s,body);columns[index<split?0:1].append(d);
    }
    if(!candidate.verdicts.length)list.replaceChildren(elem('p','empty-state','Este cultivo no tiene un desglose de filtros disponible.'));
  }
  function renderWater(candidate) {
    const holder=clear(byId('water-chart'));
    const stages=candidate.stages.filter(s=>val(s.etc)!=null);
    if(!stages.length){holder.append(elem('div','empty-state','La demanda de agua no pudo calcularse para esta opción.'));byId('water-note').textContent='Necesitamos datos de cultivo, clima y parcela para estimar riego.';return;}
    const width=550,height=228,left=105,right=58,top=15,row=46,bottom=27;
    const x=d3.scaleLinear().domain([0,d3.max(stages,s=>val(s.etc))*1.15]).range([left,width-right]);
    const labels={inicial:'Inicio',desarrollo:'Desarrollo',media:'Mitad del ciclo',final:'Final'};
    const svg=d3.select(holder).append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','img').attr('aria-label','Demanda estimada de agua por etapa del cultivo');
    svg.selectAll('text.stage').data(stages).join('text').attr('class','crop-label').attr('x',5).attr('y',(_,i)=>top+i*row+23).text(s=>labels[s.name]||pretty(s.name));
    svg.selectAll('rect.bar-bg').data(stages).join('rect').attr('x',left).attr('y',(_,i)=>top+i*row+7).attr('width',width-left-right).attr('height',22).attr('rx',5).attr('fill','#edf3ec');
    svg.selectAll('rect.bar').data(stages).join('rect').attr('x',left).attr('y',(_,i)=>top+i*row+7).attr('width',s=>x(val(s.etc))-left).attr('height',22).attr('rx',5).attr('fill','#70a88a');
    svg.selectAll('text.amount').data(stages).join('text').attr('class','bar-label').attr('x',s=>Math.min(width-right+6,x(val(s.etc))+7)).attr('y',(_,i)=>top+i*row+23).text(s=>`${num(val(s.etc),0)} mm`);
    svg.append('g').attr('class','axis').attr('transform',`translate(0,${height-bottom})`).call(d3.axisBottom(x).ticks(4).tickFormat(v=>`${v} mm`));
    byId('water-note').textContent=`Total ETc: ${fmt(candidate.etcTotal,'mm')}. Riego neto: ${fmt(candidate.netWater,'m³/ha')}; riego bruto: ${fmt(candidate.grossWater,'m³/ha')}. Son estimaciones del ejemplo, no una cuota de canal.`;
  }
  function renderNutrients(candidate) {
    const holder=clear(byId('nutrient-chart'));
    const data=[['N',candidate.export.N,'#6d9e7a'],['P₂O₅',candidate.export.P2O5,'#c1a563'],['K₂O',candidate.export.K2O,'#9c7b75']];
    const known=data.filter(d=>val(d[1])!=null);
    if(!known.length) holder.append(elem('div','empty-state','No hay coeficientes suficientes para estimar qué nutrientes salen con esta cosecha.'));
    else {
      const width=550,height=196,left=100,right=75,top=12,row=43,bottom=24,max=Math.max(...known.map(d=>val(d[1])));
      const x=d3.scaleLinear().domain([0,max*1.16]).range([left,width-right]);
      const svg=d3.select(holder).append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','img').attr('aria-label','Nutrientes exportados con la cosecha, en kilogramos por hectárea');
      svg.selectAll('text.n').data(data).join('text').attr('class','crop-label').attr('x',8).attr('y',(_,i)=>top+i*row+22).text(d=>d[0]);
      svg.selectAll('rect.bg').data(data).join('rect').attr('x',left).attr('y',(_,i)=>top+i*row+7).attr('width',width-left-right).attr('height',20).attr('rx',5).attr('fill','#edf1ec');
      svg.selectAll('rect.n').data(known).join('rect').attr('x',left).attr('y',d=>top+data.indexOf(d)*row+7).attr('width',d=>x(val(d[1]))-left).attr('height',20).attr('rx',5).attr('fill',d=>d[2]);
      svg.selectAll('text.v').data(data).join('text').attr('class','bar-label').attr('x',d=>val(d[1])==null?left+7:Math.min(width-right+7,x(val(d[1]))+8)).attr('y',(_,i)=>top+i*row+22).text(d=>val(d[1])==null?'Sin dato':`${num(val(d[1]))} kg/ha`);
      svg.append('g').attr('class','axis').attr('transform',`translate(0,${height-bottom})`).call(d3.axisBottom(x).ticks(4).tickFormat(v=>`${v} kg`));
    }
    const box=clear(byId('soil-balance'));box.append(elem('h4','','Después de la cosecha, en el modelo'));
    const pairs=[['Salinidad (ECe)',candidate.soilEce,'dS/m'],['Balance N',candidate.soilBalance.N,'kg/ha'],['Balance P₂O₅',candidate.soilBalance.P2O5,'kg/ha'],['Balance K₂O',candidate.soilBalance.K2O,'kg/ha']];
    for(const [label,m,unit] of pairs){const line=elem('div','balance-row');line.append(elem('span','',label),elem('strong','',fmt(m,unit)));box.append(line);}
    box.append(elem('p','balance-note','“Sin dato” permanece desconocido. El balance modelado no es una medición de fertilidad ni una dosis de abono.'));
  }
  function renderRecovery(candidate) {
    const box=clear(byId('recovery-note'));
    const intro=elem('div','');intro.append(elem('span','recovery-kicker','LA PRÓXIMA CAMPAÑA'),elem('h3','','¿Cuándo estará listo el suelo otra vez?'));
    intro.append(elem('p','','No hay un plazo único de recuperación: depende del suelo medido, agua, residuos, fertilización y manejo entre campañas.'));
    box.append(intro);
    const actions=elem('div','recovery-actions');
    const deficits=['N','P2O5','K2O'].filter(key=>val(candidate.soilBalance[key])!=null&&val(candidate.soilBalance[key])<0)
      .map(key=>({N:'N',P2O5:'P₂O₅',K2O:'K₂O'})[key]);
    const steps=[];
    if(deficits.length)steps.push(`Revisar el balance de ${deficits.join(', ')} y medir nutrientes antes de reponerlos.`);
    if(val(candidate.soilBalance.N)==null)steps.push('El balance de N es desconocido. Si se trata de una leguminosa, su fijación tampoco garantiza N disponible al siguiente cultivo.');
    if(val(candidate.soilEce)!=null)steps.push('Medir ECe después de cosechar; la salinidad mostrada es una proyección.');
    if(!steps.length)steps.push('Tomar una muestra de suelo al terminar la campaña y ajustar el próximo cultivo con esos resultados.');
    for(const step of steps.slice(0,3))actions.append(elem('p','',step));box.append(actions);
  }
  function renderScenarios(candidate) {
    const box=clear(byId('scenario-grid'));
    for(const s of state.example.scenarios){
      const selected=s.order.find(r=>r.crop===candidate.crop);
      const card=elem('article','scenario-card');card.append(elem('div','scenario-kicker','ESCENARIO CLIMÁTICO'),elem('h3','',scenarioNames[s.id]||pretty(s.id)));
      card.append(elem('div','scenario-value'+(selected?.p50<0?' negative':''),selected?.p50==null?'Sin cifra':sole(selected.p50)+' /ha'));
      const p=elem('p','');p.append(document.createTextNode('Primero en este escenario: '),elem('strong','',s.first?pretty(s.first):'ninguno viable'));card.append(p);
      const track=elem('div','scenario-track');const fill=elem('div','scenario-fill'+(selected?.p50<0?' negative':''));fill.style.width=selected?.p50==null?'0%':`${Math.min(100,Math.max(8,Math.abs(selected.p50)/15000*100))}%`;track.append(fill);card.append(track);box.append(card);
    }
    const seq=clear(byId('sequence-panel'));
    const best=state.example.sequences.find(s=>s.viable);
    seq.append(elem('strong','','Secuencia evaluada'));
    seq.append(elem('span','',best?best.crops.map(pretty).join(' → '):'No hay una secuencia viable con estas restricciones.'));
    if(best)seq.append(elem('small','',`Margen total modelado: ${fmt(best.margin,'PEN/ha')}`));
  }
  function profileCard(crop,title) {
    const p=getProfile(crop);const card=elem('article','profile-card');card.append(elem('div','profile-kicker',title));
    if(!p){card.append(elem('h3','',pretty(crop)),elem('p','',crop?'No hay ficha resumida para este cultivo.':'El cultivo anterior no está registrado en este ejemplo.'));return card;}
    card.append(elem('h3','',pretty(p.cultivo)),elem('span','profile-type',p.tipo||'Tipo no especificado'));
    const facts=elem('div','profile-facts');
    for(const [label,key] of [['Ciclo / primera cosecha','ciclo'],['Kc de mitad de ciclo','kc_mitad_ciclo'],['Salinidad sin pérdida','ECe_sin_perdida_dS_m'],['Temperatura óptima','temperatura_optima'],['pH óptimo','pH_optimo'],['Raíz máxima','raiz_max'],['N por tonelada','saca_del_suelo_N'],['P₂O₅ / K₂O por tonelada','saca_del_suelo_P2O5']]){
      let value=p[key];if(key==='saca_del_suelo_P2O5')value=(p.saca_del_suelo_P2O5||'Sin dato')+' / '+(p.saca_del_suelo_K2O||'Sin dato');
      const node=elem('div','profile-fact');node.append(elem('span','',label),elem('strong','',value||'Sin dato'));facts.append(node);
    }
    card.append(facts);
    const rotation=elem('div','profile-rotation');rotation.append(elem('p','',`Después conviene estudiar: ${p.conviene_despues||'Sin regla específica verificada.'}`),elem('p','',`Evitar o vigilar: ${p.evitar_o_cuidar_despues||'Sin regla específica verificada.'}`));card.append(rotation);
    card.append(elem('p','profile-sources',`Referencias: ${p.fuentes_principales||'Consultar el dataset detallado.'}`));return card;
  }
  function renderProfiles() {
    const grid=clear(byId('crop-profiles'));
    grid.append(profileCard(state.example.previousCrop,'Cultivo anterior'),profileCard(byId('profile-select').value,'Cultivo que exploras'));
  }
  function render() {
    const candidate=currentCandidate();if(!candidate)return;
    renderRecommendation(candidate);renderMetrics(candidate);renderAlternatives();renderMarginChart();renderFilters(candidate);renderWater(candidate);renderNutrients(candidate);renderRecovery(candidate);renderScenarios(candidate);
    byId('profile-select').value=getProfile(candidate.crop)?candidate.crop:state.data.profiles[0].cultivo;
    renderProfiles();
  }

  async function loadEvidence() {
    const button=byId('load-evidence');button.disabled=true;button.textContent='Cargando datos…';
    try {
      if(!state.evidence){
        state.evidence=await d3.csv('../piura-agro/consolidado/piura_super_dataset.csv', row=>{
          const normalized={};for(const [key,value] of Object.entries(row))normalized[key.replace(/^\uFEFF/,'')]=value;
          return normalized;
        });
      }
      byId('evidence-content').hidden=false;button.textContent='Base completa abierta';button.hidden=true;
      if(!byId('evidence-query').value)byId('evidence-query').value=state.crop;
      filterEvidence();
    } catch (error) {
      button.disabled=false;button.textContent='Reintentar carga';
      const content=byId('evidence-content');content.hidden=false;
      byId('evidence-count').textContent='No se pudo abrir el CSV. Abre el dashboard con un servidor desde la raíz del repositorio.';
      console.error(error);
    }
  }
  function filterEvidence() {
    if(!state.evidence)return;
    const query=byId('evidence-query').value.trim().toLocaleLowerCase('es');
    const status=byId('evidence-status').value;
    state.evidenceFiltered=state.evidence.filter(r=>(!status||r.estado===status)&&(!query||[r.tema,r.cultivo,r.zona,r.variable,r.fuente].some(x=>(x||'').toLocaleLowerCase('es').includes(query))));
    state.evidenceLimit=12;renderEvidenceTable();
  }
  function renderEvidenceTable() {
    const rows=state.evidenceFiltered;
    byId('evidence-count').textContent=`${nf.format(rows.length)} filas encontradas · ${nf.format(state.evidence.length)} filas en la base completa`;
    const body=clear(byId('evidence-table'));
    for(const r of rows.slice(0,state.evidenceLimit)){
      const tr=elem('tr','');
      const topic=elem('td','');topic.append(elem('strong','',r.cultivo?pretty(r.cultivo):'General'),elem('span','',r.tema||'—'));tr.append(topic);
      for(const value of [zones[r.zona]||r.zona||'—',r.variable||'—',(r.valor||r.rango||'Sin dato')+(r.unidad?' '+r.unidad:''),r.estado||'—'])tr.append(elem('td','',value));
      const source=elem('td','');const src=(r.fuente||'Fuente no indicada');source.append(elem('span','',src.length>95?src.slice(0,95)+'…':src));
      if(safeUrl(r.url_o_doi)){source.append(document.createTextNode(' '));addLink(source,'Abrir ↗',r.url_o_doi);}tr.append(source);body.append(tr);
    }
    if(!rows.length){const tr=elem('tr','');const td=elem('td','', 'No se encontraron datos con esos filtros.');td.colSpan=6;tr.append(td);body.append(tr);}
    byId('more-evidence').hidden=state.evidenceLimit>=rows.length;
  }
  function setupEvidence() {
    byId('load-evidence').addEventListener('click',loadEvidence);
    let timer;byId('evidence-query').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(filterEvidence,180);});
    byId('evidence-status').addEventListener('change',filterEvidence);
    byId('more-evidence').addEventListener('click',()=>{state.evidenceLimit+=12;renderEvidenceTable();});
  }
  async function init() {
    setupEvidence();
    try {
      const response=await fetch('./data/dashboard.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);
      state.data=await response.json();
      if(!state.data.examples?.length||!state.data.profiles?.length)throw new Error('Snapshot incompleto');
      populateControls();
      const query=new URL(location.href).searchParams;
      chooseExample(query.get('parcela')||state.data.examples[0].id,query.get('cultivo'));
    }catch(error){
      console.error(error);
      byId('data-stamp').textContent='No se pudieron cargar los datos';
      byId('recommendation-card').replaceChildren(elem('div','error-state','No se pudo abrir el dashboard. Inicia un servidor desde la raíz del repositorio: python -m http.server 8000; luego entra a /dashboard/.'));
    }
  }
  init();
})();
