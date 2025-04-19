import json
import pandas as pd
import io

def load_categories(path: str = "categories.json") -> dict:
    """Load keyword → category mapping."""
    with open(path) as f:
        return json.load(f)


def load_data(csv_file) -> pd.DataFrame:
    """
    Read a bank CSV, auto-detect the header row by scanning for 'Date' and 'Amount' columns,
    then load and normalize the DataFrame.
    """
    # Read raw text from uploaded file
    raw = csv_file.getvalue()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = raw

    # Preview first 20 rows without header
    preview = pd.read_csv(io.StringIO(text), header=None, nrows=20)

    # Find header row index: look for row containing both 'date' and 'amount'
    header_idx = None
    for idx, row in preview.iterrows():
        cells = row.astype(str).str.lower().str.strip().values
        if "date" in cells and "amount" in cells:
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("Could not auto-detect header row; ensure your CSV has 'Date' and 'Amount' columns.")

    # Load full CSV using detected header row
    df = pd.read_csv(io.StringIO(text), header=header_idx)

    # Normalize column names
    df = df.rename(columns={
        next(col for col in df.columns if str(col).lower().strip().startswith("date")): "Date",
        next(col for col in df.columns if str(col).lower().strip().startswith("desc")): "Description",
        next(col for col in df.columns if str(col).lower().strip().startswith("amt") or str(col).lower().strip().startswith("amount")): "Amount",
    })

    # Drop duplicate-named columns
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Parse Date (coerce & drop invalid rows)
    - Convert Amount to numeric
    """
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    return df


def categorize(df: pd.DataFrame, cats: dict) -> pd.DataFrame:
    """
    Assign a Category to each Description based on keyword matching.
    """
    def find_cat(desc: str):
        text = str(desc).lower()
        for cat, keywords in cats.items():
            if any(kw in text for kw in keywords):
                return cat
        return "Other"

    df["Category"] = df["Description"].astype(str).apply(find_cat)
    return df


def monthly_trends(df: pd.DataFrame) -> pd.Series:
    """Compute total Amount per calendar month."""
    return df.set_index("Date").resample("M")["Amount"].sum().sort_index()


def category_breakdown(df: pd.DataFrame) -> pd.Series:
    """Sum Amount by Category."""
    return df.groupby("Category")["Amount"].sum().sort_values(ascending=False)


def top_merchants(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top-N Descriptions by total Amount spent."""
    return (
        df.groupby("Description")["Amount"]
          .sum()
          .nlargest(n)
          .reset_index(name="Total Spent")
    )
