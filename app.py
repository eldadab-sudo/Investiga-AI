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
VERSION='V4.7'
server.CASES.clear()
RECENT=defaultdict(lambda: deque(maxlen=60))
FAMILY_SEEN=defaultdict(lambda: defaultdict(int))

NATURAL_REPLACEMENTS={'לא-גרפי':'','לא גרפי':'','ברמה כללית בלבד':'','ברמה כללית':'','ללא תיאור גרפי':'','ללא מידע מבצעי':'','ללא פרטים מבצעיים':'','מבלי להיכנס לפרטים מבצעיים':'','מבלי לעסוק בשיטות':''}
BAD_TITLE_ENDINGS={'אותו','אותה','אותם','אחד','אחת','של','עם','בלי','לאותו','לאותה','באותו','באותה','שלא','שהיה','שהייתה','אשר','את','על','אל','מן','מול','בין'}
BAD_TITLE_PHRASES=['שלוש גרסאות לאותו','שתי גרסאות לאותו','האירוע בתחום','אדם מרכזי','תרחיש חדש','תיק חקירה']

def clean_text(s):
    s=s or ''
    for a,b in NATURAL_REPLACEMENTS.items():s=s.replace(a,b)
    s=re.sub(r'\s+([,.;:])',r'\1',s);s=re.sub(r'\s{2,}',' ',s)
    return s.strip(' ,;')

def words(s):return [x for x in re.split(r'\s+',clean_text(s)) if x and x not in ['—','-']]
def norm(s):return ' '.join(re.sub(r'[^\w\u0590-\u05ff ]',' ',clean_text(s).lower()).split())

def valid_title(s):
    ws=words(s);n=norm(s)
    if not 1<=len(ws)<=3:return False
    if ws[-1] in BAD_TITLE_ENDINGS:return False
    if any(p in n for p in BAD_TITLE_PHRASES):return False
    if len(''.join(ws))<5:return False
    return True

def fallback_title(f):
    # Hand-curated compact titles are preferable to mechanically cutting a sentence after word 3.
    key=f.get('key','');mapping={
      'card_fraud':'עסקאות באישון לילה','business_burglary':'הקופה הריקה','employee_theft':'חוסר במשמרת','online_fraud':'המוכר שנעלם','forgery':'החתימה המזויפת','violence_versions':'גרסאות סותרות','public_order':'אחרי ההתקהלות',
      'missing_weapon':'הנשק החסר','missing_ammo':'פער בספירה','property_theft':'בין שתי משמרות','procurement_fraud':'הזמנה חריגה','service_forgery':'המסמך ששונה','soldier_violence':'גרסאות מהפלוגה','vehicle_incident':'הדקות החסרות','unauthorized_property':'ציוד ללא רישום',
      'terror_affiliation':'הקשר הסמוי','terror_assistance':'החוליה החסרה','terror_event':'אחרי האירוע','foreign_contact':'הקשר הזר','link_gap':'השם שחזר','harm_intent':'הכוונה הנסתרת',
      'conflicting_reports':'דוחות סותרים','source_reliability':'מקור בספק','human_vs_system':'מול נתוני המערכת','reporting_chain':'שרשרת הדיווח','partial_assessment':'התמונה החסרה',
      'false_invoices':'החשבונית הכפולה','undeclared_income':'ההכנסה הנסתרת','vat_mismatch':'הפער בספרים','smuggling':'המשלוח החשוד','related_company':'החברה המקושרת','unusual_expenses':'ההוצאה החריגה',
      'false_eligibility':'הזכאות שבמחלוקת','residence_mismatch':'הכתובת השנייה','undeclared_work':'העבודה שלא דווחה','suspect_documents':'המסמך החריג','employer_reporting':'הדיווח החסר','status_transition':'הגרסה ששינתה מעמד',
      'bid_coordination':'המכרז המתואם','price_coordination':'מחיר זהה','competitor_links':'הקשר בין מתחרים','similar_docs':'אותו ניסוח','market_allocation':'חלוקת השוק',
      'inside_info':'לפני ההודעה','late_report':'הדיווח המאוחר','unusual_trading':'העסקה המוקדמת','misleading_investors':'המצג המטעה','officer_activity':'פעולת הבכיר',
      'billing_after_cancel':'החיוב שנמשך','misleading_ad':'ההבטחה בפרסום','consumer_exploitation':'העסקה הלוחצת','complaint_pattern':'אותה תלונה','promise_vs_contract':'הבטחה מול חוזה',
      'agri_docs':'המשלוח בלי מסמך','food_smuggling':'מקור הסחורה','unregulated_sale':'המכירה האסורה','tree_cutting':'הכריתה החשודה','shipment_origin':'מאין הגיע המשלוח',
      'work_accident':'אחרי התאונה','training_gap':'ההדרכה החסרה','ignored_defect':'הליקוי שנשכח','contractor_responsibility':'מי היה אחראי','late_signature':'החתימה המאוחרת',
      'waste_dumping':'הפסולת בלילה','sewage_discharge':'הזרימה לנחל','air_pollution':'החריגה במדידה','hazardous_waste':'המסמך החסר','order_violation':'הצו שהופר',
      'illegal_hunting':'העקבות בשטח','wildlife_trade':'הכלוב החשוד','nature_damage':'הפגיעה בשמורה','reserve_activity':'מחוץ לשביל','heritage_damage':'הסימנים באתר',
      'data_access':'מי פתח','external_disclosure':'הקובץ שיצא','purpose_misuse':'שימוש אחר','permissions_failure':'הרשאה חריגה','incident_report':'הדיווח שלא תאם'}
    t=mapping.get(key,'')
    if valid_title(t):return t
    original=clean_text(f.get('title',''))
    return original if valid_title(original) else 'התיק החדש'

def case_too_similar(org,c):
    nt=norm(c.get('title',''));nb=set(norm(c.get('brief','')).split())
    for old in RECENT[org]:
        if nt and nt==norm(old.get('title','')):return True
        ob=set(norm(old.get('brief','')).split())
        if nb and ob and len(nb&ob)/max(1,min(len(nb),len(ob)))>.58:return True
    return False

def remember(org,c,family):
    RECENT[org].append({'title':c.get('title',''),'brief':c.get('brief',''),'level':c.get('level',''),'family':family});FAMILY_SEEN[org][family]+=1

def family_candidates(org):return sorted(SCENARIO_FAMILIES.get(org) or [],key=lambda f:(FAMILY_SEEN[org][f['key']],random.random()))
def recent_text(org):
    xs=list(RECENT[org])[-18:];return 'אין תיקים קודמים.' if not xs else '\n'.join(f"- {x['level']}: {x['title']} — {x['brief'][:160]}" for x in xs)

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
    for f in family_candidates(org):
        if FAMILY_SEEN[org][f['key']]==0:
            c={'title':fallback_title(f),'level':level,'org':org,'person':f['person'],'status':f['status'],'procedure':profile['kind'],'brief':clean_text(f['brief']),'legal':'יש לפעול לפי סמכות הגוף והדין הפומבי הרלוונטי, להגדיר את מעמד האדם ולבחון שינוי במעמד אם העובדות מצדיקות זאת.','truth':'לתרחיש קיימת אמת עובדתית קבועה. אין להסיק אשמה רק מן הפער הראשוני, וכל פרט חדש חייב להתיישב עם עובדות התיק.','facts':f"התיק כולל ציר זמן, גרסאות ומסמכים קונקרטיים. רמת {level}: {LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])}"}
            if not case_too_similar(org,c):return c,f['key']
    return None,None

def ai_case(org,level,profile,f,previous,attempt):
    training=ORG_TRAINING.get(org,{});pb=PLAYBOOKS.get(org,{});level_dna=LEVEL_DNA.get(level,LEVEL_DNA['בינוני'])
    shape={'title':'','level':level,'org':org,'person':'','status':'','procedure':profile['kind'],'brief':'','legal':'','truth':'','facts':''}
    prompt=f'''צור תיק חקירה חדש לחלוטין עבור {org}. אסור לחזור על עלילה או כותרת שכבר הופיעו:\n{previous}\nמשפחת השראה: {f['key']}. בנה אירוע אחר בתוך המשפחה.\nייעוד: {profile['mandate']}\nDNA: {pb.get('investigative_dna','')}\nחומרים: {', '.join(training.get('evidence') or [])}\nרמה: {level} — {level_dna}\n
כותרת: 1–3 מילים בלבד, קצרה, טבעית ומסקרנת. היא חייבת להיות צירוף עברי שלם שעומד בפני עצמו. אסור לחתוך משפט כדי לעמוד במגבלת המילים. דוגמאות לסגנון: "הקופה הריקה", "החתימה המזויפת", "הנשק החסר", "הדיווח המאוחר", "הכתובת השנייה". אל תשתמש בתבנית "שלוש גרסאות לאותו..." או בכותרת שנגמרת במילת יחס/מילה תלויה כגון "אותו", "של", "עם".
brief 120–190 מילים, מקצועי וטבעי, עם שם ותפקיד, זמן, מקום, אירוע מוגדר, 2–4 ראיות/מסמכים, גרסה ראשונית ופער חקירתי. אין ביטויי מטא כגון "לא גרפי", "ברמה כללית", "ללא מידע מבצעי", "אדם מרכזי" או "בתחום הרשות". truth קבוע; facts 12–18 עובדות. הרמות הן עלילות שונות ולא אותה עלילה עם תוספת מורכבות. מגבלות בטיחות נשארות מאחורי הקלעים; בתיקי ביטחון/צבא אין פרטי גישה, אבטחה, אחסון, שימוש באמצעי לחימה, יעד, אמצעי, מסלול, התחמקות, שיבוש או שיטות מסווגות.
החזר JSON בלבד: {json.dumps(shape,ensure_ascii=False)}'''
    raw=fast_ai([{'role':'system','content':prompt}],1050,True,22)
    if not raw:return None
    try:
        c=json.loads(raw);req=['title','person','status','brief','legal','truth','facts']
        if not all(isinstance(c.get(k),str) and c[k].strip() for k in req):return None
        if not valid_title(c['title']):return None
        banned=['אדם מרכזי','בתחום הרשות','אירוע קונקרטי','מקום הקשור לפעילות הרשות','לא גרפי','לא-גרפי','ברמה כללית','ללא מידע מבצעי','ללא פרטים מבצעיים']
        if any(x in c['title']+' '+c['brief']+' '+c['person'] for x in banned):return None
        c['brief']=clean_text(c['brief']);c['org']=org;c['level']=level;c['procedure']=profile['kind']
        return None if case_too_similar(org,c) else c
    except Exception as e:print('PARSE',repr(e));return None

def resilient_generate_case(org,level='בינוני'):
    profile=server.ORG_PROFILES.get(org)
    if not profile:return None
    previous=recent_text(org);candidates=family_candidates(org)
    for attempt,f in enumerate(candidates[:2],1):
        c=ai_case(org,level,profile,f,previous,attempt)
        if c:remember(org,c,f['key']);return c
    c,key=untouched_family_fallback(org,level,profile)
    if c:remember(org,c,key);return c
    return None

def organization_actor_prompt(c):
    t=ORG_TRAINING.get(c.get('org'),{});return BASE_ACTOR(c)+f'''\n\nהתנהגות ייחודית: {t.get('interview','התנהג באופן טבעי ועקבי.')}\nאל תמסור הכול בבת אחת. שאלה כללית מקבלת תשובה כללית; שאלה מדויקת יכולה לחשוף פרט מדויק. אל תחזור על מידע ללא צורך. אל תמציא ראיה, אדם, מסמך או אירוע שלא הוגדרו בתיק.'''

def organization_score(c,h):
    r=BASE_SCORE(c,h);t=ORG_TRAINING.get(c.get('org'),{})
    if t:r['organization_assessment']={'organization':c.get('org'),'focus':t.get('evaluate',[]),'summary':'האם החוקר מיפה את העובדות, זיהה פערים, הצליב מקורות, בדק חלופות ופעל בהתאם לאופי החקירה של הרשות.'}
    return r

class H(server.H):
    def do_GET(self):
      p=urlparse(self.path).path
      if p=='/api/version':return self.out({'version':VERSION,'max_title_words':3,'semantic_title_validation':True,'cross_level_duplicate_guard':True,'repeat_fallback':False,'recent_memory':60})
      if p=='/api/training':return self.out([{'org':o,'investigative_dna':PLAYBOOKS.get(o,{}).get('investigative_dna',''),'focus':t.get('evaluate',[]),'evidence':t.get('evidence',[]),'level_dna':LEVEL_DNA} for o,t in ORG_TRAINING.items()])
      return super().do_GET()

server.generate_case=resilient_generate_case;server.actor_prompt=organization_actor_prompt;server.score=organization_score
if __name__=='__main__':
 os.chdir(server.ROOT);print('INVESTIGA V4.7 SEMANTIC TITLE ENGINE');ThreadingHTTPServer(('0.0.0.0',server.PORT),H).serve_forever()
