import streamlit as st
import pandas as pd

st.set_page_config(page_title="RAYS Attribution", layout="wide")

st.title("RAYS Capital Attribution Dashboard")

st.subheader("March Attribution Snapshot")

data = {
    "Category": [
        "Long",
        "Short",
        "Box",
        "Forward",
        "Other",
        "Mgmt Fee & Other Monthly Fees",
        "Overall Official Return"
    ],
    "Percent": [
        "-4.18%",
        "0.36%",
        "0.00%",
        "0.00%",
        "0.00%",
        "2.59%",
        "-1.23%"
    ]
}

df = pd.DataFrame(data)

st.dataframe(df, use_container_width=True)

st.bar_chart(df.set_index("Category"))