AI Identity Verification Agent (POC-3)

An AI-powered identity verification backend built with FastAPI, LangGraph, Gemini Vision, and PostgreSQL.

The system verifies identity documents such as Aadhaar, PAN, Passport, and Driving License by extracting data using AI OCR and matching it against user-provided information.

Project Overview

This system performs automated identity verification through a multi-agent pipeline.

Workflow:

Document Upload
      ↓
Gemini Vision OCR
      ↓
Identity Extraction
      ↓
Data Matching
      ↓
Fraud / Tamper Detection
      ↓
Verification Decision
      ↓
Store Result in PostgreSQL
Tech Stack
Component	Technology
Backend API	FastAPI
AI OCR	Google Gemini Vision
AI Workflow	LangGraph
LLM Integration	LangChain
Database	PostgreSQL
ORM	SQLAlchemy
Environment Config	python-dotenv
Image Handling	Pillow
System Architecture
Client
  ↓
FastAPI Routes (/verify)
  ↓
LangGraph Verification Pipeline
  ↓
Verification Agent (OCR + Fraud Detection)
  ↓
Identity Agent (Extracted vs Claimed Data)
  ↓
Matching Agent (Similarity Scoring)
  ↓
Decision Agent (Final Verdict)
  ↓
PostgreSQL Database (verification_records)
Project Structure
verification-agent/
│
├── app/
│   ├── main.py
│   │
│   ├── routes/
│   │   └── verify_route.py
│   │
│   ├── agents/
│   │   ├── verification_agent.py
│   │   ├── identity_agent.py
│   │   ├── matching_agent.py
│   │   └── decision_agent.py
│   │
│   ├── graph/
│   │   └── agent_graph.py
│   │
│   ├── database/
│   │   └── db.py
│   │
│   └── models/
│       └── schemas.py
│
├── .env
├── requirements.txt
└── README.md
Installation
1. Clone the repository
git clone <repo-url>
cd verification-agent
2. Create virtual environment
python -m venv .venv

Activate:

Windows

.venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
Environment Variables

Create a .env file in the project root.

GEMINI_API_KEY=your_gemini_api_key

DATABASE_URL=postgresql://postgres:root@localhost:5432/poc3_db
Database Setup

Create database:

CREATE DATABASE poc3_db;

Tables will be created automatically when the server starts.

Running the Server
uvicorn app.main:app --reload

Server runs at:

http://127.0.0.1:8000
API Documentation

Swagger UI:

http://127.0.0.1:8000/docs
Verification Endpoint
POST /api/v1/verify

Uploads a document and verifies identity.

Request Fields
Field	Type	Description
candidate_id	string	Unique candidate ID
document_type	enum	AADHAAR_CARD / PAN_CARD / PASSPORT
image_front	file	Document image
image_back	file	Optional back side
full_name	string	Claimed name
date_of_birth	string	YYYY-MM-DD
gender	string	Optional
id_number	string	ID number
Example Response
{
  "verification_id": "VER-9FF963C5",
  "candidate_id": "TEST001",
  "status": "VERIFIED",
  "confidence_score": 99.2,
  "extracted_data": {
    "full_name": "RAVI KUMAR",
    "date_of_birth": "1995-01-01",
    "gender": "Male",
    "id_number": "1234 5678 9012"
  },
  "verification_result": {
    "identity_verified": true,
    "can_proceed": true
  }
}
Database Table
verification_records

Columns:

verification_id
candidate_id
status
confidence_score
document_type
extracted_name
extracted_dob
claimed_name
claimed_dob
name_match_score
dob_matched
tamper_detected
failure_reason
created_at
Features

✔ AI OCR using Gemini Vision
✔ Document authenticity checks
✔ Data similarity matching
✔ Fraud detection flags
✔ Confidence scoring
✔ Verification decision engine
✔ PostgreSQL persistence

Future Improvements

• Fuzzy name matching (RapidFuzz)
• Aadhaar number validation algorithm
• OpenCV tamper detection
• Multi-document verification
• Verification dashboard UI

Author

AI Identity Verification System — POC-3

Built using FastAPI + LangGraph + Gemini Vision