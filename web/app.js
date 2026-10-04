'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const repo = 'https://github.com/solarfren69420/GameDecompLibrary';
const colors = ['#4e758b','#807450','#557d68','#74629d','#a6654f','#547e9e','#8c635a','#627f73'];
const state = {data:null,category:'decomp',page:1,selected:null,pageSize:20};
function mark(project){
  let hash=0;for(const c of project.id) hash=(hash+c.charCodeAt(0))%colors.length;
  const letters=project.name.replace(/^The (Legend of Zelda: )?/,'').split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();
  return `<span class="project-mark" style="--cover:${colors[hash]}" aria-hidden="true">${esc(letters)}</span>`;
}
function platformLabel(project){
  const p=project.platform;
  if(project.category==='tool')return project.type;
  if(project.category==='related')return project.type;
  if(p.startsWith('Switch'))return 'Switch';
  if(p.startsWith('Windows'))return 'Windows';
  return p==='Not specified'?'Unspecified':p;
}
function badge(project){
  const p=platformLabel(project);
  const kind=/GameCube|Wii|Nintendo 64/.test(p)?'cube':/Switch|Game Boy|Nintendo DS/.test(p)?'nintendo':/Xbox/.test(p)?'xbox':/PlayStation/.test(p)?'ps':'pc';
  return `<span class="platform-badge ${kind}">${esc(p)}</span>`;
}
function metric(project,key){
  const v=project.progress[key];
  if(v===null||v===undefined){
    const label=project.category==='tool'||project.category==='related'?'Not applicable':project.progress.kind==='claim'?'Completion claim':project.progress.kind==='functions'?'Function count':key==='linked'?'Not reported':'Not published';
    return `<span class="unknown" title="${esc(project.progress.label)}">${label}</span>`;
  }
  return `<div class="metric"><span class="track" aria-hidden="true"><i style="width:${Number(v)}%"></i></span><span class="metric-value">${v}%</span></div>`;
}
function filters(){
  const query=$('search').value.toLocaleLowerCase().trim();
  let list=state.data.projects.filter(p=>p.category===state.category);
  list=list.filter(p=>(!$('platform').value||platformLabel(p)===$('platform').value)&&(!query||[p.name,p.url,p.type,p.description,p.group,...p.notes].join(' ').toLocaleLowerCase().includes(query)));
  const status=$('status').value;
  if(status==='reported')list=list.filter(p=>p.progress.decompiled!==null);
  if(status==='complete')list=list.filter(p=>p.progress.decompiled===100);
  if(status==='unknown')list=list.filter(p=>p.progress.decompiled===null);
  if($('sort').value==='name')list.sort((a,b)=>a.name.localeCompare(b.name));
  if($('sort').value==='progress')list.sort((a,b)=>(b.progress.decompiled??-1)-(a.progress.decompiled??-1));
  if($('sort').value==='date')list.sort((a,b)=>(b.report_date||'').localeCompare(a.report_date||''));
  return list;
}
function render(){
  const list=filters(), pages=Math.max(1,Math.ceil(list.length/state.pageSize));
  state.page=Math.min(state.page,pages);
  const start=(state.page-1)*state.pageSize, visible=list.slice(start,start+state.pageSize);
  $('result-count').textContent=`${list.length} ${state.category==='tool'?'tools':'projects'}${$('search').value?' found':' in the library'}`;
  $('rows').innerHTML=visible.map(p=>`<tr class="${p.id===state.selected?'is-selected':''}"><td><div class="project-cell">${mark(p)}<div><a class="project-name" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.name)}</a><span class="repo-name">${esc(p.url.replace(/^https:\/\/(github|gitlab)\.com\//,''))}</span></div></div></td><td>${badge(p)}</td><td>${metric(p,'decompiled')}</td><td>${metric(p,'linked')}</td><td>${p.sources.length?`<a class="source-link" target="_blank" rel="noopener noreferrer" href="${esc(p.sources[0])}" title="Snapshot ${esc(p.snapshot_date)}"><span aria-hidden="true">◎</span> Source ↗</a>`:'<span class="unknown">Unverified</span>'}</td><td><button class="detail-button" data-project="${esc(p.id)}" aria-label="View details for ${esc(p.name)}" aria-pressed="${p.id===state.selected}">›</button></td></tr>`).join('');
  $('empty').hidden=!!list.length;
  document.querySelector('.table-scroll').hidden=!list.length;
  $('page-info').textContent=list.length?`Showing ${start+1}–${Math.min(start+state.pageSize,list.length)} of ${list.length}`:'0 projects';
  $('page-number').textContent=`${state.page} / ${pages}`;
  $('previous').disabled=state.page===1;
  $('next').disabled=state.page===pages;
  $('platform-heading').textContent=state.category==='tool'||state.category==='related'?'Project type':'Platform';
}
function selectProject(id,updateHash=true){
  const p=state.data.projects.find(p=>p.id===id);if(!p)return;
  state.selected=p.id;
  const date=p.report_date?p.report_date.slice(0,10):p.snapshot_date;
  const metrics=`<div class="detail-row"><span>Decompiled</span><span>${metric(p,'decompiled')}</span></div><div class="detail-row"><span>Fully linked</span><span>${metric(p,'linked')}</span></div>`;
  const sources=p.sources.map((url,i)=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${i===0?'Progress / project evidence':'Additional evidence'} ↗</a>`).join('');
  const targetNotes=p.targets.length>1?`<div class="notes">${p.targets.map(t=>`<p><strong>${esc(t.name)}</strong><br>${esc(t.platform)}<br>${esc(t.progress.label)}</p>`).join('')}</div>`:'';
  $('selected').innerHTML=`<h2>Selected project</h2><div class="selected-head">${mark(p)}<div><a class="selected-title" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.name)}</a><span class="selected-repo">${esc(p.url.split('/').slice(3).join('/'))}</span></div></div>${badge(p)}${p.description?`<p class="description">${esc(p.description)}</p>`:''}${metrics}<div class="detail-row"><span>Metric</span><span>${esc({reported:'Published target',unknown:'No numeric metric',claim:'Maintainer claim',functions:'Matching functions'}[p.progress.kind])}</span></div><div class="detail-row"><span>Build / tests</span><span>Not verified here</span></div>${targetNotes}<div class="evidence">${sources}${p.report_commit?`<a href="${esc(p.report_commit)}" target="_blank" rel="noopener noreferrer">Reported commit ↗</a>`:''}<div class="date">${p.report_date?'Underlying report':'Source snapshot'}: ${esc(date)}<br>Catalog snapshot: ${esc(p.snapshot_date)}</div><details><summary>Scope & original source notes</summary><div class="notes">${p.notes.map(note=>`<p>${esc(note)}</p>`).join('')||'<p>No additional notes supplied.</p>'}</div></details></div><div class="detail-actions"><a href="${repo}/edit/main/data/projects/${encodeURIComponent(p.id)}.json" target="_blank" rel="noopener noreferrer">Edit entry ↗</a><a href="${repo}/issues/new?template=update-project.yml&title=${encodeURIComponent('[Update] '+p.name)}&repository=${encodeURIComponent(p.url)}" target="_blank" rel="noopener noreferrer">Suggest update ↗</a><button class="detail-button" id="copy-link" aria-label="Copy link to this project" title="Copy project link">⧉</button></div>`;
  $('copy-link').addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(`${location.href.split('#')[0]}#project=${encodeURIComponent(p.id)}`);$('copy-link').textContent='✓';$('copy-link').title='Copied';}
    catch{const a=document.createElement('input');a.value=location.href;a.setAttribute('aria-label','Project link');$('copy-link').replaceWith(a);a.select();}
  });
  if(updateHash)history.replaceState(null,'',`#project=${encodeURIComponent(p.id)}`);
  render();
}
function changeCategory(category,selectDefault=true){
  state.category=category;state.page=1;
  document.querySelectorAll('[data-category]').forEach(b=>{const active=b.dataset.category===category;b.setAttribute('aria-selected',active);b.tabIndex=active?0:-1;});
  $('catalog-panel').setAttribute('aria-labelledby',`tab-${category}`);
  const platforms=[...new Set(state.data.projects.filter(p=>p.category===category).map(platformLabel))].sort();
  $('platform').innerHTML=`<option value="">All ${category==='tool'||category==='related'?'types':'platforms'}</option>`+platforms.map(p=>`<option value="${esc(p)}">${esc(p)}</option>`).join('');
  $('status').value='';$('status').disabled=category==='tool'||category==='related';
  render();
  const visible=filters();
  if(selectDefault&&visible.length&&!visible.some(p=>p.id===state.selected))selectProject(visible[0].id);
}
function openSharedProject(){
  if(!location.hash.startsWith('#project='))return;
  let id;try{id=decodeURIComponent(location.hash.slice(9));}catch{return;}
  const project=state.data.projects.find(p=>p.id===id);if(!project)return;
  $('search').value='';
  changeCategory(project.category,false);
  selectProject(project.id,false);
  state.page=Math.floor(filters().findIndex(p=>p.id===id)/state.pageSize)+1;
  render();
}
async function init(){
  try{
    const response=await fetch('catalog.json');if(!response.ok)throw new Error('Catalog unavailable');
    state.data=await response.json();
    const total=state.data.projects.length;
    $('stats').innerHTML=[['blue','▦',`${total} projects`,'One shared source library'],['green','⌘',`${state.data.counts.decomp} game projects`,'Original repositories preserved'],['purple','⚙',`${state.data.counts.tool} bindings & tools`,'Rust and companion tooling'],['gold','↗','Open to contributions','Submit a GitHub. Build together.']].map(([color,icon,title,sub])=>`<div class="stat"><span class="stat-icon ${color}" aria-hidden="true">${icon}</span><div><strong>${esc(title)}</strong><small>${esc(sub)}</small></div></div>`).join('');
    for(const category of ['decomp','tool','related','unconfirmed'])$(`count-${category}`).textContent=state.data.counts[category]||0;
    $('discovery').innerHTML=state.data.discovery.map(url=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(url.includes('decomp.dev')?'decomp.dev progress tracker':url.split('/').pop())} ↗</a>`).join('');
    for(const id of ['search','platform','status','sort'])$(id).addEventListener(id==='search'?'input':'change',()=>{state.page=1;render();});
    $('clear-filters').addEventListener('click',()=>{$('search').value='';$('platform').value='';$('status').value='';state.page=1;render();});
    $('previous').addEventListener('click',()=>{state.page--;render();});
    $('next').addEventListener('click',()=>{state.page++;render();});
    $('rows').addEventListener('click',event=>{const button=event.target.closest('[data-project]');if(button)selectProject(button.dataset.project);});
    document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>changeCategory(button.dataset.category)));
    document.querySelector('.tabs').addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const tabs=[...document.querySelectorAll('[data-category]')],index=tabs.indexOf(document.activeElement);
      const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
      tabs[next].focus();changeCategory(tabs[next].dataset.category);
    });
    document.addEventListener('keydown',event=>{if(event.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){event.preventDefault();$('search').focus();}});
    window.addEventListener('hashchange',openSharedProject);
    let initial=null;
    if(location.hash.startsWith('#project=')){try{const id=decodeURIComponent(location.hash.slice(9));initial=state.data.projects.find(p=>p.id===id);}catch{}}
    changeCategory(initial?.category||'decomp',false);
    selectProject(initial?.id||state.data.projects[0].id,false);
    if(initial){const position=filters().findIndex(p=>p.id===initial.id);state.page=Math.floor(position/state.pageSize)+1;render();}
  }catch(error){$('result-count').textContent='The catalog could not be loaded.';$('empty').hidden=false;$('empty').innerHTML=`<h2>Unable to load the catalog</h2><p>Refresh this page, or <a href="${repo}/blob/main/CATALOG.md">browse all projects on GitHub</a>.</p>`;console.error(error);}
}
init();
