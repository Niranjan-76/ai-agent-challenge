#!/usr/bin/env python3
"""
Local fallback parser agent for ICICI bank PDFs.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import pandas as pd
import importlib.util
import pdfplumber

# -----------------------------
# ParserAgent class
# -----------------------------
class ParserAgent:
    """Agent that generates and tests PDF parsers locally."""
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.memory = []

    def test_parser(self, parser_path: Path, pdf_path: Path, expected_df: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """Test a parser module dynamically."""
        try:
            spec = importlib.util.spec_from_file_location("parser", parser_path)
            parser_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser_module)
            result_df = parser_module.parse(str(pdf_path))

            if result_df.equals(expected_df):
                return True, None
            else:
                error_parts = [
                    f"Column mismatch: Expected {list(expected_df.columns)}, Got {list(result_df.columns)}",
                    f"Shape mismatch: Expected {expected_df.shape}, Got {result_df.shape}",
                    f"\nExpected DataFrame:\n{expected_df.head(5).to_string()}",
                    f"\nActual DataFrame:\n{result_df.head(5).to_string()}"
                ]
                return False, "\n".join(error_parts)

        except Exception as e:
            import traceback
            return False, f"Exception: {type(e).__name__}: {str(e)}\nTraceback:\n{traceback.format_exc()}"

    def run(self, bank_name: str, data_dir: Path, output_dir: Path) -> bool:
        print(f"🤖 Starting agent for {bank_name} bank...")

        pdf_path = data_dir / f"{bank_name}_sample.pdf"
        csv_path = data_dir / f"{bank_name}_sample.csv"
        parser_path = output_dir / f"{bank_name}_parser.py"

        if not pdf_path.exists() or not csv_path.exists():
            print(f"❌ Missing files in {data_dir}")
            return False

        expected_df = pd.read_csv(csv_path)

        # Write a valid parser file
        parser_code = '''import pandas as pd
import pdfplumber

def parse(pdf_path: str) -> pd.DataFrame:
    columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                if len(table) < 2:
                    continue
                header = table[0]
                for row in table[1:]:
                    if row == header or row == columns or all(cell is None or str(cell).strip() == "" for cell in row):
                        continue

                    while len(row) < 5:
                        row.append("")

                    clean_row = []
                    for i, cell in enumerate(row):
                        val = str(cell).strip() if cell is not None else ""
                        if i in [2,3,4]:
                            try:
                                val = float(val.replace(",", "")) if val else 0.0
                            except ValueError:
                                val = 0.0
                        clean_row.append(val)
                    all_rows.append(clean_row)

    df = pd.DataFrame(all_rows, columns=columns)
    return df
'''
        parser_path.write_text(parser_code)
        print(f"💾 Saved fallback parser to {parser_path}")

        success, error_msg = self.test_parser(parser_path, pdf_path, expected_df)
        if success:
            print("✅ Parser works correctly!")
            return True
        else:
            print(f"❌ Test failed:\n{error_msg}")
            return False

# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate bank statement parsers locally")
    parser.add_argument("--target", required=True, help="Bank name (e.g., icici)")
    args = parser.parse_args()

    bank_name = args.target.lower()
    data_dir = Path("data") / bank_name
    output_dir = Path("custom_parsers")
    output_dir.mkdir(exist_ok=True)

    agent = ParserAgent(max_iterations=3)
    success = agent.run(bank_name, data_dir, output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
