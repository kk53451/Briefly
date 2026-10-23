(() => {
  'use strict';
  const viewButtons=[...document.querySelectorAll('button[data-view]')];
  const names={journal:'A · 데일리 저널',radio:'B · 데일리 라디오',clear:'C · 클리어 브리프'};
  let selected=[];
  try{selected=JSON.parse(localStorage.getItem('briefly-bi-shortlist')||'[]');if(!Array.isArray(selected))selected=[];}catch{}
  function fit(frame){const width=Number(frame.dataset.width),height=Number(frame.dataset.height),actual=frame.clientWidth;if(!actual)return;const scale=actual/width;frame.style.height=`${height*scale}px`;const iframe=frame.querySelector('iframe');iframe.style.width=`${width}px`;iframe.style.height=`${height}px`;iframe.style.transform=`scale(${scale})`;}
  const observer=new ResizeObserver(entries=>entries.forEach(e=>fit(e.target)));
  document.querySelectorAll('.frame-viewport').forEach(frame=>{observer.observe(frame);fit(frame);});
  function view(value){document.body.dataset.view=value;viewButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===value)));requestAnimationFrame(()=>document.querySelectorAll('.frame-viewport').forEach(fit));const url=new URL(location.href);url.searchParams.set('view',value);history.replaceState(null,'',url);}
  viewButtons.forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
  const initial=new URL(location.href).searchParams.get('view');if(['mobile','web','paired'].includes(initial))view(initial);
  function sync(){document.querySelectorAll('[data-pick]').forEach(b=>{const picked=selected.includes(b.dataset.pick);b.setAttribute('aria-pressed',String(picked));b.textContent=picked?'✓':'＋';b.setAttribute('aria-label',`${names[b.dataset.pick]} ${picked?'후보에서 해제':'후보로 표시'}`);});document.querySelector('.selection-status').textContent=selected.length?`비교 후보: ${selected.map(id=>names[id]).filter(Boolean).join(' / ')} · 선택은 이 브라우저에만 저장됩니다.`:'마음에 드는 방향의 ＋를 눌러 후보로 표시할 수 있습니다.';}
  document.querySelectorAll('[data-pick]').forEach(b=>b.addEventListener('click',()=>{const id=b.dataset.pick;selected=selected.includes(id)?selected.filter(x=>x!==id):[...selected,id];try{localStorage.setItem('briefly-bi-shortlist',JSON.stringify(selected));}catch{}sync();}));sync();
})();
