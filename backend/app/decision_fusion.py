class DecisionFusionEngine:
    def combine(self, rule_analysis, ml_prediction, anomaly_score):
        rule_score = rule_analysis.get("rule_based_analysis", {}).get("risk_score", 0)
        final_score = rule_analysis.get("final_risk_score", rule_score)
        critical_override = False

        # Increase risk if the ML model detects an anomaly.
        if ml_prediction == "ANOMALY":
            final_score += 35

        # Cap the score at 100.
        final_score = min(final_score, 100)

        # Respect any critical rule-based decision.
        if rule_analysis.get("decision") == "BLOCK":
            decision = "BLOCK"
            critical_override = True
        elif final_score >= 70:
            decision = "BLOCK"
        elif final_score >= 40:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "final_risk_score": final_score,
            "decision": decision,
            "rule_based_analysis": rule_analysis.get("rule_based_analysis", {}),
            "ml_anomaly_analysis": {
                "prediction": ml_prediction,
                "anomaly_score": float(anomaly_score),
            },
            "critical_override_applied": critical_override,
        }