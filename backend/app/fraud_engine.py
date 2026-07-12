

import pandas as pd

from backend.app.data_loader import load_datasets


class FraudEngine:
    def __init__(self):
        self.data = load_datasets()
        self.vendors = self.data["vendors"]
        self.invoices = self.data["historical_invoices"]
        self.purchase_orders = self.data["purchase_orders"]

    def analyze_invoice(self, invoice):
        """Run deterministic fraud checks on one invoice."""
        signals = []

        vendor_id = invoice.get("vendor_id")
        vendor_matches = self.vendors[self.vendors["vendor_id"] == vendor_id]

        # 1. Vendor verification
        if vendor_matches.empty:
            signals.append({
                "check": "vendor_verification",
                "severity": "critical",
                "message": "Vendor is not present in the approved vendor master."
            })
            return self._build_result(signals)

        vendor = vendor_matches.iloc[0]

        # 2. Bank account manipulation detection
        if str(invoice.get("bank_account")) != str(vendor["registered_bank_account"]):
            signals.append({
                "check": "bank_account_change",
                "severity": "critical",
                "message": "Invoice bank account does not match the vendor's registered bank account."
            })

        # 3. Exact duplicate detection
        duplicate_matches = self.invoices[
            (self.invoices["vendor_id"] == vendor_id)
            & (self.invoices["invoice_number"].astype(str) == str(invoice.get("invoice_number")))
        ]

        if not duplicate_matches.empty:
            signals.append({
                "check": "duplicate_invoice",
                "severity": "high",
                "message": f"Invoice number already exists in historical records ({len(duplicate_matches)} match(es))."
            })

        # 4. GST pattern validation
        expected_gst = float(vendor["usual_gst_rate"])
        actual_gst = float(invoice.get("gst_rate", 0))

        if actual_gst != expected_gst:
            signals.append({
                "check": "gst_rate_mismatch",
                "severity": "medium",
                "message": f"GST rate is {actual_gst}%, while this vendor historically uses {expected_gst}%."
            })

        # 5. Financial arithmetic validation
        subtotal = float(invoice.get("subtotal", 0))
        gst_amount = float(invoice.get("gst_amount", 0))
        total_amount = float(invoice.get("total_amount", 0))
        expected_gst_amount = round(subtotal * actual_gst / 100, 2)
        expected_total = round(subtotal + gst_amount, 2)

        if abs(gst_amount - expected_gst_amount) > 1:
            signals.append({
                "check": "gst_calculation_error",
                "severity": "high",
                "message": f"GST amount is inconsistent. Expected approximately {expected_gst_amount:.2f}."
            })

        if abs(total_amount - expected_total) > 1:
            signals.append({
                "check": "total_calculation_error",
                "severity": "high",
                "message": f"Invoice total is inconsistent. Expected approximately {expected_total:.2f}."
            })

        # 6. Purchase order validation
        po_id = invoice.get("po_id")
        if not po_id:
            signals.append({
                "check": "missing_purchase_order",
                "severity": "medium",
                "message": "No purchase order is linked to this invoice."
            })
        else:
            po_matches = self.purchase_orders[
                self.purchase_orders["po_id"].astype(str) == str(po_id)
            ]

            if po_matches.empty:
                signals.append({
                    "check": "invalid_purchase_order",
                    "severity": "high",
                    "message": "The referenced purchase order does not exist."
                })
            else:
                po = po_matches.iloc[0]

                if str(po["vendor_id"]) != str(vendor_id):
                    signals.append({
                        "check": "po_vendor_mismatch",
                        "severity": "critical",
                        "message": "The purchase order belongs to a different vendor."
                    })

                if total_amount > float(po["po_total"]) * 1.02:
                    signals.append({
                        "check": "po_overbilling",
                        "severity": "high",
                        "message": f"Invoice total exceeds the purchase order total of {float(po['po_total']):.2f}."
                    })

        return self._build_result(signals)

    def _build_result(self, signals):
        severity_points = {
            "low": 5,
            "medium": 15,
            "high": 25,
            "critical": 40,
        }

        risk_score = min(
            100,
            sum(severity_points[signal["severity"]] for signal in signals)
        )

        if risk_score >= 70:
            decision = "BLOCK"
        elif risk_score >= 30:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "risk_score": risk_score,
            "decision": decision,
            "signals": signals,
        }