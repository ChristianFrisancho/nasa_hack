"""Bundle the static dashboard and compressed evidence into one openable HTML file."""
import base64
import gzip
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
html = (HERE / 'index.html').read_text(encoding='utf-8')
css = (HERE / 'styles.css').read_text(encoding='utf-8')
css = re.sub(r'^@import url\([^\n]+\);\s*', '', css)
d3 = (HERE / 'vendor' / 'd3.min.js').read_text(encoding='utf-8')
app = (HERE / 'app.js').read_text(encoding='utf-8')
data = (HERE / 'data' / 'dashboard.json').read_text(encoding='utf-8')
quick_data = (HERE / 'data' / 'quick_rotation.json.gz').read_bytes()
evidence = (ROOT / 'piura-agro' / 'consolidado' / 'piura_super_dataset.csv').read_bytes()

if '</script' in d3.lower() or '</script' in app.lower():
    raise ValueError('Unsafe inline script end tag in source')

evidence_b64 = base64.b64encode(gzip.compress(evidence, compresslevel=9, mtime=0)).decode('ascii')
quick_data_b64 = base64.b64encode(quick_data).decode('ascii')
data = data.replace('<', '\\u003c')
html = html.replace('<link rel="stylesheet" href="./styles.css">', '<style>\n' + css + '\n</style>')
html = html.replace('<script defer src="./vendor/d3.min.js"></script>',
                    '<script>\n' + d3 + '\n</script>')
html = html.replace('<script defer src="./app.js"></script>',
                    '<script id="dashboard-inline-data" type="application/json">' + data + '</script>\n'
                    '<script id="quick-rotation-inline-data" type="application/octet-stream">' + quick_data_b64 + '</script>\n'
                    '<script id="evidence-inline-data" type="application/octet-stream">' + evidence_b64 + '</script>\n'
                    '<script>\n' + app + '\n</script>')

if '<script defer src=' in html or '<link rel="stylesheet"' in html:
    raise ValueError('An external local asset was not bundled')

output = HERE / 'standalone.html'
output.write_text(html, encoding='utf-8')
print(f'{output.relative_to(ROOT)}: {output.stat().st_size:,} bytes, opens with file://')
