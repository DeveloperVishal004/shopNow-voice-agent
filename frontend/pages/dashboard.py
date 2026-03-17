import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

API_BASE = "http://localhost:8000"

def fetch_daily_report():
    try:
        response = requests.get(f"{API_BASE}/report/daily")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")
        return None

def show():
    st.title("Live Operations Dashboard")
    st.markdown("Real-time call analytics for ShopNow support team")

    # auto refresh every 30 seconds
    st.button("Refresh Data")

    data = fetch_daily_report()

    if not data:
        st.warning("No data available yet. Start making calls to see stats here.")
        return

    # ── top metric cards ─────────────────────────────────
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Calls",
            value=data.get("total_calls", 0)
        )

    with col2:
        st.metric(
            label="FCR Rate",
            value=f"{data.get('fcr_percent', 0)}%",
            delta=f"+{round(data.get('fcr_percent', 0) - 52, 1)}% vs baseline"
        )

    with col3:
        st.metric(
            label="Escalations",
            value=data.get("escalated_calls", 0)
        )

    with col4:
        avg = data.get("avg_sentiment", 0)
        st.metric(
            label="Avg Sentiment",
            value=f"{avg:.2f}",
            delta="positive" if avg > 0 else "negative"
        )

    st.markdown("---")

    # ── charts row ───────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Calls by intent")
        intent_data = data.get("calls_by_intent", {})
        if intent_data:
            df_intent = pd.DataFrame({
                "Intent":     list(intent_data.keys()),
                "Call Count": list(intent_data.values())
            })
            fig = px.bar(
                df_intent,
                x="Intent",
                y="Call Count",
                color="Intent",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No intent data yet")

    with col_right:
        st.subheader("Calls by language")
        lang_data = data.get("calls_by_language", {})
        if lang_data:
            df_lang = pd.DataFrame({
                "Language": list(lang_data.keys()),
                "Calls":    list(lang_data.values())
            })
            fig2 = px.pie(
                df_lang,
                names="Language",
                values="Calls",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No language data yet")

    st.markdown("---")

    # ── resolution breakdown ─────────────────────────────
    st.subheader("Resolution breakdown")
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        resolved  = data.get("resolved_calls", 0)
        escalated = data.get("escalated_calls", 0)
        total     = data.get("total_calls", 1)

        fig3 = go.Figure(go.Indicator(
            mode  = "gauge+number",
            value = data.get("fcr_percent", 0),
            title = {"text": "First Contact Resolution %"},
            gauge = {
                "axis": {"range": [0, 100]},
                "bar":  {"color": "#2ecc71"},
                "steps": [
                    {"range": [0,  50], "color": "#fadbd8"},
                    {"range": [50, 75], "color": "#fdebd0"},
                    {"range": [75, 100], "color": "#d5f5e3"},
                ],
                "threshold": {
                    "line":  {"color": "red", "width": 2},
                    "thickness": 0.75,
                    "value": 52    # baseline FCR before AI
                }
            }
        ))
        fig3.update_layout(
            height=250,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_res2:
        st.markdown("#### Summary")
        st.markdown(f"- Total calls handled : **{total}**")
        st.markdown(f"- Resolved by AI      : **{resolved}**")
        st.markdown(f"- Escalated to human  : **{escalated}**")
        st.markdown(f"- FCR rate            : **{data.get('fcr_percent', 0)}%**")
        st.markdown(f"- Baseline FCR        : **52%**")
        improvement = data.get("fcr_percent", 0) - 52
        if improvement > 0:
            st.success(f"FCR improved by {improvement:.1f}% vs pre-AI baseline")
        else:
            st.info("Keep making calls to see FCR improvement")