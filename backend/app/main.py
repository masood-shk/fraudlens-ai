

import shutil
import tempfile
from pathlib import Path

from datetime import datetime
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.analysis_pipeline import AnalysisPipeline


app = FastAPI(
    title="FraudLens AI API",
    description="AI and ML-powered invoice fraud detection API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://fraudlens-ai-theta.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = AnalysisPipeline()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "FraudLens AI API",
    }


@app.post("/api/analyze")
def analyze_invoice(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a PDF, PNG, JPG, or JPEG invoice.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)

        if temp_path.stat().st_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large. Maximum upload size is 10 MB.",
            )

        result = pipeline.analyze(temp_path)
        print("========== PIPELINE RESULT ==========")
        print(result)
        print("====================================")

        now = datetime.now()
        case_id = f"FL-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        generated_at = now.strftime("%d %b %Y, %I:%M %p")

        fraud = result.get("fraud_analysis", {})
        invoice = result.get("extracted_invoice", {})

        decision = fraud.get("decision", "REVIEW")
        risk_score = fraud.get("final_risk_score", 0)

        findings = fraud.get("rule_based_analysis", {}).get("signals", [])

        critical_findings = []
        for finding in findings:
            if isinstance(finding, dict):
                critical_findings.append(
                    finding.get("title")
                    or finding.get("message")
                    or finding.get("description")
                    or str(finding)
                )
            else:
                critical_findings.append(str(finding))

        if not critical_findings:
            critical_findings.append("No major fraud indicators detected.")

        recommendation_map = {
            "APPROVE": [
                "Proceed with payment.",
                "Archive the investigation record.",
            ],
            "REVIEW": [
                "Send the invoice for manual review.",
                "Verify supporting documents before payment.",
            ],
            "BLOCK": [
                "Do not release payment.",
                "Escalate to the Finance Compliance team.",
            ],
        }

        result["investigation_report"] = {
            "case_id": case_id,
            "generated_at": generated_at,
            "generated_by": "FraudLens AI",
            "status": "Completed",
            "invoice": {
                "invoice_number": invoice.get("invoice_number", "Unknown"),
                "vendor": invoice.get("vendor", "Unknown"),
                "invoice_date": invoice.get("invoice_date", "Unknown"),
                "amount": invoice.get("amount", "Unknown"),
            },
            "decision": decision,
            "risk_score": risk_score,
            "summary": f"The invoice was classified as {decision} with a risk score of {risk_score} based on the combined fraud analysis.",
            "critical_findings": critical_findings,
            "recommended_actions": recommendation_map.get(
                str(decision).upper(),
                ["Perform additional manual verification."]
            ),
        }
        print("========== FINAL RESPONSE ==========")
        print(result)
        print("====================================")
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invoice analysis failed: {str(exc)}",
        ) from exc
    finally:
        file.file.close()
        if temp_path and temp_path.exists():
            temp_path.unlink()