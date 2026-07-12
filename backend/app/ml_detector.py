

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.app.data_loader import load_datasets


class MLAnomalyDetector:
    def __init__(self):
        data = load_datasets()
        self.invoices = data["historical_invoices"].copy()
        self.vendors = data["vendors"].copy()
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.12,
            random_state=42,
        )
        self.feature_columns = [
            "subtotal",
            "gst_rate",
            "total_amount",
            "amount_vs_vendor_average",
        ]
        self._train()

    def _prepare_training_data(self):
        training_data = self.invoices.merge(
            self.vendors[["vendor_id", "historical_avg_invoice_amount"]],
            on="vendor_id",
            how="left",
        )

        training_data["amount_vs_vendor_average"] = (
            training_data["total_amount"]
            / training_data["historical_avg_invoice_amount"].replace(0, np.nan)
        )

        return training_data[self.feature_columns].fillna(0)

    def _train(self):
        features = self._prepare_training_data()
        scaled_features = self.scaler.fit_transform(features)
        self.model.fit(scaled_features)

    def analyze(self, invoice):
        vendor_matches = self.vendors[
            self.vendors["vendor_id"] == invoice.get("vendor_id")
        ]

        if vendor_matches.empty:
            return {
                "anomaly_score": 100,
                "is_anomaly": True,
                "reason": "Unknown vendor cannot be compared with historical behavior.",
            }

        vendor = vendor_matches.iloc[0]
        vendor_average = float(vendor["historical_avg_invoice_amount"])
        total_amount = float(invoice.get("total_amount", 0))

        feature_row = pd.DataFrame([{
            "subtotal": float(invoice.get("subtotal", 0)),
            "gst_rate": float(invoice.get("gst_rate", 0)),
            "total_amount": total_amount,
            "amount_vs_vendor_average": (
                total_amount / vendor_average if vendor_average > 0 else 0
            ),
        }])

        scaled_row = self.scaler.transform(feature_row[self.feature_columns])
        prediction = int(self.model.predict(scaled_row)[0])
        decision_score = float(self.model.decision_function(scaled_row)[0])

        # Convert Isolation Forest's unbounded decision value into a
        # presentation-friendly 0-100 anomaly score. This is a risk indicator,
        # not a calibrated probability of fraud.
        anomaly_score = int(
            round(100 / (1 + np.exp(12 * decision_score)))
        )
        anomaly_score = max(0, min(100, anomaly_score))

        ratio = total_amount / vendor_average if vendor_average > 0 else 0
        if ratio >= 3:
            reason = (
                f"Invoice total is {ratio:.1f}x the vendor's historical average."
            )
        elif prediction == -1:
            reason = "Invoice pattern is unusual compared with historical invoice behavior."
        else:
            reason = "Invoice pattern is within the learned historical range."

        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": prediction == -1,
            "reason": reason,
            "amount_vs_vendor_average": round(ratio, 2),
        }