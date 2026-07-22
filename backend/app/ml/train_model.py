import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from feature_engineering import engineer_features


def load_data():
    """Load project datasets."""
    invoices = pd.read_csv("data/historical_invoices.csv")
    vendors = pd.read_csv("data/vendors.csv")
    purchase_orders = pd.read_csv("data/purchase_orders.csv")
    return invoices, vendors, purchase_orders


if __name__ == "__main__":
    print("Loading datasets...")
    invoices, vendors, purchase_orders = load_data()

    print(f"Invoices: {len(invoices)}")
    print(f"Vendors: {len(vendors)}")
    print(f"Purchase Orders: {len(purchase_orders)}")

    print("\nEngineering features...")
    features_df = engineer_features(
        invoices,
        vendors,
        purchase_orders
    )

    print("Merged dataset shape:", features_df.shape)
    print("\nColumns:")
    print(features_df.columns.tolist())
    print("\nPreview:")
    print(features_df.head())

    print("\nSelecting ML features...")

    feature_columns = [
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

    X = features_df[feature_columns]

    print("Feature matrix shape:", X.shape)

    print("\nScaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )

    model.fit(X_scaled)

    joblib.dump(model, "backend/app/ml/model.pkl")
    joblib.dump(scaler, "backend/app/ml/scaler.pkl")

    print("\nModel saved to backend/app/ml/model.pkl")
    print("Scaler saved to backend/app/ml/scaler.pkl")
