# 🤖 AI Verification Agent

An Agentic AI system for automated document verification using OCR, LLMs, and multi-agent workflows.

---

## 🚀 Overview

This project simulates an intelligent document verification pipeline that extracts, validates, and verifies user documents using AI agents.

The system combines:
- OCR for text extraction  
- LLMs for understanding and parsing  
- RAG-style validation logic  
- Multi-agent workflows for decision-making  

---

## 🧠 Architecture

Document → OCR → LLM Parsing → Agent Workflow → Decision Output

### Agents:
- Identity Agent → Extracts structured data  
- Matching Agent → Compares with user input  
- Decision Agent → Final verification result  

---

## ⚙️ Tech Stack

- Python  
- FastAPI  
- LangChain / LangGraph  
- LLM APIs (Gemini / GPT / Claude)  
- OCR Processing  
- SQLAlchemy  

---

## 📌 Features

- Document type detection (Aadhaar, etc.)
- Structured data extraction
- Multi-agent reasoning pipeline
- Fraud / inconsistency detection
- API-based verification system

---

## 🔌 API Endpoint

```bash
POST /api/v1/verify

## expected output -

{
  "document_type_detected": "AADHAAR_CARD",
  "full_name": "RAVI KUMAR",
  "ocr_confidence": 0.98,
  "tamper_detected": false
}
