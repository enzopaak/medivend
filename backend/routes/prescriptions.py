"""
Prescription management routes — approval queue, review, status.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import json, base64
from datetime import datetime

from supabase_client import get_supabase
from models import PrescriptionCreate, PrescriptionReview, PrescriptionResponse

router = APIRouter()


@router.get("/", summary="Get all prescriptions (admin/pharmacist)")
def get_prescriptions(status: Optional[str] = None, limit: int = 50):
    sb = get_supabase()
    try:
        q = sb.table("prescriptions").select("*").order("uploaded_at", desc=True).limit(limit)
        if status:
            q = q.eq("validation_status", status)
        return q.execute().data
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/pending", summary="Get pending queue count")
def get_pending_count():
    sb = get_supabase()
    try:
        result = sb.table("prescriptions").select("*", count="exact").eq("validation_status", "pending").execute()
        return {"pending_count": result.count}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/patient/{user_id}", summary="Get prescriptions for a patient")
def get_patient_prescriptions(user_id: int):
    sb = get_supabase()
    try:
        return sb.table("prescriptions").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute().data
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/", summary="Upload new prescription")
def create_prescription(
    user_id: int = Form(...),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    sb = get_supabase()
    try:
        # Simulate AI OCR extraction
        ocr_text = notes or ""
        parsed = ai_extract_drug(ocr_text)

        payload = {
            "user_id": user_id,
            "ocr_raw_text": ocr_text,
            "parsed_data": parsed,
            "validation_status": "pending",
            "uploaded_at": datetime.utcnow().isoformat()
        }

        # Upload image to Supabase Storage if provided
        if file:
            contents = file.file.read()
            path = f"prescriptions/{user_id}/{datetime.utcnow().timestamp()}_{file.filename}"
            sb.storage.from_("prescriptions").upload(path, contents)
            payload["image_storage_path"] = path

        result = sb.table("prescriptions").insert(payload).execute()

        # Log audit
        sb.table("auditlogs").insert({
            "action_type": "PRESCRIPTION_UPLOADED",
            "details": {"user_id": user_id, "drug_detected": parsed.get("drug")},
        }).execute()

        return {"success": True, "prescription_id": result.data[0]["prescription_id"], "ai_result": parsed}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.patch("/{prescription_id}/review", summary="Approve or reject prescription")
def review_prescription(prescription_id: int, review: PrescriptionReview, reviewer_id: int = 1):
    sb = get_supabase()
    try:
        update = {
            "validation_status": review.validation_status,
            "rejection_reason": review.rejection_reason,
        }
        result = sb.table("prescriptions").update(update).eq("prescription_id", prescription_id).execute()

        if not result.data:
            raise HTTPException(404, "Prescription not found")

        # Audit log
        sb.table("auditlogs").insert({
            "user_id": reviewer_id,
            "action_type": review.validation_status.upper(),
            "details": {
                "prescription_id": prescription_id,
                "reason": review.rejection_reason,
                "alternative_drug": review.alternative_drug_id
            }
        }).execute()

        return {"success": True, "status": review.validation_status}
    except Exception as e:
        raise HTTPException(500, str(e))


def ai_extract_drug(text: str) -> dict:
    """
    Simple rule-based drug extraction.
    In production: replace with an actual OCR + NLP model (e.g. Amazon Textract, or a fine-tuned BERT).
    """
    drug_keywords = {
        "desloratadine": "Desloratadine 5mg",
        "panadol": "Panadol 500mg", "paracetamol": "Panadol 500mg",
        "amoxicillin": "Amoxicillin 500mg", "amoxil": "Amoxicillin 500mg",
        "ibuprofen": "Ibuprofen 400mg", "brufen": "Ibuprofen 400mg",
        "urea": "Urea 10% Cream",
        "calamine": "Calamine Lotion 8%",
        "diosmin": "Diosmin 500mg", "capillo": "Diosmin 500mg",
        "perampanel": "Perampanel 2mg", "fycompa": "Perampanel 2mg",
        "multivitamin": "Multivitamins Syrup",
        "freestyle": "FreeStyle Libre 2 Sensor",
        "insulin": "BD Insulin Pen Needle 4mm",
        "zinc oxide": "Zinc Oxide 15% Cream",
        "accu-chek": "Accu-Chek Test Strips",
        "charcoal": "Activated Charcoal Powder",
    }

    text_lower = text.lower()
    detected = None
    confidence = 0.0

    for keyword, drug in drug_keywords.items():
        if keyword in text_lower:
            detected = drug
            confidence = 0.91
            break

    return {
        "drug": detected or "Unknown — Manual review required",
        "confidence": confidence,
        "raw_text": text[:200],
        "extraction_method": "keyword_matching_v1",
        "requires_manual_review": detected is None
    }
