import json
from pathlib import Path


class CurriculumEngine:
    def __init__(self):
        data_path = Path(__file__).resolve().parents[3] / "data" / "curriculum_data.json"

        with open(data_path, "r", encoding="utf-8") as f:
            self.curriculum = json.load(f)

    ####################################################
    # Basic Course Retrieval
    ####################################################

    def get_course(self, course_code):
        return self.curriculum.get(course_code.upper())

    def course_exists(self, course_code):
        return course_code.upper() in self.curriculum

    ####################################################
    # Course Information
    ####################################################

    def get_course_name(self, course_code):
        course = self.get_course(course_code)

        if not course:
            return None

        return course["name"]

    def get_hard_prerequisites(self, course_code):
        course = self.get_course(course_code)

        if not course:
            return []

        return course.get("hard_prerequisites", [])

    def get_soft_prerequisites(self, course_code):
        course = self.get_course(course_code)

        if not course:
            return []

        return course.get("soft_prerequisites", [])

    def get_corequisites(self, course_code):
        course = self.get_course(course_code)

        if not course:
            return []

        return course.get("corequisites", [])

    def get_offered_term(self, course_code):
        course = self.get_course(course_code)

        if not course:
            return None

        return course.get("offered_term")

    ####################################################
    # Eligibility Checking
    ####################################################

    def check_eligibility(
        self,
        course_code,
        passed_courses,
        taken_courses,
        current_term
    ):

        course_code = course_code.upper()

        course = self.get_course(course_code)

        if not course:

            return {
                "eligible": False,
                "reason": "course_not_found",
                "message": "I couldn't find that course."
            }

        ####################################################
        # Offered this term?
        ####################################################

        offered = course["offered_term"]

        if current_term != offered:

            return {
                "eligible": False,
                "reason": "not_offered",
                "offered_term": offered,
                "message":
                    f"{course_code} is normally offered during Term {offered}. "
                    "You may apply for a Special Class, subject to department and university approval."
            }

        ####################################################
        # Hard prerequisites
        ####################################################

        missing_hard = []

        for prereq in course["hard_prerequisites"]:

            if prereq not in passed_courses:
                missing_hard.append(prereq)

        if missing_hard:

            return {
                "eligible": False,
                "reason": "missing_hard_prerequisites",
                "missing": missing_hard,
                "message":
                    "You still need to PASS:\n"
                    + ", ".join(missing_hard)
            }

        ####################################################
        # Soft prerequisites
        ####################################################

        missing_soft = []

        for prereq in course["soft_prerequisites"]:

            if prereq not in taken_courses:
                missing_soft.append(prereq)

        if missing_soft:

            return {
                "eligible": False,
                "reason": "missing_soft_prerequisites",
                "missing": missing_soft,
                "message":
                    "You must have previously TAKEN:\n"
                    + ", ".join(missing_soft)
            }

        ####################################################
        # Corequisites
        ####################################################

        return {
            "eligible": True,
            "reason": "eligible",
            "corequisites": course["corequisites"],
            "message":
                f"You are eligible to enroll in {course_code}."
        }

    ####################################################
    # Recommendation Engine
    ####################################################

    def recommend_courses(
        self,
        passed_courses,
        taken_courses,
        current_term
    ):

        recommendations = []

        for code in self.curriculum:

            if code in passed_courses:
                continue

            result = self.check_eligibility(
                code,
                passed_courses,
                taken_courses,
                current_term
            )

            if result["eligible"]:
                recommendations.append({
                    "code": code,
                    "name": self.curriculum[code]["name"]
                })

        return recommendations

    ####################################################
    # Display Helpers
    ####################################################

    def get_course_information(self, course_code):

        course = self.get_course(course_code)

        if not course:
            return None

        return {
            "name": course["name"],
            "year": course["year"],
            "term": course["term"],
            "offered_term": course["offered_term"],
            "units": course["units"],
            "hard_prerequisites": course["hard_prerequisites"],
            "soft_prerequisites": course["soft_prerequisites"],
            "corequisites": course["corequisites"]
        }

    def describe_course(self, code):
        code = code.upper()

        if code not in self.curriculum:
            return "I couldn't find that course."

        course = self.curriculum[code]

        message = []

        message.append(f"{code} - {course['name']}")
        message.append(f"Year {course['year']} Term {course['term']}")
        message.append(f"{course['units']} units")

        return "\n".join(message)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

def _load_json(name: str) -> dict:
    path = DATA_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_course_index() -> dict:
    """
    Returns {course_code: {..scores.., ..sentiment..}} -- one merged record
    per course so the response generator only needs a single lookup.
    """
    scores = _load_json("course_scores.json")
    sentiment = _load_json("course_sentiments.json")

    index = {}
    for code, score_info in scores.items():
        merged = dict(score_info)
        merged.update(sentiment.get(code, {}))
        index[code] = merged
    return index


# Built once at import time -- chatbot_engine.py imports COURSE_INDEX directly,
# so this never re-reads disk per message.
COURSE_INDEX = build_course_index()

# code -> full name lookup, used by the response templates
CODE_TO_NAME = {code: info["course_name"] for code, info in COURSE_INDEX.items()}

CURRICULUM = CurriculumEngine()
