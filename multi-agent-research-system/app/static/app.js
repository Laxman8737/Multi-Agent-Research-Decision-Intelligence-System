const $=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
$('#theme').addEventListener('click',()=>{const r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'});
let LIVE=false;(location.protocol=='file:'?Promise.reject():fetch(new URL('api/health', document.baseURI), {headers:{'Accept':'application/json'}})).then(r=>r.ok&&r.json()).then(j=>{LIVE=!!j&&j.status=='ok';ban()}).catch(ban);
function ban(){$('#banner').innerHTML=LIVE?'<div class="tag ok">● live API connected</div>':'<div class="banner">Recorded mode: real outputs captured from the agent workflow. Run <code>docker compose up</code> (see GitHub) for the live API.</div>';if(!LIVE)$('#q').readOnly=true}
DATA.demo.forEach(d=>{const b=document.createElement('button');b.className='btn sm';b.textContent=d.label;b.onclick=()=>{$('#q').value=d.question;show(d.result)};$('#presets').appendChild(b)});
const C={verified:'ok',single_source:'warn',conflict:'bad'};
function show(r){$('#out').innerHTML=`<div class="flow">${r.trace.map((t,i)=>`${i?'<span class="arr">→</span>':''}<span class="node"><b>${t.agent}</b><br><span class="muted">${esc(t.summary)} · ${t.ms}ms</span></span>`).join('')}</div>
<div style="margin-top:12px">${r.flags.slice(0,1).map(f=>`<span class="tag bad">⚠ ${esc(f)}</span>`).join('')}<span class="tag">${r.total_ms} ms</span><span class="tag">${r.usage.tokens_in}→${r.usage.tokens_out} tokens</span><span class="tag">$${r.usage.usd}</span><span class="tag">${r.tool_calls.length} tool calls</span></div>
<div class="scroll" style="margin-top:12px"><table><tr><th>Fact</th><th>Year</th><th>Status</th><th>Values (sources)</th></tr>${r.facts.map(f=>`<tr><td>${esc(f.subject)}</td><td>${f.year}</td><td class="${C[f.status]}">${f.status}</td><td>${Object.entries(f.values).map(([v,s])=>esc(v+' '+f.unit+' ('+s.join(', ')+')')).join(' vs ')}</td></tr>`).join('')}</table></div>
<pre class="ans" style="white-space:pre-wrap;overflow-x:auto;font:inherit;font-size:.82rem">${esc(r.report)}</pre>`}
$('#ask').onclick=async()=>{const q=$('#q').value.trim();if(q.length<8)return;if(!LIVE){const m=DATA.demo.find(d=>d.question==q);return m?show(m.result):($('#out').innerHTML='<div class="banner">Recorded mode: pick one of the presets above.</div>')}
try{const r=await fetch('api/research',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question:q})});if(!r.ok){let message='Request failed ('+r.status+')';try{const body=await r.json();message=body.detail||message}catch{}throw new Error(message)}show(await r.json())}catch(e){$('#out').innerHTML='<div class="banner">Error: '+esc(e.message)+'</div>'}};

// Keyboard accessibility: Enter submits the current question.
$('#q').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('#ask').click()}});
