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
from case_blueprints import CASE_BLUEPRINTS

BASE_ACTOR=server.actor_prompt
BASE_SCORE=server.score
VERSION='V4.4'
server.CASES.clear()

# Keep memory of what the user has already seen during this server lifetime.
RECENT=defaultdict(lambda: deque(maxlen=20))
BP_CURSOR=defaultdict(int)
GEN_COUNTER=defaultdict(int)


def norm(s):
    s=re.sub(r'[^\w\u0590-\u05ff ]',' ',(s or '').lower())
    return ' '.join(s.split())


def signature(c):
    return norm((c or {}).get('title',''))+'|'+norm((c or {}).get('brief',''))[:180]


def title_seen(org,title):
    n=norm(title)
    return any(norm(x.get('title',''))==n for x in RECENT[org])


def case_too_similar(org,c):
    if not c:return True
    nt=norm(c.get('title',''))
    nb=set(norm(c.get('brief','')).split())
    for old in RECENT[org]:
        if nt and nt==norm(old.get('title','')):return True
        ob=set(norm(old.get('brief','')).split())
        if nb and ob:
            overlap=len(nb & ob)/max(1,min(len(nb),len(ob)))
            if overlap>0.72:return True
    return False


def remember(org,c):
    RECENT[org].append({'title':c.get('title',''),'brief':c.get('brief',''),'level':c.get('level','')})


def fast_ai(messages,tokens=1000,json_mode=False,timeout=22):
    key=getattr(server,'KEY','');model=getattr(server,'MODEL','gpt-5.6-luna')
    if not key:return None
    try:
        payload={'model':model,'messages':messages,'max_completion_tokens':tokens}
        if json_mode:payload['response_format']={'type':'json_object'}
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(req,timeout=timeout).read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('FAST AI',repr(e));return None


def next_blueprint(org):
    pool=CASE_BLUEPRINTS.get(org) or []
    if not pool:return None
    # Cycle instead of random-choice: never repeat the same seed until all seeds were used.
    start=BP_CURSOR[org] % len(pool)
    for off in range(len(pool)):
        idx=(start+off)%len(pool)
        bp=pool[idx]
        if not any(norm(x.get('title',''))==norm(bp.get('title','')) for x in list(RECENT[org])[-len(pool):]):
            BP_CURSOR[org]=idx+1
            return bp
    bp=pool[start]
    BP_CURSOR[org]=start+1
    return bp


def recent_text(org):
    xs=list(RECENT[org])[-8:]
    if not xs:return 'אין תיקים קודמים.'
    return '\n'.join(f"- {x['level']}: {x['title']} — {x['brief'][:150]}" for x in xs)


def local_variant(org,level,profile,bp):
    """Guaranteed non-identical fallback when the model is unavailable."""
    GEN_COUNTER[org]+=1
    n=GEN_COUNTER[org]
    base_title=bp['title']
    suffixes={
      'בסיסי':['הפער הראשון','הגרסה השנייה','הדקה החסרה','המסמך שלא תאם'],
      'בינוני':['שתי גרסאות, מסמך אחד','העדות ששינתה את התמונה','הזמן שלא הסתדר','הקשר שלא הופיע ברישום'],
      'מתקדם':['שלוש גרסאות לאותו ערב','המסמך ששינה משמעות','העד שידע יותר מדי','הסתירה שהתגלתה רק בהצלבה']
    }
    suffix=suffixes.get(level,suffixes['בינוני'])[(n-1)%4]
    title=f'{base_title} — {suffix}' if title_seen(org,base_title) else base_title
    additions={
      'בסיסי':'בתיק קיימת גרסה נגדית אחת ופרט מתועד אחד שאינו מתיישב איתה במלואו.',
      'בינוני':'בנוסף קיימת גרסה של אדם נוסף ומסמך שמחזק חלק מן הגרסה אך סותר פרט אחר, ולכן יש לפחות שתי השערות סבירות.',
      'מתקדם':'בנוסף קיימים שלושה מקורות שאינם מתיישבים זה עם זה, מסמך שניתן לפרש בשתי דרכים ופרט שמקבל משמעות אחרת רק לאחר הצלבת הזמנים; ייתכן שמעמדו של אחד המעורבים ישתנה.'
    }
    c={
      'title':title,'level':level,'org':org,'person':bp['person'],'status':bp['status'],'procedure':profile['kind'],
      'brief':bp['brief']+' '+additions.get(level,additions['בינוני']),
      'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי הרלוונטי, לזהות במפורש את מעמד האדם ולבחון שינוי במעמד אם העובדות מצדיקות זאת.',
      'truth':'לתיק קיימת אמת עובדתית קבועה. כל דמות יודעת רק את החלק המתאים לתפקידה; אחת הגרסאות חלקית, אך אין להסיק מכך לבדה מי אחראי.',
      'facts':f'התיק כולל ציר זמן, שמות, גרסאות ומסמכים קונקרטיים מתוך האירוע. רמת {level}: {LEVEL_DNA.get(level,LEVEL_DNA["בינוני"])}'
    }
    return c


def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org);bp=next_blueprint(org)
    if not profile or not bp:return None
    pb=PLAYBOOKS.get(org,{});training=ORG_TRAINING.get(org,{})
    level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    previous=recent_text(org)
    nonce=random.randint(100000,999999)
    prompt=f'''צור תיק חקירה חדש לחלוטין עבור {org}. מזהה גיוון פנימי: {nonce}.

התיקים הבאים כבר הוצגו למשתמש ואסור לחזור על העלילה, הכותרת, האדם המרכזי או המבנה שלהם:
{previous}

השתמש בזרע הבא רק כהשראה לסוג התיק, לא כטקסט להעתקה:
{bp['title']} | {bp['person']} | {bp['brief']}

ייעוד: {profile['mandate']}
בסיס משפטי ציבורי: {profile['legal_basis']}
DNA חקירתי: {pb.get('investigative_dna','')}
חומרים אופייניים: {', '.join(training.get('evidence') or [])}
רמה: {level} — {level_dna}

דרישות מוחלטות:
1. זה חייב להיות אירוע שונה מכל התיקים הקודמים המופיעים למעלה, לא רק ניסוח שונה.
2. המצא שם אחר, מקום כללי אחר, מועד אחר, מערכת יחסים אחרת ופרט חקירתי מרכזי אחר.
3. כותרת חדשה שלא הופיעה קודם.
4. brief של 120–190 מילים: מה קרה, למי, מתי, היכן באופן כללי, מי המעורבים, 2–4 ראיות/מסמכים קיימים, גרסה ראשונית, הסתירה או הפער ומה צריך לברר. אין לגלות פתרון.
5. truth: אמת מלאה וספציפית. facts: 12–18 עובדות קונקרטיות לשיחה.
6. אסור לכתוב "אדם מרכזי", "בתחום הרשות", "אירוע קונקרטי", "מקום הקשור לפעילות הרשות" או נוסח גנרי דומה.
7. רמת בסיסי, בינוני ומתקדם חייבות להיות תיקים שונים במבנה ובמורכבות, ולא אותו סיפור עם תווית אחרת.

בסיסי: אירוע ממוקד, עד שתי גרסאות, פער מרכזי אחד וחלופה אחת.
בינוני: 3+ מקורות/מעורבים, שתי סתירות ושתי השערות סבירות.
מתקדם: 4+ מקורות/מעורבים, שלוש השערות, ראיה דו-משמעית, סתירה שמתגלית רק בהצלבה ו-Blind Spot ממשי.

בתיקי ביטחון/צבא שמור הכול ברמה כללית ולא-מבצעית: בלי פרטי אבטחה, גישה, אחסון, שימוש באמצעי לחימה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות מסווגות. אין תיאור גרפי.
החזר JSON בלבד: {json.dumps(shape,ensure_ascii=False)}'''
    raw=fast_ai([{'role':'system','content':prompt}],1000,True,22)
    c=None
    if raw:
      try:
        cand=json.loads(raw)
        banned=['אדם מרכזי','בתחום הרשות','אירוע קונקרטי','מקום הקשור לפעילות הרשות','חומרי הבדיקה האפשריים']
        req=['title','person','status','brief','legal','truth','facts']
        if all(isinstance(cand.get(k),str) and cand[k].strip() for k in req) and not any(x in (cand.get('brief','')+' '+cand.get('person','')) for x in banned):
          cand['org']=org;cand['level']=level;cand['procedure']=profile['kind']
          if not case_too_similar(org,cand):c=cand
      except Exception as e:print('PARSE',repr(e))
    if c is None:c=local_variant(org,level,profile,bp)
    remember(org,c)
    return c


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
      if p=='/api/version':return self.out({'version':VERSION,'duplicate_guard':True,'recent_memory':20,'blueprint_cycle':True,'generation_timeout_seconds':22})
      if p=='/api/training':
        return self.out([{'org':o,'investigative_dna':PLAYBOOKS.get(o,{}).get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA} for o,t in ORG_TRAINING.items()])
      return super().do_GET()

server.generate_case=resilient_generate_case
server.actor_prompt=organization_actor_prompt
server.score=organization_score

if __name__=='__main__':
 os.chdir(server.ROOT);print('INVESTIGA V4.4 UNIQUE CASE ENGINE');ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
