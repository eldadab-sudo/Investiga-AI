from pathlib import Path
import base64
import re

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

# Correct brand direction and create a geometric cyan A that matches the reference logo.
brand_css='''.brand-word{direction:ltr;unicode-bidi:isolate;font-family:Arial Black,Arial,sans-serif;font-weight:900;letter-spacing:1px;display:inline-flex;align-items:flex-end;line-height:.9;font-size:28px}.brand-word .brand-main{color:#f5f7fa;display:inline-block}.brand-word .brand-a{position:relative;display:inline-block;width:.78em;height:.94em;margin-left:.04em;flex:0 0 .78em}.brand-word .brand-a:before,.brand-word .brand-a:after{content:"";position:absolute;bottom:0;width:.17em;height:1em;background:#27b9ee;border-radius:.025em;transform-origin:bottom center}.brand-word .brand-a:before{left:.19em;transform:skew(-18deg)}.brand-word .brand-a:after{right:.19em;transform:skew(18deg)}header{display:grid!important;grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;padding:18px 6vw!important}.brand-lockup{grid-column:2;display:flex!important;flex-direction:column;align-items:center;justify-content:center;gap:8px;text-align:center}.brand-lockup>.app-brand-mark{width:58px!important;height:58px!important;border-radius:15px!important}.brand{display:flex;flex-direction:column;align-items:center;gap:7px}.brand #version{margin:0}.brand-lockup+div.muted{grid-column:1;grid-row:1;text-align:center;justify-self:center;max-width:170px;line-height:1.25}.page-brand{display:none!important}@media(max-width:760px){header{grid-template-columns:1fr!important;padding:14px 16px 16px!important;gap:7px}.brand-lockup{grid-column:1;grid-row:1}.brand-lockup+div.muted{grid-column:1;grid-row:2;max-width:none;font-size:14px;line-height:1.2}.brand-word{font-size:27px;letter-spacing:.7px}.brand-lockup>.app-brand-mark{width:60px!important;height:60px!important}.brand{gap:6px}}'''

# Remove prior injected brand/header CSS block if present, then append the refined one.
if '.brand-word{' in s:
    start=s.find('.brand-word{')
    end=s.find('</style>',start)
    if start!=-1 and end!=-1:
        s=s[:start]+brand_css+s[end:]
else:
    s=s.replace('</style>',brand_css+'</style>',1)

new_brand='<div class="brand"><span class="brand-word"><span class="brand-main">INVESTIG</span><span class="brand-a" aria-label="A"></span></span><span id="version" class="tag">...</span></div>'
# Normalize any previous brand variant to the new one.
s=re.sub(r'<div class="brand"><span class="brand-word">.*?</span>\s*<span id="version" class="tag">\.\.\.</span></div>',new_brand,s,count=1,flags=re.S)
s=s.replace('<div class="brand">INVESTIGA <span id="version" class="tag">...</span></div>',new_brand)

p.write_text(s,encoding='utf-8')
print('Refined INVESTIGA wordmark and centered header')
