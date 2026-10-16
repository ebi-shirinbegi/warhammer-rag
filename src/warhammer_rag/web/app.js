const $ = selector => document.querySelector(selector);
let token = '', busy = false, failedQuestion = '', saveQueue = Promise.resolve(), draftTimer;
const welcome = $('#welcome');
const initialSources = $('#sources').innerHTML;
const newRecord = () => ({id:crypto.randomUUID().replaceAll('-',''), title:'New consultation', messages:[], draft:'', error:''});
let active = newRecord();
const compactSidebar = window.matchMedia('(max-width: 1100px)');
function setSidebar(open, restoreFocus = false) {
  $('#history-panel').hidden = !open;
  document.body.classList.toggle('sidebar-open', open);
  $('#sidebar-backdrop').hidden = !open || !compactSidebar.matches;
  $('.shell').inert = open && compactSidebar.matches;
  $('#history-toggle').setAttribute('aria-expanded', String(open));
  if (restoreFocus) $('#history-toggle').focus();
}
function closeDrawer() { if (compactSidebar.matches) setSidebar(false); }
setSidebar(!compactSidebar.matches);
compactSidebar.addEventListener('change', () => setSidebar(!compactSidebar.matches));
async function goHome() {
  if (busy) return;
  try { await save(); active = newRecord(); render(); closeDrawer(); await listHistory(); $('#question').focus(); }
  catch (error) { report(error); }
}
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function api(path, options = {}, retry = true) {
  const response = await fetch(path, {...options, headers:{'Content-Type':'application/json','X-Chat-Token':token}});
  const result = await response.json();
  if (response.status === 403 && retry) {
    token = (await (await fetch('/api/status')).json()).token;
    return api(path, options, false);
  }
  if (!response.ok) throw new Error(result.error || 'Request failed. Please retry.');
  return result;
}
function save() {
  clearTimeout(draftTimer);
  if (!active.messages.length && !active.draft) return Promise.resolve();
  const body = JSON.stringify(active);
  saveQueue = saveQueue.catch(()=>{}).then(()=>api('/api/conversations',{method:'POST',body}));
  return saveQueue;
}
function report(error) { $('#error').textContent=error.message; $('#error').hidden=false; }
function message(role, paragraphs, sources = [], mode = null) {
  const article = node('article', undefined, `message ${role}`);
  article.append(node('div', role === 'user' ? 'YOUR TRANSMISSION' : mode === 'database_lookup' ? 'VERIFIED DATASHEET' : 'ARCHIVE RESPONSE', 'author'));
  for (const paragraph of paragraphs) {
    article.append(node('p', paragraph.text));
    for (const id of paragraph.citations || []) {
      const source = sources.find(item => item.id === id);
      if (!source) continue;
      const button = node('button', `${id} · ${source.locator}`, 'citation');
      button.addEventListener('click', () => {
        showSources(sources);
        const details = document.getElementById(`source-${id}`);
        details.open=true; details.scrollIntoView({block:'nearest'}); details.focus();
      });
      article.append(button);
    }
  }
  $('#conversation').append(article);
}
function showSources(sources) {
  $('#sources').replaceChildren(); $('#source-count').textContent=String(sources.length).padStart(2,'0');
  if (!sources.length) { $('#sources').innerHTML=initialSources; return; }
  for (const source of sources) {
    const details=node('details',undefined,'source'); details.id=`source-${source.id}`; details.tabIndex=-1;
    details.append(node('summary',`${source.id} / ${source.title}`),node('div',source.locator,'locator'));
    if (source.url && source.url.startsWith('/sources/core-rules.pdf#page=')) {
      const link=node('a','Open source page ↗'); link.href=source.url; link.target='_blank'; link.rel='noopener'; details.append(link);
    }
    let content=source.content;
    if (source.kind==='sqlite') { try { content=JSON.stringify(JSON.parse(content),null,2); } catch { /* Preserve source text. */ } }
    details.append(node('pre',content)); $('#sources').append(details);
  }
}
function render() {
  document.querySelectorAll('.message').forEach(element=>element.remove());
  welcome.hidden=active.messages.length>0;
  let sources=[];
  for (const entry of active.messages) {
    if(entry.role==='user') message('user',[{text:entry.text}]);
    else { message('assistant',entry.paragraphs,entry.sources,entry.response_mode); sources=entry.sources; }
  }
  showSources(sources); $('#question').value=active.draft;
  $('#error').textContent=active.error; $('#error').hidden=!active.error;
  failedQuestion=active.messages.at(-1)?.role==='user' ? active.messages.at(-1).text : '';
  $('#conversation').scrollTop=active.messages.length ? $('#conversation').scrollHeight : 0;
}
function setBusy(value) {
  busy=value; $('#send').disabled=value; $('#reset').disabled=value; $('#history-toggle').disabled=value;
  $('#question').disabled=value; $('#working').hidden=!value;
  document.querySelectorAll('[data-question], .home-link, #sidebar-new, #history-list button').forEach(button=>button.disabled=value);
}
function history() {
  const turns=[];
  for(let i=0;i<active.messages.length-1;i++) {
    const a=active.messages[i], b=active.messages[i+1];
    if(a.role==='user' && b.role==='assistant') turns.push({role:'user',content:a.text},{role:'assistant',content:b.paragraphs.map(p=>p.text).join('\n\n').slice(0,12000)});
  }
  return turns.slice(-12);
}
async function submit(question) {
  if(busy || !question.trim()) return;
  const prior=history(); active.error=''; active.draft=question;
  if(question!==failedQuestion) active.messages.push({role:'user',text:question});
  if(active.title==='New consultation') active.title=question.slice(0,100);
  render(); $('#question').value=''; setBusy(true);
  try {
    await save(); // Persist the question before the potentially slow network request.
    const result=await api('/api/ask',{method:'POST',body:JSON.stringify({question,history:prior})});
    active.messages.push({role:'assistant',...result}); active.draft=''; active.error='';
    await save(); render();
  } catch(error) {
    active.error=error.message || 'Connection lost. Please retry.'; active.draft=question;
    try { await save(); } catch { active.error+=' Could not save locally; keep this tab open.'; }
    render();
  } finally { setBusy(false); await listHistory().catch(report); $('#question').focus(); }
}
async function listHistory() {
  const records=await api('/api/conversations'); $('#history-list').replaceChildren();
  if(!records.length) $('#history-list').append(node('p','No saved conversations yet.','history-note'));
  for(const record of records) {
    const row=node('div',undefined,'history-item');
    row.classList.toggle('active', record.id===active.id);
    const open=node('button',record.title,'history-open');
    open.setAttribute('aria-current',record.id===active.id?'true':'false');
    open.addEventListener('click',async()=>{if(busy)return;try{await save(); active=await api(`/api/conversations/${record.id}`); render(); closeDrawer(); await listHistory();}catch(error){report(error);}});
    const date=node('small',new Date(record.updated).toLocaleString());
    const controls=node('div',undefined,'history-controls');
    const rename=node('button','Rename','quiet');
    rename.addEventListener('click',async()=>{if(busy)return;await save().catch(report);const title=prompt('Conversation name',record.title);if(!title?.trim())return;try{const item=await api(`/api/conversations/${record.id}`);item.title=title.trim().slice(0,100);await api('/api/conversations',{method:'POST',body:JSON.stringify(item)});if(active.id===item.id)active.title=item.title;await listHistory();}catch(error){report(error);}});
    const remove=node('button','Delete','quiet');
    remove.addEventListener('click',async()=>{if(busy)return;await save().catch(report);if(!confirm('Delete this saved conversation?'))return;try{await api(`/api/conversations/delete/${record.id}`,{method:'POST'});if(active.id===record.id){active=newRecord();render();}await listHistory();}catch(error){report(error);}});
    controls.append(rename,remove);row.append(open,date,controls);$('#history-list').append(row);
  }
}
$('#chat-form').addEventListener('submit',event=>{event.preventDefault();submit($('#question').value.trim());});
$('#question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();submit($('#question').value.trim());}});
$('#question').addEventListener('input',()=>{active.draft=$('#question').value;clearTimeout(draftTimer);draftTimer=setTimeout(()=>save().catch(report),350);});
document.querySelectorAll('[data-question]').forEach(button=>button.addEventListener('click',()=>submit(button.dataset.question)));
$('#reset').addEventListener('click',goHome);
$('#sidebar-new').addEventListener('click',goHome);
document.querySelectorAll('.home-link').forEach(button=>button.addEventListener('click',goHome));
$('#history-toggle').addEventListener('click',async()=>{setSidebar($('#history-panel').hidden);if(!$('#history-panel').hidden){await listHistory().catch(report);if(compactSidebar.matches)$('#history-close').focus();}});
$('#history-close').addEventListener('click',()=>setSidebar(false,true));
$('#sidebar-backdrop').addEventListener('click',()=>setSidebar(false,true));
document.addEventListener('keydown',event=>{
  if(event.key==='Escape')setSidebar(false,true);
  if(event.key==='Tab' && compactSidebar.matches && !$('#history-panel').hidden){
    const buttons=[...$('#history-panel').querySelectorAll('button:not(:disabled)')];
    const first=buttons[0],last=buttons.at(-1);
    if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
  }
});
(async()=>{
  setBusy(true);
  try {
    const status=await api('/api/status'); token=status.token;
    $('#connection').textContent=status.indexed?'Local archive ready':'Setup required'; $('#signal').classList.toggle('ready',status.indexed);
    const records=await api('/api/conversations');
    if(records.length)active=await api(`/api/conversations/${records[0].id}`);
    render(); await listHistory();
    if(!status.indexed)report(new Error('Run warhammer-rag index to prepare the archive.'));
  } catch(error){report(error);$('#connection').textContent='Archive unavailable';}
  finally{setBusy(false);}
})();
