import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# Load ratio data
data_file = Path("data/cleaned/ratios.csv")
df = pd.read_csv(data_file)

# Make sure the charts folder exists
charts_dir = Path("charts")
charts_dir.mkdir(parents=True, exist_ok=True)

print(df)

def create_ratio_chart(column, title, ylabel, filename):
    pivot = df.pivot(
        index="fiscal_year",
        columns="company",
        values=column
    )

    pivot.plot(
        kind="bar",
        figsize=(10, 6)
    )

    plt.title(title)
    plt.xlabel("Fiscal Year")
    plt.ylabel(ylabel)
    plt.xticks(rotation=0)
    plt.legend(title="Company")
    plt.tight_layout()

    output_path = charts_dir / filename

    plt.savefig(
        output_path,
        dpi=300
    )

    plt.close()

    print(f"Saved {output_path}")

create_ratio_chart(
    "debt_to_equity",
    "Debt-to-Equity Ratio by Company",
    "Debt-to-Equity Ratio",
    "debt_to_equity.png"
)

create_ratio_chart(
    "gross_margin",
    "Gross Margin by Company",
    "Gross Margin",
    "gross_margin.png"
)

create_ratio_chart(
    "net_margin",
    "Net Margin by Company",
    "Net Margin",
    "net_margin.png"
)

create_ratio_chart(
    "roe",
    "Return on Equity by Company",
    "Return on Equity",
    "roe.png"
)