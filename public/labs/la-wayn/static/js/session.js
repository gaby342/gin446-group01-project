(() => {
  const id=document.querySelector('meta[name="session-id"]').content, me=document.querySelector('meta[name="current-user"]').content;
  const statusUrl=`/sessions/${id}/status`, voteUrl=`/sessions/${id}/vote`, card=document.querySelector('#restaurant-card'), outcome=document.querySelector('#outcome');
  let state, busy=false, activePlace=null;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render(data){state=data;const session=data.session;
    document.querySelector('.round-badge').innerHTML=`ROUND <b>${session.round_no}</b>`;
    document.querySelector('.swipe-header .eyebrow').innerHTML=`<span class="live-dot"></span> ${session.state==='runoff'?'QUICK RUNOFF':'GROUP SWIPE SESSION'}`;
    const f=data.filters||{};const selected=[...(f.cuisines||[]).map(x=>x.replaceAll('_',' ')),...(f.open_now?['open now']:[]),...(f.vegetarian?['vegetarian']:[]),...(f.halal?['halal']:[])];
    const filterBox=document.querySelector('.filter-summary');filterBox.innerHTML=`<b>Search settings</b><small>${session.radius_m} m radius</small>${selected.map(x=>`<small>${esc(x)}</small>`).join('')}<small>Everyone swipes at their own pace. The deck updates live.</small>`;
    if(session.state==='matched'){activePlace=null;showMatch(data);return;} if(session.state==='no_match'){activePlace=null;showNoMatch();return;}
    outcome.classList.add('hidden'); card.classList.remove('hidden');
    const pending=data.places.filter(p=>!data.own_votes[String(p.id)]); const current=pending[0];
    const voted=Object.keys(data.own_votes).length, total=data.places.length;
    document.querySelector('#progress-label').textContent=`${Math.min(voted,total)} of ${total} cards`;document.querySelector('#progress-bar').style.width=`${total?Math.min(100,voted/total*100):0}%`;
    document.querySelectorAll('.member-row').forEach(row=>{const uid=row.dataset.member;const votes=data.places.map(p=>p.votes?.[uid]).filter(Boolean);row.querySelector('.member-vote').textContent=votes.length?`${votes.length} ✓`:'…';});
    if(!current){activePlace=null;card.classList.add('hidden');document.querySelector('#empty-deck').classList.remove('hidden');document.querySelector('#empty-deck span').textContent='Your votes are in. Waiting for your crew…';return;}
    document.querySelector('#empty-deck').classList.add('hidden');card.classList.remove('hidden');activePlace=current;
    card.querySelector('.restaurant-name').textContent=current.name;card.querySelector('.restaurant-cuisine').textContent=`${current.cuisine} · ${current.distance_m<1000?`${current.distance_m} m`:`${(current.distance_m/1000).toFixed(1)} km`} away`;
    card.querySelector('.card-category').textContent=current.category;card.querySelector('.restaurant-meta').innerHTML=[current.address,current.opening_hours?`Hours: ${esc(current.opening_hours)}`:''].filter(Boolean).map(x=>`<span>${esc(x)}</span>`).join('');
    card.querySelector('.osm-link').href=current.osm_url;
    const rating=card.querySelector('.rating-pill');if(current.rating_count){rating.textContent=`★ ${Number(current.group_rating).toFixed(1)} · ${current.rating_count} group rating${current.rating_count===1?'':'s'}`;rating.classList.remove('hidden');}else rating.classList.add('hidden');
    const votes=current.votes||{};const yes=Object.values(votes).filter(v=>v==='yes').length;document.querySelector('.vote-legend').innerHTML=`<span>♥ ${yes} yes so far</span><span>${data.members.length} people</span>`;
  }
  async function refresh(){try{const r=await fetch(statusUrl,{cache:'no-store'});if(r.ok)render(await r.json());}catch(_){} }
  async function cast(v){if(busy||!activePlace)return;busy=true;document.querySelectorAll('.vote-button').forEach(b=>b.disabled=true);try{const r=await fetch(voteUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({place_id:activePlace.id,vote:v})});const x=await r.json();if(!r.ok)throw Error(x.error);await refresh();}catch(err){alert(err.message||'Vote could not be saved.');}finally{busy=false;document.querySelectorAll('.vote-button').forEach(b=>b.disabled=false);}}
  document.querySelectorAll('.vote-button').forEach(b=>b.addEventListener('click',()=>cast(b.dataset.vote)));
  let dragStart=null;
  card.addEventListener('pointerdown',e=>{if(e.target.closest('a,button'))return;dragStart={x:e.clientX,y:e.clientY};card.setPointerCapture(e.pointerId);});
  card.addEventListener('pointerup',e=>{if(!dragStart)return;const dx=e.clientX-dragStart.x,dy=e.clientY-dragStart.y;dragStart=null;if(Math.abs(dx)>75&&Math.abs(dx)>Math.abs(dy)*1.2)cast(dx>0?'yes':'no');});
  document.addEventListener('keydown',e=>{if(e.target.closest('input,textarea,select,button,a'))return;if(e.key==='ArrowRight')cast('yes');if(e.key==='ArrowLeft')cast('no');});
  function showMatch(data){card.classList.add('hidden');document.querySelector('#empty-deck').classList.add('hidden');const place=data.places.find(p=>p.id===data.session.match_place_id)||data.places[0];outcome.className='outcome match-outcome';outcome.innerHTML=`<span class="outcome-icon">✳</span><span class="eyebrow">UNANIMOUS. IT'S A MATCH.</span><h2>${esc(place?.name||'Dinner is decided')}</h2><p>Your whole crew said yes. See you there?</p>${place?`<div class="match-actions"><a class="button" target="_blank" rel="noopener" href="${esc(place.osm_url)}">Open map ↗</a><button class="button button-outline" id="rate-toggle">Rate after your visit</button></div><form class="rating-form hidden" id="rating-form"><label>How was it? <select name="rating"><option value="5">★★★★★ Loved it</option><option value="4">★★★★ Great</option><option value="3">★★★ Good</option><option value="2">★★ So-so</option><option value="1">★ Not for us</option></select></label><textarea name="note" maxlength="500" placeholder="A note for next time (optional)"></textarea><button class="button">Save group rating</button><span class="rating-saved"></span></form>`:''}`;
    document.querySelector('#rate-toggle')?.addEventListener('click',()=>document.querySelector('#rating-form').classList.toggle('hidden'));
    document.querySelector('#rating-form')?.addEventListener('submit',async e=>{e.preventDefault();const f=e.currentTarget;const r=await fetch(`/groups/${data.session.group_id}/places/${place.id}/rating`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(f)))});if(r.ok)f.querySelector('.rating-saved').textContent='Saved for your group!';});
  }
  function showNoMatch(){card.classList.add('hidden');document.querySelector('#empty-deck').classList.add('hidden');outcome.className='outcome';outcome.innerHTML=`<span class="outcome-icon">↻</span><span class="eyebrow">THE GROUP HAS SPOKEN</span><h2>No unanimous pick this time.</h2><p>Try another area or loosen a filter to get a fresh deck.</p><a class="button" href="/groups/${state.session.group_id}">Back to your group</a>`;}
  refresh();setInterval(refresh,2500);
})();
