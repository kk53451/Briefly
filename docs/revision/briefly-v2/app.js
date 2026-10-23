(()=>{
 'use strict';
 const topics=[
  {category:'경제',title:'기준금리가 멈춘 자리, 우리 생활은 어떻게 달라질까',time:0,duration:'1:44',lede:'금리 결정 너머의 이야기. 대출과 저축, 소비에 남는 영향을 살펴봅니다.',body:['기준금리가 유지되는 상황을 가정한 브리핑입니다. 같은 금리라도 가계가 체감하는 변화는 대출 조건과 예금 상품에 따라 다를 수 있습니다.','결정의 배경과 생활에 미치는 영향을 나누어 읽습니다. 지금 유지되는 조건이 무엇인지, 앞으로 달라질 수 있는 조건은 무엇인지 차례로 살펴보는 구성입니다.','숫자 하나로 모든 사람의 상황을 설명하기는 어렵습니다. 원문 자료와 서로 다른 해설을 함께 확인하면 내 생활과 연결된 맥락을 더 분명하게 이해할 수 있습니다.'],sources:['금리 결정 배경을 설명하는 공식 발표','가계 대출과 예금 조건에 관한 보도','경제 지표와 전문가 해설']},
  {category:'사회',title:'차가 비켜난 도시에 사람의 자리가 생긴다',time:104,duration:'1:43',lede:'걷기와 대중교통이 바꾸는 일상. 이동의 편의와 도시의 여유를 함께 봅니다.',body:['도심의 보행 공간을 늘리는 계획을 가정했습니다. 자동차가 지나던 자리를 사람들이 머무는 공간으로 바꾸면, 거리에서 보내는 시간도 달라질 수 있습니다.','계획의 효과는 이용자에 따라 다르게 나타납니다. 보행자의 안전과 버스의 이동, 상인의 물류 접근성처럼 함께 확인할 조건들이 있습니다.','정책의 의도와 실제 결과를 구분하고 다양한 이용자의 관점을 연결합니다. 일상에서 어떤 변화가 생기는지 이해하는 데 필요한 출처를 모아 읽는 경험입니다.'],sources:['교통과 보행 공간에 관한 정책 계획','주민과 상인 의견을 다룬 현장 보도','대중교통 이용 환경 분석']},
  {category:'기술',title:'AI가 만든 콘텐츠, 표시가 신뢰를 만들 수 있을까',time:207,duration:'1:45',lede:'사진과 글에 붙는 작은 표시. 알려주는 것과 아직 알 수 없는 것을 구분합니다.',body:['AI로 만든 콘텐츠에 표시를 붙이는 상황을 가정했습니다. 표시가 알려주는 것은 제작 과정의 일부이며, 내용의 정확성을 보증하는 것은 아닙니다.','제작자가 공개할 수 있는 정보와 이용자가 확인할 수 있는 정보에는 차이가 있습니다. 도구마다 적용 범위도 달라 같은 표시가 항상 같은 의미를 갖지는 않을 수 있습니다.','어디까지 알 수 있고 무엇이 남아 있는지를 짧게 구분합니다. 설명을 읽은 뒤 원문 정책과 기술적 한계를 함께 확인할 수 있도록 출처를 연결합니다.'],sources:['콘텐츠 표시 방식에 관한 서비스 정책','제작자와 이용자 경험을 다룬 보도','표시 기술의 적용 범위와 한계에 관한 해설']}
 ];
 const key='briefly-v2-saved',reader=document.querySelector('.reader'),player=document.querySelector('.player'),toast=document.querySelector('.toast');
 const progressKey='briefly-v3-read-2026-10-23';
 let saved=[],completed=[],resumeTopic=0,visited=false,position=0,playing=false,timer=null,toastTimer=null;
 function parse(value){try{const a=JSON.parse(value||'[]');return Array.isArray(a)?a.filter(x=>Number.isInteger(x)&&x>=0&&x<3):[];}catch{return [];}}
 try{saved=parse(localStorage.getItem(key));}catch{}
 function loadProgress(value){try{const state=JSON.parse(value||'{}');completed=[...new Set(parse(JSON.stringify(state.completed)))];resumeTopic=Number.isInteger(state.resume)&&state.resume>=0&&state.resume<3?state.resume:0;visited=state.visited===true;}catch{completed=[];resumeTopic=0;visited=false;}}
 try{loadProgress(localStorage.getItem(progressKey));}catch{}
 function remember(){try{localStorage.setItem(progressKey,JSON.stringify({completed,resume:resumeTopic,visited}));}catch{}}
 function syncProgress(){
  const count=completed.length;
  document.querySelector('[data-progress-count]').textContent=`${count} / 3`;
  document.querySelector('[data-progress-label]').textContent=count===3?'오늘의 브리핑 완독':'읽은 이야기';
  const track=document.querySelector('.reading-track');track.setAttribute('aria-valuenow',String(count));track.setAttribute('aria-valuetext',`${count}개 이야기 읽음, 전체 3개`);
  track.querySelectorAll('i').forEach((el,n)=>el.classList.toggle('done',completed.includes(n)));
  document.querySelectorAll('[data-read-status]').forEach(el=>el.hidden=!completed.includes(Number(el.dataset.readStatus)));
  document.querySelector('[data-read-label]').textContent=count===3?'다시 읽기':visited?'이어서 읽기':'읽기 시작';
  document.querySelector('[data-read-time]').textContent=count===3?'처음부터':visited?`${resumeTopic+1}번째 이야기`:'약 2분';
  document.querySelector('[data-finish-label]').innerHTML=count===3?'오늘의 맥락을 모두 읽었어요.<br>다시 보고 싶은 이야기는 보관함에 남겨보세요.':'오늘은 여기까지.<br>세 이야기를 읽으면 하루의 맥락이 이어져요.';
 }
 function complete(n){if(!completed.includes(n))completed.push(n);remember();syncProgress();}

 const icon=n=>`<svg class="icon${n==='play'?' fill':''}" aria-hidden="true"><use href="#i-${n}"/></svg>`;
 function notify(s){toast.textContent=s;toast.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.hidden=true,2400);}
 function sync(){document.querySelectorAll('[data-action=save]').forEach(b=>{const n=Number(b.dataset.topic),yes=saved.includes(n);b.setAttribute('aria-pressed',String(yes));b.setAttribute('aria-label',`${topics[n].category} 이야기 ${yes?'저장 해제':'저장'}`);const label=b.querySelector('[data-save-label]');if(label)label.textContent=yes?'저장됨':'저장';});}
 function save(n){saved=saved.includes(n)?saved.filter(x=>x!==n):[...saved,n];try{localStorage.setItem(key,JSON.stringify(saved));}catch{}sync();notify(saved.includes(n)?'이야기를 저장했어요':'저장을 해제했어요');}
 function show(content,label,eyebrow='오늘의 브리핑'){reader.innerHTML=`<div class="reader-body"><div class="reader-header"><span class="reader-label">${eyebrow}</span><button class="icon-btn" data-action="close" aria-label="닫기">${icon('close')}</button></div>${content}</div>`;reader.setAttribute('aria-label',label);if(!reader.open)reader.showModal();reader.scrollTop=0;reader.querySelector('[data-action=close]').focus({preventScroll:true});sync();}
 function read(n=0){resumeTopic=n;visited=true;remember();syncProgress();const t=topics[n];show(`<div class="reader-progress" aria-label="${n+1}번째 이야기, 전체 3개">${topics.map((_,i)=>`<i class="${completed.includes(i)?'complete':''} ${i===n?'current':''}"></i>`).join('')}</div><h2>${t.title}</h2><p class="lede">${t.lede}</p><div class="reader-actions"><button class="btn primary" data-action="listen" data-topic="${n}">${icon('headphones')}이 구간 듣기 ${t.duration}</button><button class="btn secondary" data-action="save" data-topic="${n}">${icon('save')}<span data-save-label>저장</span></button></div><div class="reader-content">${t.body.map(p=>`<p>${p}</p>`).join('')}</div><button class="text-link" data-action="sources" data-topic="${n}">${icon('link')}출처 확인</button><p class="reader-source-note">이 글은 디자인 검토용 가상 뉴스입니다. 실제 뉴스·금융·정책 정보가 아닙니다.</p><nav class="reader-next" aria-label="읽기 순서">${n>0?`<button class="btn secondary" data-action="read" data-topic="${n-1}">이전 이야기</button>`:'<span></span>'}${n<2?`<button class="btn primary" data-action="advance" data-topic="${n}">읽고 다음으로 ${icon('arrow')}</button>`:`<button class="btn primary" data-action="finish" data-topic="${n}">다 읽었어요 ${icon('check')}</button>`}</nav>`,t.title,`${t.category} / ${n+1}번째 이야기`);}
 function sources(n){const t=topics[n];show(`<h2>이야기의 바탕이 된 자료</h2><p>${t.title}</p><ul class="source-list">${t.sources.map(s=>`<li>${s}<small>출처 구성 예시 / 실제 기사 연결 전</small></li>`).join('')}</ul><p class="reader-source-note">가상 자료입니다. 실제 서비스에서는 기사 제목, 매체, 발행 시각과 원문 링크를 제공합니다.</p><button class="btn secondary" data-action="read" data-topic="${n}">이야기로 돌아가기</button>`,'출처 확인',t.category+' / 출처');}
 function savedList(){show(`<h2>보관함</h2>${saved.length?saved.map(n=>`<button class="saved-item" data-action="read" data-topic="${n}"><small>${topics[n].category} / 10월 23일</small>${topics[n].title}</button>`).join(''):`<div class="empty-state">${icon('save')}<h3>다시 읽고 싶은 이야기를 모아보세요.</h3><p>이야기 옆 저장 버튼을 누르면 여기에 모입니다.</p><button class="btn primary" data-action="close">오늘의 이야기 보기</button></div>`}<p class="reader-source-note">저장한 이야기는 이 브라우저에만 보관됩니다.</p>`,'보관함','나의 이야기');}
 const current=()=>position>=207?2:position>=104?1:0;
 const format=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
 function update(){player.querySelector('.player-title').textContent=topics[current()].title;player.querySelector('[data-current]').textContent=format(position);player.querySelector('input').value=position;const b=player.querySelector('[data-player=toggle]');b.innerHTML=icon(playing?'pause':'play');b.setAttribute('aria-label',playing?'일시정지':'미리보기 재생');
  document.querySelector('[data-listen-label]').textContent=playing?'일시정지':position>=312?'다시 듣기':position>0?'이어서 듣기':'전체 듣기';
  document.querySelector('[data-listen-icon]').innerHTML=icon(playing?'pause':'play');
  document.querySelector('[data-listen-time]').textContent=position>0&&position<312?`${format(312-position)} 남음`:'5분 12초';
  document.querySelector('.listen-main').setAttribute('aria-pressed',String(playing));
  document.querySelectorAll('.chapter-nav button').forEach((el,n)=>el.setAttribute('aria-pressed',String(!player.hidden&&current()===n)));
 }

 function setPlaying(value){playing=value;clearInterval(timer);if(playing){if(position>=312)position=0;timer=setInterval(()=>{position=Math.min(312,position+1);if(position===312)setPlaying(false);update();},1000);}update();}
 function listen(n){const pause=n===undefined&&!player.hidden&&playing;if(n!==undefined)position=topics[n].time;reader.close();player.hidden=false;document.body.classList.add('has-player');setPlaying(!pause);}
 document.addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(!b)return;const a=b.dataset.action,n=Math.min(2,Math.max(0,Number(b.dataset.topic)||0));if(a==='read')read(n);if(a==='resume')read(completed.length===3?0:resumeTopic);if(a==='advance'){complete(n);read(Math.min(2,n+1));}if(a==='sources')sources(n);if(a==='save')save(n);if(a==='saved')savedList();if(a==='close')reader.close();if(a==='listen')listen(b.dataset.topic===undefined?undefined:n);if(a==='home'){reader.close();window.scrollTo({top:0,behavior:'smooth'});}if(a==='finish'){complete(n);reader.close();notify(completed.length===3?'오늘의 브리핑을 모두 읽었어요':'이 이야기를 다 읽었어요');}if(a==='archive')show(`<h2>지난 브리핑</h2><button class="saved-item" data-action="read" data-topic="0"><small>2026.10.23 / 오전</small>금리는 멈추고, 일상은 움직인다.</button><p class="reader-source-note">디자인 검토용으로 한 회차만 제공됩니다.</p>`,'지난 브리핑','회차 보관함');});
 player.addEventListener('click',e=>{const b=e.target.closest('[data-player]');if(!b)return;if(b.dataset.player==='toggle')setPlaying(!playing);if(b.dataset.player==='read')read(current());if(b.dataset.player==='close'){setPlaying(false);player.hidden=true;document.body.classList.remove('has-player');update();}});
 player.querySelector('input').addEventListener('input',e=>{position=Number(e.target.value);if(position===312)setPlaying(false);update();});
 reader.addEventListener('click',e=>{if(e.target===reader){const r=reader.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)reader.close();}});
 window.addEventListener('storage',e=>{if(e.key===key){saved=parse(e.newValue);sync();}if(e.key===progressKey){loadProgress(e.newValue);syncProgress();}});
 sync();syncProgress();update();const initial=new URL(location.href).searchParams.get('action');if(initial==='read')read();if(initial==='listen')listen();
})();
