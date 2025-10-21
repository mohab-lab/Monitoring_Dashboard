import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ============= PAGE SETUP =============
st.set_page_config(page_title="لوحة متابعة المشروع الزراعي", layout="wide")
st.title("📊 لوحة المتابعة - مدارس المزارعين و إدارة الأعمال الزراعية")
st.markdown("### تحديث مباشر من ملفات Excel متعددة")

# ============= FILE UPLOAD =============
st.sidebar.header("📁 تحميل ملف البيانات")
uploaded_file = st.sidebar.file_uploader("اختر ملف Excel", type=["xlsx"])

if uploaded_file is None:
    st.info("⬆️ يرجى تحميل ملف Excel يحتوي على الأوراق الأربعة المطلوبة.")
    st.stop()

# ============= LOAD EXCEL SHEETS =============
try:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    st.sidebar.success(f"تم تحميل الملف بنجاح ✅ \n\nالأوراق: {sheet_names}")
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل الملف: {e}")
    st.stop()

# ============= SELECT SHEET =============
selected_sheet = st.sidebar.selectbox("اختر الورقة", sheet_names)
df = pd.read_excel(xls, selected_sheet)

# ============= CLEAN DATA =============
df.columns = df.columns.str.strip()
if "الرقم القومي" not in df.columns or "رقم التليفون" not in df.columns:
    st.error("يجب أن يحتوي الملف على الأعمدة: الرقم القومي و رقم التليفون.")
    st.stop()

# ============= KPIs CALCULATION =============
total_beneficiaries = df["الرقم القومي"].nunique()

# نسبة السيدات
if "الجنس" in df.columns:
    women_count = df[df["الجنس"].str.contains("أنثى", na=False)].shape[0]
    women_percent = (women_count / total_beneficiaries) * 100
else:
    women_count = women_percent = 0

# ذوي الاحتياجات
special_needs = 0
for col in df.columns:
    if "ذوي احتياجات" in col:
        special_needs += df[col].notna().sum()
special_needs_percent = (special_needs / total_beneficiaries) * 100 if total_beneficiaries else 0

# القرى
village_counts = df["القرية"].value_counts() if "القرية" in df.columns else pd.Series()

# تكافل وكرامة
takaful_count = 0
for col in df.columns:
    if "تكافل" in col:
        takaful_count += df[col].notna().sum()

# ============= DISPLAY KPI BOXES =============
st.subheader(f"📄 نظرة عامة: {selected_sheet}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("إجمالي المستفيدين", total_beneficiaries)
col2.metric("عدد السيدات", women_count, f"{women_percent:.1f}%")
col3.metric("ذوي الاحتياجات", special_needs, f"{special_needs_percent:.1f}%")
col4.metric("مستفيدو تكافل وكرامة", takaful_count)

# ============= GRAPHS =============
st.markdown("### 📍 عدد المستفيدين لكل قرية")
if not village_counts.empty:
    fig = px.bar(village_counts, x=village_counts.index, y=village_counts.values,
                 color=village_counts.values, title="عدد المستفيدين حسب القرية",
                 labels={"x": "القرية", "y": "عدد المستفيدين"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⚠️ لا توجد بيانات عن القرى في هذه الورقة.")

# ============= DOWNLOAD CLEANED DATA =============
st.sidebar.download_button(
    label="⬇️ تحميل البيانات المعالجة",
    data=df.to_csv(index=False).encode('utf-8-sig'),
    file_name=f"{selected_sheet}_cleaned.csv",
    mime="text/csv"
)

st.success("✅ تم تحديث لوحة المتابعة بنجاح! يمكنك اختيار ورقة أخرى أو تحميل ملف جديد.")
