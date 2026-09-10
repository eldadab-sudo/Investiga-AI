import json
import os
import random
import re
import urllib.request
from collections import defaultdict, deque
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server
from scenario_playbooks import PLAYBOOKS, LEVEL_DNA
from org_training import ORG_TRAINING
from scenario_factory import SCENARIO_FAMILIES

BASE_ACTOR=server.actor_prompt
BASE_SCORE=server.score
VERSION='V4.5'
server.CASES.clear()
RECENT=defaultdict(lambda: deque(maxlen=40))
FAMILY_CURSOR=defaultdict(int)


def norm(s):
    s=re.sub(r'[^\w\u0590-\u05ff ]',' ',(s or '').lower())
    return ' '.join(s.split())


def family_used(org,key):
    return any(x.get('family')==key for x in RECENT[org])


def next_family(org):
    pool=SCENARIO_FAMILIES.get(org) or []
    if not pool:return None
    start=FAMILY_CURSOR[org]%len(pool)
    for off in range(len(pool)):
        idx=(start+off)%len(pool); f=pool[idx]
        if not family_used(org,f['key']):
            FAMILY_CURSOR[org]=idx+1;return f
    # All families have been used: clear only family-cycle memory, while retaining textual history.
    for x in RECENT[org]:x['family']=None
    f=pool[start];FAMILY_CURSOR[org]=start+1;return f


def case_too_similar(org,c):
    nt=norm(c.get('title','')); nb=set(norm(c.get('brief','')).split())
    for old in RECENT[org]:
        if nt and nt==norm(old.get('title','')):return True
        ob=set(norm(old.get('brief','')).split())
        if nb and ob and len(nb&ob)/max(1,min(len(nb),len(ob)))>.68:return True
    return False


def remember(org,c,family):
    RECENT[org].append({'title':c.get('title',''),'brief':c.get('brief',''),'level':c.get('level',''),'family':family})


def fast_ai(messages,tokens=1050,json_mode=False,timeout=22):
    key=getattr(server,'KEY','');model=getattr(server,'MODEL','gpt-5.6-luna')
    if not key:return None
    try:
        payload={'model':model,'messages':messages,'max_completion_tokens':tokens}
        if json_mode:payload['response_format']={'type':'json_object'}
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(req,timeout=timeout).read())['choices'][0]['message']['content'].strip()
    except Exception as e:print('FAST AI',repr(e));return None


def recent_text(org):
    xs=list(RECENT[org])[-12:]
    return 'אין תיקים קודמים.' if not xs else '\n'.join(f"- {x['level']}: {x['title']} — {x['brief'][:130]}" for x in xs)


def fallback_case(org,level,profile,f):
    # Crucial change: fallback is a DIFFERENT PLOT FAMILY, never the same case with a title suffix.
    complexity={
      'בסיסי':'החומר הראשוני מציג פער מרכזי אחד ושתי אפשרויות סבירות לכל היותר. החוקר נדרש לסווג נכון את האירוע ולבחון את הגרסה מול החומר הקיים.',
      'בינוני':'לתיק מצטרפות שתי גרסאות נוספות ומסמך נוסף שאינו מתיישב עם פרט אחד בגרסה הראשונית. קיימות לפחות שתי השערות סבירות ויש צורך בהצלבת ציר הזמן.',
      'מתקדם':'לתיק ארבעה מקורות לפחות, שלוש השערות סבירות וראיה אחת שניתן לפרש בשתי דרכים. סתירה משמעותית מתגלה רק לאחר הצלבת זמנים, וקיים Blind Spot שעלול להוביל למסקנה מוקדמת.'
    }
    return {'title':f['title'],'level':level,'org':org,'person':f['person'],'status':f['status'],'procedure':profile['kind'],
      'brief':f['brief']+' '+complexity.get(level,complexity['בינוני']),
      'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי הרלוונטי, להגדיר את מעמד האדם ולבחון שינוי במעמד אם העובדות מצדיקות זאת.',
      'truth':'לתרחיש אמת עובדתית קבועה. הגרסאות אינן זהות, אך אין להסיק אשמה מעצם הסתירה; כל פרט חדש חייב להתיישב עם האירוע והחומר שהוגדרו.',
      'facts':f"העובדות הקבועות נגזרות מן האירוע המתואר ומחומריו. רמת {level}: {LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])}"}


def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org);f=next_family(org)
    if not profile or not f:return None
    training=ORG_TRAINING.get(org,{});pb=PLAYBOOKS.get(org,{})
    previous=recent_text(org);level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''צור תיק חקירה חדש עבור {org} ממשפחת אירוע שעדיין לא הוצגה בסבב הנוכחי.

משפחת האירוע שנבחרה: {f['key']}
נקודת מוצא קונקרטית: {f['title']} | {f['person']} | {f['brief']}

אסור להפוך את אחד התיקים שכבר הוצגו לאותו סיפור עם כותרת אחרת. תיקים קודמים:
{previous}

ייעוד: {profile['mandate']}
בסיס משפטי פומבי: {profile['legal_basis']}
DNA: {pb.get('investigative_dna','')}
חומרים אופייניים: {', '.join(training.get('evidence') or [])}
רמה: {level} — {level_dna}

כתוב סיפור קונקרטי ומלא. שנה באופן משמעותי שמות, זמן, מקום כללי, קשר בין האנשים, ראיות והפער החקירתי מניסוחים קודמים. brief 120–190 מילים. כלול 2–4 פריטי חומר שכבר קיימים, גרסה ראשונית, פער ומה נדרש לברר. truth חייב לקבע מה באמת קרה; facts יכלול 12–18 עובדות קבועות.

בסיסי = אירוע ממוקד, עד שתי גרסאות ופער מרכזי אחד. בינוני = לפחות 3 מקורות/מעורבים, שתי סתירות ושתי השערות. מתקדם = לפחות 4 מקורות/מעורבים, שלוש השערות, ראיה דו-משמעית, סתירה שרואים רק בהצלבה ו-Blind Spot.
אסור ניסוח גנרי כמו "אדם מרכזי" או "בתחום הרשות". בתיקי ביטחון/צבא אין פרטי אבטחה, גישה, אחסון, שימוש באמצעי לחימה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות מסווגות. אין תיאור גרפי.
החזר JSON בלבד: {json.dumps(shape,ensure_ascii=False)}'''
    raw=fast_ai([{'role':'system','content':prompt}],1050,True,22);c=None
    if raw:
      try:
        cand=json.loads(raw);req=['title','person','status','brief','legal','truth','facts'];banned=['אדם מרכזי','בתחום הרשות','אירוע קונקרטי','מקום הקשור לפעילות הרשות']
        if all(isinstance(cand.get(k),str) and cand[k].strip() for k in req) and not any(x in cand.get('brief','') for x in banned):
          cand['org']=org;cand['level']=level;cand['procedure']=profile['kind']
          if not case_too_similar(org,cand):c=cand
      except Exception as e:print('PARSE',repr(e))
    if c is None:c=fallback_case(org,level,profile,f)
    remember(org,c,f['key']);return c


def organization_actor_prompt(c):
    t=ORG_TRAINING.get(c.get('org'),{})
    return BASE_ACTOR(c)+f'''\n\nהתנהגות ייחודית: {t.get('interview','התנהג באופן טבעי ועקבי.')}\nאל תמסור הכול בבת אחת. שאלה כללית מקבלת תשובה כללית; שאלה מדויקת יכולה לחשוף פרט מדויק. אל תחזור על מידע ללא צורך. אל תמציא ראיה, אדם, מסמך או אירוע שלא הוגדרו בתיק.'''


def organization_score(c,h):
    r=BASE_SCORE(c,h);t=ORG_TRAINING.get(c.get('org'),{})
    if t:r['organization_assessment']={'organization':c.get('org'),'focus':t.get('evaluate',[]),'summary':'האם החוקר מיפה את העובדות, זיהה פערים, הצליב מקורות, בדק חלופות ופעל בהתאם לאופי החקירה של הרשות.'}
    return r

class H(server.H):
    def do_GET(self):
      p=urlparse(self.path).path
      if p=='/api/version':return self.out({'version':VERSION,'scenario_family_engine':True,'orgs_with_families':len(SCENARIO_FAMILIES),'recent_memory':40})
      if p=='/api/training':return self.out([{'org':o,'investigative_dna':PLAYBOOKS.get(o,{}).get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA} for o,t in ORG_TRAINING.items()])
      return super().do_GET()

server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
 os.chdir(server.ROOT);print('INVESTIGA V4.5 DISTINCT SCENARIO FAMILY ENGINE');ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
