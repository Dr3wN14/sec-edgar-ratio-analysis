SELECT
    company,
    fiscal_year,

    ROUND(
        total_debt * 1.0 / NULLIF(equity, 0),
        3
    ) AS debt_to_equity,

    ROUND(
        gross_profit * 1.0 / NULLIF(revenue, 0),
        3
    ) AS gross_margin,

    ROUND(
        net_income * 1.0 / NULLIF(revenue, 0),
        3
    ) AS net_margin,

    ROUND(
        net_income * 1.0 / NULLIF(equity, 0),
        3
    ) AS roe

FROM financials

ORDER BY company, fiscal_year;