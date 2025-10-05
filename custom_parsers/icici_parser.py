import pandas as pd
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
