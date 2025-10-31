import streamlit as st
import pandas as pd
from ml import mapper, anomaly, predictor

# ----- PAGE SETUP -----
st.set_page_config(
    page_title="Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Monitoring Dashboard")
st.markdown("A flexible and simple view for beneficiary data and ML insights")

# ----- SIDEBAR -----
st.sidebar.header("⚙️ Settings")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel file (or leave local data/project_data.xlsx)",
    type=["xlsx"]
)

# ----- LOAD DATA -----
@st.cache_data
def load_data(file):
    if file:
        return pd.read_excel(file)
    else:
        return pd.read_excel("project_data.xlsx")

try:
    data = load_data(uploaded_file)
    st.success("✅ Data loaded successfully")
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# ----- COLUMN MAPPING -----
mapping = mapper.auto_map_columns(data)
gender_col = mapping.get("gender")

# ----- STATS -----
st.subheader("📈 Summary Statistics")

total = len(data)
women = len(data[data[gender_col].str.contains("انث", case=False, na=False)]) if gender_col else 0
men = total - women
pct_women = (women / total * 100) if total > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("إجمالي المستفيدين", total)
with col2:
    st.metric("عدد السيدات", women, f"{pct_women:.1f}%")
with col3:
    st.metric("عدد الرجال", men, f"{100 - pct_women:.1f}%")

# ----- MACHINE LEARNING INSIGHTS -----
st.divider()
st.subheader("🤖 Machine Learning Insights")

predictions = predictor.run_model(data)
anomalies = anomaly.detect(data)

tab1, tab2 = st.tabs(["Predictions", "Anomalies"])
with tab1:
    st.dataframe(predictions.head(10))
with tab2:
    st.dataframe(anomalies.head(10))

# ----- RAW DATA VIEW -----
st.divider()
st.subheader("🧾 Raw Data Preview")
st.dataframe(data.head(15))
