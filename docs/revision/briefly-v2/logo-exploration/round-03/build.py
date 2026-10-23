"""Build the six SVG concepts and the review page. No image API is involved."""
from pathlib import Path
import base64
import html
import json

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
BLUE = '#244BEB'

CONCEPTS = [
    dict(id='01', slug='unfold', name='Unfold', ko='하루를 여는 틈',
         idea='페이지 사이의 틈이 새로운 방향으로 열린다. 펼친 책의 정면 대신, 종이가 움직이는 순간을 잡았다.',
         method='두 면의 기하 · 비대칭 절개',
         shapes='<path d="M19 24C32 25 45 31 49 43L44 77C38 65 25 60 16 56Z"/><path d="M58 20C69 27 80 39 84 51L53 79L58 48C59 38 59 28 58 20Z"/>'),
    dict(id='02', slug='gather', name='Gather', ko='흩어진 이야기가 하나로',
         idea='각각의 짧은 문장이 한 지점으로 모인다. 흩어진 소식을 선별해 하나의 브리핑으로 만드는 행동을 담았다.',
         method='캡슐 모듈 · 크기와 방향의 리듬',
         shapes='<rect x="17" y="54" width="14" height="14" rx="7"/><rect x="32" y="37" width="13" height="31" rx="6.5"/><rect x="49" y="22" width="13" height="46" rx="6.5"/><path d="M69 24C69 20 72 18 76 20C82 23 85 27 85 32V61C85 66 81 70 76 72L69 75Z"/>',
         transform='rotate(18 50 50)'),
    dict(id='03', slug='cadence', name='Cadence', ko='문장이 소리가 되는 결',
         idea='세 줄의 문장이 접히며 같은 방향으로 흐른다. 글의 질서와 소리의 리듬을 하나의 선 체계로 연결했다.',
         method='평행 곡선 · 일정한 획과 여백',
         shapes='<g fill="none" stroke="currentColor" stroke-width="9" stroke-linecap="round"><path d="M22 24V48C22 68 35 78 55 78"/><path d="M43 24V45C43 60 53 67 68 67"/><path d="M64 24V41C64 51 71 56 82 56"/></g>',
         transform='rotate(-12 50 50)'),
    dict(id='04', slug='daymark', name='Daymark', ko='오늘을 찍는 한 점',
         idea='지나가는 하루의 곡선 위에 한 점을 남긴다. 짧게 읽고, 오늘의 맥락을 기억하는 작은 일상의 표식이다.',
         method='원과 점 · 열린 내부 공간',
         shapes='<path d="M68 21C61 17 55 16 48 17C30 19 18 34 19 51C20 70 34 83 53 83C67 83 78 75 82 63C70 67 60 64 55 55C48 42 55 30 68 21Z"/><circle cx="77" cy="33" r="9"/>'),
    dict(id='05', slug='interleaf', name='Interleaf', ko='행간에서 만나는 맥락',
         idea='서로 다른 두 관점 사이에 새로운 여백이 생긴다. 내용을 쌓는 것보다, 관계를 읽게 하는 브리핑의 역할이다.',
         method='겹친 두 면 · 음각으로 만든 교차점',
         shapes='<path d="M19 24H61C72 24 81 34 81 45V49H57C56 35 43 31 19 39Z"/><path d="M81 76H39C28 76 19 66 19 55V51H43C44 65 57 69 81 61Z"/>',
         transform='rotate(-28 50 50)'),
    dict(id='06', slug='swift', name='Swift', ko='소식을 건네는 종이새',
         idea='접힌 종이와 날아가는 새가 번갈아 읽힌다. 가볍게 도착하지만 방향은 분명한, 짧은 데일리 브리핑이다.',
         method='접힌 면 · 두 가지로 읽히는 실루엣',
         shapes='<path d="M15 23C33 24 46 34 49 49L48 78L28 56C22 49 21 36 15 23Z"/><path d="M55 51L70 34C75 28 82 28 89 31L77 40C71 46 68 60 60 68L53 75Z"/>'),
]

def group(concept):
    transform = f' transform="{concept["transform"]}"' if concept.get('transform') else ''
    return f'<g fill="currentColor"{transform}>{concept["shapes"]}</g>'

def svg(concept, icon=False):
    title = html.escape(f'BRIEFLY {concept["name"]} {"app icon" if icon else "symbol"}')
    background = f'<rect width="100" height="100" rx="23" fill="{BLUE}"/>' if icon else ''
    color = ' style="color:#fff"' if icon else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-labelledby="title"{color}><title id="title">{title}</title>{background}{group(concept)}</svg>'

def wordmark():
    # Show the actual selected B region of the original board. No new font or redraw.
    return '<svg class="wordmark" viewBox="668 115 438 190" role="img" aria-label="선택한 B 워드마크 원본"><image href="../logo-options.png" width="1774" height="887"/></svg>'

for concept in CONCEPTS:
    for kind in ['symbol', 'app-icon']:
        (ASSETS / f'{concept["id"]}-{concept["slug"]}-{kind}.svg').write_text(svg(concept, kind == 'app-icon'), encoding='utf-8')

cards = []
for c in CONCEPTS:
    mark = f'<svg viewBox="0 0 100 100" aria-hidden="true">{group(c)}</svg>'
    sizes = ''.join(f'<div class="size-sample"><span class="app-icon" style="width:{s}px;height:{s}px">{mark}</span><span>{s}</span></div>' for s in (16, 24, 32, 64))
    cards.append(f'''<article class="logo-card" id="concept-{c['id']}" data-id="{c['id']}">
      <div class="card-top"><span class="serial">{c['id']} / {c['name'].upper()}</span><button class="pin" type="button" data-pin="{c['id']}" aria-label="{c['id']} {c['name']} 비교에 담기" aria-pressed="false">비교 +</button></div>
      <button class="concept-open" data-detail="{c['id']}" aria-label="{c['id']} {c['name']} 자세히 보기"><span class="app-icon hero-icon">{mark}</span><span class="naked-symbol">{mark}</span></button>
      <h2>{c['ko']}</h2><p>{c['idea']}</p>
      <div class="card-bottom"><span>{c['method']}</span><a href="assets/{c['id']}-{c['slug']}-symbol.svg" download aria-label="{c['name']} 심벌 SVG 다운로드">SVG ↗</a></div>
      <div class="size-row" aria-label="실제 CSS 픽셀 크기 비교">{sizes}<span class="size-caption">실제 크기 · px</span></div>
    </article>''')

template = (ROOT / 'template.html').read_text(encoding='utf-8')
payload = [{k: v for k, v in c.items() if k not in ('shapes', 'transform')} for c in CONCEPTS]
page = template.replace('{{WORDMARK}}', wordmark()).replace('{{CARDS}}', '\n'.join(cards)).replace('{{CONCEPT_DATA}}', json.dumps(payload, ensure_ascii=False))
(ROOT / 'index.html').write_text(page, encoding='utf-8')

# Portable comparison board with the unchanged B raster embedded as a viewport.
reference = base64.b64encode((ROOT.parent / 'logo-options.png').read_bytes()).decode()
elements = ['<rect width="1500" height="1160" fill="#FFFFFF"/>', f'<svg x="50" y="20" width="205" height="90" viewBox="668 115 438 190"><image href="data:image/png;base64,{reference}" width="1774" height="887"/></svg>', '<text x="1450" y="74" text-anchor="end" font-family="Arial,sans-serif" font-size="15" letter-spacing="3" fill="#666A71">SYMBOL STUDIES / 03</text>']
for n, c in enumerate(CONCEPTS):
    x, y = 50 + (n % 3) * 490, 145 + (n // 3) * 525
    elements += [f'<g transform="translate({x} {y})">', f'<text y="22" font-family="Arial,sans-serif" font-size="16" letter-spacing="2" fill="#343840">{c["id"]} / {c["name"].upper()}</text>', f'<g transform="translate(30 65) scale(2.9)" color="{BLUE}"><rect width="100" height="100" rx="23" fill="{BLUE}"/><g color="#fff">{group(c)}</g></g>', f'<g transform="translate(350 160) scale(.8)" color="#181A20">{group(c)}</g>']
    for j, size in enumerate([16, 24, 32, 64]):
        sx = 35 + j * 70
        elements.append(f'<g transform="translate({sx} 390) scale({size / 100})"><rect width="100" height="100" rx="23" fill="{BLUE}"/><g color="#fff">{group(c)}</g></g>')
        elements.append(f'<text x="{sx + size / 2}" y="472" font-family="Arial,sans-serif" font-size="12" fill="#666A71" text-anchor="middle">{size}</text>')
    elements.append('</g>')
elements.extend(['<path d="M525 145V1135M1015 145V1135M50 640H1450" stroke="#DCDDD7"/>'])
(ROOT / 'comparison.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1160" viewBox="0 0 1500 1160">' + ''.join(elements) + '</svg>', encoding='utf-8')
print('Built six symbol SVGs, six app-icon SVGs, index.html and comparison.svg.')
