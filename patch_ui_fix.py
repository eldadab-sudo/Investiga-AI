from pathlib import Path
import base64,re
p=Path('web/index.html'); s=p.read_text(encoding='utf-8')

def uri(path,mime):
 q=Path(path)
 return 'data:'+mime+';base64,'+base64.b64encode(q.read_bytes()).decode() if q.exists() else ''
app=uri('web/investiga-mark.webp','image/webp')
mahash=uri('web/mahash-logo.webp','image/webp')
if app: s=s.replace('/investiga-mark.webp',app)
if mahash: s=s.replace('/mahash-logo.webp',mahash)

css='''
.app-header{position:sticky;top:0;z-index:60;background:#0b1620;border-bottom:1px solid #253747;padding:18px 12px 20px!important;display:flex!important;justify-content:center!important;align-items:center!important}
.app-brand-stack{width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:9px}
.app-header-logo{display:block;width:72px;height:72px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 9px 26px rgba(0,0,0,.32)}
.wordmark{direction:ltr!important;unicode-bidi:isolate;display:flex;align-items:flex-end;justify-content:center;gap:0;height:47px;margin:0 auto;color:#f7f9fb;font-family:Arial,Helvetica,sans-serif;font-size:40px;font-weight:900;letter-spacing:1.2px;line-height:47px}
.wordmark-a{position:relative;display:inline-block;width:34px;height:42px;margin-left:2px;flex:0 0 34px}
.wordmark-a:before,.wordmark-a:after{content:'';position:absolute;bottom:1px;width:9px;height:42px;background:#24bdf2;border-radius:1px}
.wordmark-a:before{left:6px;transform:skew(-20deg)}
.wordmark-a:after{right:6px;transform:skew(20deg)}
.app-meta{direction:ltr;display:flex;align-items:center;justify-content:center;gap:10px;margin-top:0}
.app-meta .muted{font-size:14px;color:#9fb0bf;line-height:1.2}.app-meta .tag{margin:0;font-size:13px;padding:5px 10px}
.page-brand{display:none!important}.wrap{padding-top:14px!important}
#home .hero{text-align:center;padding:22px 0 16px!important;max-width:760px;margin:0 auto}#home .hero>.tag{display:table;margin:0 auto 18px}#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.22}#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.62}#orgStep>h2{text-align:center;margin:32px auto 22px}
@media(max-width:760px){.app-header{padding:16px 12px 18px!important}.app-header-logo{width:70px;height:70px}.wordmark{font-size:38px;height:45px;line-height:45px;letter-spacing:.8px}.wordmark-a{width:32px;height:40px;flex-basis:32px}.wordmark-a:before,.wordmark-a:after{height:40px;width:8px}.app-meta .muted{font-size:13px}.app-meta .tag{font-size:12px;padding:4px 9px}.wrap{padding-top:10px!important}#home .hero{padding:20px 8px 14px!important}#home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}#home .hero h1{font-size:clamp(34px,9vw,47px);line-height:1.22;margin-top:0}#home .hero p{font-size:clamp(19px,5vw,24px);line-height:1.65}#orgStep>h2{font-size:clamp(26px,7vw,35px);margin-top:28px}}
'''
# remove prior injected UI CSS from first known marker through style end, preserving original style before it
for marker in ['.app-header{','.brand-word{']:
 i=s.find(marker)
 if i!=-1:
  j=s.find('</style>',i)
  if j!=-1: s=s[:i]+s[j:]
  break
s=s.replace('</style>',css+'</style>',1)
logo=app or '/investiga-mark.webp'
header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo}" alt="INVESTIGA"><div class="wordmark" aria-label="INVESTIGA"><span>INVESTIG</span><span class="wordmark-a" aria-hidden="true"></span></div><div class="app-meta"><span id="version" class="tag">...</span><span class="muted">AI Investigation Simulator</span></div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',header,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
print('deterministic header applied')
