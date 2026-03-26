from typing import Any, Dict, Optional
from difflib import SequenceMatcher
from datetime import datetime


# Thresholds

NAME_MATCH_THRESHOLD = 0.85      # 85% — fuzzy name similarity
ID_MATCH_THRESHOLD = 0.85        # 85% — fuzzy ID similarity
OCR_CONFIDENCE_THRESHOLD = 0.60  # 60% — minimum OCR confidence
IMAGE_QUALITY_THRESHOLD = 0.50   # 50% — minimum image quality


def run_identity_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identity Agent — matches OCR-extracted data against candidate-claimed data.
    Produces an `identity_result` dict with match scores and flags.
    """
    request = state.get("request")
    if request is None:
        raise ValueError(
            "run_identity_agent: 'request' is missing from state. "
            "Ensure the VerificationRequest object is stored under the 'request' key."
        )
    ocr = state.get("ocr_result", {})

    claimed = request.claimed_data
    doc_type_declared = request.document.type.value

    flags = []

    # ── Image Quality 
    quality_score = ocr.get("image_quality_score") or 0.0
    quality_acceptable = quality_score >= IMAGE_QUALITY_THRESHOLD
    if not quality_acceptable:
        flags.append(f"Image quality too low ({quality_score:.0%}). Please upload a clearer image.")

    # ── OCR Confidence 
    ocr_confidence = ocr.get("ocr_confidence") or 0.0
    ocr_acceptable = ocr_confidence >= OCR_CONFIDENCE_THRESHOLD
    if not ocr_acceptable:
        flags.append(f"OCR confidence too low ({ocr_confidence:.0%}). Document text may be unreadable.")

    # ── Name Match 
    extracted_name: Optional[str] = ocr.get("full_name")
    name_score: float = 0.0
    name_matched = False

    if extracted_name and claimed.full_name:
        name_score = _fuzzy_name_match(claimed.full_name, extracted_name)
        name_matched = name_score >= NAME_MATCH_THRESHOLD
        
        if name_matched:
            if name_score < 1.0:
                flags.append(f"Minor name spelling difference identified: '{extracted_name}' (OCR) vs '{claimed.full_name}' (Claimed). Confidence: {name_score:.0%}")
        else:
            flags.append(
                f"Name mismatch: claimed '{claimed.full_name}' vs extracted '{extracted_name}' "
                f"(similarity {name_score:.0%})."
            )
    else:
        flags.append("Could not extract name from document.")

    # ── DOB Match 
    extracted_dob_raw: Optional[str] = ocr.get("date_of_birth")
    dob_matched = False

    if extracted_dob_raw and claimed.date_of_birth:
        norm_extracted = _normalize_date(extracted_dob_raw)
        norm_claimed = _normalize_date(claimed.date_of_birth)
        
        dob_matched = norm_extracted == norm_claimed
        if not dob_matched:
            flags.append(
                f"Date of birth mismatch: claimed '{claimed.date_of_birth}' vs extracted '{extracted_dob_raw}'."
            )
    else:
        flags.append("Could not extract date of birth from document.")

    # ── ID Match 
    extracted_id: Optional[str] = ocr.get("id_number")
    id_score: float = 0.0
    id_matched: Optional[bool] = None

    if claimed.id_number:
        if extracted_id:
            id_score = _fuzzy_id_match(claimed.id_number, extracted_id)
            id_matched = id_score >= ID_MATCH_THRESHOLD
            if id_matched and id_score < 1.0:
                flags.append(f"Minor ID spelling difference: '{extracted_id}' (OCR) vs '{claimed.id_number}' (Claimed).")
            elif not id_matched:
                flags.append(
                    f"ID mismatch: claimed '{claimed.id_number}' vs extracted '{extracted_id}' "
                    f"(similarity {id_score:.0%})."
                )
        else:
            flags.append("Could not extract ID number from document.")
            id_matched = False

    # ── Document Type 
    detected_type: Optional[str] = ocr.get("document_type_detected")
    type_matched = (
        detected_type is not None
        and detected_type.upper().replace("_", " ") == doc_type_declared.upper().replace("_", " ")
    )
    if not type_matched:
        flags.append(
            f"Document type mismatch: declared '{doc_type_declared}', detected '{detected_type}'."
        )

    # ── Tamper Detection 
    tamper_detected: bool = ocr.get("tamper_detected", False)
    tamper_details: Optional[str] = ocr.get("tamper_details")
    if tamper_detected:
        flags.append(f"Document tampering detected: {tamper_details or 'Possible digital alteration'}.")

    identity_result = {
        "extracted_name": extracted_name,
        "extracted_dob": extracted_dob_raw,
        "extracted_id": extracted_id,
        "detected_document_type": detected_type,
        "name_score": round(float(name_score), 4),
        "id_score": round(float(id_score), 4),
        "name_matched": name_matched,
        "dob_matched": dob_matched,
        "id_matched": id_matched,
        "type_matched": type_matched,
        "quality_score": quality_score,
        "quality_acceptable": quality_acceptable,
        "ocr_confidence": ocr_confidence,
        "ocr_acceptable": ocr_acceptable,
        "tamper_detected": tamper_detected,
        "tamper_details": tamper_details,
        "flags": flags,
    }

    return {**state, "identity_result": identity_result}


# Helpers


def _fuzzy_name_match(name_a: str, name_b: str) -> float:
    """Robust name comparison: handles reordering, case, and minor typos."""
    a = _normalize_name(name_a)
    b = _normalize_name(name_b)

    # Direct similarity
    direct = SequenceMatcher(None, a, b).ratio()

    # Token-set: sort tokens and compare (handles "Ajay Kumar" vs "Kumar Ajay")
    tokens_a = sorted(a.split())
    tokens_b = sorted(b.split())
    token_sorted_a = " ".join(tokens_a)
    token_sorted_b = " ".join(tokens_b)
    token_ratio = SequenceMatcher(None, token_sorted_a, token_sorted_b).ratio()

    return max(direct, token_ratio)


def _normalize_name(name: str) -> str:
    """Clean and lowercase name string."""
    if not name: return ""
    return " ".join(name.lower().strip().split())


def _normalize_date(date_str: str) -> Optional[str]:
    """Try multiple date formats and return YYYY-MM-DD or raw string."""
    if not date_str: return None
    
    # Common formats to try
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d %b %Y", "%d %B %Y", "%Y/%m/%d", "%d.%m.%Y",
        "%Y.%m.%d", "%b %d, %Y"
    ]
    
    clean_date = date_str.strip().replace(",", " ").replace(".", "-").replace("/", "-")
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Fallback to simple cleaning if no format matched
    return "".join(filter(lambda x: x.isdigit() or x == '-', clean_date))


def _fuzzy_id_match(id_a: str, id_b: str) -> float:
    """Direct similarity ratio ignoring spaces, dashes, and case."""
    if not id_a or not id_b: return 0.0
    a = "".join(filter(str.isalnum, id_a.lower()))
    b = "".join(filter(str.isalnum, id_b.lower()))
    return SequenceMatcher(None, a, b).ratio()
