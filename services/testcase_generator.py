"""
Intelligent Test Case Generator Service.

Module 0: AI-Powered Test Case Generator
Generates comprehensive, well-structured test cases from extracted requirements
using NLP heuristics, requirement semantics analysis, and template-driven synthesis.

Features:
 - Multi-variant coverage per requirement (Positive, Negative, Boundary, Edge, Security)
 - Intent & entity extraction from requirement text
 - Context-aware step and expected-result synthesis
 - Priority & module auto-inference
 - Deduplication & quality scoring
 - Deterministic + extensible for LLM plug-in
"""

import re
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from models.requirement import Requirement
from models.testcase import TestCase
from utils.logger import get_logger
from utils.text_utils import clean_text

logger = get_logger("TestCaseGenerator")


class TestType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    EDGE = "edge"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"


# ---- Keyword / intent heuristics ------------------------------------------

SECURITY_KEYWORDS = {
    "lock",
    "attempt",
    "failed",
    "security",
    "password",
    "auth",
    "credential",
    "verify",
    "otp",
    "token",
    "session",
    "permission",
    "role",
    "access",
    "encrypt",
}
BOUNDARY_KEYWORDS = {
    "limit",
    "maximum",
    "minimum",
    "range",
    "search",
    "filter",
    "price",
    "count",
    "number",
    "length",
    "size",
    "exceed",
    "boundary",
}
NEGATIVE_TRIGGERS = {
    "invalid",
    "incorrect",
    "wrong",
    "fail",
    "error",
    "missing",
    "empty",
    "null",
}
HIGH_PRIORITY_KEYWORDS = {
    "shall",
    "must",
    "critical",
    "lock",
    "security",
    "payment",
    "auth",
    "login",
    "password",
}
CRITICAL_PRIORITY_KEYWORDS = {"payment", "security", "encrypt", "lock", "critical"}

# Verb / action extraction helpers
ACTION_VERBS = r"\b(can|shall|should|must|will|allow|allows|support|supports|provide|provides|enable|enables|perform|ensure|ensures)\b"


def _extract_action_phrase(requirement_text: str) -> str:
    """Extract the core action phrase from a requirement sentence."""
    text = requirement_text.strip()
    # Try to capture after 'shall/must/can' verb
    m = re.search(
        r"(?:shall|must|should|can|will|allow(?:s)?|support(?:s)?|provide(?:s)?)\s+(.+?)(?:\.|$)",
        text,
        re.IGNORECASE,
    )
    if m:
        phrase = m.group(1).strip().rstrip(".")
        # Remove leading articles
        phrase = re.sub(r"^(the\s+|a\s+|an\s+)?", "", phrase, flags=re.IGNORECASE)
        return phrase.strip()
    # Fallback: take text after first noun
    return text


def _infer_priority(requirement: Requirement) -> str:
    text_lower = requirement.requirement.lower()
    if any(kw in text_lower for kw in CRITICAL_PRIORITY_KEYWORDS):
        return "Critical"
    if any(kw in text_lower for kw in HIGH_PRIORITY_KEYWORDS):
        return "High"
    if requirement.category and requirement.category.lower() in {
        "security",
        "authentication",
        "payment",
    }:
        return "High"
    return "Medium"


def _infer_module(requirement: Requirement) -> Optional[str]:
    if requirement.category:
        return requirement.category.strip()
    text_lower = requirement.requirement.lower()
    if any(
        k in text_lower for k in {"login", "auth", "password", "credential", "session"}
    ):
        return "Authentication"
    if any(k in text_lower for k in {"profile", "avatar", "phone", "account"}):
        return "User Profile"
    if any(k in text_lower for k in {"search", "filter", "catalog", "product"}):
        return "Search"
    if any(k in text_lower for k in {"payment", "checkout", "order", "cart"}):
        return "Commerce"
    return "Functional"


def _sanitize_id(base: str, counter: int) -> str:
    safe = re.sub(r"[^A-Z0-9\-]", "", base.upper().replace(" ", "-"))
    return f"{safe}-{counter:03d}"


# ---- Template synthesis ----------------------------------------------------

TEMPLATES: Dict[str, Dict[str, Any]] = {
    TestType.POSITIVE: {
        "title_tpl": "Verify {action_cap} — Positive / Happy Path",
        "desc_tpl": 'POSITIVE SCENARIO for {req_id}: Verify that the system correctly fulfills "{short_action}" under valid conditions and expected user flow. Requirement: "{requirement}"',
        "steps_tpl": [
            "Precondition: User/session is in valid state for '{short_action}'",
            "Provide valid inputs as per requirement specifications for '{short_action}'",
            "Trigger the primary action ({verb_phrase}) via UI / API",
            "Verify successful outcome: system completes '{short_action}' without errors and shows success confirmation",
        ],
        "expected_tpl": "POSITIVE EXPECTED: Operation succeeds. The system fulfills '{short_action}' per {req_id} and displays appropriate success confirmation with correct state update.",
        "default_priority": None,  # inferred
    },
    TestType.NEGATIVE: {
        "title_tpl": "Verify {action_cap} — Invalid / Negative Input Handling",
        "desc_tpl": 'NEGATIVE SCENARIO for {req_id}: Verify that the system gracefully handles INVALID or incorrect inputs for "{short_action}" and does NOT perform the operation. (Requirement {req_id} error-handling check)',
        "steps_tpl": [
            "Precondition: Reset state before testing INVALID input for '{short_action}'",
            "Inject INVALID or malformed input (empty, wrong format, disallowed value, SQL-like payload) for '{short_action}'",
            "Attempt to trigger the action with the invalid data",
            "Observe system response: expect inline validation error, no state change, and no crash",
        ],
        "expected_tpl": "NEGATIVE EXPECTED: System REJECTS invalid input with a clear, user-friendly error message. No unintended state change or data corruption occurs. Error is logged.",
        "default_priority": "High",
    },
    TestType.BOUNDARY: {
        "title_tpl": "Verify {action_cap} — Boundary Value & Limits",
        "desc_tpl": 'BOUNDARY SCENARIO for {req_id}: Verify min/max and just-outside-boundary conditions for "{short_action}" as implied by {req_id}. Focus on limit values, not happy-path.',
        "steps_tpl": [
            "Analyse and list boundary values for '{short_action}' (minimum, maximum, just inside/outside limit)",
            "BOUNDARY TEST 1: Execute with minimum valid boundary value for '{short_action}'",
            "BOUNDARY TEST 2: Execute with maximum valid boundary value for '{short_action}'",
            "BOUNDARY TEST 3: Execute with just-outside-boundary INVALID value for '{short_action}' and verify rejection",
        ],
        "expected_tpl": "BOUNDARY EXPECTED: System ACCEPTS values within the valid boundary for '{short_action}' and REJECTS out-of-range values with appropriate validation feedback per {req_id}.",
        "default_priority": "Medium",
    },
    TestType.EDGE: {
        "title_tpl": "Verify {action_cap} — Edge Case & Empty State",
        "desc_tpl": 'EDGE-CASE SCENARIO for {req_id}: Verify empty states, concurrent access, missing optional data, or first-time-user conditions for "{short_action}". Distinct from positive/negative flows.',
        "steps_tpl": [
            "Setup EDGE precondition: empty dataset, no prior history, or first-time user for '{short_action}'",
            "Attempt '{short_action}' under EDGE conditions (e.g., concurrent request, stale cache, missing optional field)",
            "Verify system stability: no crash, sensible fallback or empty-state message, and consistent data",
        ],
        "expected_tpl": "EDGE EXPECTED: System remains stable for '{short_action}' under edge conditions; shows sensible default or informative empty-state message. No crash or silent failure. Per {req_id}.",
        "default_priority": "Medium",
    },
    TestType.SECURITY: {
        "title_tpl": "Verify {action_cap} — Security / Authorization Check",
        "desc_tpl": 'SECURITY SCENARIO for {req_id}: Verify that "{short_action}" enforces authentication, authorization, and data protection (unauth/unauthorized/tampering) per {req_id}.',
        "steps_tpl": [
            "SECURITY PRECHECK: Ensure no valid session / token is present for '{short_action}'",
            "Attempt '{short_action}' as unauthenticated/unauthorized actor; attempt request tampering (modify payload, replay token, IDOR)",
            "Verify access DENIED: HTTP 401/403 or domain error, event audited, no data leakage",
        ],
        "expected_tpl": "SECURITY EXPECTED for {req_id}: Unauthorized access to '{short_action}' is DENIED (401/403). Sensitive data is not exposed and the event is audited. No privilege escalation.",
        "default_priority": "Critical",
    },
    TestType.PERFORMANCE: {
        "title_tpl": "Verify {action_cap} — Load & Response Time",
        "desc_tpl": 'PERFORMANCE SCENARIO for {req_id}: Verify that "{short_action}" meets response time and stability under normal load.',
        "steps_tpl": [
            "Execute '{short_action}' with representative data volume",
            "Measure response time and resource consumption for '{short_action}'",
            "Repeat under concurrent/repeated invocations (sanity load) for '{short_action}'",
        ],
        "expected_tpl": "PERFORMANCE EXPECTED: '{short_action}' completes within threshold (e.g., < 2s) per {req_id} without degradation or inconsistency.",
        "default_priority": "Low",
    },
}


def _synthesize_testcase(
    requirement: Requirement,
    test_type: TestType,
    seq_index: int,
    global_counter: int,
    total_strategy_count: int,
) -> TestCase:
    req_text = clean_text(requirement.requirement)
    action_phrase = _extract_action_phrase(req_text)
    short_action = action_phrase[:60].strip().rstrip(".")
    req_anchor = requirement.id
    import re as _re

    req_keywords = _re.findall(r"\b[a-z]{3,}\b", req_text.lower())
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "shall",
        "can",
        "user",
        "system",
        "allow",
        "using",
        "will",
        "should",
        "shall",
        "via",
        "per",
    }
    distinctive = [w for w in req_keywords if w not in stop][:5]
    keyword_hint = ", ".join(distinctive[:3]) if distinctive else req_anchor
    # Requirement fingerprint added to every field to disambiguate embeddings across requirements
    fingerprint = (
        f"[{req_anchor}: {keyword_hint}]" if keyword_hint else f"[{req_anchor}]"
    )
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "shall",
        "can",
        "user",
        "system",
        "allow",
        "using",
        "shall",
        "will",
        "should",
    }
    distinctive = [w for w in req_keywords if w not in stop][:5]
    keyword_hint = ", ".join(distinctive[:3]) if distinctive else req_anchor
    # Capitalize first letter for title
    action_cap = (
        short_action[:1].upper() + short_action[1:] if short_action else requirement.id
    )

    tpl = TEMPLATES[test_type]

    # Build title/desc/expected with templating
    title = tpl["title_tpl"].format(
        action_cap=action_cap,
        short_action=short_action,
        req_id=requirement.id,
        requirement=req_text,
    )
    # Suffix type-specific discriminator + requirement keywords to reduce inter-req collisions
    # Each variant gets a unique semantic tail, not identical prefix
    type_tag = {
        TestType.POSITIVE: f"[{req_anchor} POS]",
        TestType.NEGATIVE: f"[{req_anchor} NEG invalid]",
        TestType.BOUNDARY: f"[{req_anchor} BOUNDARY limits {keyword_hint}]",
        TestType.EDGE: f"[{req_anchor} EDGE empty-state]",
        TestType.SECURITY: f"[{req_anchor} SEC authz]",
        TestType.PERFORMANCE: f"[{req_anchor} PERF load]",
    }.get(test_type, f"[{req_anchor}]")
    title = f"{title} {type_tag}"
    if len(title) > 150:
        title = title[:147] + "..."

    description = tpl["desc_tpl"].format(
        requirement=req_text,
        req_id=requirement.id,
        short_action=short_action,
        action_cap=action_cap,
    )
    # Add unique semantic tail per variant type to improve embedding separation
    variant_tail = {
        TestType.POSITIVE: f" Focus: happy-path, valid-flow, success-confirmation for {req_anchor}.",
        TestType.NEGATIVE: f" Focus: malformed, empty, forbidden-value handling for {req_anchor}. Must not succeed.",
        TestType.BOUNDARY: f" Focus: min/max/edge-limit numbers, ranges and thresholds from {req_anchor}: {keyword_hint}.",
        TestType.EDGE: f" Focus: empty-dataset, no-history, concurrent, stale-cache edge for {req_anchor}.",
        TestType.SECURITY: f" Focus: unauthenticated, unauthorized, tampered request, session-hijack for {req_anchor}.",
        TestType.PERFORMANCE: f" Focus: response-time, concurrency, load-profile for {req_anchor}.",
    }.get(test_type, f" Requirement: {req_anchor}.")
    description = f"{description}{variant_tail}"

    steps = [
        s.format(
            short_action=short_action, verb_phrase=action_phrase, req_id=requirement.id
        )
        for s in tpl["steps_tpl"]
    ]

    expected = tpl["expected_tpl"].format(
        short_action=short_action,
        req_id=requirement.id,
    )

    # Priority resolution
    inferred_priority = _infer_priority(requirement)
    # Template priority overrides for specific types when not generic
    if tpl["default_priority"] and test_type in {TestType.SECURITY, TestType.NEGATIVE}:
        # Keep High/Critical for those types, but downgrade if requirement is Low-ish
        priority = (
            tpl["default_priority"]
            if inferred_priority in {"Medium", "High", "Critical"}
            else inferred_priority
        )
    else:
        priority = inferred_priority
        if test_type == TestType.BOUNDARY and inferred_priority == "Medium":
            priority = "Medium"
        if test_type == TestType.PERFORMANCE:
            priority = "Low"

    tc_id = f"TC-GEN-{global_counter:04d}"
    module = _infer_module(requirement)

    return TestCase(
        id=tc_id,
        title=title,
        description=description,
        steps=steps,
        expected_result=expected,
        priority=priority,
        requirement_ids=[requirement.id],
        module=module,
    )


def _select_test_types_for_requirement(
    requirement: Requirement,
    include_negative: bool = True,
    include_boundary: bool = True,
    include_edge: bool = True,
    include_security: bool = False,
    include_performance: bool = False,
    cases_per_req: int = 3,
    strategy: str = "comprehensive",
) -> List[TestType]:
    """Determine which test type variants to generate for a given requirement.

    Uses relevance scoring so security/boundary variants surface when they
    are actually relevant, rather than always filling slots sequentially.
    """
    text_lower = requirement.requirement.lower()
    selected: List[TestType] = [TestType.POSITIVE]

    if strategy == "minimal":
        return selected[: min(cases_per_req, 1)]

    # ---- Candidate scoring -------------------------------------------------
    candidates: List[Tuple[TestType, float]] = []

    if include_negative:
        candidates.append((TestType.NEGATIVE, 10.0))

    # Boundary relevance: 9 if strong boundary keywords, else 5
    if include_boundary:
        boundary_relevant = any(kw in text_lower for kw in BOUNDARY_KEYWORDS)
        b_score = 9.0 if boundary_relevant else 5.0
        candidates.append((TestType.BOUNDARY, b_score))

    if include_edge:
        candidates.append((TestType.EDGE, 6.0))

    # Security relevance: tiered scoring
    strong_security = {
        "lock",
        "attempt",
        "failed",
        "security",
        "permission",
        "role",
        "access",
        "encrypt",
        "session",
        "auth",
    }
    weak_security = {"password", "credential", "verify", "otp", "token"}
    has_strong = any(kw in text_lower for kw in strong_security)
    has_weak = any(kw in text_lower for kw in weak_security)
    security_relevant = has_strong or has_weak
    sec_score: Optional[float] = None
    if has_strong:
        sec_score = 10.0
    elif has_weak:
        sec_score = 5.5  # intentionally below EDGE (6.0) so generic login prefers edge
    if include_security:
        # Explicitly requested security should win unless it's completely irrelevant
        sec_score = max(sec_score or 0, 8.5)
    elif security_relevant and sec_score is not None:
        candidates.append((TestType.SECURITY, sec_score))
    if include_security and sec_score is not None:
        # Ensure security is in candidates even if already added
        if not any(c[0] == TestType.SECURITY for c in candidates):
            candidates.append((TestType.SECURITY, sec_score))
        else:
            # Upgrade existing score if forced
            for idx, (tt, sc) in enumerate(candidates):
                if tt == TestType.SECURITY:
                    candidates[idx] = (tt, max(sc, sec_score))
    elif include_security and sec_score is None:
        # Forced security but no keyword hit — still add with moderate score
        candidates.append((TestType.SECURITY, 8.5))
    elif sec_score is not None and not include_security:
        # Already handled security_relevant branch; do nothing extra
        pass

    if include_performance:
        candidates.append((TestType.PERFORMANCE, 4.0))

    # Sort candidates by score descending
    candidates_sorted = sorted(candidates, key=lambda x: x[1], reverse=True)

    for ttype, _score in candidates_sorted:
        if len(selected) >= cases_per_req:
            break
        if ttype not in selected:
            selected.append(ttype)

    # Canonical ordering for deterministic output
    priority_order = [
        TestType.POSITIVE,
        TestType.NEGATIVE,
        TestType.BOUNDARY,
        TestType.SECURITY,
        TestType.EDGE,
        TestType.PERFORMANCE,
    ]
    selected = sorted(
        selected, key=lambda t: priority_order.index(t) if t in priority_order else 99
    )

    return selected[:cases_per_req]


class TestCaseGenerator:
    """Intelligent template + heuristic test case generator."""

    def __init__(self):
        self.logger = logger

    def generate(
        self,
        requirements: List[Requirement],
        cases_per_requirement: int = 3,
        include_negative: bool = True,
        include_boundary: bool = True,
        include_edge: bool = True,
        include_security: bool = False,
        include_performance: bool = False,
        strategy: str = "comprehensive",
        id_prefix: str = "TC-GEN",
        ensure_unique_titles: bool = True,
    ) -> List[TestCase]:
        """
        Generate test cases for a list of requirements.

        Args:
            requirements: List of Requirement models.
            cases_per_requirement: Number of variants per requirement (1-5).
            include_negative: Include negative/invalid test variant.
            include_boundary: Include boundary value variant.
            include_edge: Include edge-case variant.
            include_security: Force include security variant.
            include_performance: Include performance variant.
            strategy: "comprehensive" or "minimal".
            id_prefix: Prefix for generated IDs.
            ensure_unique_titles: Deduplicate titles if needed.

        Returns:
            List[TestCase] generated.
        """
        start = time.perf_counter()
        if not requirements:
            logger.warning("TestCaseGenerator received empty requirements list.")
            return []

        cases_per_requirement = max(1, min(5, int(cases_per_requirement)))
        if strategy not in {"comprehensive", "minimal"}:
            strategy = "comprehensive"

        logger.info(
            f"Generating test cases: {len(requirements)} requirements x {cases_per_requirement} variants (strategy={strategy})"
        )

        all_tcs: List[TestCase] = []
        counter = 1
        seen_titles: Set[str] = set()

        for req_idx, req in enumerate(requirements, start=1):
            types = _select_test_types_for_requirement(
                req,
                include_negative=include_negative,
                include_boundary=include_boundary,
                include_edge=include_edge,
                include_security=include_security,
                include_performance=include_performance,
                cases_per_req=cases_per_requirement,
                strategy=strategy,
            )

            for type_idx, ttype in enumerate(types, start=1):
                tc = _synthesize_testcase(req, ttype, type_idx, counter, len(types))
                # Override ID prefix if custom
                if id_prefix != "TC-GEN":
                    tc.id = f"{id_prefix}-{counter:04d}"

                # Ensure unique titles
                if ensure_unique_titles:
                    base_title = tc.title
                    dedup_counter = 2
                    while tc.title.lower() in seen_titles:
                        tc.title = f"{base_title} (Variant {dedup_counter})"
                        dedup_counter += 1
                    seen_titles.add(tc.title.lower())
                else:
                    seen_titles.add(tc.title.lower())

                all_tcs.append(tc)
                counter += 1

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"Generated {len(all_tcs)} test cases from {len(requirements)} requirements in {elapsed_ms:.2f} ms."
        )
        return all_tcs

    def generate_for_single_requirement(
        self,
        requirement: Requirement,
        **kwargs,
    ) -> List[TestCase]:
        """Convenience wrapper for a single requirement."""
        return self.generate([requirement], **kwargs)

    def export_json(self, testcases: List[TestCase], pretty: bool = True) -> str:
        """Return JSON string for generated cases."""
        import json

        dicts = [tc.to_dict() for tc in testcases]
        return json.dumps(dicts, indent=2 if pretty else None, ensure_ascii=False)


# Singleton-style convenience function matching existing codebase style
_default_generator: Optional[TestCaseGenerator] = None


def get_generator() -> TestCaseGenerator:
    global _default_generator
    if _default_generator is None:
        _default_generator = TestCaseGenerator()
    return _default_generator
