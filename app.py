# app.py - improved diagnostics + manual mapping + robust gender detection
import streamlit as st
import pandas as pd
import os
import re
from ml import mapper, anomaly

st.set_page_config(page_title="لوحة متابعة المشروع (debuggable)", layout="wide")
st.title("📊 لوحة متابعة المشروع — Debug & Robust Detection")

# ---------- helpers ----------
ARABIC_NORMALIZE_MAP = {
    '\u0622':'ا', '\u0623':'ا', '\u0625':'ا', '\u0629':'ه', '\u0649':'ي',
    '\u0671':'ا'
}
ZERO_WIDTH = ['\u200f', '\u200e', '\u200b']

def normalize_arabic_text(s):
    if pd.isna(s):
        return ""
    s = str(s)
    # remove zero-width characters
    for zw in ZERO_WIDTH:
        s = s.replace(zw, "")
    s = s.strip()
    s = s.lower()
    # normalize letters
    for k, v in ARABIC_NORMALIZE_MAP.items():
        s = s.replace(k, v)
    # replace punctuation with space
    s = re.sub(r'[^\w\s٪%\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

FEMALE_TOKENS = ["انثى", "انث", "انثآ", "انثـ", "سيدة", "سيدات", "امرأة", "امراة", "female", "f"]

MISSING_VALS = set(["", "na", "n/a", "none", "nan", "-", "0", "غير متوفر", "غيرمتوفر", "غير متاحة"])

def is_female_value(v):
    s = normalize_arabic_text(v)
    if s in MISSING_VALS:
        return False
    # direct token match
    for t in FEMALE_TOKENS:
        if t in s:
            return True
    # sometimes gender stored as single letter 'f' or 'F'
    if s.strip().lower() in ("f", "f.", "f/"):
        return True
    return False

# ---------- load file ----------
uploaded = st.file_uploader("Upload Excel file (or leave local data/project_data.xlsx)", type=["xlsx"])
local_path = os.path.join("data", "project_data.xlsx")
if uploaded:
    file_path = uploaded
elif os.path.exists(local_path):
    file_path = local_path
else:
    st.info("Please upload an Excel file or place project_data.xlsx into data/")
    st.stop()

xls = pd.ExcelFile(file_path)
sheets = xls.sheet_names
sheet = st.sidebar.selectbox("Select sheet", sheets)
df = pd.read_excel(file_path, sheet_name=sheet)

# sanitize column names
df.columns = df.columns.astype(str).str.strip().str.replace('\u200f','').str.replace('\u200e','')

st.write("### Detected columns")
st.write(list(df.columns))

# auto-map using ml.mapper
col_map = mapper.map_columns(df.columns)
st.write("### Auto column map suggestion")
st.json(col_map)

# Allow manual override for gender column (critical)
candidate_gender_cols = [c for c in df.columns]
chosen_gender_col = st.sidebar.selectbox("Select GENDER column (override)", options=["(auto)"] + candidate_gender_cols, index=0)

if chosen_gender_col == "(auto)":
    gender_col = col_map.get("gender")
    if gender_col not in df.columns:
        gender_col = None
else:
    gender_col = chosen_gender_col

st.write("**Using gender column:**", gender_col)

# show distinct sample values and counts for the chosen (or candidate) gender column(s)
st.write("### Gender column diagnostics")
diag_cols = []
if gender_col:
    diag_cols = [gender_col]
else:
    # show top 3 likely columns by fuzzy mapping heuristic
    diag_cols = [c for c in df.columns][:3]

for c in diag_cols:
    st.write(f"Column: `{c}`")
    # show value counts (top 30)
    try:
        vc = df[c].astype(str).map(lambda x: normalize_arabic_text(x)).value_counts(dropna=False)
        st.write(vc.head(30))
    except Exception as e:
        st.write("Could not compute value counts:", e)

# compute women count using robust matcher, with diagnostics
if gender_col and gender_col in df.columns:
    # normalize column to strings
    values = df[gender_col].astype(str).apply(normalize_arabic_text)
    # treat certain placeholders as missing
    values = values.map(lambda x: "" if x in MISSING_VALS else x)

    df["_is_female"] = values.apply(lambda v: is_female_value(v))
    women_count = int(df["_is_female"].sum())
    total = df.shape[0]
    female_pct = round((women_count / total) * 100, 2) if total > 0 else 0

    st.metric("Women count (detected)", women_count, f"{female_pct}% of rows")
    st.write("Examples of values detected as female (unique):")
    st.write(sorted(set(values[df["_is_female"]].unique()) )[:40])

    st.write("Examples of non-empty values NOT detected as female (these might be variants):")
    # non-empty and not female
    not_female_vals = [v for v in set(values.unique()) if v and not is_female_value(v)]
    st.write(sorted(not_female_vals)[:40])

else:
    st.warning("No gender column selected/found. Please choose one from the sidebar override.")

# additional tips and fixes
st.markdown("---")
st.subheader("Quick fixes & recommendations")
st.write("""
- If the gender column shows values like `0` or empty cells for women, fix the source Excel:
  - Replace `0` with blank or with `أنثى` /`ذكر`.
  - Ensure the column is text-formatted, not numeric.
- If you see variations like `انثى` / `أنث` / `سيدة`, we already match them — but if you have other words, copy one example from the 'non-detected' list above and paste it below to add to detection tokens.
""")

# allow user to add custom female token
custom_token = st.text_input("Add custom token/word that should count as female (e.g. 'ست')", value="")
if custom_token:
    FEMALE_TOKENS.append(normalize_arabic_text(custom_token))
    st.success(f"Token '{custom_token}' added to female detection list. Re-run to apply.")

# final download of the df with detection column
if "_is_female" in df.columns:
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("Download CSV with _is_female column", data=csv, file_name=f"{sheet}_with_female_flag.csv", mime="text/csv")

st.info("If results are still incorrect, please paste a small sample (5-10 rows) of the problematic sheet here and I will analyze the exact values and provide a tuned rule.")
