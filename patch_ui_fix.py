from pathlib import Path
import base64

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')

# Embed assets directly into the HTML so the app does not depend on static-file routing.
app_path=Path('web/investiga-mark.webp')
mahash_path=Path('web/mahash-logo.webp')

if app_path.exists():
    app_uri='data:image/webp;base64,'+base64.b64encode(app_path.read_bytes()).decode('ascii')
    s=s.replace('/investiga-mark.webp', app_uri)

if mahash_path.exists():
    mahash_uri='data:image/webp;base64,'+base64.b64encode(mahash_path.read_bytes()).decode('ascii')
    s=s.replace('/mahash-logo.webp', mahash_uri)

# Brand wordmark: keep INVESTIGA, but render the final A in the distinctive logo style.
brand_css='''.brand-word{font-weight:900;letter-spacing:4px;display:inline-flex;align-items:baseline;gap:1px}.brand-word .brand-a{font-size:1.06em;font-weight:900;display:inline-block;transform:translateY(-.02em) scaleX(.86);font-family:Arial Black,Arial,sans-serif}'''
if '.brand-word{' not in s:
    s=s.replace('</style>', brand_css+'</style>', 1)

s=s.replace('<div class="brand">INVESTIGA <span id="version" class="tag">...</span></div>',
            '<div class="brand"><span class="brand-word">INVESTIG<span class="brand-a">Λ</span></span> <span id="version" class="tag">...</span></div>')

p.write_text(s,encoding='utf-8')
print('Embedded app/Mahash logos and styled INVESTIGA wordmark')
