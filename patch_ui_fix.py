from pathlib import Path
import base64,re
p=Path('web/index.html'); s=p.read_text(encoding='utf-8')
def uri(path,mime):
 q=Path(path); return 'data:'+mime+';base64,'+base64.b64encode(q.read_bytes()).decode() if q.exists() else ''
app=uri('web/investiga-mark.webp','image/webp'); mahash=uri('web/mahash-logo.webp','image/webp')
if app:s=s.replace('/investiga-mark.webp',app)
if mahash:s=s.replace('/mahash-logo.webp',mahash)
css='''
.app-header{position:sticky;top:0;z-index:60;background:#0b1620;border-bottom:1px solid #253747;padding:14px 12px 16px!important;display:flex!important;justify-content:center!important;align-items:center!important}
.app-brand-stack{width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:7px}.app-header-logo{display:block;width:68px;height:68px;border-radius:17px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 8px 22px rgba(0,0,0,.32)}
.wordmark{direction:ltr!important;unicode-bidi:isolate;display:flex;align-items:center;justify-content:center;height:43px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;font-size:38px;font-weight:900;letter-spacing:.3px;line-height:43px;color:#fff}.wordmark-text{display:block}.wordmark-a{position:relative;display:block;width:35px;height:40px;margin-left:1px;flex:0 0 35px}.wordmark-a .l,.wordmark-a .r{position:absolute;top:1px;width:9px;height:39px;background:linear-gradient(#38d1ff,#159bd5);border-radius:1px}.wordmark-a .l{left:8px;transform:skew(-20deg)}.wordmark-a .r{right:8px;transform:skew(20deg)}
.app-meta{direction:ltr;display:flex;align-items:center;justify-content:center;gap:10px}.app-meta .muted{font-size:14px;color:#9fb0bf;line-height:1.2}.app-meta .tag{margin:0;font-size:13px;padding:5px 10px}.page-brand{display:none!important}.wrap{padding-top:12px!important}#home .hero{text-align:center;padding:20px 0 14px!important;max-width:760px;margin:0 auto}#home .hero>.tag{display:table;margin:0 auto 18px}#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.2}#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.6}#orgStep>h2{text-align:center;margin:30px auto 22px}
@media(max-width:760px){.app-header{padding:13px 10px 15px!important}.app-header-logo{width:66px;height:66px}.wordmark{font-size:36px;height:41px;line-height:41px}.wordmark-a{width:33px;height:38px;flex-basis:33px}.wordmark-a .l,.wordmark-a .r{height:37px;width:8px}.app-meta .muted{font-size:13px}.app-meta .tag{font-size:12px;padding:4px 9px}.wrap{padding-top:8px!important}#home .hero{padding:18px 8px 12px!important}#home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}#home .hero h1{font-size:clamp(34px,9vw,46px)}#home .hero p{font-size:clamp(19px,5vw,23px);line-height:1.6}#orgStep>h2{font-size:clamp(26px,7vw,34px);margin-top:26px}}
'''
for marker in ['.app-header{','.brand-word{']:
 i=s.find(marker)
 if i!=-1:
  j=s.find('</style>',i)
  if j!=-1:s=s[:i]+s[j:]
  break
s=s.replace('</style>',css+'</style>',1)
logo=app or '/investiga-mark.webp'
header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo}" alt=""><div class="wordmark" aria-label="INVESTIGA"><span class="wordmark-text">INVESTIG</span><span class="wordmark-a" aria-hidden="true"><i class="l"></i><i class="r"></i></span></div><div class="app-meta"><span id="version" class="tag">...</span><span class="muted">AI Investigation Simulator</span></div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',header,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8');print('clean exact header applied')
