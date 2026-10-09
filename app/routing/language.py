"""Language detection and policy resolution for voice room personas.

Enforces:
- Natural conversational Hinglish by default for Indian audiences
- Instant and natural English response when user speaks or requests English
- Persistent language preference handling ('Ab se English mein bolo')
- Code-switching support preserving English technical terms inside Hinglish
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

LanguageMode = Literal["en", "hi"]

# Regex for explicit user English requests / switches
_EXPLICIT_ENGLISH_PATTERNS = re.compile(
    r"(?i)\b("
    r"in\s+english|"
    r"answer\s+(in\s+)?english|"
    r"explain\s+(in\s+)?english|"
    r"speak\s+(in\s+)?english|"
    r"completely\s+in\s+english|"
    r"purely\s+in\s+english|"
    r"english\s+mein|"
    r"english\s+me|"
    r"english\s+please|"
    r"ab\s+se\s+english"
    r")\b"
)

# Regex for explicit user Hindi/Hinglish requests / switches
_EXPLICIT_HINDI_PATTERNS = re.compile(
    r"(?i)\b("
    r"in\s+hindi|"
    r"answer\s+(in\s+)?hindi|"
    r"explain\s+(in\s+)?hindi|"
    r"speak\s+(in\s+)?hindi|"
    r"hindi\s+mein|"
    r"hindi\s+me|"
    r"hindi\s+please|"
    r"ab\s+se\s+hindi"
    r")\b"
)

# Permanent switch indicators ('Ab se English...', 'From now on...')
_PERSISTENT_ENGLISH_SWITCH = re.compile(
    r"(?i)\b(ab\s+se\s+english|from\s+now\s+on\s+english|always\s+english|speak\s+only\s+english)\b"
)
_PERSISTENT_HINDI_SWITCH = re.compile(
    r"(?i)\b(ab\s+se\s+hindi|from\s+now\s+on\s+hindi|always\s+hindi|speak\s+only\s+hindi)\b"
)

# Common Roman Hindi / Hinglish functional keywords
_HINGLISH_KEYWORDS = {
    "kya",
    "kyu",
    "kyun",
    "hai",
    "hain",
    "ho",
    "hoon",
    "kaise",
    "kaisa",
    "kaisi",
    "karo",
    "karein",
    "karna",
    "karte",
    "karti",
    "samjhao",
    "samjhao na",
    "batao",
    "bataiye",
    "mein",
    "me",
    "aur",
    "bhai",
    "behen",
    "ye",
    "yeh",
    "woh",
    "mera",
    "meri",
    "mere",
    "tera",
    "teri",
    "tere",
    "apna",
    "apni",
    "apne",
    "nahi",
    "nhi",
    "na",
    "hota",
    "hoti",
    "hote",
    "theek",
    "thoda",
    "kuch",
    "chahiye",
    "chal",
    "raha",
    "rahi",
    "rahe",
    "mujhe",
    "tum",
    "tumhe",
    "aap",
    "aapko",
    "hum",
    "humko",
    "dono",
    "dekho",
    "dekhiye",
    "iska",
    "iski",
    "iske",
    "uska",
    "uski",
    "uske",
    "inka",
    "unka",
    "wahi",
    "bolo",
    "boliye",
    "suno",
    "sunao",
    "cheez",
    "baat",
    "kaam",
    "sirf",
    "bas",
    "lekin",
    "par",
    "toh",
    "to",
    "bhi",
    "accha",
    "achha",
}


@dataclass(frozen=True)
class LanguagePolicyResult:
    """Result of language policy evaluation."""

    mode: LanguageMode
    reason: str
    new_persistent_preference: LanguageMode | None = None

    @property
    def system_directive(self) -> str:
        """Instruction directive injected into persona prompts for this turn."""
        if self.mode == "en":
            return (
                "### LANGUAGE DIRECTIVE (MANDATORY):\n"
                "The user requested or spoke in English. You MUST reply 100% in natural, fluent English.\n"
                "Do NOT use Hindi or Hinglish words for this turn. Maintain your natural personality."
            )
        return (
            "### LANGUAGE DIRECTIVE (MANDATORY):\n"
            "The user spoke in Hindi or Hinglish. Reply in natural, conversational Hinglish.\n"
            "Keep technical and programming terms (e.g., API, database, React, state, deployment) in English."
        )


def resolve_language_mode(
    text: str | None,
    current_preference: LanguageMode | None = None,
) -> LanguagePolicyResult:
    """Determine the appropriate language response mode for an utterance.

    Args:
        text: Transcribed or typed input text.
        current_preference: Active persistent preference if previously established.

    Returns:
        LanguagePolicyResult: The target language mode ('en' or 'hi'), reason, and any updated preference.
    """
    if not text or not text.strip():
        # Fall back to current preference or Hinglish default
        mode = current_preference or "hi"
        return LanguagePolicyResult(
            mode=mode,
            reason="empty_input_default",
            new_persistent_preference=current_preference,
        )

    clean_text = text.strip()

    # 1. Check persistent language preference switches
    if _PERSISTENT_ENGLISH_SWITCH.search(clean_text):
        return LanguagePolicyResult(
            mode="en",
            reason="persistent_english_switch",
            new_persistent_preference="en",
        )

    if _PERSISTENT_HINDI_SWITCH.search(clean_text):
        return LanguagePolicyResult(
            mode="hi",
            reason="persistent_hindi_switch",
            new_persistent_preference="hi",
        )

    # 2. Check explicit turn-level language requests
    if _EXPLICIT_ENGLISH_PATTERNS.search(clean_text):
        return LanguagePolicyResult(
            mode="en",
            reason="explicit_english_request",
            new_persistent_preference=current_preference,
        )

    if _EXPLICIT_HINDI_PATTERNS.search(clean_text):
        return LanguagePolicyResult(
            mode="hi",
            reason="explicit_hindi_request",
            new_persistent_preference=current_preference,
        )

    # 3. If a persistent preference is active and user didn't switch, follow it
    if current_preference is not None:
        return LanguagePolicyResult(
            mode=current_preference,
            reason="persisted_user_preference",
            new_persistent_preference=current_preference,
        )

    # 4. Check for presence of Devanagari script
    if re.search(r"[\u0900-\u097F]", clean_text):
        return LanguagePolicyResult(
            mode="hi",
            reason="devanagari_script_detected",
            new_persistent_preference=None,
        )

    # 5. Word token analysis for Roman Hindi / Hinglish keywords
    tokens = [
        re.sub(r"[^\w]", "", word.lower())
        for word in clean_text.split()
        if re.sub(r"[^\w]", "", word.lower())
    ]

    hinglish_matches = [token for token in tokens if token in _HINGLISH_KEYWORDS]

    if hinglish_matches:
        return LanguagePolicyResult(
            mode="hi",
            reason=f"hinglish_tokens_detected:{','.join(hinglish_matches[:3])}",
            new_persistent_preference=None,
        )

    # 6. Default to English for utterances without Hindi/Hinglish vocabulary
    return LanguagePolicyResult(
        mode="en",
        reason="english_utterance_detected",
        new_persistent_preference=None,
    )
