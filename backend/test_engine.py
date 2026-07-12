from pprint import pprint

from app.fraud_engine import FraudEngine

from app.ml_detector import MLAnomalyDetector
from app.risk_engine import RiskFusionEngine


engine = FraudEngine()
ml_detector = MLAnomalyDetector()

risk_engine = RiskFusionEngine()


normal_invoice = {
    "invoice_number": "NEW-INV-0001",
    "vendor_id": "V001",
    "po_id": "",
    "subtotal": 50000.00,
    "gst_rate": 12,
    "gst_amount": 6000.00,
    "total_amount": 56000.00,
    "bank_account": "100000007919",
}


suspicious_invoice = {
    "invoice_number": "V001/2025/00001",
    "vendor_id": "V001",
    "po_id": "INVALID-PO-999",
    "subtotal": 500000.00,
    "gst_rate": 28,
    "gst_amount": 5000.00,
    "total_amount": 700000.00,
    "bank_account": "999999999999",
}


print("\n=== NORMAL INVOICE TEST ===")
pprint(engine.analyze_invoice(normal_invoice))

print("\n=== SUSPICIOUS INVOICE TEST ===")
pprint(engine.analyze_invoice(suspicious_invoice))


print("\n=== NORMAL INVOICE ML TEST ===")
pprint(ml_detector.analyze(normal_invoice))

print("\n=== SUSPICIOUS INVOICE ML TEST ===")
pprint(ml_detector.analyze(suspicious_invoice))


print("\n=== FINAL NORMAL INVOICE ANALYSIS ===")
pprint(risk_engine.analyze_invoice(normal_invoice))

print("\n=== FINAL SUSPICIOUS INVOICE ANALYSIS ===")
pprint(risk_engine.analyze_invoice(suspicious_invoice))