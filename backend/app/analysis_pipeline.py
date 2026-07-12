

from backend.app.invoice_extractor import InvoiceExtractor
from backend.app.vendor_matcher import VendorMatcher


class AnalysisPipeline:
    def __init__(self):
        self.invoice_extractor = InvoiceExtractor()
        self.vendor_matcher = VendorMatcher()

    def analyze(self, file_path):
        # Step 1: Extract structured invoice data from the uploaded document.
        extracted_invoice = self.invoice_extractor.extract(file_path)

        # Step 2: Match the extracted vendor against the vendor master.
        vendor_match = self.vendor_matcher.match(
            vendor_name=extracted_invoice.get("vendor_name", ""),
            vendor_gstin=extracted_invoice.get("vendor_gstin", ""),
        )

        # If no trusted vendor match exists, stop before vendor-history and ML
        # analysis because those checks require a valid internal vendor identity.
        if not vendor_match["matched"]:
            return {
                "status": "completed",
                "extracted_invoice": extracted_invoice,
                "vendor_match": vendor_match,
                "fraud_analysis": {
                    "final_risk_score": 80,
                    "decision": "BLOCK",
                    "reason": "The invoice vendor could not be matched to the approved vendor master.",
                    "rule_based_analysis": {
                        "risk_score": 40,
                        "signals": [
                            {
                                "check": "vendor_verification",
                                "severity": "critical",
                                "message": "Vendor is not present in the approved vendor master.",
                            }
                        ],
                    },
                    "ml_anomaly_analysis": None,
                    "critical_override_applied": True,
                },
            }

        # Step 3: Attach the internal vendor ID required by the fraud engines.
        invoice_for_analysis = extracted_invoice.copy()
        invoice_for_analysis["vendor_id"] = vendor_match["vendor_id"]

        # Import here so the existing app.* package imports work when this
        # pipeline is run through the current backend script structure.
        from backend.app.risk_engine import RiskFusionEngine

        risk_engine = RiskFusionEngine()
        fraud_analysis = risk_engine.analyze_invoice(invoice_for_analysis)

        return {
            "status": "completed",
            "extracted_invoice": extracted_invoice,
            "vendor_match": vendor_match,
            "fraud_analysis": fraud_analysis,
        }