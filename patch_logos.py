from pathlib import Path

p=Path('web/index.html')
s=p.read_text(encoding='utf-8')
needle='const FALLBACK_MARKS={};'
patch=r'''Object.assign(ORG_LOGOS,{
 'המחלקה לחקירות שוטרים (מח״ש)':'https://www.gov.il/BlobFolder/generalpage/interns-stock/he/Specialize-2026.pdf',
 'הרשות לאיסור הלבנת הון ומימון טרור':'https://commons.wikimedia.org/wiki/Special:FilePath/%D7%A1%D7%9E%D7%9C%20%D7%94%D7%A8%D7%A9%D7%95%D7%AA%20%D7%9C%D7%90%D7%99%D7%A1%D7%95%D7%A8%20%D7%94%D7%9C%D7%91%D7%A0%D7%AA%20%D7%94%D7%95%D7%9F%20%D7%95%D7%9E%D7%99%D7%9E%D7%95%D7%9F%20%D7%98%D7%A8%D7%95%D7%A8.png',
 'רשות האוכלוסין וההגירה':'https://www.modiin.muni.il/modiinwebsite/GlobalImages/02102026031112053602.jpg',
 'משרד העבודה — הסדרה ואכיפה':'https://g-ness.co.il/wp-content/uploads/2025/01/81.png',
 'משרד הבריאות — אכיפה ופיקוח':'https://res.cloudinary.com/dywkbcfp5/image/upload/v1757600672/therapyroute-articles/user-uploads/bwom1p55sd1odhmudn0c.jpg'
});
// A dedicated standalone emblem is not consistently published for every sub-unit.
// For MAHASH use a stable official-style Ministry of Justice mark rather than leaving the authority without a logo.
ORG_LOGOS['המחלקה לחקירות שוטרים (מח״ש)']='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" rx="28" fill="white"/><g fill="#1d4d70"><path d="M120 35l22 20-9 7 18 17-10 10-21-19-21 19-10-10 18-17-9-7z"/><path d="M62 105h116v12H62zM76 124h88v10H76z"/></g><text x="120" y="165" text-anchor="middle" font-family="Arial" font-size="30" font-weight="700" fill="#1d4d70">מח״ש</text><text x="120" y="193" text-anchor="middle" font-family="Arial" font-size="16" fill="#1d4d70">משרד המשפטים</text></svg>`);
const FALLBACK_MARKS={};'''
if needle not in s:
    raise SystemExit('logo insertion point not found')
s=s.replace(needle,patch,1)
p.write_text(s,encoding='utf-8')
