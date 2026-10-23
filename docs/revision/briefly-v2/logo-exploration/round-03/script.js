const concepts=JSON.parse(document.getElementById('concept-data').textContent);
const storageKey='briefly-symbol-round03-shortlist';
let chosen=new Set();
try{const saved=JSON.parse(localStorage.getItem(storageKey)||'[]');if(Array.isArray(saved))chosen=new Set(saved.filter(id=>concepts.some(c=>c.id===id)));}catch{}
let filtered=false;
const filterButton=document.getElementById('filter');
function update(){
  if(!chosen.size)filtered=false;
  document.getElementById('count').textContent=chosen.size;
  filterButton.disabled=!chosen.size;
  filterButton.setAttribute('aria-pressed',String(filtered));
  document.querySelector('.logo-grid').classList.toggle('filtered',filtered);
  document.querySelectorAll('[data-pin]').forEach(button=>{const active=chosen.has(button.dataset.pin);button.setAttribute('aria-pressed',String(active));button.textContent=active?'담김 ✓':'비교 +';});
  document.querySelectorAll('.logo-card').forEach(card=>card.hidden=filtered&&!chosen.has(card.dataset.id));
}
document.querySelectorAll('[data-pin]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.pin;chosen.has(id)?chosen.delete(id):chosen.add(id);try{localStorage.setItem(storageKey,JSON.stringify([...chosen]));}catch{}update();}));
filterButton.addEventListener('click',()=>{filtered=!filtered;update();});
for(const setting of ['tone','mask']){
  document.querySelectorAll(`button[data-${setting}]`).forEach(button=>button.addEventListener('click',()=>{
    document.body.dataset[setting]=button.dataset[setting];
    document.querySelectorAll(`button[data-${setting}]`).forEach(peer=>peer.setAttribute('aria-pressed',String(peer===button)));
  }));
}
const dialog=document.getElementById('detail');
document.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>{
  const c=concepts.find(item=>item.id===button.dataset.detail);
  const mark=button.querySelector('svg');
  document.querySelector('.detail-symbol').replaceChildren(mark.cloneNode(true));
  document.getElementById('detail-title').textContent=`${c.id} ${c.name} — ${c.ko}`;
  document.getElementById('detail-description').textContent=c.idea;
  const samples=document.querySelector('.detail-sizes');samples.replaceChildren();
  for(const size of [16,24,32,64,128]){
    const sample=document.createElement('div');sample.className='size-sample';
    const tile=document.createElement('span');tile.className='app-icon';tile.style.width=`${size}px`;tile.style.height=`${size}px`;tile.append(mark.cloneNode(true));
    const label=document.createElement('span');label.textContent=`${size}px`;sample.append(tile,label);samples.append(sample);
  }
  const prefix=`assets/${c.id}-${c.slug}`;
  document.getElementById('download-symbol').href=`${prefix}-symbol.svg`;
  document.getElementById('download-icon').href=`${prefix}-app-icon.svg`;
  document.getElementById('download-png').href=`${prefix}-app-icon-1024.png`;
  dialog.showModal();
}));
document.getElementById('close-detail').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
update();
