/* SkillBridge domain expansion: richer non-placeholder surfaces. */
const domainCopy={
  Research:["Research Collaboration","Connect faculty with industry problem statements, applied research and co-creation opportunities.","Problem statements","Joint research","Publication support","Innovation funding"],
  Training:["Industry Training","Browse workshops, faculty development programs and role-specific upskilling tracks.","FDP programs","Technical workshops","Soft-skill training","Certification pathways"],
  Mentorship:["Mentorship Network","Build structured mentor relationships around career direction, projects and industry readiness.","Career mentoring","Project mentoring","Interview readiness","Research mentoring"],
  "Training Programs":["Industry Training Programs","Publish and discover structured programs with outcomes, skills and completion evidence.","Cohort programs","Certification","Hands-on labs","Assessment"],
  "Faculty Opportunities":["Faculty Opportunities","Discover internships, consulting, research and training opportunities aligned with academic expertise.","Industry internships","Research calls","Faculty development","Consulting"],
  "Skill Gap Analytics":["Skill Gap Analytics","Compare current student skill supply with industry demand and identify high-priority curriculum gaps.","Demand trends","Skill coverage","Gap analysis","Curriculum signals"],
  "Internships & Placements":["Internships & Placements","Track opportunity participation, applications and outcomes from one institution workspace.","Open roles","Application funnel","Selection outcomes","Placement insights"]
};
function richDomainPage(title){
 const d=domainCopy[title]||[title,"Explore SkillBridge opportunities, programs and collaboration pathways.","Discover","Track","Collaborate","Grow"];
 return '<div class="section-title"><div><span class="eyebrow">SKILLBRIDGE DOMAIN</span><h2>'+d[0]+'</h2><p class="muted">'+d[1]+'</p></div></div><div class="grid">'+d.slice(2).map((x,i)=>'<div class="card op-card"><span class="tag">0'+(i+1)+'</span><h3>'+x+'</h3><p class="muted">Industry-aligned information, participation details and next steps.</p><button class="btn-sm primary" onclick="toast(\'Module ready for live data\')">Explore →</button></div>').join('')+'</div>';
}
["Research","Training","Mentorship","Training Programs","Faculty Opportunities","Skill Gap Analytics","Internships & Placements"].forEach(k=>{pages[k]=()=>richDomainPage(k)});
