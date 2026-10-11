import json
import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Project paths and company files
# --------------------------------------------------

RAW_DATA_DIR = Path("data/raw")
CLEAN_DATA_DIR = Path("data/cleaned")

CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)

company_files = {
    "AAPL": RAW_DATA_DIR / "AAPL_companyfacts.json",
    "MSFT": RAW_DATA_DIR / "MSFT_companyfacts.json",
    "GOOGL": RAW_DATA_DIR / "GOOGL_companyfacts.json",
    "AMZN": RAW_DATA_DIR / "AMZN_companyfacts.json",
    "META": RAW_DATA_DIR / "META_companyfacts.json",
}


# --------------------------------------------------
# Reusable extraction functions
# --------------------------------------------------

def extract_annual_metric(us_gaap, concept_name):
    """
    Extract unique annual period values for an income-statement concept.

    Returns:
        dict mapping fiscal-year-end year -> value
    """

    if concept_name not in us_gaap:
        return {}

    concept = us_gaap[concept_name]

    if "USD" not in concept["units"]:
        return {}

    observations = concept["units"]["USD"]
    annual_values = {}

    for observation in observations:
        if (
            observation.get("form") == "10-K"
            and observation.get("fp") == "FY"
            and observation.get("start")
            and observation.get("end")
        ):
            end_date = observation["end"]
            year = int(end_date[:4])

            # Keep the first unique annual period encountered for the year.
            if year not in annual_values:
                annual_values[year] = observation["val"]

    return annual_values


def extract_point_in_time_metric(us_gaap, concept_name):
    """
    Extract unique fiscal-year-end values for a balance-sheet concept.

    Returns:
        dict mapping fiscal-year-end year -> value
    """

    if concept_name not in us_gaap:
        return {}

    concept = us_gaap[concept_name]

    if "USD" not in concept["units"]:
        return {}

    observations = concept["units"]["USD"]
    values = {}

    for observation in observations:
        if (
            observation.get("form") == "10-K"
            and observation.get("fp") == "FY"
            and observation.get("end")
        ):
            end_date = observation["end"]
            year = int(end_date[:4])

            if year not in values:
                values[year] = observation["val"]

    return values


# --------------------------------------------------
# Load and extract one company's financial metrics
# --------------------------------------------------

def extract_company_metrics(file_path):
    """
    Load one SEC Company Facts JSON file and extract the metrics
    needed for the project.
    """

    with open(file_path, "r") as file:
        data = json.load(file)

    us_gaap = data["facts"]["us-gaap"]

    # Revenue
    revenue = extract_annual_metric(
        us_gaap,
        "RevenueFromContractWithCustomerExcludingAssessedTax",
    )

    # Net income
    net_income = extract_annual_metric(
        us_gaap,
        "NetIncomeLoss",
    )

    # Stockholders' equity
    equity = extract_point_in_time_metric(
        us_gaap,
        "StockholdersEquity",
    )

    # Long-term debt, including current maturities when reported
    # under the combined LongTermDebt concept.
    debt = extract_point_in_time_metric(
        us_gaap,
        "LongTermDebt",
    )

    # Gross profit:
    # Prefer reported GrossProfit when available.
    gross_profit = extract_annual_metric(
        us_gaap,
        "GrossProfit",
    )

    # Possible cost concepts used to calculate gross profit
    cost_concepts = [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    ]

    cost_values = {}

    for concept_name in cost_concepts:
        concept_values = extract_annual_metric(
            us_gaap,
            concept_name,
        )

        for year, value in concept_values.items():
            if year not in cost_values:
                cost_values[year] = value


    # For years without reported GrossProfit,
    # calculate gross profit from revenue and cost.
    for year in revenue:
        if year not in gross_profit and year in cost_values:
            gross_profit[year] = revenue[year] - cost_values[year]
    return {
        "revenue": revenue,
        "gross_profit": gross_profit,
        "net_income": net_income,
        "equity": equity,
        "total_debt": debt,
    }


# --------------------------------------------------
# Extract metrics for all five companies
# --------------------------------------------------

all_company_metrics = {}

for ticker, file_path in company_files.items():
    all_company_metrics[ticker] = extract_company_metrics(file_path)




# --------------------------------------------------
# Determine years that are complete for every company
# --------------------------------------------------

company_complete_years = {}

for ticker, metrics in all_company_metrics.items():

    metric_year_sets = [
        set(metrics["revenue"].keys()),
        set(metrics["gross_profit"].keys()),
        set(metrics["net_income"].keys()),
        set(metrics["equity"].keys()),
        set(metrics["total_debt"].keys()),
    ]

    complete_years = set.intersection(*metric_year_sets)

    company_complete_years[ticker] = complete_years

common_years = set.intersection(*company_complete_years.values())

target_years = sorted(common_years)[-3:]


if len(target_years) < 3:
    raise ValueError(
        "Fewer than three complete fiscal years are shared "
        "across all five companies."
    )


# --------------------------------------------------
# Build the clean 15-row dataset
# --------------------------------------------------

rows = []

for ticker, metrics in all_company_metrics.items():
    for year in target_years:

        row = {
            "company": ticker,
            "fiscal_year": year,
            "revenue": metrics["revenue"].get(year),
            "gross_profit": metrics["gross_profit"].get(year),
            "net_income": metrics["net_income"].get(year),
            "equity": metrics["equity"].get(year),
            "total_debt": metrics["total_debt"].get(year),
        }

        rows.append(row)


df = pd.DataFrame(rows)

df = df.sort_values(
    by=["company", "fiscal_year"]
).reset_index(drop=True)


# --------------------------------------------------
# Validate the dataset
# --------------------------------------------------

expected_rows = len(company_files) * len(target_years)

if len(df) != expected_rows:
    raise ValueError(
        f"Expected {expected_rows} rows, but found {len(df)}."
    )


duplicate_count = df.duplicated(
    subset=["company", "fiscal_year"]
).sum()

if duplicate_count > 0:
    raise ValueError(
        f"Found {duplicate_count} duplicate company/year rows."
    )


if df.isnull().any().any():
    missing = df[df.isnull().any(axis=1)]

    print("\nRows containing missing values:")
    print(missing)

    raise ValueError(
        "Missing financial values were found in the dataset."
    )


# Basic reasonableness checks
financial_columns = [
    "revenue",
    "gross_profit",
    "equity",
    "total_debt",
]

for column in financial_columns:
    if (df[column] < 0).any():
        print(
            f"Warning: negative values found in {column}. "
            "Review these observations manually."
        )


# --------------------------------------------------
# Export the clean dataset
# --------------------------------------------------

output_file = CLEAN_DATA_DIR / "financials.csv"

df.to_csv(output_file, index=False)

# --------------------------------------------------
# Load the clean dataset into SQLite
# --------------------------------------------------

database_file = Path("data/financial_analysis.db")

conn = sqlite3.connect(database_file)

df.to_sql(
    "financials",
    conn,
    if_exists="replace",
    index=False
)

conn.close()


# --------------------------------------------------
# Final summary
# --------------------------------------------------

print("\n=== Dataset Complete ===")
print(f"Target fiscal years: {target_years}")
print(f"Rows created: {len(df)}")
print(f"Saved to: {output_file}")
print(f"SQLite database: {database_file}")

print("\n=== Financial Dataset ===")
print(df)