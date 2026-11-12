"""Streamlit-independent facade over the per-chat NLP pipeline."""
from pipeline import NLPPipeline

_PIPELINE = NLPPipeline()


def get_response(user_input: str, session_state: dict | None = None,
                 *, message_id: str | None = None) -> str:
    return _PIPELINE.process_turn(user_input or "", session_state, message_id=message_id)
