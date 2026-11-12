"""End-to-end regression tests for the consolidated NLP pipeline and router."""
import unittest
from chatbot_engine import get_response
from pipeline import NLPPipeline, preprocess, interpret
from pipeline.logic.data.course_aliases import COURSE_ALIAS_MAP, suggest_courses


class TestNLPPipeline(unittest.TestCase):
    def test_alias_resolution_in_preprocess(self):
        for raw, expected in (
            ("prog1", "CC/CBPROG1"),
            ("dsalg", "CBDSALG"),
            ("cbemc 1", "CBEMC-1"),
        ):
            ctx = preprocess(raw)
            self.assertIn(expected, ctx.normalized_text)
        self.assertIn("prog1", COURSE_ALIAS_MAP)

    def test_course_survey_and_curriculum_fallback(self):
        reply = get_response("How hard is prog1?")
        self.assertIn("CC/CBPROG1", reply)
        self.assertIn("/5", reply)

        # Near-miss course code triggers fuzzy suggestion
        near_miss = get_response("How hard is cbprog?")
        self.assertIn("Did you mean:", near_miss)
        self.assertTrue(len(suggest_courses("cbprog")) > 0)

    def test_academic_retrieval_and_handbook_subrules(self):
        prereq = get_response("What are the prerequisites for CBDSALG?")
        self.assertIn("CBDSALG", prereq)
        self.assertIn("Must have passed", prereq)

        handbook = get_response("What is the grading system?")
        self.assertIn("According to the handbook", handbook)
        self.assertIn("<b>", handbook)

        gpa = get_response("How do I calculate my GPA?")
        self.assertTrue(len(gpa) > 0)
        self.assertNotIn("not available yet", gpa.lower())

    def test_multiturn_eligibility_collects_passed_and_taken(self):
        session = {}
        r1 = get_response("Am I eligible for CBOPESY?", session)
        self.assertEqual(session.get("active_workflow"), "Academic_Eligibility")
        self.assertIn("CBOPESY", r1)

        r2 = get_response("CBPROG1, CBPROG2", session)
        self.assertEqual(session.get("active_workflow"), "Academic_Eligibility")
        self.assertIn("previously taken", r2)
        self.assertEqual(session["pending_slot"], "taken_courses")
        term_prompt = get_response("none", session)
        self.assertIn("Term 1, Term 2, or Term 3", term_prompt)

        r3 = get_response("Term 2", session)
        self.assertIsNone(session.get("active_workflow"))
        self.assertTrue(len(r3) > 0)

    def test_multiturn_booking_workflow_lock_and_completion(self):
        captured = []
        pipeline = NLPPipeline(booking_service=lambda draft: captured.append(draft))
        session = {}

        r1 = pipeline.process_turn("Book a consultation with Mr. Morales tomorrow", session)
        self.assertEqual(session.get("active_workflow"), "Booking")
        self.assertIn("time", r1.lower())

        # Follow-up includes 'GPA' keyword but stays locked in Booking workflow
        r2 = pipeline.process_turn("2:00 PM online on Google Meet about my GPA", session)
        self.assertIsNone(session.get("active_workflow"))
        self.assertIsNotNone(session.get("completed_booking"))
        self.assertEqual(session["completed_booking"]["advisor"], "Mr. Morales")
        self.assertEqual(session["completed_booking"]["time"], "2:00 PM")
        self.assertEqual(session["completed_booking"]["modality"], "Online")
        self.assertEqual(session["completed_booking"]["place"], "Google Meet")
        self.assertEqual(len(captured), 1)
        self.assertIn("Mr. Morales", r2)

    def test_upstream_support_and_cancel_clear_active_workflow(self):
        session = {}
        get_response("Book a consultation with Mr. Morales tomorrow", session)
        self.assertEqual(session.get("active_workflow"), "Booking")

        cancel_reply = get_response("cancel", session)
        self.assertIsNone(session.get("active_workflow"))
        self.assertIn("cancelled", cancel_reply.lower())

        # Crisis flag preempts active workflow
        get_response("Am I eligible for CBOPESY?", session)
        self.assertEqual(session.get("active_workflow"), "Academic_Eligibility")
        crisis_reply = get_response("I want to hurt myself because of CBOPESY", session)
        self.assertIsNone(session.get("active_workflow"))
        self.assertIn("safety matters more", crisis_reply.lower())

    def test_side_question_preserves_eligibility_and_course_reference(self):
        session = {}
        get_response("Am I eligible for CBOPESY?", session)
        reply = get_response("Actually, what are its prerequisites?", session)
        self.assertIn("CBOPESY", reply)
        self.assertIn("Must have passed", reply)
        self.assertEqual(session["pending_slot"], "passed_courses")
        self.assertNotIn("passed_courses", session["slots"])

    def test_competing_intents_keep_the_selected_course(self):
        pipeline, session = NLPPipeline(), {}
        result = pipeline.process_result("How hard is CBOPESY and what is the workload of CBALGCM?", session)
        self.assertEqual(result.status, "needs_clarification")
        result = pipeline.process_result("2", session)
        self.assertIn("CBALGCM", result.reply)
        self.assertIn("workload", result.reply)
        self.assertEqual(result.diagnostics["rule_id"], "R04_SELECTED")
        self.assertFalse(session["clarification_options"])

    def test_missing_course_and_fuzzy_selection_retain_intent(self):
        session = {}
        get_response("How hard is cbprog?", session)
        self.assertEqual(session["pending_intent"], "difficulty")
        reply = get_response("prog1", session)
        self.assertIn("difficulty", reply)
        self.assertIn("CC/CBPROG1", reply)

    def test_booking_policy_and_negation_do_not_cancel(self):
        session = {}
        get_response("Book a consultation with Prof. Reyes tomorrow", session)
        for text in ("What is the cancellation policy for consultations?", "How do I cancel my booking?", "Don't cancel my consultation"):
            get_response(text, session)
            self.assertEqual(session["active_workflow"], "Booking")
            self.assertEqual(session["slots"]["advisor"], "Prof. Reyes")
            self.assertNotIn("cancelled_booking", session)

    def test_switch_and_resume_workflows(self):
        session = {}
        get_response("Am I eligible for CBOPESY?", session)
        get_response("Book a consultation with Prof. Reyes", session)
        self.assertEqual(session["active_workflow"], "Booking")
        get_response("resume", session)
        self.assertEqual(session["active_workflow"], "Academic_Eligibility")
        self.assertEqual(session["slots"]["target_course"], "CBOPESY")
        self.assertEqual(session["pending_slot"], "passed_courses")
        get_response("resume", session)
        self.assertEqual(session["slots"]["advisor"], "Prof. Reyes")
        get_response("cancel", session)
        self.assertFalse(session["suspended_workflows"])

    def test_taken_courses_satisfy_soft_prerequisites_without_being_passed(self):
        from pipeline.logic.data.courses import CURRICULUM
        session = {}
        get_response("Am I eligible for CBDSALG?", session)
        get_response("none", session)
        get_response("I failed CBPROG2 and CCDSTRU", session)
        self.assertEqual(session["slots"]["passed_courses"], [])
        self.assertEqual(set(session["slots"]["taken_courses"]), {"CBPROG2", "CCDSTRU"})
        reply = get_response(f"Term {CURRICULUM.get_offered_term('CBDSALG')}", session)
        self.assertNotIn("must have previously TAKEN", reply)
        self.assertIsNone(session["active_workflow"])

    def test_invalid_and_negated_course_lists_do_not_advance(self):
        session = {}
        get_response("Am I eligible for CBOPESY?", session)
        for text in ("I did not pass CBPROG1", "CBZZZZ999", "I failed CBPROG1"):
            get_response(text, session)
            self.assertEqual(session["pending_slot"], "passed_courses")
            self.assertNotIn("passed_courses", session["slots"])

    def test_replayed_message_does_not_create_a_second_draft(self):
        captured, session = [], {}
        pipeline = NLPPipeline(booking_service=captured.append)
        message = "Book a consultation with Prof. Reyes tomorrow at 9 AM online via Zoom"
        first = pipeline.process_result(message, session, message_id="booking-1")
        session.pop("completed_booking")  # UI has consumed the event.
        repeated = pipeline.process_result(message, session, message_id="booking-1")
        self.assertEqual(len(captured), 1)
        self.assertEqual(first.reply, repeated.reply)
        self.assertTrue(repeated.duplicate)
        self.assertIsNone(session.get("completed_booking"))
        with self.assertRaises(ValueError):
            pipeline.process_result("cancel", session, message_id="booking-1")

    def test_session_isolation_and_failed_handler_rollback(self):
        from copy import deepcopy
        pipeline, first, second = NLPPipeline(), {}, {}
        pipeline.process_turn("Am I eligible for CBOPESY?", first)
        pipeline.process_turn("hello", second)
        self.assertIsNone(second["active_workflow"])
        before = deepcopy(first["slots"])
        def broken(ctx):
            ctx.session_state["slots"].clear()
            raise RuntimeError("Simulated handler failure")
        pipeline.router.registry["Academic"] = broken
        with self.assertLogs("pipeline", level="ERROR"):
            result = pipeline.process_result("none", first)
        self.assertEqual(result.status, "error")
        self.assertEqual(first["slots"], before)


if __name__ == "__main__":
    unittest.main()
