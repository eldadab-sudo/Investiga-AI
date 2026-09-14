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

# Match the supplied logo: bold white INVESTIG + cyan geometric A without a crossbar.
brand_css='''.brand-word{font-family:Arial Black,Arial,sans-serif;font-weight:900;letter-spacing:1.2px;display:inline-flex;align-items:baseline;line-height:1}.brand-word .brand-main{color:#f5f7fa}.brand-word .brand-a{position:relative;display:inline-block;width:.72em;height:.82em;margin-left:.035em;transform:translateY(.055em)}.brand-word .brand-a:before,.brand-word .brand-a:after{content:"";position:absolute;bottom:0;width:.16em;height:.92em;background:#25b9f2;border-radius:.025em}.brand-word .brand-a:before{left:.16em;transform:skew(-18deg)}.brand-word .brand-a:after{right:.16em;transform:skew(18deg)}'''
if '.brand-word{' not in s:
    s=s.replace('</style>', brand_css+'</style>', 1)
else:
    start=s.find('.brand-word{')
    end=s.find('</style>',start)
    if start!=-1 and end!=-1:
        # Replace the previously injected brand CSS block at the end of the style element.
        s=s[:start]+brand_css+s[end:]

old='<div class="brand"><span class="brand-word">INVESTIG<span class="brand-a">Λ</span></span> <span id="version" class="tag">...</span></div>'
new='<div class="brand"><span class="brand-word"><span class="brand-main">INVESTIG</span><span class="brand-a" aria-label="A"></span></span> <span id="version" class="tag">...</span></div>'
s=s.replace(old,new)
s=s.replace('<div class="brand">INVESTIGA <span id="version" class="tag">...</span></div>',new)

p.write_text(s,encoding='utf-8')
print('Embedded logos and matched INVESTIGA wordmark to reference')
