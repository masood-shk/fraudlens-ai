# FraudLens AI Synthetic Dataset

Synthetic Indian enterprise accounts-payable dataset for hackathon prototyping.

Files:
- vendors.csv: 30 vendor master records
- historical_invoices.csv: 2,000 invoices with controlled fraud/anomaly cases
- purchase_orders.csv: 500 purchase orders
- employees.csv: 20 approvers/employees
- approval_history.csv: approval records linked to invoices

Important:
- `is_fraud`, `fraud_type`, and `is_fraud_ground_truth` are ground-truth labels for development/evaluation only.
- Do NOT use ground-truth labels as input features for the fraud detector.
- GSTINs, bank accounts, IFSC codes, company names, and all other records are synthetic and not intended to represent real entities.
- This dataset is suitable for a hackathon prototype, not production fraud-model validation.
