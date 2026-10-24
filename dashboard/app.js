/* Raíz: live rotation calculations plus transparent published Piura examples. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const nf = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 1 });
  const names = { arroz:'Arroz', arveja:'Arveja', caupi:'Caupí', algodon:'Algodón',
    'maiz amarillo duro':'Maíz amarillo duro', 'maiz choclo':'Maíz choclo',
    limon:'Limón', platano:'Plátano', papaya:'Papaya', yuca:'Yuca',
    'frijol grano':'Frijol grano', 'frijol verde':'Frijol verde',
    'frijol de palo':'Frijol de palo', cebolla:'Cebolla', papa:'Papa', piquillo:'Piquillo', zapallo:'Zapallo' };
  const soilVariables={ECe_medida_local:'Salinidad medida del suelo',clase_drenaje_local:'Drenaje',pH_rango_zona:'Rango de pH cartográfico',profundidad_efectiva_enraizamiento:'Profundidad de raíces estimada',pendiente_media_cultivo:'Pendiente media de cultivo'};
  const soilConditions={
    aluvial:{label:'Aluvial · textura media/fina',description:'Sedimentos aluviales descritos en Palo Verde y Piura; la textura y profundidad varían dentro de cada unidad.',units:['Palo Verde','Piura']},
    arenoso:{label:'Arenoso · baja retención',description:'Cerezal: textura arenosa, fertilidad descrita como muy baja y menor retención de agua y nutrientes.',units:['Cerezal']},
    salino:{label:'Salino · drenaje pobre',description:'Pajarito y Ramón están descritos como salinos y con drenaje pobre; hace falta ECe medida del lote.',units:['Pajarito','Ramón']},
    yesoso:{label:'Yeso / carbonatos',description:'Curumuy se asocia a terraza marina con yeso/carbonatos; confirmar química y agua en el perfil.',units:['Curumuy']},
    arido:{label:'Clima árido / superárido',description:'Es una condición climática descrita en sectores del Bajo Piura, no un tipo taxonómico de suelo. El agua disponible debe medirse.',units:[]},
    agrietado:{label:'Agrietado / expansivo · por confirmar',description:'No se verificó una serie Vertisol/vertic en los mapas consultados. Observar grietas y medir arcilla/expansividad antes de clasificar.',units:[]}
  };
  const zones = {bajo_piura:'Bajo Piura', medio_piura:'Medio Piura', alto_piura:'Alto Piura',
    chira:'Chira', san_lorenzo:'San Lorenzo', sierra_piura:'Sierra de Piura', piura_region:'Región Piura'};
  const filterNames = {salinidad:'Sales en el suelo', drenaje:'Drenaje', pendiente:'Pendiente', agua:'Agua disponible',
    sanidad:'Plagas y sanidad', calendario:'Clima y calendario', pH:'Acidez del suelo',
    profundidad:'Profundidad del suelo', presupuesto:'Presupuesto', normas:'Normas'};
  const scenarioNames = {sin_el_nino:'Sin El Niño', el_nino_moderado:'El Niño moderado',
    el_nino_fuerte_extraordinario:'El Niño fuerte / extraordinario'};
  const resultNames = {pasa:'Pasa', advierte:'Alerta', no_evaluable:'Sin evaluar', descarta:'Descarta'};
  const state = {data:null, quick:null, example:null, crop:null, customPrior:null, customMode:false, selectedSoil:'', selectedCondition:'', liveResponseActive:false, evidence:null, evidenceFiltered:[], evidenceLimit:12};

  function elem(tag, cls, value) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  }
  function clear(node) { node.replaceChildren(); return node; }
  function pretty(value) { return names[value] || (value ? value[0].toUpperCase() + value.slice(1).toLowerCase().replaceAll('_',' ') : 'No registrado'); }
  function canonicalCrop(value){
    const text=(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    const alias={'frijol castilla/grano seco':'frijol grano','frijol caupi':'caupi','uva de mesa':'uva','banano (ano 1)':'banano','banano (ano 2)':'banano','naranja (referencia citricos)':'naranja','cana de azucar (planta)':'cana de azucar','cana de azucar (soca)':'cana de azucar'};
    return alias[text]||text;
  }
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
  function getProfile(crop) { return state.data?.profiles.find(p => p.cultivo === crop || canonicalCrop(p.cultivo) === canonicalCrop(crop)); }
  function option(select, value, label) { const o = elem('option','',label); o.value=value; select.append(o); }

  function populateControls() {
    const prior = clear(byId('previous-select'));
    option(prior,'__unregistered__','No especificado · sin historial previo');
    state.data.drapCrops.forEach((crop,index)=>{
      const profile=crop.profileCrop&&getProfile(crop.profileCrop);
      const detail=profile?' · ficha agronómica':' · registro DRAP';
      option(prior,`drap:${index}`,`${pretty(crop.name)}${detail}`);
    });
    const parcels = clear(byId('parcel-select'));
    option(parcels,'','Selecciona una parcela de ejemplo');
    for (const e of state.data.examples) option(parcels,e.id,e.label);
    const profiles = clear(byId('profile-select'));
    for (const p of state.data.profiles) option(profiles,p.cultivo,pretty(p.cultivo));
    const soilCrops=clear(byId('soil-crop-select'));
    for(const p of state.data.profiles)option(soilCrops,p.cultivo,pretty(p.cultivo));
    soilCrops.addEventListener('change',renderSoils);
    byId('soil-region-select').addEventListener('change',renderSoils);
    const soilSelect=clear(byId('soil-unit-select'));
    option(soilSelect,'','Elige una unidad edáfica');
    for(const soil of state.data.soilUnits)option(soilSelect,soil.soil_unit,`${soil.soil_unit} · ${soil.soil_taxonomy_order_1999}`);
    soilSelect.addEventListener('change',()=>{
      state.selectedSoil=soilSelect.value;
      if(state.selectedSoil)byId('soil-region-select').value='bajo';
      renderSoilSelection();renderSoils();markLiveDirty();
    });
    const conditionSelect=clear(byId('soil-condition-select'));
    option(conditionSelect,'','Elige una condición (opcional)');
    for(const [key,condition] of Object.entries(soilConditions))option(conditionSelect,key,condition.label);
    conditionSelect.addEventListener('change',()=>{
      state.selectedCondition=conditionSelect.value;
      if(state.selectedCondition)byId('soil-region-select').value='bajo';
      renderSoilSelection();renderSoils();markLiveDirty();
    });
    prior.addEventListener('change', () => {
      if(prior.value==='__unregistered__'){
        chooseCustomPrior(null);
        return;
      }
      const crop=state.data.drapCrops[Number(prior.value.split(':')[1])];
      if(!crop)return;
      chooseCustomPrior(crop);
    });
    parcels.addEventListener('change', () => {if(parcels.value)chooseExample(parcels.value);});
    profiles.addEventListener('change', renderProfiles);
    byId('data-stamp').textContent = `${state.data.counts.drapCrops} cultivos con cosecha DRAP · ${state.data.counts.annualChoices} anuales comparables + ${state.data.counts.motorPerennials} sistemas perennes · ${state.data.counts.soilUnits} unidades edáficas`;
    byId('drap-crop-search').addEventListener('input',renderDrapCrops);
    byId('drap-crop-role').addEventListener('change',renderDrapCrops);
    byId('run-live-model').addEventListener('click',evaluateLiveRotation);
    byId('run-quick-model').addEventListener('click',evaluateQuickRotation);
    for(const id of ['live-zone','live-month','live-scenario','live-area','live-water-mode','live-water','live-budget','live-ece','live-ph','live-depth','live-slope','live-drainage','live-ecw','live-water-table','live-psi','live-efficiency','live-irrigation-interval','live-fertilizer-n','live-fertilizer-p','live-fertilizer-k','live-pests']){
      byId(id).addEventListener('change',markLiveDirty);byId(id).addEventListener('input',markLiveDirty);
    }
    const monthWater=clear(byId('month-water-grid'));
    const monthLabels=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    monthLabels.forEach((month,index)=>{const label=elem('label','',month),input=elem('input','');input.type='number';input.min='0';input.step='100';input.id=`live-water-month-${index+1}`;input.setAttribute('aria-label',`Agua disponible en ${month}`);label.append(input);input.addEventListener('input',markLiveDirty);monthWater.append(label);});
    renderDrapCrops();
  }

  function priorValue(crop){
    if(!crop)return '__unregistered__';
    const index=state.data.drapCrops.findIndex(item=>item.profileCrop===crop);
    return index<0?'__unregistered__':`drap:${index}`;
  }

  function chooseCustomPrior(crop){
    state.customPrior=crop;state.customMode=true;state.crop=null;state.liveResponseActive=false;
    if(crop)byId('previous-select').value=`drap:${state.data.drapCrops.indexOf(crop)}`;
    byId('parcel-select').value='';
    if(crop?.profileCrop&&getProfile(crop.profileCrop)){
      byId('profile-select').value=crop.profileCrop;
      byId('soil-crop-select').value=crop.profileCrop;
    }
    byId('example-picker').hidden=true;
    byId('live-results').hidden=true;
    renderCustomPrior(crop);renderSoilSelection();renderSoils();updateUrl();
  }

  function renderCustomPrior(crop){
    for(const id of ['metrics-section','comparar','filters-section','resources-section','scenarios-section'])byId(id).hidden=true;
    const card=clear(byId('recommendation-card'));
    const top=elem('div','rec-topline');top.append(elem('span','',crop?'CULTIVO ANTERIOR · CÁLCULO A TU MEDIDA':'ROTACIÓN SIN HISTORIAL PREVIO'),elem('span','pill unknown','Calcula tu escenario'));card.append(top);
    card.append(elem('h2','custom-crop-title',crop?pretty(crop.name):'Sin cultivo anterior especificado'));
    card.append(elem('p','rec-message',crop?'Este cultivo anterior se puede evaluar con tus datos de parcela. El ranking aparecerá al pulsar «Calcular y comparar cultivos siguientes»; no se reutiliza el de otra parcela.':'El motor comparará los cultivos anuales con tus condiciones. Al no haber historial, no aplicará una restricción por familia anterior.'));
    if(crop){
      const stats=elem('div','custom-crop-stats');
      for(const [label,value] of [['Área cosechada media',`${num(crop.harvestAreaMeanHa,0)} ha/año`],['Producción media',`${num(crop.productionMeanT,0)} t/año`],['Rendimiento mediano',crop.yieldP50==null?'Sin rendimiento calculable':`${num(crop.yieldP50,1)} t/ha`],['Años con cosecha',`${crop.years} (${crop.fromYear}–${crop.toYear})`]]){
        const item=elem('div','custom-crop-stat');item.append(elem('span','',label),elem('strong','',value));stats.append(item);
      }
      card.append(stats);
    }
    const note=elem('p','custom-crop-note','Ingresa zona, disponibilidad de agua, suelo y presupuesto para ordenar las alternativas. Los datos de laboratorio vacíos quedarán señalados como pendientes.');card.append(note);
    const profile=crop?.profileCrop&&getProfile(crop.profileCrop);
    if(profile){const button=elem('button','outline-button','Abrir ficha agronómica');button.type='button';button.addEventListener('click',()=>{byId('profile-select').value=profile.cultivo;renderProfiles();byId('cultivos').scrollIntoView({behavior:'smooth'});});card.append(button);}
    renderProfiles();
  }

  function chooseExample(id, crop) {
    state.customPrior=null;state.customMode=false;state.liveResponseActive=false;
    byId('live-results').hidden=true;
    byId('example-picker').hidden=false;
    for(const section of ['metrics-section','comparar','filters-section','resources-section','scenarios-section'])byId(section).hidden=false;
    state.example = state.data.examples.find(e => e.id === id) || state.data.examples[0];
    state.crop = crop && state.example.candidates.some(c => c.crop === crop) ? crop :
      (state.example.candidates.find(c => c.rank === 1) || state.example.candidates[0]).crop;
    byId('parcel-select').value = state.example.id;
    byId('previous-select').value = priorValue(state.example.previousCrop);
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
    if (location.protocol === 'file:' || location.protocol === 'data:') return;
    const url = new URL(location.href);
    if(state.customMode){url.searchParams.delete('parcela');url.searchParams.delete('cultivo');if(state.customPrior)url.searchParams.set('cultivo_anterior',state.customPrior.name);else url.searchParams.delete('cultivo_anterior');history.replaceState(null,'',url);return;}
    url.searchParams.delete('cultivo_anterior');
    url.searchParams.set('parcela',state.example.id);
    url.searchParams.set('cultivo',state.crop);
    history.replaceState(null,'',url);
  }

  function markLiveDirty(){
    if(!byId('live-results'))return;
    if(state.liveResponseActive){
      state.liveResponseActive=false;
      if(state.customMode)renderCustomPrior(state.customPrior);else render();
    }
    if(byId('live-results').hidden)return;
    byId('live-results').hidden=true;
    byId('live-model-status').textContent='Cambiaste una entrada. Vuelve a calcular para actualizar el orden y las razones.';
  }

  function selectedPriorRecord(){
    if(state.customPrior)return state.customPrior;
    const value=byId('previous-select').value;
    return value.startsWith('drap:')?state.data.drapCrops[Number(value.split(':')[1])]:null;
  }

  function quickKey(crop,month){
    const unit=state.selectedSoil,condition=state.selectedCondition||({Palo:'aluvial','Palo Verde':'aluvial',Piura:'aluvial',Cerezal:'arenoso',Pajarito:'salino',Ramón:'salino',Curumuy:'yesoso'}[unit]||'');
    const mode=condition==='salino'?'salino':['arido','arenoso'].includes(condition)?'agua':'normal';
    const poor=['Pajarito','Ramón'].includes(unit)||condition==='salino';
    return [crop?.motorCrop||'',crop?.family||'',month,mode,poor?'pobre':'sin_drenaje_pobre'].join('|');
  }

  function quickReferenceNotes(result){
    result.notes=[
      'Escenario de referencia Bajo Piura: 6 000 m³/ha/mes (derivado del ejemplo del repositorio) y eficiencia 57 % (ANA, línea base del sistema Medio/Bajo Piura). No son mediciones de tu parcela.',
      'El motor sí usa mes, familia del cultivo anterior, drenaje inferido del mapa y condición seleccionada.',
      'ECe, pH, profundidad, pendiente, presupuesto y plagas no se inventan; sus alertas siguen visibles en cada alternativa.'
    ];
    result.globalMissing=[];
    result.quickMode=true;
    result.summary=`Se aceptan ${result.ranking.length} de 14 cultivos anuales en este escenario; se muestran sus tres primeros puestos.`;
    return result;
  }

  function evaluateQuickRotation(){
    const status=byId('quick-model-status'),crop=selectedPriorRecord(),month=Number(byId('quick-month').value);
    const key=quickKey(crop,month),result=state.quick?.[key];
    if(!result){status.textContent='No encuentro esta combinación en el paquete rápido. Actualiza los datos del dashboard y vuelve a abrirlo.';return;}
    const output=quickReferenceNotes(structuredClone(result));
    output.previousCrop=crop?.name||'sin historial';
    output.soilUnit=state.selectedSoil||'sin unidad seleccionada';
    output.soilCondition=state.selectedCondition||'según unidad de suelo';
    output.zone='bajo_piura';
    renderLiveResults(output);
    status.textContent=`Referencia calculada · ${output.ranking.length} opciones anuales aceptadas. Revisa las alertas antes de trasladarla a una parcela.`;
    byId('live-results').scrollIntoView({behavior:'smooth',block:'start'});
  }

  async function evaluateLiveRotation(){
    const button=byId('run-live-model'),status=byId('live-model-status'),crop=selectedPriorRecord();
    const payload={
      previous_crop:crop?.name||'',previous_family:crop?.family||'',previous_model_crop:crop?.motorCrop||'',
      zone:byId('live-zone').value,planting_month:Number(byId('live-month').value),area_ha:byId('live-area').value,
      irrigation_mode:byId('live-water-mode').value,water_m3_month:byId('live-water').value,budget_pen:byId('live-budget').value,
      ece:byId('live-ece').value,ph:byId('live-ph').value,depth_cm:byId('live-depth').value,slope_pct:byId('live-slope').value,
      drainage:byId('live-drainage').value,ecw:byId('live-ecw').value,soil_unit:state.selectedSoil,
      soil_condition:state.selectedCondition,scenario:byId('live-scenario').value,
      water_table_m:byId('live-water-table').value,psi_pct:byId('live-psi').value,
      irrigation_efficiency:byId('live-efficiency').value,irrigation_interval_days:byId('live-irrigation-interval').value,
      fertilizer_n:byId('live-fertilizer-n').value,fertilizer_p:byId('live-fertilizer-p').value,
      fertilizer_k:byId('live-fertilizer-k').value,
      pests:byId('live-pests').value.split(',').map(name=>name.trim()).filter(Boolean)
    };
    const monthly={};for(let month=1;month<=12;month++){const value=byId(`live-water-month-${month}`).value;if(value!=='')monthly[month]=Number(value);}
    if(Object.keys(monthly).length)payload.water_m3_by_month=monthly;
    button.disabled=true;button.textContent='Calculando…';status.textContent='Ejecutando el motor agronómico con estas entradas…';
    try{
      const response=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const raw=await response.text();
      let body;
      try{body=JSON.parse(raw);}catch{
        if(raw.trimStart().startsWith('<'))throw new Error('este alojamiento está sirviendo una página estática y no tiene conectado el motor en vivo. Usa «Cálculo rápido» o ejecuta dashboard/server.py para el cálculo detallado.');
        throw new Error('el servidor devolvió una respuesta que no es JSON');
      }
      if(!response.ok)throw new Error(body.error||`El motor respondió ${response.status}`);
      renderLiveResults(body);
      status.textContent=body.ranking.length?`Cálculo terminado · ${body.ranking.length} cultivos anuales aceptados, ordenados por el motor.`:'Cálculo terminado · no hay recomendación suficiente; revisa los datos esenciales que faltan.';
      byId('live-results').scrollIntoView({behavior:'smooth',block:'start'});
    }catch(error){
      byId('live-results').hidden=true;
      status.textContent=`No pude ejecutar el motor: ${error.message}. Abre el tablero con “python dashboard/server.py”, no con un servidor estático.`;
    }finally{button.disabled=false;button.textContent='Calcular y comparar cultivos siguientes';}
  }

  function measureText(measure,unit){
    if(!measure||measure.value==null)return 'Pendiente de dato';
    const range=measure.min!=null&&measure.max!=null&&Number(measure.min)!==Number(measure.max)?` (${num(measure.min)}–${num(measure.max)})`:'';
    return `${num(measure.value)}${range}${unit||measure.unit?' '+(unit||measure.unit):''}`;
  }

  function renderLiveResults(result){
    state.liveResponseActive=true;
    const card=clear(byId('recommendation-card')),accepted=result.accepted||[],best=accepted[0];
    const previous=pretty(result.previousCrop);
    const topStatus=!best?'Faltan datos esenciales':best.margen_mc?.p50!=null&&best.margen_mc.p50<0?'Primera opción · margen negativo':'Ranking calculado';
    const topline=elem('div','rec-topline');topline.append(elem('span','','ORDEN CALCULADO POR EL MOTOR · '+(result.climateZone||'clima regional')),
      elem('span','pill '+(best?'good':'unknown'),topStatus));card.append(topline);
    card.append(elem('h2','custom-crop-title',best?`${previous} → ${pretty(best.cultivo)}`:`No hay una siguiente opción recomendada todavía`));
    card.append(elem('p','rec-message',best?`${result.quickMode?'Primera opción del escenario rápido.':'Primera opción calculada con tus entradas.'} ${result.summary}`:`El motor no encontró un cultivo anual que pueda recomendar con seguridad. ${result.summary}`));
    if(best){
      const margin=best.margen_mc?.p50!=null?`S/ ${num(best.margen_mc.p50,0)}/ha (P10 ${num(best.margen_mc.p10,0)})`:'Margen: faltan datos';
      card.append(elem('p','custom-crop-note',`Puesto 1 de ${result.ranking.length} aceptados · ${best.familia} · ciclo ${measureText(best.duracion,'días')} · agua bruta ${measureText(best.agua?.riego_bruto_m3_ha,'m³/ha')} · ${margin}.`));
    }
    const cards=clear(byId('live-ranking'));
    if(accepted.length){
      accepted.slice(0,result.quickMode?3:5).forEach(item=>cards.append(renderLiveCandidate(item,result.ranking.indexOf(item.cultivo)+1,result.ranking.indexOf(item.cultivo)===0)));
    }else cards.append(elem('p','live-empty','No hay una opción anual aceptada para estas entradas. Revisa los datos esenciales pendientes y los motivos de descarte que aparecen abajo.'));
    const other=clear(byId('live-alternatives'));
    for(const item of result.accepted.slice(result.quickMode?3:5))other.append(renderLiveCandidate(item,result.ranking.indexOf(item.cultivo)+1,false));
    if(result.quickMode)for(const crop of result.ranking.slice(3)){
      const row=elem('article','live-status-row');row.append(elem('strong','',pretty(crop)),elem('span','pill good',`Aceptado · puesto ${result.ranking.indexOf(crop)+1}`));
      row.append(elem('p','', 'Alternativa aceptada por el escenario de referencia; usa el cálculo detallado para abrir todos sus filtros.'));other.append(row);
    }
    for(const item of result.withoutData||[])other.append(renderCompactStatus(item,'Sin datos suficientes'));
    for(const item of result.rejected||[])other.append(renderCompactStatus(item,'Descartado'));
    const perennials=clear(byId('live-perennials'));
    for(const item of result.perennials||[]){const row=elem('article','live-perennial');row.append(elem('strong','',pretty(item.cultivo)),elem('span','',item.decision==='aceptado'?'Evaluado como sistema perenne':'Requiere revisar filtros'));row.append(elem('p','',`Primera cosecha: ${measureText(item.anios_a_primera_produccion,'años')} · agua anual ${measureText(item.agua_anual?.riego_bruto_m3_ha,'m³/ha')}.`));if(item.datos_faltantes?.length)row.append(elem('small','',`Pendiente: ${item.datos_faltantes.slice(0,3).join('; ')}`));perennials.append(row);}
    const notes=clear(byId('live-notes'));
    if(result.rankingRule)notes.append(elem('p','live-ranking-rule',`Cómo se ordenó: ${result.rankingRule}`));
    for(const text of [...(result.notes||[]),...(result.warnings||[]),...(result.globalMissing||[])].slice(0,12))notes.append(elem('p','',text));
    byId('live-results-title').textContent=best?`Siguiente mejor: ${pretty(best.cultivo)}`:'Qué dato falta para ordenar la rotación';
    byId('live-results-summary').textContent=`Cultivo anterior: ${previous} · suelo: ${result.soilUnit} · condición: ${result.soilCondition} · zona de cálculo: ${result.zone}.`;
    byId('live-results').hidden=false;
    for(const id of ['metrics-section','comparar','filters-section','resources-section','scenarios-section'])byId(id).hidden=true;
  }

  function renderLiveCandidate(item,rank,featured){
    const card=elem('article',`live-candidate${featured?' featured':''}`),head=elem('div','live-candidate-head');
    head.append(elem('span','rank-bubble',String(rank)),elem('div','',null));
    head.lastChild.append(elem('h4','',pretty(item.cultivo)),elem('small','',`${item.familia} · ${item.decision}`));
    card.append(head);
    const metrics=elem('div','live-candidate-metrics');
    const margin=item.margen_mc?.p50==null?'Pendiente':`S/ ${num(item.margen_mc.p50,0)}/ha · P10 ${num(item.margen_mc.p10,0)}`;
    for(const [label,value] of [['Margen simulado',margin],['Ciclo',measureText(item.duracion,'días')],['Riego bruto',measureText(item.agua?.riego_bruto_m3_ha,'m³/ha')],['Rendimiento',measureText(item.rendimiento,'t/ha')]]){const m=elem('div','');m.append(elem('span','',label),elem('strong','',value));metrics.append(m);}card.append(metrics);
    const reasons=(item.veredictos||[]).filter(v=>v.resultado!=='pasa');
    const explanation=elem('details','live-reasons');explanation.append(elem('summary','',`${reasons.length} alertas o datos pendientes · Ver por qué`));
    for(const verdict of reasons.slice(0,6))explanation.append(elem('p','',`${filterNames[verdict.filtro]||pretty(verdict.filtro)}: ${verdict.motivo}`));
    if(item.datos_faltantes?.length)explanation.append(elem('p','',`Datos que podrían cambiar el orden: ${item.datos_faltantes.join('; ')}`));
    card.append(explanation);return card;
  }

  function renderCompactStatus(item,status){
    const row=elem('article','live-status-row');
    row.append(elem('strong','',pretty(item.cultivo)),elem('span','pill unknown',status));
    const reasons=item.motivos_descarte||item.datos_faltantes||[];
    row.append(elem('p','',reasons.slice(0,3).join(' · ')||'Revisar las mediciones y filtros del cultivo.'));
    return row;
  }
  function recommendationLevel(candidate, top) {
    if (!top) return {label:'Ninguna opción viable', css:'danger'};
    if (candidate.decision === 'sin datos') return {label:'No recomendada · fuera del ranking', css:'unknown'};
    if (candidate.decision === 'descartado') return {label:'Cultivo descartado', css:'danger'};
    if (candidate.p50 != null && candidate.p50 < 0) return {label:'Pérdida estimada', css:'danger'};
    const tally = counts(candidate);
    if (tally.advierte || tally.no_evaluable || (candidate.p10 != null && candidate.p10 < 0)) return {label:'Opción con reservas',css:'warning'};
    return {label:'Opción evaluada',css:'good'};
  }
  function editorialMessage(example, candidate, top) {
    if (!top) {
      const missing=candidate.verdicts.filter(v=>v.result==='no_evaluable').map(v=>filterNames[v.filter]||pretty(v.filter));
      const detail=candidate.decision==='sin datos'?` ${pretty(candidate.crop)} también está fuera del ranking porque faltan datos para evaluar ${missing.join(', ')||'filtros críticos'}.`:'';
      return `En este ejemplo no hay ninguno viable entre los cultivos evaluados.${detail} La siguiente decisión es corregir las restricciones o buscar otro escenario.`;
    }
    if (candidate.decision === 'sin datos') {
      const missing=candidate.verdicts.filter(v=>v.result==='no_evaluable').map(v=>filterNames[v.filter]||pretty(v.filter));
      const p=getProfile(candidate.crop),months=Number.parseFloat(p?.ciclo||'');
      const cycleNote=Number.isFinite(months)&&months>=12?` Su ficha reporta un ciclo de ${p.ciclo}; se clasifica mejor como semiperenne que como rotación anual.`:'';
      return `${pretty(candidate.crop)} no es una recomendación ni tiene puesto: el motor la dejó fuera porque no pudo evaluar ${missing.join(', ')||'filtros críticos'}.${cycleNote}`;
    }
    if (candidate.decision === 'descartado') return `${pretty(candidate.crop)} quedó fuera por una o más restricciones que no se deben compensar con un margen alto.`;
    if (candidate.p50 != null && candidate.p50 < 0) return `Es la primera opción del ranking, pero su margen mediano es negativo (${sole(candidate.p50)}/ha). No conviene sembrarla sin revisar agua y costos.`;
    if (example.id === 'bajo_piura_tras_arroz' && candidate.crop === 'arveja') return 'Arveja ocupa el primer lugar, pero el calor durante la floración y la ausencia de siembras registradas en el llano de Bajo Piura hacen que sea una opción exploratoria.';
    if (counts(candidate).no_evaluable > 0) return 'Esta opción supera los filtros que pudieron evaluarse. Faltan datos de campo que todavía podrían cambiar la decisión.';
    return 'Esta opción encabeza el ranking del ejemplo. Compara los riesgos y verifica las mediciones de tu campo antes de sembrar.';
  }
  function renderRecommendation(candidate) {
    const box = clear(byId('recommendation-card'));
    const top = topCandidate();
    const ranked=candidate.rank!=null;
    const level = recommendationLevel(candidate,top);
    const head = elem('div','rec-topline');
    head.append(elem('span','',ranked&&top?.crop===candidate.crop?'PRIMERA OPCIÓN DEL RANKING':ranked?`PUESTO ${candidate.rank} · OPCIÓN EVALUADA`:'CULTIVO EXPLORADO · SIN PUESTO'));
    head.append(elem('span','pill '+level.css,level.label)); box.append(head);
    const journey = elem('div','crop-journey');
    const previous = elem('div','crop-node'); previous.append(elem('span','','Venimos de'),elem('strong','',pretty(state.example.previousCrop)));
    const arrow = elem('span','journey-arrow','→'); arrow.setAttribute('aria-hidden','true');
    const next = elem('div','crop-node next'); next.append(elem('span','',ranked?'Opción evaluada':'No recomendada'),elem('strong','',ranked?pretty(candidate.crop):'Fuera del ranking'));
    journey.append(previous,arrow,next); box.append(journey);
    box.append(elem('p','rec-message',editorialMessage(state.example,candidate,top)));
    if (ranked || candidate.decision === 'descartado' || candidate.decision === 'sin datos') {
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
    const cycleMonths=Number.parseFloat(p.ciclo||'');
    const cropType=p.cultivo==='frijol de palo'&&cycleMonths>=12?'Semiperenne · cosecha escalonada':(p.tipo||'Tipo no especificado');
    card.append(elem('h3','',pretty(p.cultivo)),elem('span','profile-type',cropType));
    const facts=elem('div','profile-facts');
    for(const [label,key] of [['Ciclo / primera cosecha','ciclo'],['Kc de mitad de ciclo','kc_mitad_ciclo'],['Salinidad sin pérdida','ECe_sin_perdida_dS_m'],['Temperatura óptima','temperatura_optima'],['pH óptimo','pH_optimo'],['Raíz máxima','raiz_max'],['N por tonelada','saca_del_suelo_N'],['P₂O₅ / K₂O por tonelada','saca_del_suelo_P2O5'],['N fijado por campaña','deja_N_fijado_por_campana']]){
      let value=p[key];
      if(key==='deja_N_fijado_por_campana'&&p.familia_botanica==='Fabaceae'&&String(value||'').startsWith('no fija N'))value='Leguminosa; fijación de N no cuantificada';
      if(key==='saca_del_suelo_P2O5')value=(p.saca_del_suelo_P2O5||'Sin dato')+' / '+(p.saca_del_suelo_K2O||'Sin dato');
      const node=elem('div','profile-fact');node.append(elem('span','',label),elem('strong','',value||'Sin dato'));facts.append(node);
    }
    card.append(facts);
    const rotation=elem('div','profile-rotation');
    const family=p.familia_botanica;
    const alternateFamilies=[...new Set(state.data.profiles.map(x=>x.familia_botanica).filter(x=>x&&x!==family))].slice(0,5);
    const rotationText=p.conviene_despues||`Guía general: alternar ${family||'la familia botánica de este cultivo'} con otra familia. En el catálogo aparecen ${alternateFamilies.join(', ')||'otras familias'}; esta regla orienta la secuencia, no sustituye el filtro de suelo, agua, clima y mercado.`;
    const watchText=p.evitar_o_cuidar_despues||`Evita repetir ${family||'la misma familia'} en campañas seguidas cuando haya presión de plagas o enfermedades compartidas; confirma el historial sanitario del lote.`;
    rotation.append(elem('p','',`Rotación y relevo: ${rotationText}`),elem('p','',`Vigilancia: ${watchText}`));card.append(rotation);
    card.append(elem('p','profile-sources',`Referencias: ${p.fuentes_principales||'Consultar el dataset detallado.'}`));
    const detailRows=state.data.cropDetails[canonicalCrop(p.cultivo)]||[];
    const details=elem('details','crop-data-details');details.append(elem('summary','',detailRows.length?`Ver ${detailRows.length} registros agronómicos con evidencia y fuente`:'Sin ficha agronómica detallada para este cultivo en las tablas cargadas'));
    if(!detailRows.length)details.append(elem('p','crop-note','Este cultivo conserva su ficha resumen y aparece en el motor, pero falta una ficha por etapa. No se le asignaron cifras de otro cultivo parecido.'));
    if(detailRows.length){const tally={estimado:0,observado:0,desconocido:0};for(const row of detailRows)if(row.status in tally)tally[row.status]++;details.append(elem('p','crop-note',`${tally.observado} observados · ${tally.estimado} estimados · ${tally.desconocido} desconocidos. “Estimado” incluye referencias bibliográficas y análogos; revisa confianza, método y notas en cada fila.`));}
    const scroll=elem('div','crop-data-scroll'),table=elem('table',''),head=elem('thead',''),trh=elem('tr','');
    for(const title of ['Dato','Valor / rango','Variedad, etapa y lugar','Evidencia y confianza','Fuente, fecha y notas'])trh.append(elem('th','',title));head.append(trh);table.append(head);
    const tbody=elem('tbody','');
    for(const row of detailRows){
      const tr=elem('tr','');tr.append(elem('td','',pretty(row.variable)));
      tr.append(elem('td','',`${row.value||'—'}${row.min||row.max?` (${row.min||'—'}–${row.max||'—'})`:''}${row.unit?' '+row.unit:''}`));
      tr.append(elem('td','',`${row.variety||'Variedad no indicada'} · ${row.stage||'Etapa no especificada'} · ${row.place||zones[row.zone]||row.zone||'lugar no indicado'}${row.date?' · '+row.date:''}`));
      const quality=elem('td','');quality.append(elem('span','pill '+(row.status==='observado'?'good':row.status==='desconocido'?'unknown':'warning'),row.status||'estado no indicado'));
      quality.append(elem('small','crop-note',`${row.evidence||'tipo de evidencia no indicado'} · confianza ${row.confidence||'no indicada'}${row.method?' · '+row.method:''}`));tr.append(quality);
      const source=elem('td','');addLink(source,row.source||'Fuente sin nombre',row.url);if(row.date)source.append(elem('small','crop-note',row.date));if(row.notes)source.append(elem('small','crop-note',row.notes));tr.append(source);tbody.append(tr);
    }
    table.append(tbody);scroll.append(table);details.append(scroll);card.append(details);return card;
  }
  function renderProfiles() {
    const grid=clear(byId('crop-profiles'));
    const previous=state.customPrior?(state.customPrior.profileCrop||canonicalCrop(state.customPrior.name)):state.example?.previousCrop;
    grid.append(profileCard(previous,'Cultivo anterior'),profileCard(byId('profile-select').value,'Cultivo que exploras'));
  }
  function renderDrapCrops(){
    const query=byId('drap-crop-search').value.trim().toLowerCase();
    const role=byId('drap-crop-role').value;
    const rows=state.data.drapCrops.filter(c=>(role==='todos'||c.motorRole===role)&&(!query||pretty(c.name).toLowerCase().includes(query)));
    const body=clear(byId('drap-crop-table'));
    for(const c of rows){
      const tr=elem('tr','');
      const label=elem('td','');label.append(elem('strong','',pretty(c.name)),elem('small','crop-note',`DRAP ${c.fromYear}–${c.toYear}`));
      const cropProfile=c.profileCrop&&state.data.profiles.find(p=>canonicalCrop(p.cultivo)===c.profileCrop);
      if(cropProfile){const button=elem('button','crop-profile-link','Abrir ficha agronómica');button.type='button';button.addEventListener('click',()=>{byId('profile-select').value=cropProfile.cultivo;renderProfiles();byId('crop-profiles').scrollIntoView({behavior:'smooth',block:'start'});});label.append(button);}
      tr.append(label,elem('td','',`${num(c.harvestAreaMeanHa,0)} ha/año`),elem('td','',`${num(c.productionMeanT,0)} t/año`),elem('td','',c.yieldP50==null?'Sin rendimiento calculable':`${num(c.yieldP50,1)} t/ha (${num(c.yieldP10,1)}–${num(c.yieldP90,1)})`),elem('td','',c.priceMedianNominal==null?'Sin precio':`S/ ${num(c.priceMedianNominal,2)}/kg`),elem('td','',`${c.years} (${c.fromYear}–${c.toYear})`));
      const status=c.motorRole==='rotacion_anual'?'Motor · anual':c.motorRole==='perenne'?'Motor · perenne':'DRAP · producción local';tr.append(elem('td','',status));body.append(tr);
    }
    byId('drap-crop-count').textContent=`${rows.length} de ${state.data.drapCrops.length} cultivos registrados. Las áreas y producción son promedios por año con cosecha reportada; el precio es nominal, no ajustado por inflación.`;
    const chart=clear(byId('crop-production-chart'));
    const top=state.data.drapCrops.slice().sort((a,b)=>(b.latestProductionT||0)-(a.latestProductionT||0)).slice(0,12);
    const w=850,left=185,right=85,rowH=27,topPad=15,bottom=25,h=topPad+top.length*rowH+bottom;
    const max=d3.max(top,c=>c.latestProductionT)||1,x=d3.scaleLinear().domain([0,max]).range([left,w-right]);
    const svg=d3.select(chart).append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img').attr('aria-label','Producción reportada por cultivo en el último año disponible de la DRAP');
    const g=svg.selectAll('g').data(top).join('g').attr('transform',(_,i)=>`translate(0,${topPad+i*rowH})`).attr('tabindex',0).attr('role','button').attr('aria-label',c=>`${pretty(c.name)}, ${num(c.latestProductionT,0)} toneladas en ${c.latestYear}`).on('click',(_,c)=>{byId('drap-crop-search').value=pretty(c.name);renderDrapCrops();byId('drap-crop-table').scrollIntoView({behavior:'smooth',block:'start'});});
    g.append('text').attr('class','crop-label').attr('x',left-10).attr('y',16).attr('text-anchor','end').text(c=>pretty(c.name));
    g.append('rect').attr('x',left).attr('y',2).attr('width',c=>x(c.latestProductionT)-left).attr('height',19).attr('rx',5).attr('fill','#76a77b');
    g.append('text').attr('class','bar-label').attr('x',c=>x(c.latestProductionT)+6).attr('y',16).text(c=>`${num(c.latestProductionT,0)} t · ${c.latestYear}`);
  }
  function soilCropGuidance(unit,crop){
    const threshold=getProfile(crop)?.ECe_sin_perdida_dS_m;
    if(unit.soil_unit==='Pajarito'||unit.soil_unit==='Ramón')return threshold?
      `Salinidad y mal drenaje documentados. ${pretty(crop)} tiene umbral bibliográfico de ${threshold}; falta ECe medida en esta unidad para comparar.`:
      'Salinidad y mal drenaje documentados. Falta un umbral fiable del cultivo y ECe medida de esta unidad.';
    if(unit.soil_unit==='Cerezal')return `Suelo arenoso con baja retención de agua y nutrientes. Para ${pretty(crop)} hay que valorar frecuencia de riego y fertilización; el mapa no permite declararlo apto.`;
    if(unit.soil_unit==='Curumuy')return 'Yeso y carbonatos posibles. La química del perfil y el acceso al agua deben medirse antes de escoger el cultivo.';
    return 'Suelo aluvial sin limitación específica cuantificada en esta ficha. La compatibilidad queda pendiente de medir ECe, pH, drenaje y profundidad en el lote.';
  }
  function renderSoilSelection(){
    const box=clear(byId('soil-selection-summary'));
    const soil=state.data.soilUnits.find(item=>item.soil_unit===state.selectedSoil);
    const condition=soilConditions[state.selectedCondition];
    if(!soil&&!condition){box.append(elem('p','','Elige una unidad edáfica y, si la conoces, una condición dominante del terreno.'));return;}
    if(soil){
      box.append(elem('strong','soil-selection-title',soil.soil_unit));
      box.append(elem('p','',`${soil.soil_taxonomy_order_1999} · ${soil.soil_taxonomy_group_1999} · ${soil.fao_1990_map_label}`));
      box.append(elem('p','',`Textura: ${soil.texture_evidence||'sin descripción'} · Relieve: ${soil.geomorphic_setting||'no consignado'}`));
      box.append(elem('p','',`Limitación documentada: ${soil.known_constraints||'no consignada'}`));
      const source=elem('div','soil-source');addLink(source,'Fuente SIAR Piura ↗',soil.source_url);box.append(source);
    }
    if(condition){box.append(elem('strong','soil-selection-title',condition.label),elem('p','',condition.description));}
    box.append(elem('p','soil-selection-caveat','Clasificación/cartografía de referencia; no representa mediciones de tu parcela ni recalcula el ranking del ejemplo.'));
  }
  function renderSoils(){
    const mode=byId('soil-region-select').value,crop=byId('soil-crop-select').value;
    const box=clear(byId('soil-cards')),summary=clear(byId('soil-summary')),mapBox=clear(byId('soil-map-units')),conditions=clear(byId('soil-conditions'));
    if(mode==='bajo'){
      summary.append(elem('p','',`El mapa histórico del Bajo Piura registra ${state.data.soilUnits.length} unidades edáficas —seis series/subgrupos de Entisoles y Aridisoles— y ${state.data.soilMapUnits.length} asociaciones cartográficas con pendientes. “Árido”, “húmedo/mal drenado”, “arenoso” y “agrietado” describen clima o propiedades del suelo; no son intercambiables con el nombre taxonómico.`));
      const conditionsList=[
        ['Aluvial, textura media a fina','Palo Verde y Piura. Sedimentos aluviales; baja a media fertilidad descrita. La textura y profundidad cambian entre perfiles.'],
        ['Arenoso, retención baja','Cerezal. Arena/arena franca, muy baja fertilidad y menor retención de agua y nutrientes.'],
        ['Salino y con drenaje pobre','Pajarito y Ramón. El estudio describe salinidad y mal drenaje; su rango de CE cubre el área y no asigna el mismo valor a cada parcela.'],
        ['Yeso/carbonatos','Curumuy. Terraza marina; la química y el acceso al agua son condicionantes que deben confirmarse en el lote.'],
        ['Árido / superárido','El estudio SIAR describe zonas de vida desecadas y superáridas en sectores del Bajo Piura. Es clasificación climática y el agua limita el cultivo; no equivale a un orden de suelo.'],
        ['Agrietado / expansivo','La cartografía verificada no clasifica una serie Vertisol/vertic. Las grietas estacionales deben observarse en campo y confirmarse con arcilla/expansividad; no se infieren solo por zona.']
      ];
      for(const [title,description] of conditionsList){const card=elem('article','soil-condition-card');card.append(elem('strong','',title),elem('p','',description));conditions.append(card);}
      let selectedUnits=state.selectedSoil?state.data.soilUnits.filter(soil=>soil.soil_unit===state.selectedSoil):state.data.soilUnits;
      const condition=soilConditions[state.selectedCondition];
      if(condition?.units.length)selectedUnits=selectedUnits.filter(soil=>condition.units.includes(soil.soil_unit));
      if(state.selectedSoil||condition?.units.length)summary.append(elem('p','soil-selection-active',`Filtro activo: ${[state.selectedSoil,condition?.label].filter(Boolean).join(' · ')}. Usa “Elige una unidad edáfica” y borra la condición para volver a todas.`));
      if(state.selectedSoil&&condition?.units.length&&!selectedUnits.length)summary.append(elem('p','soil-selection-active','La unidad y la condición seleccionadas no coinciden en el mapa consultado. Revisa los dos selectores.'));
      for(const soil of selectedUnits){
        const card=elem('article','soil-card');card.append(elem('span','soil-kicker','BAJO PIURA · UNIDAD DE SUELO'),elem('h3','',soil.soil_unit));
        card.append(elem('div','soil-taxonomy',`${soil.soil_taxonomy_order_1999} · ${soil.soil_taxonomy_group_1999} · ${soil.fao_1990_map_label}`));
        const facts=elem('div','soil-facts');
        for(const [label,value] of [['Textura descrita',soil.texture_evidence],['Fertilidad descrita',soil.fertility_evidence],['Relieve',soil.geomorphic_setting],['Profundidad de perfil medida',soil.profile_depth_cm?soil.profile_depth_cm+' cm':'Sin medición por unidad'],['ECe medida',soil.ECe_dS_m||'Sin medición por unidad'],['pH medido',soil.pH||'Sin medición por unidad'],['N disponible medido',soil.available_N_mg_kg||'Sin medición por unidad'],['P disponible medido',soil.available_P_mg_kg||'Sin medición por unidad'],['K intercambiable medido',soil.exchangeable_K_cmol_kg||'Sin medición por unidad'],['Restricción',soil.known_constraints]]){const f=elem('div','soil-fact');f.append(elem('span','',label),elem('strong','',value||'No consignado'));facts.append(f);}card.append(facts);
        card.append(elem('p','soil-match-note',soilCropGuidance(soil,crop)));
        const source=elem('div','soil-source');source.append(document.createTextNode(`SIAR Piura, pp. ${soil.source_pages}. `));addLink(source,'Abrir estudio ↗',soil.source_url);card.append(source);box.append(card);
      }
      const title=elem('h3','soil-map-title','Asociaciones cartográficas y pendiente');
      mapBox.append(title,elem('p','soil-summary','Son combinaciones de unidad y pendiente del mapa histórico; no representan lotes uniformes ni una recomendación automática de cultivo. El área es la publicada en el cuadro cartográfico.'));
      const scroller=elem('div','table-scroll'),table=elem('table',''),thead=elem('thead',''),trh=elem('tr','');
      for(const label of ['Unidad cartográfica','Clase de pendiente','Rango','Área histórica','Alcance','Fuente'])trh.append(elem('th','',label));thead.append(trh);table.append(thead);
      const tbody=elem('tbody','');
      for(const unit of state.data.soilMapUnits){const tr=elem('tr','');tr.append(elem('td','',unit.map_unit),elem('td','',unit.slope_class||'No indicada'),elem('td','',unit.slope_range||'No indicado'),elem('td','',unit.area_ha?`${num(unit.area_ha)} ha`:'Sin dato'),elem('td','',unit.status));const source=elem('td','');addLink(source,'SIAR ↗',unit.source_url);tr.append(source);tbody.append(tr);}
      table.append(tbody);scroller.append(table);mapBox.append(scroller);
    }else if(mode==='cuencas'){
      const basins=[...new Set(state.data.soilCumBasins.map(x=>x.basin))];
      summary.append(elem('p','','Extracto de tres mapas oficiales de capacidad de uso mayor del suelo (CUM), publicados en 2008. La CUM clasifica usos, limitaciones y calidad agrológica; no es taxonomía edáfica. En Huancabamba el mapa destaca pastoreo de páramo, forestal y protección; no se debe leer como recomendación de un cultivo anual.'));
      for(const basin of basins){
        const records=state.data.soilCumBasins.filter(x=>x.basin===basin),card=elem('article','soil-card');
        card.append(elem('span','soil-kicker','CUM · CARTOGRAFÍA DE CUENCA'),elem('h3','',`Río ${basin}`),elem('div','soil-taxonomy',`${records.length} combinaciones de capacidad de uso`));
        const scroll=elem('div','soil-table-scroll'),table=elem('table',''),thead=elem('thead',''),trh=elem('tr','');
        for(const title of ['Código CUM','Uso y limitaciones','Área publicada'])trh.append(elem('th','',title));thead.append(trh);table.append(thead);
        const tbody=elem('tbody','');for(const r of records){const tr=elem('tr','');tr.append(elem('td','',r.map_code),elem('td','',r.description),elem('td','',`${num(r.area_ha,0)} ha`));tbody.append(tr);}table.append(tbody);scroll.append(table);card.append(scroll);
        const source=elem('div','soil-source');source.append(document.createTextNode('Gobierno Regional de Piura · mapa histórico 2008. '));addLink(source,'Abrir mapa ↗',records[0].source_url);card.append(source);box.append(card);
      }
      mapBox.append(elem('p','soil-summary','Claves habituales de la leyenda: A = cultivo en limpio; C = cultivo permanente; P = pastoreo; F = forestal; X = protección. Los sufijos describen calidad agrológica, limitaciones y riego según la leyenda de cada mapa.'));
    }else if(mode==='montero'){
      summary.append(elem('p','','Seis clases de capacidad de uso de la microzonificación de Montero, Ayabaca (circa 2016). Son clases de uso y pendiente, no seis tipos taxonómicos de suelo ni toda la sierra piurana.'));
      for(const soil of state.data.soilCum){
        const card=elem('article','soil-card');card.append(elem('span','soil-kicker','MONTERO · CAPACIDAD DE USO'),elem('h3','',soil.cum_class),elem('div','soil-taxonomy',soil.land_use_capability));
        const facts=elem('div','soil-facts');
        for(const [label,value] of [['Pendiente',soil.slope_pct_as_documented+' %'],['Textura',soil.texture],['Profundidad',soil.effective_depth],['pH descrito',soil.pH_description],['Limitaciones',soil.limitations]]){const f=elem('div','soil-fact');f.append(elem('span','',label),elem('strong','',value||'No especificado'));facts.append(f);}card.append(facts);
        card.append(elem('p','soil-match-note',`${soil.decision_constraint}. Para ${pretty(crop)}, esta restricción de uso manda; confirma el polígono y la zonificación.`));
        const source=elem('div','soil-source');source.append(document.createTextNode(`SIGRID/CENEPRED, pp. ${soil.source_pages}. `));addLink(source,'Abrir memoria ↗',soil.source_url);card.append(source);box.append(card);
      }
    }else{
      const select=elem('select','');select.id='soil-zone-inner';select.setAttribute('aria-label','Zona de Piura');
      for(const z of state.data.soilZones){const o=elem('option','',zones[z.zone]||z.zone);o.value=z.zone;select.append(o);}summary.append(elem('label','','Datos de suelo por zona: '),select);
      const draw=()=>{clear(box);const z=state.data.soilZones.find(x=>x.zone===select.value);if(!z)return;
        if(!z.measurements.length){box.append(elem('p','empty-state','Esta tabla no contiene valores de suelo para esta zona. Consulta los CSV de fuentes y solicita muestreo local antes de inferir condiciones.'));return;}
        for(const m of z.measurements){const card=elem('article','soil-card zone-soil-card');card.append(elem('span','soil-kicker',zones[z.zone]||z.zone),elem('h3','',soilVariables[m.variable]||pretty(m.variable)));
          const value=m.value||((m.min||m.max)?`${m.min||'—'}–${m.max||'—'}`:'Sin medición');card.append(elem('div','zone-soil-value',`${value}${m.unit?' '+m.unit:''}`));
          card.append(elem('span','pill '+(m.status==='desconocido'?'unknown':m.evidence==='medicion_local'?'good':'warning'),`${m.status||'sin estado'} · ${m.evidence||'evidencia no indicada'}`));
          if(m.place)card.append(elem('p','soil-match-note','Lugar / cobertura: '+m.place));
          if(m.method)card.append(elem('p','soil-match-note','Método: '+m.method));
          if(m.notes)card.append(elem('p','soil-match-note',m.notes));const source=elem('div','soil-source');source.append(document.createTextNode((m.source||'Fuente no indicada')+' '));addLink(source,'Fuente ↗',m.url);card.append(source);box.append(card);
        }};
      select.addEventListener('change',draw);select.value=state.data.soilZones.find(z=>z.zone==='bajo_piura')?.zone||state.data.soilZones[0]?.zone;draw();
    }
  }
  function render() {
    if(state.customPrior){renderCustomPrior(state.customPrior);renderSoils();return;}
    const candidate=currentCandidate();if(!candidate)return;
    renderRecommendation(candidate);renderMetrics(candidate);renderAlternatives();renderMarginChart();renderFilters(candidate);renderWater(candidate);renderNutrients(candidate);renderRecovery(candidate);renderScenarios(candidate);
    byId('profile-select').value=getProfile(candidate.crop)?candidate.crop:state.data.profiles[0].cultivo;
    renderProfiles();renderSoilSelection();renderSoils();
  }

  async function loadEvidence() {
    const button=byId('load-evidence');button.disabled=true;button.textContent='Cargando datos…';
    try {
      if(!state.evidence){
        const embedded=byId('evidence-inline-data');
        const normalizeRow=row=>{
          const normalized={};for(const [key,value] of Object.entries(row))normalized[key.replace(/^\uFEFF/,'')]=value;
          return normalized;
        };
        if(embedded){
          if(!('DecompressionStream' in window))throw new Error('Este navegador no permite abrir los datos comprimidos; usa la versión servida del dashboard.');
          const base64=embedded.textContent.trim();
          const binary=atob(base64);
          const bytes=Uint8Array.from(binary,char=>char.charCodeAt(0));
          const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
          state.evidence=d3.csvParse(await new Response(stream).text(),normalizeRow);
        }else state.evidence=await d3.csv('../piura-agro/consolidado/piura_super_dataset.csv',normalizeRow);
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
      const inline=byId('dashboard-inline-data');
      if(inline)state.data=JSON.parse(inline.textContent);
      else {const response=await fetch('./data/dashboard.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);state.data=await response.json();}
      const quickInline=byId('quick-rotation-inline-data');
      let compressed;
      if(quickInline)compressed=Uint8Array.from(atob(quickInline.textContent.trim()),character=>character.charCodeAt(0));
      else {const response=await fetch('./data/quick_rotation.json.gz');if(!response.ok)throw new Error(`HTTP ${response.status}`);compressed=new Uint8Array(await response.arrayBuffer());}
      let quickText;
      try{const decoded=new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));quickText=await new Response(decoded).text();}
      catch{quickText=new TextDecoder().decode(compressed);}
      state.quick=JSON.parse(quickText);
      if(!state.data.examples?.length||!state.data.profiles?.length)throw new Error('Snapshot incompleto');
      populateControls();
      const query=new URL(location.href).searchParams;
      if(query.has('cultivo_anterior')){
        const crop=state.data.drapCrops.find(item=>item.name===query.get('cultivo_anterior'));
        if(crop)chooseCustomPrior(crop);else chooseExample(query.get('parcela')||state.data.examples[0].id,query.get('cultivo'));
      }else chooseExample(query.get('parcela')||state.data.examples[0].id,query.get('cultivo'));
    }catch(error){
      console.error(error);
      byId('data-stamp').textContent='No se pudieron cargar los datos';
      byId('recommendation-card').replaceChildren(elem('div','error-state','No se pudo abrir el dashboard. Inicia un servidor desde la raíz del repositorio: python -m http.server 8000; luego entra a /dashboard/.'));
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
