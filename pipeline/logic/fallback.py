"""Deterministic greetings and legacy NLTK regex fallback responses."""
import json
from pathlib import Path
from nltk.chat.util import Chat, reflections
from pipeline.context import PipelineContext

FALLBACK_RESPONSE = (
    "I can help with course difficulty, workload, prerequisites, eligibility, "
    "handbook policies, and consultation drafts. Could you rephrase your request?"
)
_PAIRS = json.loads((Path(__file__).parent / "data" / "fallback_regex_pairs.json").read_text(encoding="utf-8"))


class _DeterministicChat(Chat):
    def respond(self, text):
        # NLTK's wildcard/reflection behavior with a stable first response.
        for pattern, responses in self._pairs:
            match = pattern.match(text)
            if match:
                return self._wildcards(responses[0], match)
        return None


_CHAT = _DeterministicChat(_PAIRS, reflections)
_RESPONSES = {
    "greeting": "Hello! I'm Archi, your academic guide. Ask me about course difficulty, prerequisites, eligibility, handbook policies, or booking a consultation.",
    "thanks": "You're welcome! Let me know what else you need help with.",
}


def resolve_fallback(ctx: PipelineContext) -> str:
    return _RESPONSES.get(ctx.intent) or _CHAT.respond(ctx.raw_text) or FALLBACK_RESPONSE


handle_fallback = resolve_fallback
