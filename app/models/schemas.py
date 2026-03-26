from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class DocumentType(str, Enum):
    AADHAAR_CARD = "AADHAAR_CARD"
    PAN_CARD = "PAN_CARD"
    PASSPORT = "PASSPORT"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    UNKNOWN = "UNKNOWN"


class VerificationType(str, Enum):
    IDENTITY = "IDENTITY"



# REQUEST MODELS


class DocumentInput(BaseModel):
    type: DocumentType
    image_front: str = Field(..., description="Base64-encoded front image of the document")
    image_back: Optional[str] = Field(None, description="Base64-encoded back image (if applicable)")


class ClaimedData(BaseModel):
    full_name: str = Field(..., description="Candidate's full name as claimed")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    gender: Optional[str] = Field(None, description="Gender: Male / Female / Other")
    id_number: Optional[str] = Field(None, description="ID number on the document (optional)")


class VerificationRequest(BaseModel):
    candidate_id: str = Field(..., description="Unique candidate identifier, e.g. SR-2024-00123")
    verification_type: VerificationType = VerificationType.IDENTITY
    document: DocumentInput
    claimed_data: ClaimedData


# RESPONSE MODELS


class ExtractedData(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    id_number: Optional[str] = None
    document_type: Optional[str] = None
    image_quality_score: Optional[float] = None
    ocr_confidence: Optional[float] = None
    tamper_detected: Optional[bool] = None
    tamper_details: Optional[str] = None


class DataMatch(BaseModel):
    name_match_score: Optional[float] = None
    name_matched: Optional[bool] = None
    dob_matched: Optional[bool] = None
    id_number_matched: Optional[bool] = None
    document_type_matched: Optional[bool] = None


class DocumentAuthenticity(BaseModel):
    tamper_free: Optional[bool] = None
    quality_acceptable: Optional[bool] = None
    ocr_confidence_acceptable: Optional[bool] = None
    details: Optional[str] = None


class VerificationResult(BaseModel):
    identity_verified: bool
    can_proceed: bool
    flags: List[str] = []


class VerificationResponse(BaseModel):
    verification_id: str
    candidate_id: str
    status: str  # "VERIFIED" | "FAILED"
    confidence_score: float
    extracted_data: Optional[ExtractedData] = None
    data_match: Optional[DataMatch] = None
    document_authenticity: Optional[DocumentAuthenticity] = None
    verification_result: VerificationResult
    failure_reason: Optional[str] = None
