import json
import os
import random
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server
from scenario_playbooks import PLAYBOOKS, LEVEL_DNA
from org_training import ORG_TRAINING
from case_blueprints import CASE_BLUEPRINTS

BASE_ACTOR=server.actor_prompt
BASE_SCORE=server.score
VERSION='V4.3'

# All legacy generic cases are removed. Every displayed case is generated from a concrete authority blueprint.
server.CASES.clear()


def fast_ai(messages,tokens=950,json_mode=False,timeout=16):
    key=getattr(server,'KEY',''); model=getattr(server,'MODEL','gpt-5.6-luna')
    if not key:return None
    try:
        payload={'model':model,'messages':messages,'max_completion_tokens':tokens}
        if json_mode:payload['response_format']={'type':'json_object'}
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(req,timeout=timeout).read())['choices'][0]['message']['content'].strip()
    except Exception as e:print('FAST AI',repr(e));return None


def blueprint(org):
    pool=CASE_BLUEPRINTS.get(org) or []
    return random.choice(pool) if pool else None


def concrete_fallback(org,level,profile,bp):
    if not bp:return None
    level_note=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    return {
      'title':bp['title'],'level':level,'org':org,'person':bp['person'],'status':bp['status'],'procedure':profile['kind'],
      'brief':bp['brief'],
      'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי הרלוונטי, לזהות במפורש את מעמד האדם ולבחון שינוי במעמד אם העובדות מצדיקות זאת.',
      'truth':'לתרחיש קיימת אמת עובדתית קבועה שאינה מוצגת לחוקר. הדמות מחזיקה רק במידע שמתאים לתפקידה ולא תשנה גרסה ללא סיבה עובדתית.',
      'facts':f'חומר התיק בנוי סביב האנשים, המסמכים והפערים הקונקרטיים המפורטים בתיאור. רמת {level}: {level_note}'
    }


def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org); bp=blueprint(org)
    if not profile or not bp:return None
    pb=PLAYBOOKS.get(org,{}); training=ORG_TRAINING.get(org,{})
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''צור וריאציה חדשה ומלאה של תיק אימון חקירתי עבור {org}, על בסיס זרע התיק הבא.

זרע קונקרטי:
כותרת: {bp['title']}
אדם: {bp['person']}
מעמד: {bp['status']}
אירוע: {bp['brief']}

ייעוד הרשות: {profile['mandate']}
בסיס משפטי ציבורי: {profile['legal_basis']}
DNA חקירתי: {pb.get('investigative_dna','')}
חומרי חקירה אופייניים: {', '.join(training.get('evidence') or [])}
רמה: {level} — {level_dna}

כלל מוחלט: אסור להשתמש בביטויים גנריים כגון "אדם מרכזי", "בתחום הרשות", "אירוע קונקרטי", "מקום הקשור לפעילות הרשות", "חומרי הבדיקה האפשריים" או ניסוחים דומים. כל שם עצם משמעותי חייב להיות קונקרטי: מי האדם, מה תפקידו, מה קרה, היכן באופן כללי, מתי, איזה מסמך/ראיה קיימים ומה בדיוק הפער הראשוני.

ה-brief צריך להיות 110–180 מילים בעברית, כתוב כמו פתיח לתיק אמיתי. הוא חייב לכלול: שם ותפקיד של לפחות אדם אחד; מועד או חלון זמן; מקום כללי; מעשה/חשד מוגדר; 2–4 פריטי מידע או ראיות שכבר קיימים; לפחות גרסה אחת; פער חקירתי ברור; ומה על החוקר לברר. אין לגלות את הפתרון.

ב-truth קבע אמת מלאה, ספציפית ועקבית: מה באמת קרה, מי עשה מה, למה, ומה כל דמות מנסה להסתיר או אינה יודעת. ב-facts כתוב 12–18 עובדות קונקרטיות לשימוש הנחקר: זמנים, שמות, קשרים, מסמכים, גרסאות, סתירות ומה ייחשף בשאלה מתאימה.

הבדל הקושי הוא גם בסיפור עצמו: בסיסי — אירוע ממוקד ושתי גרסאות לכל היותר; בינוני — כמה מעורבים ושתי השערות סבירות; מתקדם — כמה שכבות, שלוש השערות, סתירות שרואים רק בהצלבה, ראיה דו-משמעית ו-Blind Spot. אל תוסיף רשימת שאלות לחוקר.

בתיקי ביטחון/צבא שמור הכול ברמה כללית ולא-מבצעית: אין פרטי אבטחה, גישה, אחסון, שימוש באמצעי לחימה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות מסווגות. אין תיאור גרפי.
החזר JSON בלבד: {json.dumps(shape,ensure_ascii=False)}'''
    raw=fast_ai([{'role':'system','content':prompt}],950,True,16)
    if raw:
      try:
        c=json.loads(raw)
        banned=['אדם מרכזי','בתחום הרשות','אירוע קונקרטי','מקום הקשור לפעילות הרשות','חומרי הבדיקה האפשריים']
        required=['title','person','status','brief','legal','truth','facts']
        if all(isinstance(c.get(k),str) and c[k].strip() for k in required) and not any(x in c.get('brief','') or x in c.get('person','') for x in banned):
          c['org']=org;c['level']=level;c['procedure']=profile['kind'];return c
      except Exception as e:print('PARSE',repr(e))
    return concrete_fallback(org,level,profile,bp)


def organization_actor_prompt(c):
    t=ORG_TRAINING.get(c.get('org'),{})
    return BASE_ACTOR(c)+f'''\n\nהתנהגות ייחודית: {t.get('interview','התנהג באופן טבעי ועקבי.')}
אל תמסור הכול בבת אחת. שאלה כללית מקבלת תשובה כללית; שאלה מדויקת יכולה לחשוף פרט מדויק. אל תחזור על מידע ללא צורך. אם החוקר מזהה סתירה אמיתית, התמודד איתה לפי האמת הקבועה. אל תמציא ראיה, אדם, מסמך או אירוע שלא הוגדרו בתיק.'''


def organization_score(c,h):
    r=BASE_SCORE(c,h);t=ORG_TRAINING.get(c.get('org'),{})
    if t:r['organization_assessment']={'organization':c.get('org'),'focus':t.get('evaluate',[]),'summary':'האם החוקר מיפה את העובדות הקונקרטיות, זיהה פערים, הצליב מקורות, בדק חלופות ופעל בהתאם לאופי החקירה של הרשות.'}
    return r


class H(server.H):
    def do_GET(self):
      p=urlparse(self.path).path
      if p=='/api/version':return self.out({'version':VERSION,'generic_cases':False,'blueprint_orgs':len(CASE_BLUEPRINTS),'generation_timeout_seconds':16})
      if p=='/api/training':
        return self.out([{'org':o,'investigative_dna':PLAYBOOKS.get(o,{}).get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA} for o,t in ORG_TRAINING.items()])
      return super().do_GET()

server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
 os.chdir(server.ROOT);print('INVESTIGA V4.3 CONCRETE CASE ENGINE');ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
