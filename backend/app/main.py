

import shutil
import tempfile
from pathlib import Path

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