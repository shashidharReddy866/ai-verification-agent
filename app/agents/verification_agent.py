import os
import base64
import json
import re
from typing import Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _build_prompt(document_type: str) -> str:
    return f"""You are an expert document OCR and fraud detection system.

Analyze the provided ID document image ({document_type}) carefully and extract the following information.
You must be robust to different formats, fonts, and cases (upper/lower).

Document Type Declared: {document_type}

Return a JSON object with EXACTLY this structure:
{{
  "document_type_detected": "<AADHAAR_CARD | PAN_CARD | PASSPORT | DRIVING_LICENSE | UNKNOWN>",
  "full_name": "<extracted full name, maintaining original capitalization>",
  "date_of_birth": "<extracted date, ideally in YYYY-MM-DD format>",
  "gender": "<Male | Female | Other | null>",
  "id_number": "<extracted ID number, keeping all characters/spaces>",
  "image_quality_score": <0.0 to 1.0 — how clear and readable the image is>,
  "ocr_confidence": <0.0 to 1.0 — overall confidence in the extracted data>,
  "tamper_detected": <true | false>,
  "tamper_details": "<description of any tampering or spelling inconsistencies, or null if none>"
}}

Instructions:
- image_quality_score: 1.0 = crystal clear, 0.0 = completely unreadable.
- ocr_confidence: how certain you are of the accuracy.
- Extract names exactly as they appear, but indicate if they seem misspelled in 'tamper_details'.
- If a field is not present or unreadable, use null.
- Handle any case (lowercase/uppercase) and any common date format.
- Return ONLY the JSON object.
"""


def run_verification_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    OCR + Fraud Detection Agent.
    Calls Gemini Vision to extract data from ID document images.
    Handles multiple images (front + back) and consolidates results.
    """
    request = state.get("request")
    document = request.document
    doc_type = document.type.value

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )

    images = []
    if document.image_front:
        images.append(("front", document.image_front))
    if document.image_back:
        images.append(("back", document.image_back))

    all_results = []

    for side, b64_image in images:
        try:
            # Validate base64
            image_bytes = base64.b64decode(b64_image)

            # Detect MIME type from magic bytes
            if image_bytes.startswith(b'\xff\xd8\xff'):
                mime = "image/jpeg"
            elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                mime = "image/png"
            elif image_bytes.startswith(b'%PDF'):
                mime = "application/pdf"
            else:
                mime = "image/jpeg"  # default

            message = HumanMessage(content=[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": _build_prompt(doc_type) + f"\n\nThis is the {side} of the document."
                }
            ])

            response = llm.invoke([message])
            raw = response.content.strip()
            print(f"Raw model response for {side} of document: {raw}")

            # Extract JSON more robustly
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                raw_json = json_match.group(0)
            else:
                raw_json = raw

            parsed = json.loads(raw_json)
            all_results.append(parsed)

        except Exception as e:
            print(f"Error during Gemini OCR processing: {e}")
            all_results.append({
                "error": str(e),
                "image_quality_score": 0.0,
                "ocr_confidence": 0.0,
                "tamper_detected": False,
            })

    # Consolidate: pick best non-null values across front/back
    ocr_result = _consolidate_results(all_results)

    return {**state, "ocr_result": ocr_result}


def _consolidate_results(results: list) -> Dict[str, Any]:
    """Merge front + back results: prefer highest-confidence non-null values."""
    if not results:
        return {}

    if len(results) == 1:
        return results[0]

    consolidated = {}
    string_fields = ["document_type_detected", "full_name", "date_of_birth",
                     "gender", "id_number", "tamper_details"]
    float_fields = ["image_quality_score", "ocr_confidence"]

    # Pick best quality result for scoring fields
    best_ocr = max(results, key=lambda r: r.get("ocr_confidence", 0) or 0)

    for field in string_fields:
        # Use first non-null value
        val = None
        for r in results:
            v = r.get(field)
            if v is not None and v != "":
                val = v
                break
        consolidated[field] = val

    for field in float_fields:
        # Average the scores
        vals: List[float] = []
        for r in results:
            v = r.get(field)
            if v is not None:
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    pass
        if vals:
            avg_score = float(sum(vals)) / len(vals)
            consolidated[field] = round(avg_score, 3)
        else:
            consolidated[field] = 0.0

    # Tamper: if any side shows tamper, flag it
    consolidated["tamper_detected"] = any(r.get("tamper_detected", False) for r in results)

    return consolidated
