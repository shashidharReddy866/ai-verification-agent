from typing import Any, Dict


# ─────────────────────────────────────────────────────────────
# Final Decision Thresholds
# ─────────────────────────────────────────────────────────────
NAME_THRESHOLD = 0.85       # Fuzzy name similarity
OCR_THRESHOLD = 0.60        # OCR confidence
QUALITY_THRESHOLD = 0.50    # Image quality

# Weight distribution for the confidence score
WEIGHT_NAME = 0.35
WEIGHT_DOB = 0.30
WEIGHT_QUALITY = 0.15
WEIGHT_OCR = 0.15
WEIGHT_TYPE = 0.05


def run_matching_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Matching / Decision Agent — applies pass/fail rules and computes
    a final confidence_score. Produces a `final_result` dict.
    """
    identity = state.get("identity_result", {})
    ocr = state.get("ocr_result", {})

    flags: list = identity.get("flags", [])
    failure_reasons = []

    # ── Critical Checks (any failure → FAILED)

    name_matched: bool = identity.get("name_matched", False)
    dob_matched: bool = identity.get("dob_matched", False)
    id_matched: bool = identity.get("id_matched") if identity.get("extracted_id") else True
    # Default to True if no ID number was claimed to match against
    if id_matched is None: id_matched = True 

    tamper_detected: bool = identity.get("tamper_detected", False)
    quality_acceptable: bool = identity.get("quality_acceptable", False)
    ocr_acceptable: bool = identity.get("ocr_acceptable", False)

    if not name_matched:
        failure_reasons.append("Name does not match within acceptable threshold.")
    if not dob_matched:
        failure_reasons.append("Date of birth does not match.")
    if not id_matched:
        failure_reasons.append("ID number does not match claimed value.")
    if tamper_detected:
        failure_reasons.append("Document tampering detected.")
    if not quality_acceptable:
        failure_reasons.append("Document image quality is too low.")
    if not ocr_acceptable:
        failure_reasons.append("OCR confidence is too low to reliably extract data.")

    # ── Confidence Score
    name_score: float = identity.get("name_score", 0.0)
    id_score: float = identity.get("id_score", 0.0)
    quality_score: float = identity.get("quality_score", 0.0)
    ocr_confidence: float = identity.get("ocr_confidence", 0.0)
    type_matched: bool = identity.get("type_matched", False)

    dob_score = 1.0 if dob_matched else 0.0
    type_score = 1.0 if type_matched else 0.5

    # Weights: Name(0.3), DOB(0.25), ID(0.15), Quality(0.1), OCR(0.15), Type(0.05)
    confidence_score = (
        name_score     * 0.30 +
        dob_score      * 0.25 +
        id_score       * 0.15 +
        quality_score  * 0.10 +
        ocr_confidence * 0.15 +
        type_score     * 0.05
    )
    confidence_score = round(min(max(confidence_score, 0.0), 1.0) * 100, 1)

    # ── Final Verdict
    passed = len(failure_reasons) == 0
    status = "VERIFIED" if passed else "FAILED"

    matching_result = {
        "status": status,
        "confidence_score": confidence_score,
        "identity_verified": passed,
        "can_proceed": passed,
        "flags": flags,
        "failure_reasons": failure_reasons,
        "failure_reason": "; ".join(failure_reasons) if failure_reasons else None,
    }

    return {**state, "matching_result": matching_result}
