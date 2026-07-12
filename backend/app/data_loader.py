from pathlib import Path
import pandas as pd


# Find the project root regardless of where the script is run from
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def load_datasets():
    """Load all FraudLens AI datasets."""

    datasets = {
        "vendors": pd.read_csv(DATA_DIR / "vendors.csv"),
        "historical_invoices": pd.read_csv(
            DATA_DIR / "historical_invoices.csv"
        ),
        "purchase_orders": pd.read_csv(
            DATA_DIR / "purchase_orders.csv"
        ),
        "employees": pd.read_csv(DATA_DIR / "employees.csv"),
        "approval_history": pd.read_csv(
            DATA_DIR / "approval_history.csv"
        ),
    }

    return datasets


if __name__ == "__main__":
    data = load_datasets()

    print("\n=== FraudLens AI Dataset Loader ===\n")

    for name, dataframe in data.items():
        print(f"{name}: {len(dataframe)} rows")

    print("\nAll datasets loaded successfully!")