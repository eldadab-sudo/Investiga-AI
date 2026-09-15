from pathlib import Path
import base64,re
p=Path('web/index.html'); s=p.read_text(encoding='utf-8')
def uri(path,mime):
 q=Path(path); return 'data:'+mime+';base64,'+base64.b64encode(q.read_bytes()).decode() if q.exists() else ''
app=uri('web/investiga-mark.webp','image/webp'); mahash=uri('web/mahash-logo.webp','image/webp')
if app:s=s.replace('/investiga-mark.webp',app)
if mahash:s=s.replace('/mahash-logo.webp',mahash)
css='''
.app-header{position:sticky;top:0;z-index:60;background:#0b1620;border-bottom:1px solid #253747;padding:14px 12px 16px!important;display:flex!important;justify-content:center!important;align-items:center!important}.app-brand-stack{width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:7px}.app-header-logo{display:block;width:74px;height:74px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 8px 22px rgba(0,0,0,.32)}.wordmark{direction:ltr!important;unicode-bidi:isolate;display:flex;align-items:flex-end;justify-content:center;margin:4px auto 3px;font-family:Arial,Helvetica,sans-serif;font-size:34px;font-weight:800;letter-spacing:-.55px;line-height:34px;color:#fff;white-space:nowrap}.wordmark-main{display:block}.logo-a{display:block;width:25px;height:34px;margin-left:1px;flex:0 0 25px}.logo-a svg{display:block;width:100%;height:100%;overflow:visible}.wordmark-img,.wordmark-text,.brand-word,.brand-a{display:none!important}.app-meta{direction:ltr;display:flex;align-items:center;justify-content:center;gap:9px}.app-meta .muted{font-size:13px;color:#9fb0bf;line-height:1.2}.app-meta .tag{margin:0;font-size:12px;padding:4px 9px}.page-brand{display:none!important}.wrap{padding-top:10px!important}#home .hero{text-align:center;padding:18px 0 12px!important;max-width:760px;margin:0 auto}#home .hero>.tag{display:table;margin:0 auto 17px}#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.2}#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.6}#orgStep>h2{text-align:center;margin:28px auto 21px}@media(max-width:760px){.app-header{padding:14px 10px 16px!important}.app-header-logo{width:72px;height:72px}.wordmark{font-size:33px;line-height:33px}.logo-a{width:24.5px;height:33px;flex-basis:24.5px}.app-meta .muted{font-size:12.5px}.app-meta .tag{font-size:12px;padding:4px 9px}.wrap{padding-top:8px!important}#home .hero{padding:17px 8px 11px!important}#home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}#home .hero h1{font-size:clamp(33px,8.7vw,44px)}#home .hero p{font-size:clamp(18px,4.8vw,22px);line-height:1.6}#orgStep>h2{font-size:clamp(25px,6.8vw,33px);margin-top:25px}}
'''
for marker in ['.app-header{','.brand-word{']:
 i=s.find(marker)
 if i!=-1:
  j=s.find('</style>',i)
  if j!=-1:s=s[:i]+s[j:]
  break
s=s.replace('</style>',css+'</style>',1)
logo=app or '/investiga-mark.webp'
a_svg='''<svg viewBox="0 0 25 34" aria-hidden="true" focusable="false"><defs><linearGradient id="investigaBlue" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#31C8F4"/><stop offset="0.55" stop-color="#16B8EE"/><stop offset="1" stop-color="#0799D8"/></linearGradient></defs><path d="M0 34 L9.25 0 H15.75 L25 34 H18.1 L12.5 11.2 L6.9 34 Z" fill="url(#investigaBlue)"/></svg>'''
header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo}" alt="INVESTIGA icon"><div class="wordmark" aria-label="INVESTIGA"><span class="wordmark-main">INVESTIG</span><span class="logo-a">{a_svg}</span></div><div class="app-meta"><span id="version" class="tag">...</span><span class="muted">AI Investigation Simulator</span></div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',header,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8');print('Applied approved INVESTIGA design: full-height proportional crossbar-free A with icon-matched cyan gradient')
