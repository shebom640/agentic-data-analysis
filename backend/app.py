import streamlit as st
import pandas as pd
import plotly.express as px

from agents.analysis_agent import AnalysisAgent
from agents.fuzzy_agent import FuzzyPredictionAgent
from agents.decision_agent import DecisionAgent


# Page Config 
st.set_page_config(
    page_title="Agentic Data Analysis Dashboard",
    layout="wide"
)

st.title("🧠 Agentic Data Analysis & Decision System")
st.markdown("Multi-Agent AI with **Analysis → Fuzzy Prediction → RAG-based Decision**")

# Load Data and Analyze
analysis_agent = AnalysisAgent("data/sales_data.csv")
summary, df = analysis_agent.analyze()


# Layout (Responsive Columns)
col1, col2 = st.columns(2)

# Visualization 1: Order Flow Over Time
with col1:
    st.subheader("📈 Order Flow Trend")
    fig1 = px.line(
        df,
        x="time",
        y="order_flow",
        markers=True,
        title="Order Flow vs Time"
    )
    st.plotly_chart(fig1, use_container_width=True)

# Visualization 2: Rating Distribution
with col2:
    st.subheader("⭐ Customer Ratings")
    fig2 = px.bar(
        df,
        x="time",
        y="rating",
        title="Ratings Over Time",
        color="rating"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Fuzzy Prediction Section
st.subheader("🔮 Fuzzy Demand Prediction")

active_orders_input = st.slider(
    "Active Orders",
    min_value=0,
    max_value=500,
    value=len(df)
)

rider_wait_input = st.slider(
    "Rider Wait Time (mins)",
    min_value=0.0,
    max_value=30.0,
    value=5.0
)

kpt_input = st.slider(
    "Kitchen Prep Time (mins)",
    min_value=0.0,
    max_value=60.0,
    value=15.0
)

fuzzy_agent = FuzzyPredictionAgent()
prediction = fuzzy_agent.predict(
    active_orders=active_orders_input,
    max_orders=500,
    rider_wait_time=rider_wait_input,
    kpt_duration=kpt_input,
    order_hour=19.0,
    avg_distance=3.0
)

st.metric(
    label="Predicted Demand Level",
    value=prediction["demand"],
    delta=f"Intensity: {prediction['demand_intensity_value']}%"
)

# Decision Agent Section
st.subheader("🧠 AI Decision (Deterministic Logic)")

decision_agent = DecisionAgent()
decision_json = decision_agent.decide(prediction, ["Zone 1", "Zone 2"])

st.json(decision_json)


# Footer
st.markdown("---")
st.markdown("📌 Built using **Agentic AI + Fuzzy Logic + RAG + LLM Reasoning**")
