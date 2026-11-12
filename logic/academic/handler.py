import re
from pathlib import Path
from routing.courses import CURRICULUM, canonical
from .csv_parser import parse_csv_rules
HANDBOOK = parse_csv_rules(str(Path(__file__).with_name('HandbookRules.csv'))) or {}
from routing.handlers.common import prepare

def handle(d, i, context, services=None):
    ctx, slots, courses, continuing, result, ask = prepare(d, i, context)
    if d.intent in ('prerequisites', 'eligibility'):
        # Follow-up eligibility answers may legitimately contain several course codes.
        collecting = continuing and ctx.get('pending_question') in ('passed_courses', 'taken_courses', 'term')
        if not collecting:
            if len(courses) > 1:
                return ask('course', 'Please choose one course: ' + ', '.join(courses))
            if courses:
                slots['course'] = courses[0]
            if not slots.get('course'):
                return ask('course', 'Which course do you mean? Please provide its code.')
        code = slots['course']
        if not CURRICULUM.course_exists(code):
            return ask('course', 'That course is unavailable in the curriculum. Please check its code.')
        if d.intent == 'prerequisites':
            return result(f'Prerequisites for {code}:\nMust have passed: ' + (', '.join(CURRICULUM.get_hard_prerequisites(code)) or 'None') + '\nMust have previously taken: ' + (', '.join(CURRICULUM.get_soft_prerequisites(code)) or 'None') + '\nMust enroll together: ' + (', '.join(CURRICULUM.get_corequisites(code)) or 'None'))
        pending = ctx.get('pending_question')
        if pending in ('passed_courses', 'taken_courses'):
            unknown = [c for c in re.findall(r'\b(?:CB|CC|LBY|MTH|STT|THS)[A-Z0-9-]+\b', i.original_text.upper()) if not CURRICULUM.course_exists(canonical(c))]
            if unknown or (not courses and not re.search(r"\b(none|no|not|didn't)\b", i.original_text, re.I)):
                return ask(pending, 'Please list valid course codes, or say none. Unknown: ' + ', '.join(unknown))
            if i.negation and courses:
                return ask(pending, 'I have not added those courses. List only courses you ' + ('passed' if pending == 'passed_courses' else 'previously took') + ', or say none.')
            slots[pending] = courses
        if 'passed_courses' not in slots:
            return ask('passed_courses', 'Which courses have you passed? List course codes, or say none.')
        if 'taken_courses' not in slots:
            return ask('taken_courses', 'Which other courses have you previously taken, including failed courses? List codes, or say none.')
        if pending == 'term':
            match = re.fullmatch(r'(?:term\s*)?([1-3])[.! ]*', re.sub(r'^(?:actually|correction|instead|i meant)[,: ]*', '', i.original_text.strip(), flags=re.I), re.I)
            if match:
                slots['term'] = int(match[1])
        if 'term' not in slots:
            return ask('term', 'Which enrollment term: Term 1, Term 2, or Term 3?')
        answer = CURRICULUM.check_eligibility(code, slots['passed_courses'], list(set(slots['passed_courses'] + slots['taken_courses'])), slots['term'])
        text = answer['message']
        if answer.get('corequisites'):
            text += '\nAlso enroll in: ' + ', '.join(answer['corequisites'])
        return result(text)
    if d.intent == 'handbook':
        rule = HANDBOOK.get(d.entities['rule_id'])
        return result(('According to the handbook: ' + rule['Rule Text']) if rule else 'That handbook section is unavailable.', 'answered' if rule else 'unsupported')
    if d.intent == 'offerings':
        match = re.search(r'\bterm\s*([1-3])\b', i.original_text, re.I) or (re.fullmatch(r'([1-3])[.! ]*', i.original_text.strip()) if continuing else None)
        if not match:
            return ask('offered_term', 'Which term: Term 1, Term 2, or Term 3?')
        return result('Normally offered: ' + ', '.join(k for k,v in CURRICULUM.curriculum.items() if v['offered_term'] == int(match[1])))
    if d.intent == 'gpa':
        return result('GPA calculation and personalized recovery calculations are not available yet. GPA is a units-weighted average of grade points; I can help you look up handbook grading policies.', 'unsupported')
    if d.intent == 'consultation_policy':
        return result('I do not have a verified consultation cancellation policy. Please check with your advisor. No booking has been changed.', 'unsupported')
    return result('Flowchart generation and updates are not available yet.', 'unsupported')
