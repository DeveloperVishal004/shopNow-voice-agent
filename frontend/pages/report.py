import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://localhost:8000"

def show():
    st.title("Daily Operations Report")
    st.markdown(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    st.markdown("---")

    try:
        response = requests.get(f"{API_BASE}/report/daily")
        data = response.json()
    except:
        st.error("Could not connect to backend")
        return

    st.subheader("Summary")
    st.markdown(f"- Total calls     : **{data.get('total_calls', 0)}**")
    st.markdown(f"- Resolved        : **{data.get('resolved_calls', 0)}**")
    st.markdown(f"- Escalated       : **{data.get('escalated_calls', 0)}**")
    st.markdown(f"- FCR rate        : **{data.get('fcr_percent', 0)}%**")
    st.markdown(f"- Avg sentiment   : **{data.get('avg_sentiment', 0):.2f}**")

    st.markdown("---")
    st.subheader("Calls by intent")
    intent_data = data.get("calls_by_intent", {})
    if intent_data:
        df = pd.DataFrame({
            "Intent": list(intent_data.keys()),
            "Calls":  list(intent_data.values())
        })
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data yet")