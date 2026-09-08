#!/usr/bin/env python3
"""
Multi-Column Financial Table Extractor & Ledger Validator
Reconstructs tabular bank/tax statements using layout clustering and bounding-box geometry.
"""

import os, json, re
from PIL import Image, ImageDraw

class FinancialTableExtractor:
    def __init__(self, y_threshold=15):
        self.y_threshold = y_threshold

    def cluster_into_rows(self, ocr_results):
        """
        ocr_results format from EasyOCR:
        [([bbox_coords], "text", confidence), ...]
        """
        # Sort items primarily by Y-coordinate of top-left corner
        items = []
        for bbox, text, conf in ocr_results:
            top_y = bbox[0][1]
            left_x = bbox[0][0]
            items.append({"text": text.strip(), "x": left_x, "y": top_y, "conf": conf})

        items.sort(key=lambda item: item["y"])

        rows = []
        current_row = []
        current_y = None

        for item in items:
            if current_y is None:
                current_y = item["y"]
                current_row.append(item)
            elif abs(item["y"] - current_y) <= self.y_threshold:
                current_row.append(item)
            else:
                # Sort row items left-to-right (by X)
                current_row.sort(key=lambda it: it["x"])
                rows.append([it["text"] for it in current_row])
                current_row = [item]
                current_y = item["y"]

        if current_row:
            current_row.sort(key=lambda it: it["x"])
            rows.append([it["text"] for it in current_row])

        return rows

    def parse_statement_ledger(self, rows):
        """Converts raw rows into structured transaction items."""
        transactions = []
        header = None

        for r in rows:
            line_str = " ".join(r)
            # Detect Date + Amount patterns (e.g. DD/MM/YYYY ... EUR/USD)
            date_match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', line_str)
            amounts = re.findall(r'[-+]?\d+[\.,]\d{2}', line_str)

            if date_match and amounts:
                tx_date = date_match.group(1)
                amount = amounts[0]
                desc = line_str.replace(tx_date, "").replace(amount, "").strip()
                transactions.append({
                    "date": tx_date,
                    "description": desc,
                    "amount": amount
                })

        return {
            "total_extracted_rows": len(rows),
            "parsed_transactions_count": len(transactions),
            "transactions": transactions
        }


if __name__ == "__main__":
    print("=== FINANCIAL STATEMENT TABULAR RECONSTRUCTION DEMO ===")
    
    # Synthetic OCR bbox result stream
    mock_ocr = [
        ([[40, 100], [120, 100], [120, 120], [40, 120]], "28/08/2026", 0.98),
        ([[150, 102], [350, 102], [350, 120], [150, 120]], "CLOUD HOSTING SERVER", 0.95),
        ([[500, 99], [600, 99], [600, 120], [500, 120]], "-120.50", 0.99),
        ([[40, 140], [120, 140], [120, 160], [40, 160]], "28/08/2026", 0.99),
        ([[150, 138], [350, 138], [350, 160], [150, 160]], "CLIENT PAYMENT INVOICE", 0.97),
        ([[500, 141], [600, 141], [600, 160], [500, 160]], "+3500.00", 0.98)
    ]

    extractor = FinancialTableExtractor(y_threshold=15)
    rows = extractor.cluster_into_rows(mock_ocr)
    ledger = extractor.parse_statement_ledger(rows)

    print("\nStructured Tabular Extraction:\n" + json.dumps(ledger, indent=2))
