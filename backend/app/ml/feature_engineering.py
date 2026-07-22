import pandas as pd
import numpy as np
def engineer_features(invoice_df, vendors_df, po_df):
    """
    Convert invoice data into ML features.
    """
    # Merge invoice data with vendor information
    df = invoice_df.merge(
        vendors_df,
        on="vendor_id",
        how="left"
    )

    # Merge invoice data with purchase order information
    df = df.merge(
        po_df,
        on="po_id",
        how="left"
    )

    # -----------------------------
    # Feature Engineering
    # -----------------------------

    # Ratio of invoice amount to vendor's historical average
    df["amount_ratio"] = (
        df["total_amount"] /
        df["historical_avg_invoice_amount"]
    )

    # Ratio of invoice amount to purchase order total
    df["po_ratio"] = (
        df["total_amount"] /
        df["po_total"]
    )

    # Encode vendor risk tier
    df["risk_tier_encoded"] = df["risk_tier"].map({
        "Low": 0,
        "Medium": 1,
        "High": 2
    })

    # Encode active vendor flag
    df["active"] = df["active"].astype(int)

    # Replace infinities and missing values
    df.replace([float("inf"), float("-inf")], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df