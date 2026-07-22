from backend.app.fraud_engine import FraudEngine
from backend.app.ml_detector import MLAnomalyDetector


class RiskFusionEngine:
    def __init__(self):
        self.rule_engine = FraudEngine()
        self.ml_detector = MLAnomalyDetector()

    def analyze_invoice(self, invoice):
        rule_result = self.rule_engine.analyze_invoice(invoice)
        ml_result = self.ml_detector.analyze(invoice)

        rule_score = rule_result["risk_score"]
        ml_score = ml_result["anomaly_score"]
        signals = rule_result["signals"]

        # Rules carry more weight because they represent concrete evidence.
        combined_score = round((rule_score * 0.7) + (ml_score * 0.3))

        critical_checks = {
            "vendor_verification",
            "bank_account_change",
            "po_vendor_mismatch",
        }

        critical_signal_detected = any(
            signal["check"] in critical_checks
            and signal["severity"] == "critical"
            for signal in signals
        )

        # Critical identity/payment redirection signals must not be diluted
        # by an otherwise normal ML score.
        if critical_signal_detected:
            combined_score = max(combined_score, 75)

        combined_score = max(0, min(100, combined_score))

        if combined_score >= 70:
            decision = "BLOCK"
        elif combined_score >= 30:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "final_risk_score": combined_score,
            "decision": decision,
            "rule_based_analysis": rule_result,
            "ml_anomaly_analysis": ml_result,
            "critical_override_applied": critical_signal_detected,
        }