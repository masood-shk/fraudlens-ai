

import json
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors
from pydantic import BaseModel, Field


load_dotenv()


class LineItem(BaseModel):
    description: str = ""
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class ExtractedInvoice(BaseModel):
    invoice_number: str = ""
    invoice_date: str = ""
    vendor_name: str = ""
    vendor_gstin: str = ""
    po_id: str = ""
    subtotal: float = 0
    gst_rate: float = 0
    gst_amount: float = 0
    total_amount: float = 0
    bank_account: str = ""
    ifsc_code: str = ""
    line_items: list[LineItem] = Field(default_factory=list)


class InvoiceExtractor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY was not found in the .env file.")

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.5-flash"

    def extract(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Invoice file not found: {file_path}")

        mime_type, _ = mimetypes.guess_type(file_path.name)
        mime_type = mime_type or "application/octet-stream"

        file_bytes = file_path.read_bytes()

        prompt = """
        You are an invoice document extraction system for an Indian accounts-payable
        fraud detection platform. Read the attached invoice carefully and extract
        only information explicitly visible in the document.

        Rules:
        - Do not invent missing values.
        - Return empty strings for missing text fields.
        - Return 0 for missing numeric fields.
        - Preserve invoice numbers, GSTINs, PO numbers, bank accounts and IFSC codes exactly.
        - GST rate should be a numeric percentage such as 18, not 0.18.
        - If CGST and SGST are shown separately, gst_rate must be their combined rate
          and gst_amount must be the combined tax amount.
        - subtotal means the amount before GST/tax.
        - total_amount means the final payable invoice amount.
        - Extract all visible line items when possible.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type,
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedInvoice,
                    temperature=0,
                ),
            )
        except errors.APIError as exc:
            print(f"Gemini API error: {exc}")
            status_code = getattr(exc, "code", None)
            error_text = str(exc).lower()

            if status_code == 429 or "quota" in error_text or "rate limit" in error_text or "resource_exhausted" in error_text:
                raise RuntimeError(
                    "Gemini API usage limit has been reached or too many requests were sent. Please try again later."
                ) from exc

            if status_code in (401, 403) or "api key" in error_text or "permission" in error_text:
                raise RuntimeError(
                    "Gemini API authentication failed. Please check the configured API key."
                ) from exc

            if status_code is not None and status_code >= 500:
                raise RuntimeError(
                    "Gemini API is temporarily unavailable. Please try again later."
                ) from exc

            raise RuntimeError(
                f"Gemini invoice extraction failed: {exc}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Invoice extraction failed: {exc}"
            ) from exc

        if response.parsed:
            return response.parsed.model_dump()

        if response.text:
            return ExtractedInvoice.model_validate(
                json.loads(response.text)
            ).model_dump()

        raise ValueError("Gemini returned an empty invoice extraction response.")