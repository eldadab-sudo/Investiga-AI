import json
import os
import random
from http.server import ThreadingHTTPServer

import server
from scenario_playbooks import PLAYBOOKS, LEVEL_DNA


def fallback_case(org, level, profile):
    pb = PLAYBOOKS.get(org, {})
    theme = random.choice(pb.get('themes') or profile.get('domains') or ['בירור עובדתי'])
    title = random.choice(pb.get('titles') or ['מה לא מסתדר בתמונה?'])
    dna = pb.get('investigative_dna', 'בירור עובדות, ציר זמן, גרסאות, ראיות וחלופות.')
    level_dna = LEVEL_DNA.get(level, LEVEL_DNA['בינוני'])
    return {
        'title': title, 'level': level, 'org': org,
        'person': 'אדם מרכזי הקשור לאירוע',
        'status': 'מעמד ייקבע בהתאם לסוג האירוע ולהתפתחות העובדות',
        'procedure': profile['kind'],
        'brief': f'התקבל אירוע בתחום: {theme}. חומר הפתיחה כולל דיווח ראשוני, מועד ומקום כלליים וקשר של האדם המרכזי לאירוע, אך אינו חושף את הפתרון. על החוקר לברר את העובדות, לבנות ציר זמן, לזהות מעורבים, להבין אילו ראיות קיימות ולסווג את האירוע בהתאם למה שייחשף.',
        'legal': 'יש לפעול לפי סמכות הגוף והדין הפומבי, לזהות את מעמד האדם ולבחון אם הוא משתנה במהלך התיק.',
        'truth': f'מאחורי התיק קיימת אמת עובדתית קבועה שאינה מוצגת לחוקר. DNA מקצועי: {dna} רמת הקושי: {level_dna}',
        'facts': f'המערכת מחזיקה עובדות נסתרות על ציר הזמן, המעורבים, הראיות, הסתירות והחלופות. הן נחשפות בהדרגה לפי איכות שאלות החוקר. {level_dna}'
    }


def resilient_generate_case(org, level='בינוני'):
    profile = server.ORG_PROFILES.get(org)
    if not profile:
        return None
    pb = PLAYBOOKS.get(org, {})
    themes = pb.get('themes') or profile.get('domains') or []
    theme = random.choice(themes) if themes else 'אירוע בתחום סמכות הגוף'
    title_examples = ', '.join(pb.get('titles') or [])
    level_dna = LEVEL_DNA.get(level, LEVEL_DNA['בינוני'])
    professional_dna = pb.get('investigative_dna', '')
    shape = {'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt = f'''אתה כותב תיק אימון איכותי לחוקר מקצועי ב-{org}.

תחום התיק שנבחר: {theme}
ייעוד הגוף: {profile['mandate']}
בסיס משפטי ציבורי: {profile['legal_basis']}
DNA חקירתי של התחום: {professional_dna}
רמת קושי: {level}
הגדרת הקושי המחייבת: {level_dna}

כתוב תרחיש שמרגיש כמו תיק אמיתי ולא כמו שאלון. הוא צריך להכיל סיפור אנושי קונקרטי, מועד ומקום כלליים, אנשים בעלי אינטרסים שונים, חומר פתיחה סביר, אמת נסתרת, ציר זמן, ראיות קיימות, לפחות סתירה משמעותית אחת והסבר חלופי סביר. אל תגלה לחוקר את הפתרון בחומר הפתיחה. המידע צריך להיחשף בשיחה בהתאם לשאלות שהוא שואל.

החוקר צריך להידרש לחשיבה: להחליט מה חשוב, לזהות פערים, לבחון אמינות, להצליב גרסאות, לבדוק חלופות ולזהות בעצמו את הסיווג המשפטי/המקצועי האפשרי. אל תכתוב בחומר הפתיחה רשימת שאלות שעליו לשאול.

הכותרת חייבת להיות קצרה, מסקרנת ובעלת מתח חקירתי, ולא תיאור טכני. סגנון כותרות אפשרי בלבד: {title_examples}. אל תעתיק בהכרח כותרת קיימת.

ב-truth קבע אמת מלאה וקבועה. ב-facts כלול 12–18 עובדות קונקרטיות קצרות: זמנים, קשרים, גרסאות, מסמכים/ראיות קיימות, סתירות ומה כל דמות יודעת. ככל שהרמה גבוהה יותר, התחכום צריך לנבוע מהמבנה והעמימות של התיק ולא רק מכמות העובדות.

כללי בטיחות: בתיקי ביטחון/צבא ניתן לתאר חוסר או גניבה של פריט מסוכן, חשד לטרור או אירוע אלים שכבר התרחש ברמה כללית בלבד. אין למסור פרטי אחסון, אבטחה, גישה, הפעלה, שימוש, בנייה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות חקירה מסווגות. אין תיאור גרפי.

החזר JSON בלבד במבנה {json.dumps(shape,ensure_ascii=False)}.'''
    raw = server.ai([{'role':'system','content':prompt}],900,True)
    if raw:
        try:
            case=json.loads(raw)
            required=['title','person','status','brief','legal','truth','facts']
            if all(isinstance(case.get(k),str) and case[k].strip() for k in required):
                case['org']=org; case['level']=level; case['procedure']=profile['kind']
                return case
        except Exception as exc:
            print('GEN CASE PLAYBOOK PARSE',repr(exc))
    return fallback_case(org,level,profile)

server.generate_case = resilient_generate_case

if __name__ == '__main__':
    os.chdir(server.ROOT)
    print('INVESTIGA V3 AUTHORITY PLAYBOOKS')
    ThreadingHTTPServer(('0.0.0.0', server.PORT), server.H).serve_forever()
