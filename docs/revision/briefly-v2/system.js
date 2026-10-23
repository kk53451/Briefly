(()=>{
 const frames=[...document.querySelectorAll('.preview-viewport')];
 function fit(el){const w=Number(el.dataset.width),h=Number(el.dataset.height),a=el.clientWidth;if(!a)return;el.style.height=`${h*a/w}px`;const f=el.querySelector('iframe');f.style.width=`${w}px`;f.style.height=`${h}px`;f.style.transform=`scale(${a/w})`;}
 const observer=new ResizeObserver(entries=>entries.forEach(e=>fit(e.target)));frames.forEach(f=>{observer.observe(f);fit(f);});
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('[data-screen]').forEach(x=>x.hidden=x.dataset.screen!==b.dataset.view);requestAnimationFrame(()=>frames.forEach(fit));}));
 const toast=document.querySelector('.toast');let timer;
 function notify(msg){toast.textContent=msg;toast.hidden=false;clearTimeout(timer);timer=setTimeout(()=>toast.hidden=true,2600);}
 document.querySelector('.demo-save').addEventListener('click',event=>{const el=event.currentTarget,yes=el.getAttribute('aria-pressed')!=='true';el.setAttribute('aria-pressed',String(yes));el.setAttribute('aria-label',yes?'예시 이야기 저장 해제':'예시 이야기 저장');document.querySelector('.demo-save-label').textContent=yes?'이야기를 저장했어요':'나중에 읽고 싶은 이야기';notify(yes?'이야기를 저장했어요':'저장을 해제했어요');});
 document.querySelectorAll('[data-demo]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.demo==='listen'||b.dataset.demo==='read'){location.href='app.html?action='+b.dataset.demo;}else if(b.dataset.demo==='reset-progress'){try{localStorage.removeItem('briefly-v3-read-2026-10-23');document.querySelectorAll('.preview-viewport iframe').forEach(f=>f.contentWindow.location.reload());notify('읽기 진행을 처음 상태로 돌렸어요');}catch{notify('이 브라우저에서는 진행 기록을 지울 수 없어요');}}else notify(b.dataset.demo==='retry'?'상태 예시입니다. 실제 서비스에서는 브리핑을 다시 불러옵니다.':'이야기를 저장했어요');}));
})();
