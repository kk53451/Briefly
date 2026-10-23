"""Compare a one-line Briefly icon and a B. icon using the chosen Softpress forms."""
from pathlib import Path
from html import escape
import re
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
BLUE = '#244BEB'
word = (ASSETS / 'app-icon.svg').read_text(encoding='utf-8')

font = instantiateVariableFont(TTFont(ROOT / 'logo-exploration/round-04/fonts/fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf'), {'wght':850,'SOFT':100,'WONK':1,'opsz':144}, inplace=False)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
parts, bounds = [], []
x = 0
for char in 'B.':
    glyph = glyphs[cmap[ord(char)]]
    pen = SVGPathPen(glyphs); glyph.draw(pen)
    box = BoundsPen(glyphs); glyph.draw(box)
    a,b,c,d = box.bounds
    parts.append(f'<path transform="translate({x:.6f} 0)" d="{pen.getCommands()}"/>')
    bounds.append((x+a,b,x+c,d))
    # Place the dot near the B; use the same font's dot, not a substitute circle.
    x = x+c+90
left=min(b[0] for b in bounds); bottom=min(b[1] for b in bounds)
right=max(b[2] for b in bounds); top=max(b[3] for b in bounds)
scale=min(73/(right-left),58/(top-bottom))
tx=(100-(right-left)*scale)/2-left*scale
ty=(100-(top-bottom)*scale)/2+top*scale
monogram=f'<g fill="#fff" transform="translate({tx:.6f} {ty:.6f}) scale({scale:.8f} {-scale:.8f})">'+''.join(parts)+'</g>'

for slug, title, body in [('full-name','Briefly — full name on one line',word), ('b-dot','Briefly — B. app icon',monogram)]:
    for square in [False, True]:
        radius=0 if square else 23
        suffix='-square' if square else ''
        svg=word.replace('rx="23"', f'rx="{radius}"') if slug=='full-name' else f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title><rect width="100" height="100" rx="{radius}" fill="{BLUE}"/>{body}</svg>'
        (ASSETS/f'app-icon-{slug}{suffix}.svg').write_text(svg,encoding='utf-8')
print('Built full-name and B. app icon options, preserving Softpress type.')
