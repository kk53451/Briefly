const concepts=JSON.parse(document.getElementById('concept-data').textContent);
for(const setting of ['view','tone']){
  document.querySelectorAll(`button[data-${setting}]`).forEach(button=>button.addEventListener('click',()=>{
    document.body.dataset[setting]=button.dataset[setting];
    document.querySelectorAll(`button[data-${setting}]`).forEach(peer=>peer.setAttribute('aria-pressed',String(peer===button)));
  }));
}
const dialog=document.getElementById('detail');
document.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>{
  const c=concepts.find(c=>c.id===button.dataset.detail),card=button.closest('.concept');
  document.getElementById('detail-word').replaceChildren(card.querySelector('.word-art svg').cloneNode(true));
  const samples=document.getElementById('detail-apps');samples.replaceChildren();
  for(const size of [48,64,128]){
    const sample=document.createElement('div');sample.className='sample';
    const app=card.querySelector('.app-art svg').cloneNode(true);app.style.width=`${size}px`;app.style.height=`${size}px`;
    const label=document.createElement('span');label.textContent=`${size}px`;sample.append(app,label);samples.append(sample);
  }
  document.getElementById('detail-title').textContent=`${c.id} ${c.name} — ${c.ko}`;
  document.getElementById('detail-idea').textContent=c.idea;
  document.getElementById('detail-method').textContent=c.detail;
  const base=`assets/${c.id}-${c.slug}`;
  document.getElementById('word-download').href=`${base}-wordmark.svg`;
  document.getElementById('app-download').href=`${base}-app-icon.svg`;
  document.getElementById('png-download').href=`${base}-app-icon-1024.png`;
  dialog.showModal();
}));
document.getElementById('close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
