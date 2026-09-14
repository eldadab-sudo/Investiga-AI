from pathlib import Path
p=Path('web/index.html')
s=p.read_text(encoding='utf-8')
# Override the Mahash logo mapping after the general authority-logo patch.
needle="const FALLBACK_MARKS={};"
patch="ORG_LOGOS['המחלקה לחקירות שוטרים (מח״ש)']='/mahash-logo.webp';\nconst FALLBACK_MARKS={};"
if needle in s and "/mahash-logo.webp" not in s:
    s=s.replace(needle,patch,1)
p.write_text(s,encoding='utf-8')
print('Mahash logo corrected')
