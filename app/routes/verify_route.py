import uuid
import base64
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.models.schemas import (
    VerificationRequest, VerificationResponse, VerificationResult,
    ExtractedData, DataMatch, DocumentAuthenticity,
    DocumentInput, ClaimedData, DocumentType, VerificationType,
)
from app.database.db import get_db, VerificationRecord
from app.graph.agent_graph import verification_graph

router = APIRouter()


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Run identity verification",
    description=(
        "Upload an ID document image (Aadhaar / PAN / Passport) and provide "
        "the candidate's claimed data. The pipeline will OCR-extract the document "
        "via Gemini Vision and return a VERIFIED or FAILED verdict."
    ),
)
async def verify_identity(
    # ── Candidate info ──────────────────────────────────────────
    candidate_id: str = Form(..., description="Unique candidate ID, e.g. SR-2024-00123"),
    verification_type: VerificationType = Form(VerificationType.IDENTITY),

    # ── Document ────────────────────────────────────────────────
    document_type: DocumentType = Form(..., description="AADHAAR_CARD | PAN_CARD | PASSPORT | DRIVING_LICENSE"),
    image_front: UploadFile = File(..., description="Front side of the ID document (JPG / PNG / PDF)"),
    image_back: Optional[UploadFile] = File(None, description="Back side of the ID document (optional)"),

    # ── Claimed data ────────────────────────────────────────────
    full_name: str = Form(..., description="Candidate's full name as it appears on the document"),
    date_of_birth: str = Form(..., description="Date of birth in YYYY-MM-DD format, e.g. 1995-05-15"),
    gender: Optional[str] = Form(None, description="Male | Female | Other"),
    id_number: Optional[str] = Form(None, description="ID number printed on the document (optional)"),

    db: Session = Depends(get_db),
):
    # ── Convert uploaded files → base64 ───────────────────────
    try:
        front_bytes = await image_front.read()
        front_b64 = base64.b64encode(front_bytes).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image_front: {e}")

    back_b64: Optional[str] = None
    if image_back and image_back.filename:
        try:
            back_bytes = await image_back.read()
            back_b64 = base64.b64encode(back_bytes).decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read image_back: {e}")

    # ── Build internal request model ───────────────────────────
    payload = VerificationRequest(
        candidate_id=candidate_id,
        verification_type=verification_type,
        document=DocumentInput(
            type=document_type,
            image_front=front_b64,
            image_back=back_b64,
        ),
        claimed_data=ClaimedData(
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            id_number=id_number,
        ),
    )

    # ── Run the pipeline ────────────────────────────────────────
    verification_id = f"VER-{uuid.uuid4().hex[:8].upper()}"

    # ── Run LangGraph Pipeline ─────────────────────────────────
    try:
        initial_state = {"request": payload}
        final_state = verification_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    ocr = final_state.get("ocr_result", {}) or {}
    identity = final_state.get("identity_result", {}) or {}
    decision = final_state.get("final_result", {}) or {}

    # ── Build Response Objects ─────────────────────────────────
    extracted = ExtractedData(
        full_name=ocr.get("full_name"),
        date_of_birth=ocr.get("date_of_birth"),
        gender=ocr.get("gender"),
        id_number=ocr.get("id_number"),
        document_type=ocr.get("document_type_detected"),
        image_quality_score=ocr.get("image_quality_score"),
        ocr_confidence=ocr.get("ocr_confidence"),
        tamper_detected=ocr.get("tamper_detected"),
        tamper_details=ocr.get("tamper_details"),
    )

    data_match = DataMatch(
        name_match_score=identity.get("name_score"),
        name_matched=identity.get("name_matched"),
        dob_matched=identity.get("dob_matched"),
        id_number_matched=identity.get("id_matched"),
        document_type_matched=identity.get("type_matched"),
    )

    doc_auth = DocumentAuthenticity(
        tamper_free=not identity.get("tamper_detected", False),
        quality_acceptable=identity.get("quality_acceptable"),
        ocr_confidence_acceptable=identity.get("ocr_acceptable"),
        details=identity.get("tamper_details"),
    )

    ver_result = VerificationResult(
        identity_verified=decision.get("identity_verified", False),
        can_proceed=decision.get("can_proceed", False),
        flags=decision.get("flags", []),
    )

    status = decision.get("status", "FAILED")
    confidence = decision.get("confidence_score", 0.0)
    failure_reason = decision.get("failure_reason")

    # ── Persist to DB ──────────────────────────────────────────
    record = VerificationRecord(
        verification_id=verification_id,
        candidate_id=payload.candidate_id,
        status=status,
        confidence_score=confidence,
        document_type=payload.document.type.value,
        extracted_name=ocr.get("full_name"),
        extracted_dob=ocr.get("date_of_birth"),
        claimed_name=payload.claimed_data.full_name,
        claimed_dob=payload.claimed_data.date_of_birth,
        name_match_score=identity.get("name_score"),
        dob_matched=identity.get("dob_matched"),
        tamper_detected=ocr.get("tamper_detected"),
        failure_reason=failure_reason,
    )
    db.add(record)
    db.commit()

    return VerificationResponse(
        verification_id=verification_id,
        candidate_id=payload.candidate_id,
        status=status,
        confidence_score=confidence,
        extracted_data=extracted,
        data_match=data_match,
        document_authenticity=doc_auth,
        verification_result=ver_result,
        failure_reason=failure_reason,
    )
