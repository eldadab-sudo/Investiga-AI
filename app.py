import json
import os
import random
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server
from scenario_playbooks import PLAYBOOKS, LEVEL_DNA
from org_training import ORG_TRAINING

BASE_ACTOR = server.actor_prompt
BASE_SCORE = server.score
VERSION = 'V4.1'


def fallback_case(org, level, profile):
    pb=PLAYBOOKS.get(org,{})
    theme=random.choice(pb.get('themes') or profile.get('domains') or ['בירור עובדתי'])
    title=random.choice(pb.get('titles') or ['מה לא מסתדר בתמונה?'])
    dna=pb.get('investigative_dna','בירור עובדות, ציר זמן, גרסאות, ראיות וחלופות.')
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    return {'title':title,'level':level,'org':org,'person':'אדם מרכזי הקשור לאירוע','status':'מעמד ייקבע בהתאם להתפתחות העובדות','procedure':profile['kind'],'brief':f'התקבל אירוע קונקרטי בתחום {theme}. ידועים מועד ומקום כלליים וקשרו של האדם המרכזי לאירוע, אך התמונה אינה שלמה. על החוקר לברר את העובדות ולבנות בעצמו את הסיווג והכיוונים.','legal':'יש לפעול לפי סמכות הגוף והדין הפומבי ולזהות את מעמד האדם לאורך התיק.','truth':f'קיימת אמת קבועה שאינה מוצגת לחוקר. {dna} {level_dna}','facts':f'קיימים ציר זמן, מספר מעורבים, מסמכים או ראיות, סתירות וחלופות שנחשפים לפי איכות השאלות. {level_dna}'}


def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org)
    if not profile:return None
    pb=PLAYBOOKS.get(org,{})
    training=ORG_TRAINING.get(org,{})
    theme=random.choice(pb.get('themes') or profile.get('domains') or ['אירוע בתחום הסמכות'])
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''כתוב תיק אימון חקירתי עמוק וריאליסטי עבור {org}.
תחום: {theme}
DNA מקצועי: {pb.get('investigative_dna','')}
רמת קושי: {level} — {level_dna}
ראיות אופייניות אפשריות: {', '.join(training.get('evidence') or [])}
כותרות השראה: {', '.join(pb.get('titles') or [])}

התרחיש חייב להרגיש כמו תיק אמיתי: אירוע קונקרטי, אנשים בעלי אינטרסים, אמת נסתרת קבועה, ציר זמן, חומר פתיחה חלקי, ראיות קיימות, סתירות והסברים חלופיים. הכותרת קצרה ומסקרנת. אל תגלה את הפתרון ב-brief ואל תיתן לחוקר רשימת שאלות. החוקר צריך לגלות בעצמו מה חשוב, לסווג את האירוע, לבדוק אמינות ולהצליב מידע.

ברמת בסיסי: נדרש חוקר מתחיל טוב — פער מרכזי, חלופה אחת וסתירה שניתן לגלות בשאלות נכונות. בינוני: נדרש ניסיון — כמה מקורות, לפחות שתי סתירות ושתי השערות סבירות. מתקדם: נדרש חוקר מנוסה — תיק רב-שכבתי, לפחות שלוש השערות, ראיה בעלת משמעות כפולה, סתירה שמתגלה רק בהצלבה ו-Blind Spot משמעותי.

ב-truth כתוב את האמת המלאה. ב-facts כתוב 12–18 עובדות קונקרטיות עם זמנים, אנשים, מסמכים, מה כל אדם יודע ומה סותר מה. אין מידע מסווג, פרטים גרפיים, הוראות לביצוע עבירה, שימוש באמצעי לחימה, גישה/אבטחה, התחמקות או שיבוש.
החזר JSON בלבד במבנה {json.dumps(shape,ensure_ascii=False)}.'''
    raw=server.ai([{'role':'system','content':prompt}],950,True)
    if raw:
        try:
            c=json.loads(raw)
            if all(isinstance(c.get(k),str) and c[k].strip() for k in ['title','person','status','brief','legal','truth','facts']):
                c['org']=org;c['level']=level;c['procedure']=profile['kind'];return c
        except Exception as e:print('GEN V4',repr(e))
    return fallback_case(org,level,profile)


def organization_actor_prompt(c):
    base=BASE_ACTOR(c)
    t=ORG_TRAINING.get(c.get('org'),{})
    return base+f'''\n\nהתנהגות ייחודית לארגון: {t.get('interview','התנהג באופן טבעי ועקבי.')}
כלל התפתחות: אל תמסור את כל הידוע לך בתשובה אחת. חשוף עובדות רק כשהשאלה נוגעת בהן. אם החוקר שואל שאלה כללית, השב באופן כללי. אם הוא מזהה פער מדויק, תן פרט מדויק יותר. אם הוא מציג סתירה אמיתית מתוך המידע שכבר נחשף, התמודד איתה באופן אנושי ועקבי עם האמת הקבועה. אל תמציא ראיה חדשה כדי לעזור לחוקר.'''


def organization_score(c,h):
    report=BASE_SCORE(c,h)
    t=ORG_TRAINING.get(c.get('org'),{})
    if not t:return report
    report['organization_assessment']={
        'organization':c.get('org'),
        'focus':t.get('evaluate') or [],
        'summary':'ההערכה הארגונית בוחנת האם החוקר פעל לפי אופי התיק של הרשות: מיפה את המידע, בדק פערים וחלופות ולא הסתפק בגרסה הראשונה.'
    }
    return report


class H(server.H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/version':
            return self.out({'version':VERSION})
        if p=='/api/training':
            rows=[]
            for org,t in ORG_TRAINING.items():
                pb=PLAYBOOKS.get(org,{})
                rows.append({'org':org,'investigative_dna':pb.get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA})
            return self.out(rows)
        return super().do_GET()

server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
    os.chdir(server.ROOT)
    print('INVESTIGA V4.1 ORG-SPECIFIC TRAINING ENGINE')
    ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
