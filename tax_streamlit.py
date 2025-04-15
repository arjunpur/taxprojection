import streamlit as st
import pandas as pd

# -------------------------------
# Helper Functions for Tax Computations
# -------------------------------

def compute_federal_tax(taxable_income):
    """
    Compute regular federal income tax (for single filers) using marginal tax brackets.
    Assumptions (approximations):
      - 10% on first $11,000
      - 12% on next $33,725   (income from $11,001 to $44,725)
      - 22% on next $50,650   (income from $44,726 to $95,375)
      - 24% on next $86,725   (income from $95,376 to $182,100)
      - 32% on next $49,150   (income from $182,101 to $231,250)
      - 35% on next $346,875  (income from $231,251 to $578,125)
      - 37% on any income above $578,125
    A standard deduction of $14,000 is assumed before this function is called.
    """
    brackets = [
        (11000, 0.10),
        (44725, 0.12),
        (95375, 0.22),
        (182100, 0.24),
        (231250, 0.32),
        (578125, 0.35)
    ]
    top_rate = 0.37
    tax = 0.0
    lower_limit = 0.0

    for bracket_limit, rate in brackets:
        if taxable_income > bracket_limit:
            taxable_slice = bracket_limit - lower_limit
            tax += taxable_slice * rate
            lower_limit = bracket_limit
        else:
            taxable_slice = taxable_income - lower_limit
            tax += taxable_slice * rate
            return tax
    if taxable_income > lower_limit:
        tax += (taxable_income - lower_limit) * top_rate
    return tax

def compute_amt_tax(amt_income):
    """
    Compute a rough AMT tax.
    Assumptions:
      - AMT exemption: $81,000 (for illustration)
      - Tax 26% on income up to $200,000 (after the exemption), then 28% thereafter.
    """
    threshold = 200000.0
    if amt_income <= 0:
        return 0.0
    if amt_income <= threshold:
        return amt_income * 0.26
    else:
        return threshold * 0.26 + (amt_income - threshold) * 0.28

def compute_ca_tax(taxable_income):
    """
    Compute California state income tax (for a single filer) using progressive tax brackets.
    Based on the approximate 2022-2023 brackets for single filers:
      - 1% on the first $9,324
      - 2% on income between $9,325 and $22,107
      - 4% on income between $22,108 and $34,892
      - 6% on income between $34,893 and $48,435
      - 8% on income between $48,436 and $61,215
      - 9.3% on income between $61,216 and $312,686
      - 10.3% on income between $312,687 and $375,221
      - 11.3% on income between $375,222 and $625,369
      - 12.3% on income above $625,369
    These brackets are applied incrementally. Returns the total CA tax liability before any credits.
    """
    brackets = [
        (9324, 0.01),
        (22107, 0.02),
        (34892, 0.04),
        (48435, 0.06),
        (61215, 0.08),
        (312686, 0.093),
        (375221, 0.103),
        (625369, 0.113)
    ]
    top_rate = 0.123  # for taxable income above the last bracket cutoff
    tax = 0.0
    lower_limit = 0.0

    for bracket_limit, rate in brackets:
        if taxable_income > bracket_limit:
            taxable_slice = bracket_limit - lower_limit
            tax += taxable_slice * rate
            lower_limit = bracket_limit
        else:
            taxable_slice = taxable_income - lower_limit
            tax += taxable_slice * rate
            return tax
    if taxable_income > lower_limit:
        tax += (taxable_income - lower_limit) * top_rate
    return tax

# -------------------------------
# Main Streamlit App
# -------------------------------
st.title("2026 Tax Projection Dashboard")
st.markdown("""
This dashboard projects your 2026 tax liability based on three key 2025 events:
1. **Double-Trigger RSUs:** RSUs vest and are taxed as ordinary income with a 37% withholding.
2. **ISO Exercise:** ISOs could be exercised. The ISO bargain element is computed as (FMV − Option Strike Price) and is added for AMT purposes.
3. **Regular Income:** Your wages (outside RSU proceeds) are subject to 22% federal withholding.

For California, tax is computed using progressive brackets, with CA withholding at 10.23%.
Additionally, you may enter Federal and CA AMT Credits to reduce your tax liability.
*All calculations are based on simplified assumptions for demonstration purposes.*
""")

# Sidebar Inputs
st.sidebar.header("Input Variables")
regular_income = st.sidebar.number_input("Enter your Regular Income for 2025 ($)", min_value=0.0, value=0.0, step=1000.0)
rsu_count = st.sidebar.number_input("Enter the total number of RSUs being taxed", min_value=0, value=0, step=1)
iso_count = st.sidebar.number_input("Enter the total number of ISOs being exercised", min_value=0, value=0, step=1)

# Use a single FMV for both RSUs and ISOs
fmv = st.sidebar.number_input("Enter the Fair Market Value (FMV) for RSUs and ISOs ($)", min_value=0.0, value=0.0, step=1.0)

# For ISOs, we also need the option strike price.
iso_strike_price = st.sidebar.number_input("Enter the Option Strike Price per ISO ($)", min_value=0.0, value=0.0, step=1.0)

# Available AMT Credits
amt_credit = st.sidebar.number_input("Enter your available Federal AMT Credit ($)", min_value=0.0, value=0.0, step=100.0)
ca_amt_credit = st.sidebar.number_input("Enter your available CA AMT Credit Carryover ($)", min_value=0.0, value=0.0, step=100.0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Assumptions:**")
st.sidebar.markdown("- Federal standard deduction: $14,000")
st.sidebar.markdown("- Federal tax brackets as approximated for a single filer")
st.sidebar.markdown("- Federal AMT exemption: $81,000; AMT rates: 26% up to $200K, 28% thereafter")
st.sidebar.markdown("- California standard deduction: $5,000")
st.sidebar.markdown("- Progressive CA tax brackets based on approximate 2022-2023 rates")
st.sidebar.markdown("- CA wages withholding at 10.23% (with 1 allowance)")
st.sidebar.markdown("- ISO bargain element = FMV − Option Strike Price")

# -------------------------------
# Calculations
# -------------------------------

# RSU and ISO Income Calculations using FMV
rsu_income = rsu_count * fmv

# ISO bargain element: if FMV exceeds the strike price, else 0.
iso_bargain_element = max(0, fmv - iso_strike_price)
iso_adjustment = iso_count * iso_bargain_element

# -- Federal Calculations --
# Regular taxable income excludes the ISO adjustment, per qualifying ISO rules.
federal_standard_deduction = 14000.0
federal_taxable_income = max(0, (regular_income + rsu_income) - federal_standard_deduction)
regular_federal_tax = compute_federal_tax(federal_taxable_income)

# AMT taxable income includes the ISO bargain element.
amt_exemption = 81000.0
amt_income = max(0, (regular_income + rsu_income + iso_adjustment) - amt_exemption)
amt_tax = compute_amt_tax(amt_income)

# Additional Federal Tax arises if AMT exceeds regular tax (after available AMT credit).
additional_federal_tax = max(0, amt_tax - amt_credit - regular_federal_tax)
total_federal_tax = regular_federal_tax + additional_federal_tax

# Federal withholding: 22% on regular income; 37% on RSU income.
withholding_regular = regular_income * 0.22
withholding_rsu = rsu_income * 0.37
federal_withholding = withholding_regular + withholding_rsu
additional_federal_due = total_federal_tax - federal_withholding

# -- California State Calculations --
# CA taxable income = (regular income + RSU income + ISO adjustment) minus a $5,000 standard deduction.
ca_standard_deduction = 5000.0
ca_taxable_income = max(0, (regular_income + rsu_income + iso_adjustment) - ca_standard_deduction)
ca_tax_liability = compute_ca_tax(ca_taxable_income)
# Apply CA AMT Credit Carryover
ca_tax_liability_after_credit = max(0, ca_tax_liability - ca_amt_credit)

# CA withholding is on wages (regular income + RSU income) at 10.23%
ca_withholding = (regular_income + rsu_income) * 0.1023
additional_state_due = ca_tax_liability_after_credit - ca_withholding

# -------------------------------
# Organize Output Data for Clear Presentation
# -------------------------------

federal_data = {
    "Description": [
        "Regular Federal Tax",
        "Tentative AMT Tax (including ISO adjustment)",
        "Federal AMT Credit Utilized",
        "Additional Federal Tax (from AMT)",
        "Total Federal Tax Liability",
        "Federal Withholding",
        "Additional Federal Tax Due (or refund negative)"
    ],
    "Amount ($)": [
        f"{regular_federal_tax:,.2f}",
        f"{amt_tax:,.2f}",
        f"{amt_credit:,.2f}",
        f"{additional_federal_tax:,.2f}",
        f"{total_federal_tax:,.2f}",
        f"{federal_withholding:,.2f}",
        f"{additional_federal_due:,.2f}"
    ]
}

ca_data = {
    "Description": [
        "CA Taxable Income",
        "CA Tax Liability (before credit)",
        "CA AMT Credit Carryover",
        "CA Tax Liability (after credit)",
        "CA Withholding (10.23%)",
        "Additional CA Tax Due (or refund negative)"
    ],
    "Amount ($)": [
        f"{ca_taxable_income:,.2f}",
        f"{ca_tax_liability:,.2f}",
        f"{ca_amt_credit:,.2f}",
        f"{ca_tax_liability_after_credit:,.2f}",
        f"{ca_withholding:,.2f}",
        f"{additional_state_due:,.2f}"
    ]
}

overall_data = {
    "Description": ["Total Additional Tax Payment Required in 2026"],
    "Amount ($)": [f"{(additional_federal_due + additional_state_due):,.2f}"]
}

# -------------------------------
# Results Display
# -------------------------------
st.header("Summary of Calculations")

st.subheader("Federal Tax Summary")
st.table(pd.DataFrame(federal_data))

st.subheader("California State Tax Summary")
st.table(pd.DataFrame(ca_data))

st.subheader("Overall Tax Impact")
st.table(pd.DataFrame(overall_data))

st.markdown("""
---
**Disclaimer:** This tool is based on simplified assumptions and illustrative rates for demonstration purposes.  
Actual tax computations are more complex and depend on numerous factors (deductions, credits, filing status, actual AMT rules, etc.).  
Please consult a tax professional for accurate tax projections.
""")