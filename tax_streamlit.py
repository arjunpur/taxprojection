import streamlit as st
import pandas as pd

# -------------------------------
# Helper Functions for Tax Computations
# -------------------------------

def compute_federal_tax(taxable_income, is_married=False):
    """
    Compute regular federal income tax using marginal tax brackets.
    For simplicity, we use approximate bracket thresholds.
    
    Single Filer (approximate):
      - 10%:      $0 – $11,000
      - 12%:  $11,001 – $44,725
      - 22%:  $44,726 – $95,375
      - 24%:  $95,376 – $182,100
      - 32%: $182,101 – $231,250
      - 35%: $231,251 – $647,850 (approx)
      - 37%: above $647,850
      
    Married Filing Jointly (approximate 2022 numbers):
      - 10%:      $0 – $20,550
      - 12%:  $20,551 – $83,550
      - 22%:  $83,551 – $178,150
      - 24%: $178,151 – $340,100
      - 32%: $340,101 – $431,900
      - 35%: $431,901 – $647,850
      - 37%: above $647,850
    """
    if is_married:
        brackets = [
            (20550, 0.10),
            (83550, 0.12),
            (178150, 0.22),
            (340100, 0.24),
            (431900, 0.32),
            (647850, 0.35)
        ]
        top_rate = 0.37
    else:
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
    Compute a simplified version of the Alternative Minimum Tax.
    Assumptions:
      - If single: AMT exemption is $81,000; if married: $126,500 (approximate values).
      - Tax 26% on AMT income (post exemption) up to $200,000, then 28% thereafter.
      (Note: Actual AMT calculations involve more adjustments and phaseouts.)
    """
    threshold = 200000.0
    if amt_income <= 0:
        return 0.0
    if amt_income <= threshold:
        return amt_income * 0.26
    else:
        return threshold * 0.26 + (amt_income - threshold) * 0.28

def compute_ca_tax(taxable_income, is_married=False):
    """
    Compute California state income tax using progressive tax brackets.
    For single filers (approximate 2022-2023):
      - 1% on the first $9,324
      - 2%: $9,325 – $22,107
      - 4%: $22,108 – $34,892
      - 6%: $34,893 – $48,435
      - 8%: $48,436 – $61,215
      - 9.3%: $61,216 – $312,686
      - 10.3%: $312,687 – $375,221
      - 11.3%: $375,222 – $625,369
      - 12.3% above $625,369
      
    For married filing jointly, thresholds are typically higher. Here we approximate by nearly doubling the single thresholds:
      - 1% on the first $18,650
      - 2%: $18,651 – $44,214
      - 4%: $44,215 – $69,784
      - 6%: $69,785 – $96,870
      - 8%: $96,871 – $122,430
      - 9.3%: $122,431 – $625,372
      - 10.3%: $625,373 – $750,442
      - 11.3%: $750,443 – $1,250,738
      - 12.3% above $1,250,738
    """
    if is_married:
        brackets = [
            (18650, 0.01),
            (44214, 0.02),
            (69784, 0.04),
            (96870, 0.06),
            (122430, 0.08),
            (625372, 0.093),
            (750442, 0.103),
            (1250738, 0.113)
        ]
        top_rate = 0.123
    else:
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
        top_rate = 0.123

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
2. **ISO Exercise:** ISOs are exercised. The ISO bargain element is computed as (FMV − Option Strike Price) and is applied for AMT purposes.
3. **Regular Income:** Your wages (outside RSU proceeds) are subject to 22% federal withholding.

For California, tax is computed using progressive brackets, with CA withholding at 10.23%.
Additionally, input your Federal and CA AMT Credits to reduce tax liability.

*All calculations are based on simplified assumptions for demonstration purposes.*
""")

# Sidebar Inputs
st.sidebar.header("Input Variables")
is_married = st.sidebar.checkbox("Are you married? (Married Filing Jointly)", value=False)

regular_income = st.sidebar.number_input("Enter your Regular Income for 2025 ($)", min_value=0.0, value=0.0, step=1000.0)
rsu_count = st.sidebar.number_input("Enter the total number of RSUs being taxed", min_value=0, value=0, step=1)
iso_count = st.sidebar.number_input("Enter the total number of ISOs being exercised", min_value=0, value=0, step=1)

# Use a single FMV for both RSUs and ISOs
fmv = st.sidebar.number_input("Enter the Fair Market Value (FMV) for RSUs and ISOs ($)", min_value=0.0, value=0.0, step=1.0)

# For ISOs, provide the option strike price.
iso_strike_price = st.sidebar.number_input("Enter the Option Strike Price per ISO ($)", min_value=0.0, value=0.0, step=1.0)

# Available AMT Credits
amt_credit = st.sidebar.number_input("Enter your available Federal AMT Credit ($)", min_value=0.0, value=0.0, step=100.0)
ca_amt_credit = st.sidebar.number_input("Enter your available CA AMT Credit Carryover ($)", min_value=0.0, value=0.0, step=100.0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Assumptions:**")
if is_married:
    st.sidebar.markdown("- Filing Status: Married Filing Jointly")
    st.sidebar.markdown("- Federal standard deduction: $28,000")
    st.sidebar.markdown("- Federal AMT exemption: $126,500")
    st.sidebar.markdown("- CA standard deduction: $10,000")
else:
    st.sidebar.markdown("- Filing Status: Single")
    st.sidebar.markdown("- Federal standard deduction: $14,000")
    st.sidebar.markdown("- Federal AMT exemption: $81,000")
    st.sidebar.markdown("- CA standard deduction: $5,000")
st.sidebar.markdown("- FMV used for both RSUs and ISOs")
st.sidebar.markdown("- ISO bargain element = FMV – Option Strike Price")
st.sidebar.markdown("- CA wages withholding at 10.23%")

# -------------------------------
# Calculations
# -------------------------------

# RSU and ISO Income Calculations using FMV
rsu_income = rsu_count * fmv

# ISO bargain element: if FMV exceeds the strike price, else 0.
iso_bargain_element = max(0, fmv - iso_strike_price)
iso_adjustment = iso_count * iso_bargain_element

# -- Federal Calculations --
# Set federal standard deduction and AMT exemption based on filing status.
if is_married:
    federal_standard_deduction = 28000.0
    amt_exemption = 126500.0
else:
    federal_standard_deduction = 14000.0
    amt_exemption = 81000.0

# Regular taxable income excludes the ISO adjustment (for a qualifying ISO exercise).
federal_taxable_income = max(0, (regular_income + rsu_income) - federal_standard_deduction)
regular_federal_tax = compute_federal_tax(federal_taxable_income, is_married)

# AMT taxable income includes the ISO bargain element.
amt_income = max(0, (regular_income + rsu_income + iso_adjustment) - amt_exemption)
amt_tax = compute_amt_tax(amt_income)

# Additional Federal Tax arises if tentative AMT (net of Federal AMT credit) exceeds regular tax.
additional_federal_tax = max(0, amt_tax - amt_credit - regular_federal_tax)
total_federal_tax = regular_federal_tax + additional_federal_tax

# Federal withholding: 22% on regular income; 37% on RSU income.
withholding_regular = regular_income * 0.22
withholding_rsu = rsu_income * 0.37
federal_withholding = withholding_regular + withholding_rsu
additional_federal_due = total_federal_tax - federal_withholding

# -- California State Calculations --
# Determine CA standard deduction based on filing status.
if is_married:
    ca_standard_deduction = 10000.0
else:
    ca_standard_deduction = 5000.0

# CA taxable income = (regular income + RSU income + ISO adjustment) - CA standard deduction.
ca_taxable_income = max(0, (regular_income + rsu_income + iso_adjustment) - ca_standard_deduction)
ca_tax_liability = compute_ca_tax(ca_taxable_income, is_married)
# Apply CA AMT Credit Carryover.
ca_tax_liability_after_credit = max(0, ca_tax_liability - ca_amt_credit)

# CA withholding is on wages (regular income + RSU income) at 10.23%.
ca_withholding = (regular_income + rsu_income) * 0.1023
additional_state_due = ca_tax_liability_after_credit - ca_withholding

# -------------------------------
# Organize Output Data for Clear Presentation
# -------------------------------
federal_data = {
    "Description": [
        "Regular Federal Tax",
        "Tentative AMT Tax (incl. ISO adjustment)",
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
Actual tax computations are more complex and depend on numerous factors (deductions, credits, filing status, AMT rules, etc.).  
Please consult a tax professional for accurate tax projections.
""")