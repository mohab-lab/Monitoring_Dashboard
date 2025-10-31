# ==============================================
# 📘 predictor.py
# ==============================================
# This file handles light ML-based predictions
# and smart data cleaning for your monitoring dashboard.
# It focuses on fixing or predicting missing/inconsistent
# values in key columns like gender, social support,
# and special needs.
# ==============================================

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import re


# ------------------------------------------------------
# 🧩 1. Helper: Clean and normalize Arabic text
# ------------------------------------------------------
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    replacements = {
        "أنثى": "انثي",
        "انثى": "انثي",
        "ذكر ": "ذكر",
        "  ": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


# ------------------------------------------------------
# 🧠 2. Predict missing genders using RandomForestClassifier
# ------------------------------------------------------
def predict_missing_gender(df):
    if "الجنس" not in df.columns:
        return df

    df["الجنس"] = df["الجنس"].apply(clean_text)

    # Encode gender
    label_encoder = LabelEncoder()
    valid_genders = df["الجنس"].dropna().unique()

    if len(valid_genders) < 2:
        # Not enough data to train model
        return df

    df_encoded = df.copy()

    # Choose numeric features that can be correlated with gender
    feature_cols = [col for col in df.columns if df[col].dtype != 'object' and df[col].notna().any()]
    feature_cols = [c for c in feature_cols if c != "الجنس"]

    if not feature_cols:
        return df  # no numeric features to train with

    # Prepare train/test data
    train = df_encoded[df_encoded["الجنس"].notna()]
    test = df_encoded[df_encoded["الجنس"].isna()]

    if train.empty or test.empty:
        return df  # nothing to predict

    X_train = train[feature_cols]
    y_train = label_encoder.fit_transform(train["الجنس"])
    X_test = test[feature_cols]

    try:
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        df.loc[df["الجنس"].isna(), "الجنس"] = label_encoder.inverse_transform(predicted)
    except Exception:
        pass

    return df


# ------------------------------------------------------
# ♿ 3. Fix invalid ID numbers and phone numbers
# ------------------------------------------------------
def fix_id_and_phone(df):
    if "الرقم القومي" in df.columns:
        df["الرقم القومي"] = df["الرقم القومي"].astype(str).apply(
            lambda x: x if re.fullmatch(r"\d{14}", x) else None
        )

    if "رقم التليفون" in df.columns:
        df["رقم التليفون"] = df["رقم التليفون"].astype(str).apply(
            lambda x: x if re.fullmatch(r"01\d{9}", x) else None
        )

    return df


# ------------------------------------------------------
# 💡 4. Predict or fix 'الصفة' (social role)
# ------------------------------------------------------
def fix_social_status(df):
    status_cols = ["تكافل أو كرامة", "ذوي احتياجات", "أخري"]
    for col in status_cols:
        if col not in df.columns:
            df[col] = 0

    # if all NaN, fill with 0
    df[status_cols] = df[status_cols].fillna(0)

    # Convert text flags to numeric
    for col in status_cols:
        df[col] = df[col].apply(lambda x: 1 if str(x).strip() not in ["", "0", "nan", "None"] else 0)

    return df


# ------------------------------------------------------
# 🚀 5. Main ML cleaning function
# ------------------------------------------------------
def auto_clean(df: pd.DataFrame):
    """
    Runs all prediction and cleaning steps in order.
    """
    df = df.copy()
    df = fix_id_and_phone(df)
    df = fix_social_status(df)
    df = predict_missing_gender(df)
    return df
