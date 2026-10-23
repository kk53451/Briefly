(() => {
  'use strict';
  const library = window.ASSET_LIBRARY;
  const labels = {logos:'로고',icons:'아이콘',components:'컴포넌트',covers:'팟캐스트 커버',photos:'사진',avatars:'아바타',emoji:'이모지',illustrations:'일러스트',textures:'텍스처',screens:'화면'};
  const $ = id => document.getElementById(id);
  const number = n => n.toLocaleString('ko-KR');
  const state = {category:'logos',search:'',style:'',group:'',page:1};
  const PAGE_SIZE = 60;
  const searchable = library.assets.map(asset => ({...asset,searchText:[asset.name,asset.originalName,asset.id,asset.style,asset.group,...(asset.sourcePath || []),labels[asset.category]].join(' ').toLowerCase()}));
  $('source-link').href = library.source;
  const option = (value, label) => { const o=document.createElement('option');o.value=value;o.textContent=label;return o; };
  for (const style of Object.keys(library.iconStyles)) $('style').append(option(style,style));
  for (const [key,label] of Object.entries(labels)) {
    const button=document.createElement('button');button.className='tab';button.type='button';button.dataset.category=key;button.setAttribute('aria-pressed',key===state.category?'true':'false');
    const text=document.createTextNode(label);const count=document.createElement('span');count.textContent=number(library.counts[key] || 0);button.append(text,count);
    button.addEventListener('click',()=>{state.category=key;state.style='';state.group='';state.page=1;$('style').value='';updateGroups();render();});
    $('categories').append(button);
  }
  function updateGroups() {
    $('group').replaceChildren(option('','모든 종류'));
    const groups=[...new Set(searchable.filter(a=>a.category===state.category).map(a=>a.group).filter(Boolean))].sort();
    for(const group of groups) $('group').append(option(group,group));
    $('group').hidden=groups.length<2;
    $('style').hidden=state.category!=='icons';
  }
  function showAsset(asset) {
    $('modal-title').textContent=asset.name;
    $('modal-sub').textContent=[asset.format.toUpperCase(),`${asset.width} × ${asset.height}${asset.scale===2?' · PNG 2×':''}`,asset.style||asset.group,asset.id].filter(Boolean).join('  /  ');
    $('modal-image').src=asset.file;$('modal-image').alt=asset.name;
    $('modal-stage').classList.toggle('icon',asset.category==='icons');
    $('modal-stage').classList.toggle('logo-vector',asset.category==='logos'&&asset.format==='svg');
    $('modal-path').textContent=asset.file;
    $('download').href=asset.file;$('download').download=asset.file.split('/').pop();
    $('original').href=asset.file;
    $('figma').href=asset.figmaUrl||library.source;
    $('modal').showModal();
  }
  function card(asset) {
    const el=document.createElement('article');el.className=`card ${asset.category}${asset.format==='svg'?' vector':''}`;
    const preview=document.createElement('button');preview.className='preview';preview.type='button';preview.setAttribute('aria-label',asset.name+' 미리보기');preview.addEventListener('click',()=>showAsset(asset));
    const img=document.createElement('img');img.src=asset.file;img.alt=asset.name;img.loading='lazy';img.decoding='async';preview.append(img);
    const body=document.createElement('div');body.className='card-body';
    const title=document.createElement('h3');title.className='card-title';title.textContent=asset.name;title.title=asset.originalName;
    const meta=document.createElement('div');meta.className='card-meta';const group=document.createElement('span');group.textContent=asset.style||asset.group||labels[asset.category];const type=document.createElement('span');type.textContent=asset.format.toUpperCase()+(asset.scale===2?' / 2×':'');meta.append(group,type);
    const actions=document.createElement('div');actions.className='card-actions';const download=document.createElement('a');download.href=asset.file;download.download=asset.file.split('/').pop();download.textContent='다운로드 ↓';const figma=document.createElement('a');figma.href=asset.figmaUrl||library.source;figma.target='_blank';figma.rel='noreferrer';figma.textContent='Figma ↗';actions.append(download,figma);
    body.append(title,meta,actions);el.append(preview,body);return el;
  }
  function render() {
    const words=state.search.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const filtered=searchable.filter(a=>a.category===state.category&&(!state.style||a.style===state.style)&&(!state.group||a.group===state.group)&&words.every(w=>a.searchText.includes(w)));
    const pages=Math.max(1,Math.ceil(filtered.length/PAGE_SIZE));state.page=Math.min(state.page,pages);
    $('grid').dataset.category=state.category;
    $('grid').replaceChildren(...filtered.slice((state.page-1)*PAGE_SIZE,state.page*PAGE_SIZE).map(card));
    if(!filtered.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='검색 결과가 없습니다. 다른 이름이나 분류로 찾아보세요.';$('grid').append(empty);}
    $('result-count').textContent=`${labels[state.category]} · ${number(filtered.length)}개${filtered.length>PAGE_SIZE?' / 한 페이지에 60개씩 표시':''}`;
    $('page-count').textContent=`${number(state.page)} / ${number(pages)}`;
    $('prev').disabled=state.page===1;$('next').disabled=state.page===pages;
    for(const button of $('categories').children)button.setAttribute('aria-pressed',button.dataset.category===state.category?'true':'false');
  }
  $('search').addEventListener('input',event=>{state.search=event.target.value;state.page=1;render();});
  $('style').addEventListener('change',event=>{state.style=event.target.value;state.page=1;render();});
  $('group').addEventListener('change',event=>{state.group=event.target.value;state.page=1;render();});
  $('light').addEventListener('change',event=>document.body.classList.toggle('light-stage',event.target.checked));
  $('prev').addEventListener('click',()=>{state.page--;render();$('result-count').scrollIntoView({block:'start'});});
  $('next').addEventListener('click',()=>{state.page++;render();$('result-count').scrollIntoView({block:'start'});});
  $('close').addEventListener('click',()=>$('modal').close());
  $('modal').addEventListener('click',event=>{if(event.target===$('modal')){const r=$('modal').getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)$('modal').close();}});
  updateGroups();render();
})();
