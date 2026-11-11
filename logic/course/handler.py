from routing.courses import CURRICULUM, COURSE_INDEX, survey_key
from .response_generator import generate_response
from routing.handlers.common import prepare

def handle(d, i, context, services=None):
    ctx, slots, courses, continuing, result, ask = prepare(d, i, context)
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
    key = survey_key(code)
    return result(generate_response(d.intent, key, COURSE_INDEX) if key else CURRICULUM.describe_course(code))
