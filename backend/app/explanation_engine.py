

class ExplanationEngine:
    def generate(self, fraud_analysis, extracted_invoice, vendor_match):
        ml = fraud_analysis.get("ml_anomaly_analysis", {})
        rule = fraud_analysis.get("rule_based_analysis", {})

        risk_score = fraud_analysis.get("final_risk_score", 0)

        if risk_score >= 70:
            risk_level = "HIGH"
            confidence = 95
            recommendation = "Block the invoice and initiate a fraud investigation."
        elif risk_score >= 40:
            risk_level = "MEDIUM"
            confidence = 88
            recommendation = "Send the invoice for manual review before payment."
        else:
            risk_level = "LOW"
            confidence = 96
            recommendation = "Invoice can be processed normally."

        top_factors = []

        if vendor_match.get("matched"):
            top_factors.append("Vendor successfully verified")

        if ml.get("prediction") == "NORMAL":
            top_factors.append("Invoice matches historical behaviour")
        else:
            top_factors.append("ML model detected anomalous behaviour")

        for signal in rule.get("signals", []):
            top_factors.append(signal.get("message", ""))

        return {
            "confidence": confidence,
            "risk_level": risk_level,
            "reason": recommendation,
            "top_factors": top_factors,
            "recommendation": recommendation,
        }