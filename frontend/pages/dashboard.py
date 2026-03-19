import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_BASE = "http://localhost:8000"

def fetch_daily_report():
    try:
        response = requests.get(f"{API_BASE}/report/daily")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def show():
    # Page Header
    st.title("📈 Command Center")
    st.markdown("Real-time call analytics and performance metrics for the ShopNow Voice Agent.")

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        st.button("↻ Refresh Data")

    data = fetch_daily_report()

    if not data or data.get("total_calls", 0) == 0:
        st.info("No data available yet. Start making calls to see stats here.")
        return

    st.markdown("---")

    # 1. KPIs
    col1, col2, col3, col4 = st.columns(4)

    total = data.get("total_calls", 0)
    resolved = data.get("resolved_calls", 0)
    escalated = data.get("escalated_calls", 0)
    
    # Better renaming for FCR. Unless there is true historical context, we call it AI Resolution Rate.
    res_rate = round((resolved / total * 100) if total > 0 else 0, 1)

    with col1:
        st.metric("Total Calls Handled", value=total, delta=f"+{total} today", delta_color="normal")

    with col2:
        st.metric("AI Resolution Rate", value=f"{res_rate}%", delta="No escalations = 100%", delta_color="off")

    with col3:
        st.metric("Escalated to Human", value=escalated)

    with col4:
        avg = data.get("avg_sentiment", 0)
        st.metric("Avg Sentiment Score", value=f"{avg:.2f}", delta="positive" if avg > 0 else "negative")

    st.markdown("---")

    # 2. Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribution by Intent")
        intent_data = data.get("calls_by_intent", {})
        if intent_data:
            df_intent = pd.DataFrame(list(intent_data.items()), columns=["Intent", "Calls"])
            df_intent = df_intent.sort_values(by="Calls", ascending=False)
            fig1 = px.bar(df_intent, x="Intent", y="Calls", color="Intent", 
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No intent data yet")

    with col_right:
        st.subheader("Language Breakdown")
        lang_data = data.get("calls_by_language", {})
        if lang_data:
            df_lang = pd.DataFrame(list(lang_data.items()), columns=["Language", "Count"])
            fig2 = px.pie(df_lang, names="Language", values="Count", hole=0.4, 
                          color_discrete_sequence=px.colors.sequential.Teal)
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No language data yet")

    st.markdown("---")

    # 3. Recent Calls Dataframe
    st.subheader("Recent Calls Log")
    recent_calls = data.get("recent_calls", [])
    if recent_calls:
        df_recent = pd.DataFrame(recent_calls)
        
        # Formatting the DataFrame
        if "created_at" in df_recent.columns:
            df_recent['created_at'] = pd.to_datetime(df_recent['created_at']).dt.strftime('%H:%M:%S')
            df_recent = df_recent.rename(columns={"created_at": "Today @ Time"})
        
        if "sentiment_avg" in df_recent.columns:
            df_recent['sentiment_avg'] = df_recent['sentiment_avg'].round(2)
        
        # Rename columns to look nicer
        col_mappings = {
            "id": "Call ID",
            "intent": "Intent Segment",
            "language": "Detected Lang",
            "outcome": "Final Outcome",
            "sentiment_avg": "Sentiment Ratio"
        }
        df_recent = df_recent.rename(columns=col_mappings)
        
        # Display the dataframe with custom UI style
        st.dataframe(
            df_recent,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No recent calls found in database.")