"""Resource-independent normalization that preserves numbers and negation."""
import re
from .context import PipelineContext, ensure_session_state
from .logic.data.course_aliases import COURSE_ALIAS_MAP

_ALIASES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(a) for a in
                                sorted(COURSE_ALIAS_MAP, key=lambda a: (-len(a), a)))
    + r")(?!\w)", re.I,
)


def preprocess(raw_input: str, session: dict | None = None) -> PipelineContext:
    ctx = PipelineContext(raw_text=raw_input, session_state=ensure_session_state(session))
    text = re.sub(r"\s+", " ", raw_input.replace("’", "'").lower()).strip()
    ctx.normalized_text = _ALIASES.sub(lambda m: COURSE_ALIAS_MAP[m[0].lower()], text)
    return ctx
