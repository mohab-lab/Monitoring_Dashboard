# ml/mapper.py
import re

def map_columns(columns):
    mapping = {
        "gender": None,
        "age": None,
        "beneficiary_id": None,
    }

    for col in columns:
        c = col.strip().lower()
        if re.search("gender|sex|النوع|جنس", c):
            mapping["gender"] = col
        elif re.search("age|عمر|سن", c):
            mapping["age"] = col
        elif re.search("id|كود|رقم", c):
            mapping["beneficiary_id"] = col

    return mapping
