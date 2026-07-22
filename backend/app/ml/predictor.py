

import joblib

from backend.app.ml.feature_engineering import engineer_features


FEATURE_COLUMNS = [
    "total_amount",
    "gst_rate_x",
    "historical_avg_invoice_amount",
    "amount_ratio",
    "po_total",
    "po_ratio",
    "expected_monthly_invoice_count",
    "risk_tier_encoded",
    "active"
]


def predict_invoice(invoice_df, vendors_df, po_df):
    """Predict whether an invoice is anomalous."""

    # Load trained artifacts
    model = joblib.load("backend/app/ml/model.pkl")
    scaler = joblib.load("backend/app/ml/scaler.pkl")

    # Generate engineered features
    features_df = engineer_features(invoice_df, vendors_df, po_df)

    # Select the same features used during training
    X = features_df[FEATURE_COLUMNS]

    # Scale features
    X_scaled = scaler.transform(X)

    # Predict anomalies
    predictions = model.predict(X_scaled)
    anomaly_scores = model.decision_function(X_scaled)

    return predictions, anomaly_scores