"""Publish approved Round 04 / 02 Softpress outlines without changing their shape."""
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from fontTools.svgLib.path import parse_path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.momentsPen import MomentsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'logo-exploration/round-04'
ASSETS = ROOT / 'assets'
BLUE = '#244BEB'
ASSETS.mkdir(exist_ok=True)

source = SOURCE / 'assets/02-softpress-wordmark.svg'
pen = BoundsPen(None)
def collect_bounds(element, parent=Identity, target=pen):
    transform = parent
    for op, arguments in re.findall(r'(translate|scale)\(([^)]+)\)', element.get('transform', '')):
        values = [float(v) for v in re.split(r'[ ,]+', arguments.strip())]
        transform = transform.translate(*values) if op == 'translate' else transform.scale(*values)
    if element.tag.endswith('}path'):
        parse_path(element.attrib['d'], TransformPen(target, transform))
    for child in element:
        collect_bounds(child, transform, target)
collect_bounds(ET.parse(source).getroot())
x0, y0, x1, y1 = pen.bounds
# Remove comparison-board whitespace only; retain the selected glyphs exactly.
pad = 3
viewbox = f'{x0-pad:.6f} {y0-pad:.6f} {x1-x0+pad*2:.6f} {y1-y0+pad*2:.6f}'
word = source.read_text(encoding='utf-8')
word = re.sub(r'viewBox="[^"]+"', f'viewBox="{viewbox}"', word, count=1)
word = word.replace('The complete name Briefly. App layout reads Bri, then efly.', 'Approved Briefly wordmark. Round 04, option 02 Softpress. All seven letters are outlined paths.')
for suffix, color in [('', BLUE), ('-white', '#FFFFFF'), ('-black', '#000000'), ('-current', 'currentColor')]:
    (ASSETS / f'logo{suffix}.svg').write_text(word.replace('fill="currentColor"', f'fill="{color}"'), encoding='utf-8')

# Center the visible ink, compensating for the y descender's light lower area.
# Keep the selected option's original scale and horizontal placement.
moments = MomentsPen(None)
source_root = ET.parse(source).getroot()
collect_bounds(source_root, target=moments)
ink_center_y = moments.momentY / moments.area
icon_scale = min(88 / (x1-x0+pad*2), 32 / (y1-y0+pad*2))
tx = 50 - (x0+x1)/2 * icon_scale
ty = 50 - ink_center_y * icon_scale
ET.register_namespace('', 'http://www.w3.org/2000/svg')
outlines = ET.tostring(source_root.find('{http://www.w3.org/2000/svg}g'), encoding='unicode').replace('fill="currentColor"', 'fill="#FFFFFF"')
app = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="Briefly full-name app icon"><title>Briefly — approved app icon</title><desc>Full name on one line. Visible letter area is vertically centered at 50.</desc><rect width="100" height="100" rx="23" fill="{BLUE}"/><g transform="translate({tx:.8f} {ty:.8f}) scale({icon_scale:.10f})">{outlines}</g></svg>'
(ASSETS / 'app-icon.svg').write_text(app, encoding='utf-8')
(ASSETS / 'app-icon-square.svg').write_text(app.replace('rx="23"', 'rx="0"'), encoding='utf-8')
(ASSETS / 'app-icon-black.svg').write_text(app.replace(BLUE, '#000000'), encoding='utf-8')
# Preserve the old asset URL, now containing the approved full-name mark.
(ASSETS / 'symbol.svg').write_text(app, encoding='utf-8')
# Keep comparison links pointing to the final centered option.
(ASSETS / 'app-icon-full-name.svg').write_text(app, encoding='utf-8')
(ASSETS / 'app-icon-full-name-square.svg').write_text(app.replace('rx="23"', 'rx="0"'), encoding='utf-8')
# The old stacked version remains an explicitly historical exploration asset.
old_stack = (SOURCE / 'assets/02-softpress-app-icon.svg').read_text(encoding='utf-8')
stacked = re.sub(r'<rect\b[^>]*/>', '', old_stack).replace('fill="#fff"', 'fill="currentColor"')
(ASSETS / 'stacked-mark.svg').write_text(stacked, encoding='utf-8')
license_dir = ASSETS / 'licenses'
license_dir.mkdir(exist_ok=True)
shutil.copyfile(SOURCE / 'fonts/fraunces/OFL.txt', license_dir / 'Fraunces-OFL.txt')
print(f'Published one-line Briefly icon. Optical vertical adjustment: {(y0+y1)/2-ink_center_y:.4f} source units; ink center = 50/100.')
