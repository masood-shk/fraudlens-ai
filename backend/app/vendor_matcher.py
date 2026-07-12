

import re

from backend.app.data_loader import load_datasets


class VendorMatcher:
    def __init__(self):
        self.vendors = load_datasets()["vendors"].copy()

    @staticmethod
    def _normalize(value):
        if not value:
            return ""
        return re.sub(r"[^a-z0-9]", "", str(value).lower())

    def match(self, vendor_name="", vendor_gstin=""):
        # 1. GSTIN is the strongest identifier.
        if vendor_gstin:
            normalized_gstin = self._normalize(vendor_gstin)
            gstin_matches = self.vendors[
                self.vendors["gstin"].apply(self._normalize) == normalized_gstin
            ]

            if not gstin_matches.empty:
                vendor = gstin_matches.iloc[0]
                return {
                    "matched": True,
                    "vendor_id": vendor["vendor_id"],
                    "vendor_name": vendor["vendor_name"],
                    "match_method": "gstin",
                    "confidence": 100,
                }

        # 2. Fall back to normalized exact vendor-name matching.
        if vendor_name:
            normalized_name = self._normalize(vendor_name)
            name_matches = self.vendors[
                self.vendors["vendor_name"].apply(self._normalize) == normalized_name
            ]

            if not name_matches.empty:
                vendor = name_matches.iloc[0]
                return {
                    "matched": True,
                    "vendor_id": vendor["vendor_id"],
                    "vendor_name": vendor["vendor_name"],
                    "match_method": "exact_name",
                    "confidence": 100,
                }

        return {
            "matched": False,
            "vendor_id": None,
            "vendor_name": vendor_name,
            "match_method": "none",
            "confidence": 0,
        }