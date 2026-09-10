import json
import os
import random
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server
from scenario_playbooks import PLAYBOOKS, LEVEL_DNA
from org_training import ORG_TRAINING

BASE_ACTOR = server.actor_prompt
BASE_SCORE = server.score
VERSION = 'V4.2'
FEATURES = [
    'פרופילי סמכות ובסיס משפטי לפי ארגון',
    'תרחישים דינמיים לפי ארגון ורמת קושי',
    'כותרות מסקרנות לפי עולם התוכן',
    'פער משמעותי בין בסיסי, בינוני ומתקדם',
    'שיחה הדרגתית ולא-חזרתית עם הנחקר',
    'אמת עובדתית קבועה ומאגר עובדות נסתר',
    'Blind Spot ובדיקת חלופות',
    'Legal & Procedural Compliance',
    'ציונים משתנים מבוססי ביצוע',
    'DNA חקירתי ומדדי הערכה ייחודיים לכל ארגון',
    'יצירת תרחיש מהירה עם מעבר אוטומטי לגיבוי'
]

# Remove legacy static scenarios that predate the current scenario standard.
# New cases are created dynamically and stored for the lifetime of the running instance.
server.CASES.clear()


def fast_ai(messages, tokens=850, json_mode=False, timeout=16):
    key=getattr(server,'KEY','')
    model=getattr(server,'MODEL','gpt-5.6-luna')
    if not key:
        return None
    try:
        payload={'model':model,'messages':messages,'max_completion_tokens':tokens}
        if json_mode:
            payload['response_format']={'type':'json_object'}
        req=urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=json.dumps(payload).encode(),
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
        )
        data=json.loads(urllib.request.urlopen(req,timeout=timeout).read())
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('FAST AI ERROR',repr(e))
        return None


def fallback_case(org, level, profile):
    pb=PLAYBOOKS.get(org,{})
    training=ORG_TRAINING.get(org,{})
    theme=random.choice(pb.get('themes') or profile.get('domains') or ['בירור עובדתי'])
    title=random.choice(pb.get('titles') or ['מה לא מסתדר בתמונה?'])
    dna=pb.get('investigative_dna','בירור עובדות, ציר זמן, גרסאות, ראיות וחלופות.')
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    evidence=', '.join((training.get('evidence') or [])[:4])
    return {
        'title':title,
        'level':level,
        'org':org,
        'person':'אדם מרכזי הקשור לאירוע',
        'status':'מעמד ייקבע בהתאם להתפתחות העובדות',
        'procedure':profile['kind'],
        'brief':f'התקבל דיווח קונקרטי בתחום {theme}. האירוע התרחש לאחרונה במקום הקשור לפעילות הרשות. קיים פער מהותי בין גרסת אדם מרכזי לבין מידע מתועד, והתמונה הראשונית מאפשרת יותר מהסבר אחד. חומרי הבדיקה האפשריים כוללים {evidence or "מסמכים, גרסאות ורישומי זמן"}. על החוקר להבין בעצמו מה התרחש, מי מעורב ומהו הסיווג המתאים, בלי לקבל את המסקנה מראש.',
        'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי, לזהות את מעמד האדם ולבחון אם המעמד משתנה לאורך התיק.',
        'truth':f'קיימת אמת עובדתית קבועה ומפורטת שאינה מוצגת לחוקר. DNA מקצועי: {dna} רמת הקושי מחייבת: {level_dna}',
        'facts':f'קיימים ציר זמן, כמה מקורות מידע, ראיות או מסמכים, סתירות והסברים חלופיים שנחשפים רק בתגובה לשאלות רלוונטיות. {level_dna}'
    }


def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org)
    if not profile:
        return None
    pb=PLAYBOOKS.get(org,{})
    training=ORG_TRAINING.get(org,{})
    theme=random.choice(pb.get('themes') or profile.get('domains') or ['אירוע בתחום הסמכות'])
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''כתוב תיק אימון חקירתי עמוק וריאליסטי עבור {org}.
תחום התיק: {theme}
ייעוד הגוף: {profile['mandate']}
בסיס משפטי ציבורי: {profile['legal_basis']}
DNA מקצועי: {pb.get('investigative_dna','')}
רמת קושי: {level} — {level_dna}
ראיות אופייניות אפשריות: {', '.join(training.get('evidence') or [])}
כותרות השראה: {', '.join(pb.get('titles') or [])}

התרחיש חייב להרגיש כמו תיק אמיתי ולא כמו תיאור גנרי: אדם מסוים, אירוע מסוים, מועד ומקום כלליים, אינטרסים שונים, אמת נסתרת קבועה, ציר זמן, חומר פתיחה חלקי, ראיות קיימות, סתירות והסברים חלופיים. הכותרת קצרה, מסקרנת ובעלת מתח חקירתי. אל תגלה את הפתרון ב-brief ואל תיתן לחוקר רשימת שאלות.

פער הקושי חייב להיות מהותי:
בסיסי — פער מרכזי אחד, עד שתי גרסאות, חלופה אחת, והתקדמות טובה באמצעות שאלות נכונות.
בינוני — כמה מקורות, לפחות שתי סתירות ושתי השערות סבירות, ומידע ראשוני חלקי שעלול להטעות.
מתקדם — תיק רב-שכבתי, לפחות שלוש השערות, ראיה בעלת משמעות כפולה, סתירה שמתגלית רק בהצלבה, אפשרות לשינוי במעמד ו-Blind Spot משמעותי.

ב-truth קבע אמת מלאה ועקבית. ב-facts כתוב 12–18 עובדות קונקרטיות הכוללות זמנים, אנשים, מסמכים/ראיות, מה כל אדם יודע ומה סותר מה. המידע ייחשף בשיחה בהדרגה בלבד.

בתיקי ביטחון/צבא ניתן לתאר חוסר או גניבה של פריט מסוכן או חשד ביטחוני ברמה כללית בלבד. אין למסור פרטי אחסון, אבטחה, גישה, שימוש, בנייה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות חקירה מסווגות. אין תיאור גרפי.

החזר JSON בלבד במבנה {json.dumps(shape,ensure_ascii=False)}.'''
    raw=fast_ai([{'role':'system','content':prompt}],850,True,16)
    if raw:
        try:
            c=json.loads(raw)
            required=['title','person','status','brief','legal','truth','facts']
            if all(isinstance(c.get(k),str) and c[k].strip() for k in required):
                c['org']=org
                c['level']=level
                c['procedure']=profile['kind']
                return c
        except Exception as e:
            print('GEN V4.2 PARSE',repr(e))
    print('GEN V4.2 FAST FALLBACK',org,level)
    return fallback_case(org,level,profile)


def organization_actor_prompt(c):
    base=BASE_ACTOR(c)
    t=ORG_TRAINING.get(c.get('org'),{})
    return base+f'''\n\nהתנהגות ייחודית לארגון: {t.get('interview','התנהג באופן טבעי ועקבי.')}
כלל התפתחות: אל תמסור את כל הידוע לך בתשובה אחת. חשוף עובדות רק כשהשאלה נוגעת בהן. שאלה כללית מקבלת תשובה כללית. שאלה מדויקת יכולה לחשוף פרט מדויק יותר. אם החוקר מזהה סתירה אמיתית מתוך החומר שכבר נחשף, התמודד איתה באופן אנושי ועקבי עם האמת הקבועה. אל תחזור על מידע שכבר נמסר בלי צורך, אל תמציא ראיה חדשה כדי לעזור לחוקר ואל תאשר הנחה שגויה.'''


def organization_score(c,h):
    report=BASE_SCORE(c,h)
    t=ORG_TRAINING.get(c.get('org'),{})
    if not t:
        return report
    report['organization_assessment']={
        'organization':c.get('org'),
        'focus':t.get('evaluate') or [],
        'summary':'ההערכה הארגונית בוחנת האם החוקר פעל לפי אופי התיק של הרשות: מיפה את המידע, בדק פערים, הצליב מקורות, בחן חלופות ולא הסתפק בגרסה הראשונה.'
    }
    return report


class H(server.H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/version':
            return self.out({'version':VERSION,'features':FEATURES,'legacy_cases_removed':True,'generation_timeout_seconds':16})
        if p=='/api/training':
            rows=[]
            for org,t in ORG_TRAINING.items():
                pb=PLAYBOOKS.get(org,{})
                rows.append({
                    'org':org,
                    'investigative_dna':pb.get('investigative_dna',''),
                    'focus':t.get('evaluate',[]),
                    'evidence':t.get('evidence',[]),
                    'level_dna':LEVEL_DNA
                })
            return self.out(rows)
        return super().do_GET()


server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
    os.chdir(server.ROOT)
    print('INVESTIGA V4.2 CONSOLIDATED ENGINE')
    print('FEATURES ACTIVE:',len(FEATURES),'LEGACY CASES:',len(server.CASES),'GEN TIMEOUT: 16s')
    ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
