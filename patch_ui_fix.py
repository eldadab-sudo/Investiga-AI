from pathlib import Path
import base64
import re

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')

app_path=Path('web/investiga-mark.webp')
mahash_path=Path('web/mahash-logo.webp')
wordmark_path=Path('web/investiga-wordmark.png')

def data_uri(path,mime):
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode('ascii') if path.exists() else ''

app_uri=data_uri(app_path,'image/webp')
mahash_uri=data_uri(mahash_path,'image/webp')
wordmark_uri=data_uri(wordmark_path,'image/png')
if app_uri: s=s.replace('/investiga-mark.webp',app_uri)
if mahash_uri: s=s.replace('/mahash-logo.webp',mahash_uri)

css='''
.app-header{position:sticky;top:0;z-index:60;background:rgba(11,22,32,.97);backdrop-filter:blur(12px);border-bottom:1px solid #253747;padding:16px 16px 18px!important;display:flex!important;justify-content:center!important;align-items:center!important}
.app-brand-stack{width:100%;max-width:520px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:8px}
.app-header-logo{display:block;width:66px;height:66px;border-radius:17px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 8px 24px rgba(0,0,0,.3)}
.brand-wordmark{display:block;width:270px;max-width:80vw;height:auto;margin:2px auto 0}
.app-meta{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:1px}
.app-meta .muted{font-size:14px;color:#9fb0bf;line-height:1.2}
.app-meta .tag{margin:0;font-size:13px;padding:5px 10px}
.page-brand{display:none!important}
.wrap{padding-top:16px!important}
#home .hero{text-align:center;padding:24px 0 18px!important;max-width:760px;margin:0 auto}
#home .hero>.tag{display:table;margin:0 auto 18px}
#home .hero h1{max-width:680px;margin-left:auto;margin-right:auto;line-height:1.25}
#home .hero p{max-width:620px;margin-left:auto;margin-right:auto;line-height:1.65}
#orgStep>h2{text-align:center;margin:34px auto 22px}
@media(max-width:760px){
 .app-header{padding:14px 12px 16px!important}
 .app-brand-stack{gap:7px}
 .app-header-logo{width:62px;height:62px;border-radius:16px}
 .brand-wordmark{width:248px;max-width:78vw}
 .app-meta{gap:8px}
 .app-meta .muted{font-size:13px}
 .app-meta .tag{font-size:12px;padding:4px 9px}
 .wrap{padding-top:10px!important}
 #home .hero{padding:20px 8px 14px!important}
 #home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}
 #home .hero h1{font-size:clamp(34px,9vw,48px);line-height:1.22;margin-top:0}
 #home .hero p{font-size:clamp(19px,5vw,25px);line-height:1.7}
 #orgStep>h2{font-size:clamp(26px,7vw,36px);margin-top:28px}
}
'''
for marker in ('.brand-word{','.app-header{'):
    if marker in s:
        start=s.find(marker); end=s.find('</style>',start)
        if start!=-1 and end!=-1:
            s=s[:start]+s[end:]; break
s=s.replace('</style>',css+'</style>',1)

logo_src=app_uri or '/investiga-mark.webp'
word_src=wordmark_uri or '/investiga-wordmark.png'
new_header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo_src}" alt=""><img class="brand-wordmark" src="{word_src}" alt="INVESTIGA"><div class="app-meta"><span class="muted">AI Investigation Simulator</span><span id="version" class="tag">...</span></div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',new_header,s,count=1,flags=re.S)

p.write_text(s,encoding='utf-8')
print('Applied exact approved wordmark and refined responsive header')
