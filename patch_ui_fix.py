from pathlib import Path
import base64
import re

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')

app_path=Path('web/investiga-mark.webp')
mahash_path=Path('web/mahash-logo.webp')

def data_uri(path,mime):
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode('ascii') if path.exists() else ''

app_uri=data_uri(app_path,'image/webp')
mahash_uri=data_uri(mahash_path,'image/webp')
if app_uri: s=s.replace('/investiga-mark.webp',app_uri)
if mahash_uri: s=s.replace('/mahash-logo.webp',mahash_uri)

css='''
.app-header{position:sticky;top:0;z-index:60;background:rgba(11,22,32,.985);backdrop-filter:blur(12px);border-bottom:1px solid #253747;padding:16px 16px 18px!important;display:flex!important;justify-content:center!important;align-items:center!important}
.app-brand-stack{width:100%;max-width:520px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:9px}
.app-header-logo{display:block;width:72px;height:72px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 9px 26px rgba(0,0,0,.32)}
.brand-wordmark-svg{display:block;width:270px;max-width:78vw;height:auto;margin:1px auto 0;overflow:visible}
.app-meta{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:1px}
.app-meta .muted{font-size:14px;color:#9fb0bf;line-height:1.2}
.app-meta .tag{margin:0;font-size:13px;padding:5px 10px}
.page-brand{display:none!important}
.wrap{padding-top:14px!important}
#home .hero{text-align:center;padding:22px 0 16px!important;max-width:760px;margin:0 auto}
#home .hero>.tag{display:table;margin:0 auto 18px}
#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.22}
#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.62}
#orgStep>h2{text-align:center;margin:32px auto 22px}
@media(max-width:760px){
 .app-header{padding:15px 12px 17px!important}
 .app-brand-stack{gap:8px}
 .app-header-logo{width:70px;height:70px;border-radius:18px}
 .brand-wordmark-svg{width:260px;max-width:80vw}
 .app-meta{gap:8px}
 .app-meta .muted{font-size:13px}
 .app-meta .tag{font-size:12px;padding:4px 9px}
 .wrap{padding-top:10px!important}
 #home .hero{padding:20px 8px 14px!important}
 #home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}
 #home .hero h1{font-size:clamp(34px,9vw,47px);line-height:1.22;margin-top:0}
 #home .hero p{font-size:clamp(19px,5vw,24px);line-height:1.65}
 #orgStep>h2{font-size:clamp(26px,7vw,35px);margin-top:28px}
}
'''
for marker in ('.brand-word{','.app-header{'):
    if marker in s:
        start=s.find(marker); end=s.find('</style>',start)
        if start!=-1 and end!=-1:
            s=s[:start]+s[end:]; break
s=s.replace('</style>',css+'</style>',1)

logo_src=app_uri or '/investiga-mark.webp'
wordmark='''<svg class="brand-wordmark-svg" viewBox="0 0 268 48" role="img" aria-label="INVESTIGA" xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="39" fill="#F7F9FB" font-family="Arial Black,Arial,sans-serif" font-size="40" font-weight="900" textLength="208" lengthAdjust="spacingAndGlyphs">INVESTIG</text>
  <g fill="#26BDF2" transform="translate(214,1)">
    <path d="M0 39 L16 0 H25 L10 39 Z"/>
    <path d="M22 0 H31 L47 39 H36 Z"/>
  </g>
</svg>'''
new_header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo_src}" alt="">{wordmark}<div class="app-meta"><span id="version" class="tag">...</span><span class="muted">AI Investigation Simulator</span></div></div></header>'''

# Replace any previous header completely. This removes broken image placeholders and legacy wordmarks.
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',new_header,s,count=1,flags=re.S)

p.write_text(s,encoding='utf-8')
print('Applied inline INVESTIGA wordmark with no external image dependency')
