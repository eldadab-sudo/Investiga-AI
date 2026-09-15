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

# IMPORTANT: never delete or splice the original stylesheet. Previous versions
# removed everything from .app-header to </style>, which also removed card/grid
# rules needed by the organization selector. Only append scoped overrides.
css='''
.app-header{position:sticky;top:0;z-index:60;background:#0b1620;border-bottom:1px solid #253747;padding:14px 12px 16px!important;display:flex!important;justify-content:center!important}
.app-brand-stack{width:100%;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px}
.app-header-logo{display:block;width:74px;height:74px;border-radius:18px;object-fit:cover;box-shadow:0 0 0 1px #31506a,0 8px 22px rgba(0,0,0,.32)}
.investiga-word{direction:ltr;display:flex!important;align-items:baseline;justify-content:center;width:auto;height:42px;margin:4px auto 0;line-height:42px;font-family:Arial,Helvetica,sans-serif;font-size:36px;font-weight:800;letter-spacing:-1px;color:#f5f7fa;white-space:nowrap}
.investiga-word .blue-a{position:relative;display:inline-block;width:.72em;height:1em;margin-left:1px;vertical-align:-.05em}
.investiga-word .blue-a:before,.investiga-word .blue-a:after{content:"";position:absolute;bottom:.03em;width:.18em;height:.98em;background:#14bced;border-radius:.025em;transform-origin:bottom center}
.investiga-word .blue-a:before{left:.16em;transform:skew(-16deg)}
.investiga-word .blue-a:after{right:.16em;transform:skew(16deg)}
.version-row{display:flex;justify-content:center;margin-top:0}.version-row .tag{margin:0;font-size:12px;padding:4px 9px}
.sim-title{font-size:13px;color:#9fb0bf;line-height:1.2;margin-top:1px}
.app-header .wordmark-approved,.app-header .wordmark-final,.app-header .wordmark,.app-header .wordmark-img,.app-header .wordmark-text,.app-header .brand-word,.app-header .brand-a,.app-header .wordmark-main,.app-header .logo-a,.app-header .app-meta{display:none!important}
.page-brand{display:none!important}.wrap{padding-top:10px!important}
#home .hero{text-align:center;padding:18px 0 12px!important;max-width:760px;margin:0 auto}
#home .hero>.tag{display:table;margin:0 auto 17px}#home .hero h1{max-width:650px;margin-left:auto;margin-right:auto;line-height:1.2}#home .hero p{max-width:610px;margin-left:auto;margin-right:auto;line-height:1.6}
#orgStep>h2{text-align:center;margin:28px auto 21px}
@media(max-width:760px){.app-header{padding:14px 10px 16px!important}.app-header-logo{width:72px;height:72px}.investiga-word{font-size:35px;height:41px;line-height:41px}.sim-title{font-size:12.5px}.wrap{padding-top:8px!important}#home .hero{padding:17px 8px 11px!important}#home .hero>.tag{font-size:12px;max-width:92vw;white-space:normal}#home .hero h1{font-size:clamp(33px,8.7vw,44px)}#home .hero p{font-size:clamp(18px,4.8vw,22px);line-height:1.6}#orgStep>h2{font-size:clamp(25px,6.8vw,33px);margin-top:25px}}
'''

# Append overrides immediately before </head>; do not alter existing CSS/JS.
style_block='<style id="investiga-ui-overrides">'+css+'</style>'
if '</head>' in s:
 s=s.replace('</head>',style_block+'</head>',1)
else:
 s=style_block+s

logo=app or '/investiga-mark.webp'
header=f'''<header class="app-header"><div class="app-brand-stack"><img class="app-header-logo" src="{logo}" alt="INVESTIGA icon"><div class="investiga-word" aria-label="INVESTIGA"><span>INVESTIG</span><span class="blue-a" aria-hidden="true"></span></div><div class="version-row"><span class="tag">V4.9</span></div><div class="sim-title">AI Investigation Simulator</div></div></header>'''
s=re.sub(r'<header(?: class="app-header")?>.*?</header>',header,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
print('Applied non-destructive header overrides; original organization/card CSS preserved')
