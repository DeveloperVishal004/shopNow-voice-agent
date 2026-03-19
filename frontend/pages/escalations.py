import streamlit as st
import requests
import pandas as pd

API_BASE = "http://localhost:8000"

def fetch_escalation_brief(call_id: str):
    try:
        response = requests.get(f"{API_BASE}/report/escalation/{call_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Could not fetch brief: {e}")
        return None

def show():
    st.title("Escalation Log")
    st.markdown("All escalated calls with full context for human agents")

    st.markdown("---")

    # ── lookup by call ID ────────────────────────────────
    st.subheader("Look up escalation brief")
    col1, col2 = st.columns([3, 1])

    with col1:
        call_id = st.text_input(
            "Enter call ID",
            placeholder="e.g. d0014178-6825-41b9-be67-988f628de48c"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        lookup = st.button("Fetch Brief")

    if lookup and call_id:
        brief = fetch_escalation_brief(call_id)

        if not brief:
            st.error("No escalation found for this call ID")
        else:
            st.markdown("---")

            # ── customer info ────────────────────────────
            st.subheader("Customer info")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Name",     brief.get("customer_name", "Unknown"))
            with col_b:
                st.metric("Phone",    brief.get("customer_phone", "Unknown"))
            with col_c:
                st.metric("Language", brief.get("language", "en").upper())

            st.markdown("---")

            # ── issue summary ────────────────────────────
            st.subheader("Issue summary")
            col_d, col_e = st.columns(2)

            with col_d:
                st.markdown("**Intent detected**")
                intent = brief.get("current_intent", "unknown")
                intent_colors = {
                    "order_status":       "🟦",
                    "return_refund":      "🟨",
                    "payment_issue":      "🟥",
                    "delivery_complaint": "🟧",
                    "product_query":      "🟩",
                    "unknown":            "⬜"
                }
                icon = intent_colors.get(intent, "⬜")
                st.markdown(f"### {icon} {intent.replace('_', ' ').title()}")

            with col_e:
                st.markdown("**Recommended tone**")
                tone = brief.get("recommended_tone", "professional and helpful")
                if "angry" in tone:
                    st.error(f"⚠ {tone}")
                elif "empathetic" in tone:
                    st.warning(f"💛 {tone}")
                else:
                    st.info(f"ℹ {tone}")

            st.markdown("---")

            # ── sentiment history ────────────────────────
            st.subheader("Sentiment history")
            sentiment_history = brief.get("sentiment_history", [])

            if sentiment_history:
                sentiment_colors = {
                    "positive": "🟢",
                    "neutral":  "🔵",
                    "negative": "🟠",
                    "angry":    "🔴"
                }
                sentiment_row = " → ".join([
                    f"{sentiment_colors.get(s, '⚪')} {s}"
                    for s in sentiment_history
                ])
                st.markdown(sentiment_row)

                # sentiment trend chart
                df_sent = pd.DataFrame({
                    "Turn":      list(range(1, len(sentiment_history) + 1)),
                    "Sentiment": sentiment_history
                })
                score_map = {
                    "positive":  1.0,
                    "neutral":   0.0,
                    "negative": -0.5,
                    "angry":    -1.0
                }
                df_sent["Score"] = df_sent["Sentiment"].map(score_map)

                import plotly.express as px
                fig = px.line(
                    df_sent,
                    x="Turn",
                    y="Score",
                    markers=True,
                    color_discrete_sequence=["#e74c3c"]
                )
                fig.add_hline(
                    y=-0.7,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Escalation threshold"
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(range=[-1.2, 1.2])
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No sentiment history available")

            st.markdown("---")

            # ── order context ────────────────────────────
            st.subheader("Order context")
            order_context = brief.get("order_context", {})
            if order_context and isinstance(order_context, dict):
                col_f, col_g, col_h = st.columns(3)
                with col_f:
                    st.metric("Order ID", order_context.get("id", "N/A"))
                with col_g:
                    st.metric("Item",     order_context.get("item_name", "N/A"))
                with col_h:
                    st.metric("Status",   order_context.get("status", "N/A"))
            else:
                st.info("No order data found for this call")

            st.markdown("---")

            # ── conversation snippet ─────────────────────
            st.subheader("Recent conversation")
            turns = brief.get("turns", [])
            if turns:
                for turn in turns[-6:]:
                    role = turn.get("role", "unknown")
                    text = turn.get("text", "")
                    if role == "customer":
                        st.markdown(f"👤 **Customer:** {text}")
                    else:
                        st.markdown(f"🤖 **Agent:** {text}")
            else:
                # fallback — show snippet if turns not available
                snippet = brief.get("conversation_snippet", "")
                if snippet:
                    st.text(snippet)
                else:
                    st.info("No conversation data available")