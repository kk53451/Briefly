"""Build the brand guide and product preview from shared local components."""
from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parent
paths = {
 'play':'<path d="m8 5 11 7-11 7V5Z"/>',
 'pause':'<path d="M8 5v14M16 5v14"/>',
 'book':'<path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1v14"/>',
 'save':'<path d="M6 3h12v18l-6-4-6 4V3Z"/>',
 'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
 'link':'<path d="m10 14 4-4m-6 7-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m0 10a4 4 0 0 0 6 0l5-5a4 4 0 0 0-6-6l-1 1" transform="translate(1 0) scale(.9)"/>',
 'home':'<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M7 8h10M7 12h10M7 16h5"/>',
 'check':'<path d="m5 12 4 4L19 6"/>',
 'arrow':'<path d="M5 12h14m-6-6 6 6-6 6"/>',
 'close':'<path d="m6 6 12 12M6 18 18 6"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'headphones':'<path d="M3 13V11a9 9 0 0 1 18 0v2M3 12h4v8H3v-8Zm14 0h4v8h-4v-8Z"/>'
}
defs='<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'+''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k,v in paths.items())+'</defs></svg>'
def icon(name): return f'<svg class="icon{" fill" if name=="play" else ""}" aria-hidden="true"><use href="#i-{name}"/></svg>'
symbol='<img class="brand-inverse" src="assets/logo-white.svg" alt="Briefly">'
def brand(href='app.html'): return f'<a class="brand" href="{href}" aria-label="Briefly"><img class="brand-logo" src="assets/logo.svg" alt="" width="132" height="47"></a>'
def versioned(name):
 return name+'?v='+hashlib.sha256((root/name).read_bytes()).hexdigest()[:10]
def head(title,css,js):
 return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#244BEB"><title>{title}</title><link rel="icon" href="assets/app-icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="assets/app-icon-square-180.png"><link rel="stylesheet" href="{versioned("tokens.css")}"><link rel="stylesheet" href="{versioned("base.css")}"><link rel="stylesheet" href="{versioned(css)}"><script src="{versioned(js)}" defer></script></head>'

topics=[('경제','1:44','기준금리가 멈춘 자리,<br>우리 생활은 어떻게 달라질까','금리 결정 너머의 이야기. 대출과 저축, 소비에 남는 영향을 살펴봅니다.'),('사회','1:43','차가 비켜난 도시에<br>사람의 자리가 생긴다','걷기와 대중교통이 바꾸는 일상. 이동의 편의와 도시의 여유를 함께 봅니다.'),('기술','1:45','AI가 만든 콘텐츠,<br>표시가 신뢰를 만들 수 있을까','사진과 글에 붙는 작은 표시. 알려주는 것과 아직 알 수 없는 것을 구분합니다.')]
stories=''
for n,(category,duration,title,desc) in enumerate(topics):
 stories+=f'''<article class="story" data-story="{n}"><div class="story-order">{n+1:02d}</div><div class="story-content"><div class="story-top"><span class="story-category">{category}</span><span class="story-time">{duration}</span><span class="read-status" data-read-status="{n}" hidden>읽음</span><button class="icon-btn" data-action="save" data-topic="{n}" aria-label="{category} 이야기 저장" aria-pressed="false">{icon('save')}</button></div><button class="story-title" data-action="read" data-topic="{n}"><h3>{title}</h3></button><p class="story-summary">{desc}</p><div class="story-bottom"><button class="text-link" data-action="sources" data-topic="{n}">{icon('link')}출처 확인</button><button class="text-link segment" data-action="listen" data-topic="{n}">{icon('headphones')}이 구간 듣기</button></div></div></article>'''
chapters=''.join(f'<button data-action="listen" data-topic="{n}" aria-label="{category} 구간 듣기" aria-pressed="false"><span>{n+1:02d}</span>{category}<i></i></button>' for n,(category,*_) in enumerate(topics))
app=(root/'app.template.html').read_text(encoding='utf-8')
replacements={'HEAD':head('Briefly — 오늘의 브리핑','app.css','app.js'),'DEFS':defs,'BRAND':brand(),'STORIES':stories,'CHAPTERS':chapters}
replacements.update({name.upper():icon(name) for name in paths})
for name,value in replacements.items():
 app=app.replace('{{'+name+'}}',value)
(root/'app.html').write_text(app,encoding='utf-8')
tokens=json.loads((root/'tokens.json').read_text(encoding='utf-8'))
palette=[('Paper','paper','읽기와 기본 화면'),('Mist','mist','보조 표면'),('Ink','ink','제목과 본문'),('Blue','blue','브랜드와 행동'),('Slate','slate','보조 정보'),('Tint','tint','보조 행동·선택')]
swatches=''.join(f'<div class="swatch"><div style="background:{tokens["color"][key]}"></div><b>{name}</b><span>{tokens["color"][key]}</span><small>{role}</small></div>' for name,key,role in palette)
guide=(root/'system.template.html').read_text(encoding='utf-8')
replacements={'HEAD':head('Briefly — BI와 디자인 시스템','system.css','system.js'),'DEFS':defs,'BRAND':brand(),'PALETTE':swatches,'SPACING':''.join(f'<span><i style="height:{v}px"></i>{v}</span>' for v in [4,8,12,16,24,32,48,64])}
replacements.update({name.upper():icon(name) for name in paths})
for name,value in replacements.items():
 guide=guide.replace('{{'+name+'}}',value)
(root/'index.html').write_text(guide,encoding='utf-8')
print('Built v0.3 brand system and mobile-first product from shared components and tokens.')
