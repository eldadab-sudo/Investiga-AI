import json
import os
import uuid
from http.server import ThreadingHTTPServer

import server


def fallback_case(org, level, profile):
    domains = profile.get('domains') or ['בירור עובדתי']
    domain = domains[uuid.uuid4().int % len(domains)]
    return {
        'title': 'הפער שדורש בירור',
        'level': level,
        'org': org,
        'person': 'דניאל רז, בעל תפקיד',
        'status': 'נחקר בתרחיש אימון',
        'procedure': profile['kind'],
        'brief': f'נמצא פער עובדתי בתחום {domain}. מטרתך לברר את רצף האירועים, מקור המידע, האחריות והפער בין הגרסאות, בהתאם לסמכות הגוף ובלא להניח מראש מסקנה.',
        'legal': 'התרחיש כפוף לייעוד הגוף ולבסיס המשפטי הציבורי הבא: ' + profile['legal_basis'],
        'truth': 'הפער נובע משילוב של טעות אנוש ומידע חלקי. הנחקר אינו מספר בתחילה את כל הפרטים משום שהוא חושש מהשלכות מקצועיות, אך אין להניח אשמה ללא בדיקה.',
        'facts': 'הנחקר יודע את ציר הזמן המרכזי, את זהות בעלי התפקידים הרלוונטיים ואת מקור הפער. הוא חושף פרטים בהדרגה כאשר נשאל שאלות ממוקדות. אין להמציא עובדות, סמכויות או ראיות שלא הוגדרו.'
    }


def resilient_generate_case(org, level='בינוני'):
    profile = server.ORG_PROFILES.get(org)
    if not profile:
        return None

    shape = {
        'title': '', 'level': level, 'org': org, 'person': '', 'status': '',
        'procedure': profile['kind'], 'brief': '', 'legal': '', 'truth': '', 'facts': ''
    }
    prompt = (
        f'צור תרחיש אימון חקירתי פיקטיבי אחד בעברית עבור {org}.\n'
        f'ייעוד הגוף: {profile["mandate"]}\n'
        f'בסיס משפטי ציבורי: {profile["legal_basis"]}\n'
        f'תחומי חקירה מותרים: {", ".join(profile.get("domains") or [])}\n'
        f'רמת קושי: {level}.\n'
        'התרחיש צריך להיות ריאליסטי, לא-גרפי ולהתמקד בבירור עובדות, גרסאות, ציר זמן, ראיות קיימות והוגנות. '
        'אין לכלול הוראות לביצוע עבירה, התחמקות, שיבוש, מידע מסווג או שיטות מבצעיות.\n'
        f'החזר JSON בלבד בדיוק במבנה {json.dumps(shape, ensure_ascii=False)}.'
    )

    for attempt in range(2):
        raw = server.ai([{'role': 'system', 'content': prompt}], 900, True)
        if raw:
            try:
                case = json.loads(raw)
                required = ['title', 'person', 'status', 'brief', 'legal', 'truth', 'facts']
                if all(isinstance(case.get(k), str) and case[k].strip() for k in required):
                    case['org'] = org
                    case['level'] = level
                    case['procedure'] = profile['kind']
                    return case
            except Exception as exc:
                print('GEN CASE PARSE', attempt, repr(exc))
        prompt += '\nהחזר אובייקט JSON תקין בלבד, ללא Markdown.'

    print('GEN CASE FALLBACK', org, level)
    return fallback_case(org, level, profile)


server.generate_case = resilient_generate_case

if __name__ == '__main__':
    os.chdir(server.ROOT)
    print('INVESTIGA V2.1')
    ThreadingHTTPServer(('0.0.0.0', server.PORT), server.H).serve_forever()
