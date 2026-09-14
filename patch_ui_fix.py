from pathlib import Path
import base64
import re

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')

# Embed image assets directly so branding never depends on static-file routing.
app_path=Path('web/investiga-mark.webp')
mahash_path=Path('web/mahash-logo.webp')
app_uri=''
mahash_uri=''
if app_path.exists():
    app_uri='data:image/webp;base64,'+base64.b64encode(app_path.read_bytes()).decode('ascii')
    s=s.replace('/investiga-mark.webp', app_uri)
if mahash_path.exists():
    mahash_uri='data:image/webp;base64,'+base64.b64encode(mahash_path.read_bytes()).decode('ascii')
    s=s.replace('/mahash-logo.webp', mahash_uri)

# One deterministic, centered header. The wordmark is an SVG so RTL cannot reorder the final A.
header_css='''
.app-header{position:sticky;top:0;z-index:60;background:rgba(13,23,33,.96);backdrop-filter:blur(10px);border-bottom:1px solid #263646;padding:18px 18px 20px!important;display:flex!important;justify-content:center!important;align-items:center!important}
.app-brand-stack{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;text-align:center;width:100%}
.app-header-logo{width:70px;height:70px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 10px 28px rgba(0,0,0,.32)}
.brand-svg{display:block;width:260px;max-width:78vw;height:auto;overflow:visible}
.app-meta{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap}
.app-meta .muted{font-size:15px;color:#9fb0bf;line-height:1}
.app-meta .tag{margin:0}
.page-brand{display:none!important}
#home .hero{text-align:center;padding:26px 0 20px!important}
#home .hero>.tag{display:table;margin:0 auto 18px}
#home .hero p{margin-left:auto;margin-right:auto}
#orgStep>h2{text-align:center;margin-top:34px}
.wrap{padding-top:18px!important}
@media(max-width:760px){
 .app-header{padding:16px 14px 18px!important}
 .app-header-logo{width:68px;height:68px;border-radius:17px}
 .brand-svg{width:250px;max-width:84vw}
 .app-meta{gap:8px}
 .app-meta .muted{font-size:14px}
 .wrap{padding-top:12px!important}
 #home .hero{padding-top:22px!important}
}
'''

# Remove previous injected brand/header CSS from the last patch, if present.
for marker in ('.brand-word{','.app-header{'):
    if marker in s:
        start=s.find(marker)
        end=s.find('</style>',start)
        if start!=-1 and end!=-1:
            s=s[:start]+s[end:]
            break
s=s.replace('</style>',header_css+'</style>',1)

logo_src=app_uri if app_uri else '/investiga-mark.webp'
wordmark='''<svg class="brand-svg" viewBox="0 0 286 54" role="img" aria-label="INVESTIGA" xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="43" fill="#F7F9FB" font-family="Arial Black,Arial,sans-serif" font-size="43" font-weight="900" letter-spacing="1">INVESTIG</text>
  <g fill="#27B9EE" transform="translate(230,2)">
    <path d="M0 40 L16 0 H26 L10 40 Z"/>
    <path d="M21 0 H31 L47 40 H36 Z"/>
  </g>
</svg>'''
new_header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo_src}" alt="INVESTIGA"><div dir="ltr">{wordmark}</div><div class="app-meta"><span id="version" class="tag">...</span><span class="muted">AI Investigation Simulator</span></div></div></header>'''

# Replace the entire old header so no legacy alignment or RTL markup survives.
s=re.sub(r'<header>.*?</header>',new_header,s,count=1,flags=re.S)
s=re.sub(r'<header class="app-header">.*?</header>',new_header,s,count=1,flags=re.S)

p.write_text(s,encoding='utf-8')
print('Applied polished centered header and deterministic SVG INVESTIGA wordmark')
