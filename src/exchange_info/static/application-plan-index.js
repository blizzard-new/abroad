/* One account-scoped index links saved plans and existing preferences without
   converting or copying legacy progress into a different school/term. */
window.UniWayPlanIndex = (() => {
  let owner='', data=null, status='idle', error='', request=0;
  const key=()=>JSON.stringify([state.account?.id, state.authSessionEpoch, activeHomeSchool()]);
  const current=()=>owner===key()?data:null;
  const link=p=>'#my-application?'+new URLSearchParams({plan:p.id,view:'today'});
  function render(){
    const host=document.querySelector('#application-plan-index');if(!host)return;
    if(!state.account){host.replaceChildren();host.hidden=true;return;}
    host.hidden=false;
    if(status==='loading'){host.innerHTML='<p role="status">正在讀取申請計畫…</p>';return;}
    if(status==='error'){host.innerHTML='<p role="alert">申請計畫暫時無法讀取。</p><button type="button" data-plan-index-retry>重新載入計畫</button>';return;}
    const items=current()?.items||[], live=items.filter(p=>!p.archived);
    const unplanned=[...state.applications].filter(name=>!live.some(p=>p.context.target_school===name));
    if(!items.length&&!unplanned.length){host.hidden=true;return;}
    const label=p=>`${p.context.target_school} · ${p.context.departure_year} ${({fall:'上學期',spring:'下學期',full_year:'全學年',undecided:'學期待確認'})[p.context.semester]||''}`;
    host.innerHTML='<h2>我的申請計畫</h2><div class="saved-plan-list">'+live.map(p=>`<a href="${escapeHtml(link(p))}"><strong>${escapeHtml(label(p))}</strong><span>繼續準備 →</span></a>`).join('')+unplanned.map(name=>`<button type="button" data-start-application="${escapeHtml(name)}"><strong>${escapeHtml(name)}</strong><span>開始準備 →</span></button>`).join('')+'</div>'+(items.some(p=>p.archived)?'<details><summary>已封存計畫</summary>'+items.filter(p=>p.archived).map(p=>`<a href="${escapeHtml(link(p))}">${escapeHtml(label(p))}</a>`).join('')+'</details>':'');
  }
  function clear(){request++;owner='';data=null;status='idle';error='';render();}
  function accept(value){request++;owner=key();data=value;status='ready';render();window.UniWayTracker?.render();}
  async function refresh(force=false){
    if(!state.account){clear();return;}
    const captured=key();
    if(owner===captured&&!force&&['loading','ready','error'].includes(status)){render();return;}
    owner=captured;data=null;status='loading';const run=++request;render();
    try{const value=await fetchJson('/account/application-paths?'+new URLSearchParams({home_school:activeHomeSchool()}));if(run!==request||captured!==key())return;data=value;status='ready';}
    catch(e){if(run!==request||captured!==key())return;status='error';error=e.message;}
    render();window.UniWayTracker?.render();
  }
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-plan-index-retry]'))refresh(true);
    const button=e.target.closest('[data-start-application]');
    if(button)window.UniWayApplicationPath?.startTarget(button.dataset.startApplication);
  });
  return {refresh,accept,clear,current};
})();
