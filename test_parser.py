"""Tests for generated parsers."""
import pytest
import pandas as pd
from pathlib import Path
import importlib.util


def test_icici_parser():
    """Test ICICI parser against sample data."""
    # Load expected output
    csv_path = Path("data/icici/icici_sample.csv")
    expected_df = pd.read_csv(csv_path)
    
    # Import generated parser
    parser_path = Path("custom_parsers/icici_parser.py")
    assert parser_path.exists(), "Parser file not found"
    
    spec = importlib.util.spec_from_file_location("icici_parser", parser_path)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    
    # Run parser
    pdf_path = Path("data/icici/icici_sample.pdf")
    result_df = parser.parse(str(pdf_path))
    
    # Compare
    assert result_df.equals(expected_df), f"Output mismatch:\nExpected:\n{expected_df}\n\nGot:\n{result_df}"
    print("✅ Parser test passed!")


if __name__ == "__main__":
    test_icici_parser()