import streamlit as st
import pandas as pd
import plotly.express as px

from analysis import (
    load_categories,
    load_data,
    clean_data,
    categorize,
    monthly_trends,
    category_breakdown,
    top_merchants,
)

st.set_page_config(page_title="💳 Personal Expense Tracker", layout="wide")
st.title("💳 Personal Expense Tracker")

# 1) File uploader
uploaded = st.file_uploader("Upload your transactions CSV", type="csv")
if not uploaded:
    st.info("Upload a CSV exported from your bank’s portal (must include Date, Description, Amount).")
    st.stop()

# 2) Load & process data
cats = load_categories()            # from categories.json
df   = load_data(uploaded)          # read & rename columns
df   = clean_data(df)               # parse dates & amounts
df   = categorize(df, cats)         # assign Category


# 3) Handle empty / invalid data
if df.empty:
    st.error("No valid transactions found. Please check your CSV and try again.")
    st.stop()

# 4) Date‐range selector (convert to Python dates)
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Date range",
    [min_date, max_date],
    key="date_range"
)

# 5) Filter DataFrame by selected dates
df = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date))
]

# 6) Monthly spending trends
st.header("📈 Monthly Spending")
mt = monthly_trends(df)
fig1 = px.line(
    mt,
    labels={"index": "Month", "value": "Total Spending"},
    title="Total Spent per Month"
)
st.plotly_chart(fig1, use_container_width=True)

# 7) Category breakdown
st.header("🎯 Spending by Category")
cb = category_breakdown(df)
fig2 = px.bar(
    cb,
    x=cb.values,
    y=cb.index,
    orientation="h",
    labels={"x": "Total Spending", "y": "Category"},
    title="Spending by Category"
)
st.plotly_chart(fig2, use_container_width=True)

# 8) Top merchants table
st.header("🏆 Top 10 Merchants")
top10 = top_merchants(df, n=10)
st.table(top10)

# 9) Raw transaction viewer
st.header("📊 Raw Transactions")
st.dataframe(df.sort_values("Date", ascending=False), height=400)
