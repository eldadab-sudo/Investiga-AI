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
VERSION='V4.6'
server.CASES.clear()
RECENT=defaultdict(lambda: deque(maxlen=60))
FAMILY_CURSOR=defaultdict(int)
FAMILY_SEEN=defaultdict(lambda: defaultdict(int))

NATURAL_REPLACEMENTS={
 'לא-גרפי':'', 'לא גרפי':'', 'ברמה כללית בלבד':'', 'ברמה כללית':'',
 'ללא תיאור גרפי':'', 'ללא מידע מבצעי':'', 'ללא פרטים מבצעיים':'',
 'מבלי להיכנס לפרטים מבצעיים':'', 'מבלי לעסוק בשיטות':'',
}

def clean_text(s):
    s=s or ''
    for a,b in NATURAL_REPLACEMENTS.items():s=s.replace(a,b)
    s=re.sub(r'\s+([,.;:])',r'\1',s)
    s=re.sub(r'\s{2,}',' ',s)
    return s.strip(' ,;')

def words(s):
    return [x for x in re.split(r'\s+',clean_text(s)) if x and x not in ['—','-']]

def short_title(s):
    ws=words(s)
    if len(ws)<=3:return ' '.join(ws)
    # Prefer a compact meaningful three-word title. Never expose more than 3 words.
    return ' '.join(ws[:3])

def norm(s):
    s=re.sub(r'[^\w\u0590-\u05ff ]',' ',clean_text(s).lower())
    return ' '.join(s.split())

def case_too_similar(org,c):
    nt=norm(c.get('title',''));nb=set(norm(c.get('brief','')).split())
    for old in RECENT[org]:
        if nt and nt==norm(old.get('title','')):return True
        ob=set(norm(old.get('brief','')).split())
        if nb and ob and len(nb&ob)/max(1,min(len(nb),len(ob)))>.58:return True
    return False

def remember(org,c,family):
    RECENT[org].append({'title':c.get('title',''),'brief':c.get('brief',''),'level':c.get('level',''),'family':family})
    FAMILY_SEEN[org][family]+=1

def family_candidates(org):
    pool=SCENARIO_FAMILIES.get(org) or []
    # Prefer families never seen; afterwards use the least-used family, not a blind cycle.
    return sorted(pool,key=lambda f:(FAMILY_SEEN[org][f['key']],random.random()))

def recent_text(org):
    xs=list(RECENT[org])[-18:]
    return 'אין תיקים קודמים.' if not xs else '\n'.join(f"- {x['level']}: {x['title']} — {x['brief'][:160]}" for x in xs)

def fast_ai(messages,tokens=1050,json_mode=False,timeout=22):
    key=getattr(server,'KEY','');model=getattr(server,'MODEL','gpt-5.6-luna')
    if not key:return None
    try:
        payload={'model':model,'messages':messages,'max_completion_tokens':tokens}
        if json_mode:payload['response_format']={'type':'json_object'}
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(req,timeout=timeout).read())['choices'][0]['message']['content'].strip()
    except Exception as e:print('FAST AI',repr(e));return None

def untouched_family_fallback(org,level,profile):
    """Fallback only to a family never shown before. Never recycle an old plot."""
    for f in family_candidates(org):
        if FAMILY_SEEN[org][f['key']]==0:
            c={'title':short_title(f['title']),'level':level,'org':org,'person':f['person'],'status':f['status'],'procedure':profile['kind'],
               'brief':clean_text(f['brief']),
               'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי הרלוונטי, להגדיר את מעמד האדם ולבחון שינוי במעמד אם העובדות מצדיקות זאת.',
               'truth':'לתרחיש קיימת אמת עובדתית קבועה. אין להסיק אשמה רק מן הפער הראשוני, וכל פרט חדש חייב להתיישב עם עובדות התיק.',
               'facts':f"התיק כולל ציר זמן, גרסאות ומסמכים קונקרטיים. רמת {level}: {LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])}"}
            if not case_too_similar(org,c):return c,f['key']
    return None,None

def ai_case(org,level,profile,f,previous,attempt):
    training=ORG_TRAINING.get(org,{});pb=PLAYBOOKS.get(org,{})
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''צור תיק חקירה חדש לחלוטין עבור {org}. זהו ניסיון יצירה {attempt}.

אסור לחזור על אף עלילה, אדם, אירוע, מסמך מרכזי או כותרת שכבר הופיעו:
{previous}

משפחת השראה בלבד: {f['key']}
אל תעתיק את הדוגמה; בנה אירוע אחר בתוך אותה משפחה. שנה את סוג המקום, מערכת היחסים, האנשים, חלון הזמן, הראיות, הסתירה וההסבר החלופי.

ייעוד: {profile['mandate']}
בסיס משפטי פומבי: {profile['legal_basis']}
DNA: {pb.get('investigative_dna','')}
חומרים אופייניים: {', '.join(training.get('evidence') or [])}
רמה: {level} — {level_dna}

כללים מחייבים:
- הכותרת בעברית, מסקרנת, 1–3 מילים בלבד. לעולם לא יותר משלוש מילים.
- brief באורך 120–190 מילים ובניסוח מקצועי וטבעי של תיק חקירה.
- אין להשתמש בביטויי מטא או בטיחות בתוך הטקסט למשתמש, כגון "לא גרפי", "לא-גרפי", "ברמה כללית", "ללא מידע מבצעי", "אדם מרכזי", "בתחום הרשות".
- כלול אדם בשם ובתפקיד, מועד/חלון זמן, מקום מובן, אירוע מוגדר, 2–4 ראיות/מסמכים קיימים, גרסה ראשונית, פער חקירתי והנושא שיש לברר.
- truth קובע אמת מלאה וקבועה. facts כולל 12–18 עובדות קונקרטיות.
- רמות הקושי הן עלילות שונות, לא אותו תיק בתוספת מורכבות: בסיסי ממוקד; בינוני עם 3+ מקורות ושתי השערות; מתקדם עם 4+ מקורות, שלוש השערות, סתירה בהצלבה ו-Blind Spot.
- בתיקי ביטחון/צבא אל תכלול פרטי גישה, אבטחה, אחסון, שימוש באמצעי לחימה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות מסווגות. שמור את מגבלות הבטיחות מאחורי הקלעים בלבד ולא כניסוח בתרחיש.

החזר JSON בלבד: {json.dumps(shape,ensure_ascii=False)}'''
    raw=fast_ai([{'role':'system','content':prompt}],1050,True,22)
    if not raw:return None
    try:
        c=json.loads(raw);req=['title','person','status','brief','legal','truth','facts']
        if not all(isinstance(c.get(k),str) and c[k].strip() for k in req):return None
        if len(words(c.get('title','')))>3:return None
        banned=['אדם מרכזי','בתחום הרשות','אירוע קונקרטי','מקום הקשור לפעילות הרשות','לא גרפי','לא-גרפי','ברמה כללית','ללא מידע מבצעי','ללא פרטים מבצעיים']
        usertext=(c.get('title','')+' '+c.get('brief','')+' '+c.get('person',''))
        if any(x in usertext for x in banned):return None
        c['title']=short_title(c['title']);c['brief']=clean_text(c['brief']);c['org']=org;c['level']=level;c['procedure']=profile['kind']
        return None if case_too_similar(org,c) else c
    except Exception as e:
        print('PARSE',repr(e));return None

def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org)
    if not profile:return None
    previous=recent_text(org)
    candidates=family_candidates(org)
    # Try two different families with AI. A returned case must pass cross-level duplicate detection.
    for attempt,f in enumerate(candidates[:2],1):
        c=ai_case(org,level,profile,f,previous,attempt)
        if c:
            remember(org,c,f['key']);return c
    # If AI is unavailable, only use a never-seen family. If none remain, fail rather than repeat a case.
    c,key=untouched_family_fallback(org,level,profile)
    if c:
        remember(org,c,key);return c
    print('NO UNIQUE CASE AVAILABLE',org,level)
    return None

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
      if p=='/api/version':return self.out({'version':VERSION,'max_title_words':3,'cross_level_duplicate_guard':True,'repeat_fallback':False,'recent_memory':60})
      if p=='/api/training':return self.out([{'org':o,'investigative_dna':PLAYBOOKS.get(o,{}).get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA} for o,t in ORG_TRAINING.items()])
      return super().do_GET()

server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
 os.chdir(server.ROOT);print('INVESTIGA V4.6 NO-REPEAT ENGINE');ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
