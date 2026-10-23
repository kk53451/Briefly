"""Create font-independent Briefly wordmark studies, with complete-name app tiles."""
from pathlib import Path
from functools import lru_cache
from html import escape
import json
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
BLUE = '#244BEB'
CONCEPTS = [
    dict(id='01', slug='editorial', name='Editorial', ko='이름이 곧 제호',
         font='dmserifdisplay/DMSerifDisplay-Regular.ttf', tracking=-21, ligature=True,
         idea='대문자 B와 높낮이가 또렷한 세리프. f와 l의 연결로 편집 브랜드다운 인상을 만듭니다.',
         detail='기존 세리프 취향을 이어가는 방향 · DM Serif Display'),
    dict(id='02', slug='softpress', name='Softpress', ko='부드럽지만 선명하게',
         font='fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf', axes={'wght':850,'SOFT':100,'WONK':1,'opsz':144}, tracking=-33, ligature=True,
         idea='둥글고 묵직한 활자를 촘촘히 묶었습니다. 매일 만나는 브리핑의 친근한 성격을 이름에 담습니다.',
         detail='둥근 획과 좁은 자간 · Fraunces'),
    dict(id='03', slug='flow', name='Flow', ko='읽다가, 듣다가',
         font='instrumentserif/InstrumentSerif-Italic.ttf', tracking=-13, ligature=True, flourish=True,
         idea='앞으로 흐르는 이탤릭과 긴 곡선. 글에서 목소리로 이어지는 경험을 타이포의 움직임으로 표현합니다.',
         detail='기울기와 긴 흐름선 · Instrument Serif Italic'),
    dict(id='04', slug='edit', name='Edit', ko='핵심만 남긴 글자',
         font='spacegrotesk/SpaceGrotesk[wght].ttf', axes={'wght':700}, tracking=-35, ligature=False, diamond=True,
         idea='단정한 산세리프에 마름모 모양의 i 점을 더했습니다. 이름 안의 작은 표식으로 선별과 집중을 드러냅니다.',
         detail='광학 자간과 i 점 재구성 · Space Grotesk'),
    dict(id='05', slug='headline', name='Headline', ko='한눈에 들어오는 제목',
         font='archivoblack/ArchivoBlack-Regular.ttf', tracking=-29, ligature=False, narrow=.82,
         idea='가로 폭을 압축한 굵은 활자. 짧은 제목처럼 이름이 빠르게 들어오고 작은 화면에서도 힘을 갖습니다.',
         detail='굵은 획과 압축된 비례 · Archivo Black'),
    dict(id='06', slug='typeset', name='Typeset', ko='이름 전체가 하나의 표식',
         font='pretendard', axes={'wght':900}, tracking=-37, ligature=False, stacked=True,
         idea='Bri / efly를 두 줄로 쌓아 정사각형 안에 이름 전체를 담았습니다. 별도 모노그램 없이 글자가 심벌이 됩니다.',
         detail='두 줄의 활자 블록 · Pretendard'),
]

@lru_cache(maxsize=None)
def get_font(slug):
    c = next(c for c in CONCEPTS if c['slug'] == slug)
    path = ROOT.parents[4] / 'flutter/assets/fonts/PretendardVariable.ttf' if c['font']=='pretendard' else ROOT/'fonts'/c['font']
    font=TTFont(path)
    if 'fvar' in font:
        font=instantiateVariableFont(font,c.get('axes',{}),inplace=False)
    return font

def letters(c, text):
    font=get_font(c['slug']); glyphs=font.getGlyphSet(); cmap=font.getBestCmap()
    unit=1000/font['head'].unitsPerEm
    names=[]; i=0
    while i < len(text):
        if c['ligature'] and text[i:i+2]=='fl':
            name=next((n for n in ('f_l','fl') if n in glyphs),None)
            if name:
                names.append((name,'fl')); i+=2; continue
        char=text[i]
        name=cmap[0x131] if char=='i' and c.get('diamond') else cmap[ord(char)]
        names.append((name,char)); i+=1
    x=0; pieces=[]; bounds=[]
    for idx,(name,char) in enumerate(names):
        pen=SVGPathPen(glyphs); glyphs[name].draw(pen)
        box=BoundsPen(glyphs); glyphs[name].draw(box)
        pieces.append(f'<path transform="translate({x:.4f} 0) scale({unit:.7f})" d="{pen.getCommands()}"/>')
        if box.bounds:
            a,b,d,e=box.bounds; bounds.append((x+a*unit,b*unit,x+d*unit,e*unit))
        if char=='i' and c.get('diamond'):
            center=x+glyphs[name].width*unit/2
            top=735; mid=668; half=64
            pieces.append(f'<path d="M{center} {top}L{center+half} {mid}L{center} {mid-half}L{center-half} {mid}Z"/>')
            bounds.append((center-half,mid-half,center+half,top))
        x+=glyphs[name].width*unit+c['tracking']
        if idx+1<len(names):
            pair=char+names[idx+1][1]
            x+= {'Br':-20,'ri':-15,'ie':-8,'efl':-13,'fly':-22,'fl':-18,'ly':-20}.get(pair,0)
    bbox=(min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds))
    return ''.join(pieces),bbox

def fitted(c,text,x,y,w,h):
    paths,(x0,y0,x1,y1)=letters(c,text)
    narrow=c.get('narrow',1)
    scale=min(w/((x1-x0)*narrow),h/(y1-y0))
    tx=x+(w-(x1-x0)*scale*narrow)/2-x0*scale*narrow
    ty=y+(h-(y1-y0)*scale)/2+y1*scale
    return f'<g transform="translate({tx:.5f} {ty:.5f}) scale({scale*narrow:.7f} {-scale:.7f})">{paths}</g>'

def stacked(c,x=12,y=14,w=76,h=72):
    # All seven letters remain, at one type size across both lines.
    first,b1=letters(c,'Bri'); second,b2=letters(c,'efly')
    top1=b1[3]; top2=b2[3]; bottom2=b2[1]
    row1h=top1-b1[1]; row2h=top2-bottom2
    gap=110
    scale=min(w/max(b1[2]-b1[0],b2[2]-b2[0]),h/(row1h+row2h+gap))
    width=max(b1[2]-b1[0],b2[2]-b2[0])*scale
    start=x+(w-width)/2
    ystart=y+(h-(row1h+row2h+gap)*scale)/2
    return f'<g transform="translate({start-b1[0]*scale:.5f} {ystart+top1*scale:.5f}) scale({scale:.7f} {-scale:.7f})">{first}</g><g transform="translate({start-b2[0]*scale:.5f} {ystart+(row1h+gap+top2)*scale:.5f}) scale({scale:.7f} {-scale:.7f})">{second}</g>'

def wordmark(c):
    if c.get('stacked'):
        return stacked(c,100,4,300,152)
    body=fitted(c,'Briefly',20,10,460,125)
    if c.get('flourish'):
        body+='<path d="M158 145C240 125 339 129 447 137" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/>'
    return body

def root_svg(c,kind):
    app=kind=='app-icon'; vb='0 0 100 100' if app else '0 0 500 160'
    body=f'<rect class="tile" width="100" height="100" rx="23" fill="{BLUE}"/><g fill="#fff">{stacked(c)}</g>' if app else f'<g fill="currentColor">{wordmark(c)}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="Briefly {c["name"]} {kind}"><title>Briefly — {c["name"]}</title><desc>The complete name Briefly. App layout reads Bri, then efly.</desc>{body}</svg>'

cards=[]
for c in CONCEPTS:
    word=root_svg(c,'wordmark'); app=root_svg(c,'app-icon')
    for kind,content in [('wordmark',word),('app-icon',app)]:
        (ASSETS/f'{c["id"]}-{c["slug"]}-{kind}.svg').write_text(content,encoding='utf-8')
    cards.append(f'''<article id="concept-{c['id']}" class="concept" data-id="{c['id']}">
      <div class="card-label"><span>{c['id']} / {c['name'].upper()}</span><button data-detail="{c['id']}" aria-label="{c['id']} {c['name']} 확대 보기">확대 ↗</button></div>
      <div class="art"><div class="word-art">{word}</div><div class="app-art">{app}</div></div>
      <h2>{c['ko']}</h2><p>{c['idea']}</p>
      <div class="application"><div class="app-small">{app}</div><div class="app-copy"><b>Briefly</b><span>Bri / efly · 전체 이름</span></div><a href="assets/{c['id']}-{c['slug']}-wordmark.svg" download aria-label="{c['name']} 워드마크 SVG 다운로드">SVG ↓</a></div>
    </article>''')

payload=[{k:v for k,v in c.items() if k in ('id','slug','name','ko','idea','detail')} for c in CONCEPTS]
template=(ROOT/'template.html').read_text(encoding='utf-8')
(ROOT/'index.html').write_text(template.replace('{{CARDS}}','\n'.join(cards)).replace('{{DATA}}',json.dumps(payload,ensure_ascii=False)),encoding='utf-8')

# Presentation board. Every logo is an outline; no font or raster dependency.
board=['<rect width="1560" height="1080" fill="#FFFFFF"/>','<text x="55" y="56" font-family="Arial,sans-serif" font-size="18" fill="#20232A" letter-spacing="2">BRIEFLY / WORDMARK STUDIES</text>','<text x="1505" y="56" text-anchor="end" font-family="Arial,sans-serif" font-size="13" fill="#6D7079" letter-spacing="2">ROUND 04 / THE WHOLE NAME</text>','<path d="M55 90H1505M55 575H1505M520 115V1030M1040 115V1030" stroke="#E1E3E7"/>']
for idx,c in enumerate(CONCEPTS):
    x=55+(idx%3)*520; y=132+(idx//3)*485
    board += [f'<g transform="translate({x} {y})">',f'<text y="0" font-family="Arial,sans-serif" font-size="14" letter-spacing="2" fill="#626874">{c["id"]} / {c["name"].upper()}</text>',f'<g transform="translate(-3 70) scale(.86)" fill="{BLUE}" color="{BLUE}">{wordmark(c)}</g>',f'<g transform="translate(7 273) scale(.83)"><rect width="100" height="100" rx="23" fill="{BLUE}"/><g fill="#fff">{stacked(c)}</g></g>',f'<g transform="translate(114 276) scale(.48)"><rect width="100" height="100" rx="23" fill="#20232A"/><g fill="#fff">{stacked(c)}</g></g>','<text x="115" y="353" font-family="Arial,sans-serif" font-size="11" fill="#626874">FULL NAME</text>','</g>']
(ROOT/'comparison.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="1080" viewBox="0 0 1560 1080">'+''.join(board)+'</svg>',encoding='utf-8')
print('Built six outlined Briefly wordmarks and six complete-name app icons.')
