import streamlit as st


st.set_page_config(
    page_title="ShopNow Voice Agent",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# sidebar navigation
st.sidebar.title("ShopNow Voice Agent")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Live Dashboard",
        "Escalations",
        "Daily Report",
        "Test Agent"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("ShopNow Support AI v1.0")

# route to pages
if page == "Live Dashboard":
    from pages import dashboard
    dashboard.show()

elif page == "Escalations":
    from pages import escalations
    escalations.show()

elif page == "Daily Report":
    from pages import report
    report.show()

elif page == "Test Agent":
    from pages import test_agent
    test_agent.show()