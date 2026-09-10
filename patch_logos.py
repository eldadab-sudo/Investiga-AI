from pathlib import Path

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')
needle='const FALLBACK_MARKS={};'
patch=r'''function makeAuthorityLogo(label,sub=''){
  const safe=(label||'').replace(/[<>&]/g,'');
  const safeSub=(sub||'').replace(/[<>&]/g,'');
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" rx="30" fill="white"/><circle cx="120" cy="82" r="42" fill="#eaf1f7" stroke="#1d4d70" stroke-width="6"/><path d="M120 48l12 22 25 4-18 17 4 25-23-12-23 12 4-25-18-17 25-4z" fill="#1d4d70"/><text x="120" y="158" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700" fill="#1d4d70">${safe}</text><text x="120" y="188" text-anchor="middle" font-family="Arial" font-size="14" fill="#52697a">${safeSub}</text></svg>`;
  return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
}
Object.assign(ORG_LOGOS,{
 'המחלקה לחקירות שוטרים (מח״ש)':makeAuthorityLogo('מח״ש','משרד המשפטים'),
 'הרשות לאיסור הלבנת הון ומימון טרור':makeAuthorityLogo('רשל״ה','מודיעין פיננסי'),
 'רשות האוכלוסין וההגירה':makeAuthorityLogo('אוכלוסין','והגירה'),
 'משרד העבודה — הסדרה ואכיפה':makeAuthorityLogo('משרד העבודה','הסדרה ואכיפה'),
 'משרד הבריאות — אכיפה ופיקוח':makeAuthorityLogo('משרד הבריאות','אכיפה ופיקוח')
});
const FALLBACK_MARKS={};'''
if needle not in s:
    raise SystemExit('logo insertion point not found')
s=s.replace(needle,patch,1)
# Replace the old plain-text fallback with a generated visual logo, so even if any external image fails the UI still has a logo.
old="function logoHtml(name,size=''){let src=ORG_LOGOS[name]||'';let cls='org-logo '+size;if(!src)return `<div class=\"logo-fallback ${size}\">${name.split(' ').slice(0,2).join('<br>')}</div>`;return `<img class=\"${cls}\" src=\"${src}\" alt=\"לוגו ${name}\" loading=\"lazy\" onerror=\"this.outerHTML='<div class=&quot;logo-fallback ${size}&quot;>${name.replace(/'/g,'')}</div>'\">`}"
new="function logoHtml(name,size=''){let src=ORG_LOGOS[name]||makeAuthorityLogo(name.split(' ').slice(0,2).join(' '),'');let cls='org-logo '+size;let fb=makeAuthorityLogo(name.split(' ').slice(0,2).join(' '),'');return `<img class=\"${cls}\" src=\"${src}\" alt=\"לוגו ${name}\" loading=\"lazy\" onerror=\"this.onerror=null;this.src='${fb}'\">`}"
if old in s:
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
