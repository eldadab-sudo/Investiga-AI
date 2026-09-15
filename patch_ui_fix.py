from pathlib import Path
import base64,re
p=Path('web/index.html'); s=p.read_text(encoding='utf-8')
def uri(path,mime):
 q=Path(path); return 'data:'+mime+';base64,'+base64.b64encode(q.read_bytes()).decode() if q.exists() else ''
app=uri('web/investiga-mark.webp','image/webp'); mahash=uri('web/mahash-logo.webp','image/webp')
if app:s=s.replace('/investiga-mark.webp',app)
if mahash:s=s.replace('/mahash-logo.webp',mahash)
css='''
.app-header{position:sticky;top:0;z-index:60;background:#0b1620;border-bottom:1px solid #253747;padding:14px 12px 16px!important;display:flex!important;justify-content:center!important}.app-brand-stack{width:100%;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px}.app-header-logo{display:block;width:74px;height:74px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 8px 22px rgba(0,0,0,.32)}.investiga-word{direction:ltr;display:flex!important;align-items:baseline;justify-content:center;width:auto;height:42px;margin:4px auto 0;line-height:42px;font-family:Arial,Helvetica,sans-serif;font-size:36px;font-weight:800;letter-spacing:-1px;color:#f5f7fa;white-space:nowrap}.investiga-word .blue-a{display:inline-block;color:#14bced;font-size:36px;font-weight:900;line-height:42px;margin-left:1px;transform:scaleX(.92);transform-origin:left center}.version-row{display:flex;justify-content:center;margin-top:0}.version-row .tag{margin:0;font-size:12px;padding:4px 9px}.sim-title{font-size:13px;color:#9fb0bf;line-height:1.2;margin-top:1px}.wordmark-approved,.wordmark-final,.wordmark,.wordmark-img,.wordmark-text,.brand-word,.brand-a,.wordmark-main,.logo-a,.app-meta{display:none!important}.page-brand{display:none!important}.wrap{padding-top:10px!important}#home .hero{text-align:center;padding:18px 0 12px!important;max-width:760px;margin:0 auto}#home .hero>.tag{display:table;margin:0 auto 17px}#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.2}#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.6}#orgStep>h2{text-align:center;margin:28px auto 21px}@media(max-width:760px){.app-header{padding:14px 10px 16px!important}.app-header-logo{width:72px;height:72px}.investiga-word{font-size:35px;height:41px;line-height:41px}.investiga-word .blue-a{font-size:35px;line-height:41px}.sim-title{font-size:12.5px}.wrap{padding-top:8px!important}#home .hero{padding:17px 8px 11px!important}#home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}#home .hero h1{font-size:clamp(33px,8.7vw,44px)}#home .hero p{font-size:clamp(18px,4.8vw,22px);line-height:1.6}#orgStep>h2{font-size:clamp(25px,6.8vw,33px);margin-top:25px}}
'''
for marker in ['.app-header{','.brand-word{']:
 i=s.find(marker)
 if i!=-1:
  j=s.find('</style>',i)
  if j!=-1:s=s[:i]+s[j:]
  break
s=s.replace('</style>',css+'</style>',1)
logo=app or '/investiga-mark.webp'
header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo}" alt="INVESTIGA icon"><div class="investiga-word" aria-label="INVESTIGA"><span>INVESTIG</span><span class="blue-a">A</span></div><div class="version-row"><span id="version" class="tag">...</span></div><div class="sim-title">AI Investigation Simulator</div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',header,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8');print('Rendered INVESTIGA wordmark directly in HTML/CSS to eliminate missing-image failure')
