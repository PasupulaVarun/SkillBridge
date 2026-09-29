(function(){
function esc(v){return String(v||"").replace(/[&<>]/g,function(m){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[m]})}
function strip(v){return String(v||"").replace(/<[^>]*>/g," ")}
window.renderLiveMarket=async function(){
 try{
  var q=((state.profile&&state.profile.skills)||[]).slice(0,3).join(" ")||"software engineer";
  var d=await apiGet("/market/jobs?q="+encodeURIComponent(q)+"&location=remote&limit=20");
  var cards=(d.jobs||[]).map(function(j){return '<article class="card op-card"><span class="tag live-tag">LIVE · '+esc(j.source)+'</span><h3>'+esc(j.title)+'</h3><p class="muted">'+esc(j.company)+' · '+esc(j.location)+'</p><p class="muted market-desc">'+esc(strip(j.description).slice(0,220))+'</p><div class="footer"><span class="muted">'+(j.created?new Date(j.created).toLocaleDateString():"Recently listed")+'</span>'+(j.url?'<a class="btn-sm primary" target="_blank" rel="noopener" href="'+j.url+'">View listing →</a>':"")+'</div></article>'}).join("");
  return '<div class="market-banner"><div><span class="eyebrow">LIVE MARKET FEED</span><h2>Current external opportunities</h2><p class="muted">Source: '+esc(d.source)+' · Updated '+(d.fetched_at?new Date(d.fetched_at).toLocaleString():"unknown")+' · Refreshes every 5 minutes</p></div><button class="btn-sm" onclick="render().then(function(){})">Refresh</button></div><div class="grid">'+(cards||'<div class="empty"><h2>No matching listings</h2><p>Try broadening your profile skills.</p></div>')+'</div>';
 }catch(e){return '<div class="empty"><h2>Market feed unavailable</h2><p>'+esc(e.message)+'</p></div>'}
};
})();