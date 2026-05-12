from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import math
import pandas as pd
import numpy as np

from agents.analysis_agent import AnalysisAgent
from agents.fuzzy_agent import FuzzyPredictionAgent
from agents.decision_agent import DecisionAgent
from agents.order_flow_agent import OrderFlowAgent


# =========================================================
# APP SETUP
# =========================================================

app = FastAPI(title="Logistics Validation Subsystem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

analysis_agent = AnalysisAgent()
fuzzy_agent = FuzzyPredictionAgent()
decision_agent = DecisionAgent()


# =========================================================
# JSON SAFETY
# =========================================================

def make_json_safe(obj):

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, pd.Series):
        return obj.to_dict()

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")

    return obj


# =========================================================
# UTILITIES
# =========================================================

def sanitize_dict(d):

    cleaned = {}

    for k, v in d.items():

        if isinstance(v, float):

            if math.isnan(v) or math.isinf(v):
                cleaned[k] = 0.0
            else:
                cleaned[k] = round(v, 4)

        else:
            cleaned[k] = v

    return cleaned


def serialize_df(df):

    df_copy = df.copy()

    for col in df_copy.columns:

        if str(df_copy[col].dtype).startswith("datetime"):
            df_copy[col] = df_copy[col].astype(str)

    return df_copy


def find_good_categorical_column(df):

    candidates = []

    for col in df.columns:

        if not isinstance(col, str):
            continue

        unique_vals = df[col].nunique()

        if unique_vals <= 1:
            continue

        if unique_vals > len(df) * 0.5:
            continue

        candidates.append((col, unique_vals))

    candidates.sort(key=lambda x: x[1])

    if candidates:
        return candidates[0][0]

    return None


def find_rating_column(df):

    for col in df.columns:
        if isinstance(col, str) and "rating" in col.lower():
            return col

    return None


def extract_metrics(df, missing_values_count=0, transformations_count=0):
    active_orders = len(df)
    cols = {col.lower().replace(" ", "_"): col for col in df.columns}

    # Extract Rider Wait Time
    rwt_col = None
    for k in ["rider_wait_time_(minutes)", "rider_wait_time_minutes", "rider_wait_time", "rwt"]:
        if k in cols:
            rwt_col = cols[k]
            break
    if not rwt_col:
        for c in df.columns:
            if "rider" in c.lower() and "wait" in c.lower():
                rwt_col = c
                break
    if rwt_col:
        avg_rider_wait = pd.to_numeric(df[rwt_col], errors="coerce").mean()
        if pd.isna(avg_rider_wait): avg_rider_wait = 5.0
    else:
        avg_rider_wait = 5.0

    # Extract Kitchen Preparation Time
    kpt_col = None
    for k in ["kpt_duration_(minutes)", "kpt_duration_minutes", "kpt_duration", "kpt"]:
        if k in cols:
            kpt_col = cols[k]
            break
    if not kpt_col:
        for c in df.columns:
            if "kpt" in c.lower():
                kpt_col = c
                break
    if kpt_col:
        avg_kpt = pd.to_numeric(df[kpt_col], errors="coerce").mean()
        if pd.isna(avg_kpt): avg_kpt = 15.0
    else:
        avg_kpt = 15.0

    # Extract Distance
    dist_col = None
    for k in ["distance_km", "distance", "dist"]:
        if k in cols:
            dist_col = cols[k]
            break
    if not dist_col:
        for c in df.columns:
            if "distance" in c.lower():
                dist_col = c
                break
    if dist_col:
        avg_dist = pd.to_numeric(df[dist_col], errors="coerce").mean()
        if pd.isna(avg_dist): avg_dist = 3.0
    else:
        avg_dist = 3.0

    # Extract Hour
    hour_col = None
    for k in ["order_hour", "order_time", "hour"]:
        if k in cols:
            hour_col = cols[k]
            break
    if not hour_col:
        for c in df.columns:
            if "hour" in c.lower():
                hour_col = c
                break
    latest = df.iloc[0] if len(df) > 0 else {}
    if hour_col:
        order_hour = float(latest.get(hour_col, 12))
    else:
        order_hour = 12.0

    # Extract Priority Zones
    subzone_col = None
    for k in ["subzone", "area", "zone"]:
        if k in cols:
            subzone_col = cols[k]
            break
    if not subzone_col:
        for c in df.columns:
            if "subzone" in c.lower() or "zone" in c.lower() or "area" in c.lower():
                subzone_col = c
                break
    priority_zones = []
    if subzone_col:
        priority_zones = df[subzone_col].value_counts().head(3).index.tolist()

    rating_col = find_rating_column(df)
    if rating_col:
        avg_rating = pd.to_numeric(df[rating_col], errors="coerce").mean()
        if pd.isna(avg_rating): avg_rating = 4.5
    else:
        avg_rating = 4.5

    return {
        "active_orders": active_orders,
        "avg_rider_wait": avg_rider_wait,
        "avg_kpt": avg_kpt,
        "avg_dist": avg_dist,
        "order_hour": order_hour,
        "avg_rating": avg_rating,
        "priority_zones": priority_zones,
        "missing_values_count": missing_values_count,
        "transformations_count": transformations_count
    }


# =========================================================
# DATASET UPLOAD
# =========================================================

@app.post("/upload")
def upload(file: UploadFile = File(...)):

    path = os.path.join(UPLOAD_DIR, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingestion agent standardizes columns, detects/sorts temporal columns,
    # and imputes missing logistics data automatically
    analysis_agent.load_data(path)

    metrics = extract_metrics(
        analysis_agent.df,
        missing_values_count=analysis_agent.missing_values_count,
        transformations_count=analysis_agent.transformations_count
    )

    return make_json_safe({
        "status": "uploaded",
        "rows": len(analysis_agent.df),
        "columns": list(analysis_agent.df.columns),
        "metrics": metrics
    })

# =========================================================
# DATA PREVIEW
# =========================================================

@app.get("/data")
def data():

    if analysis_agent.df is None:
        return []

    df = serialize_df(analysis_agent.df.copy())

    return make_json_safe(df.to_dict(orient="records"))


# =========================================================
# CHAT ENDPOINT
# =========================================================

@app.post("/chat")
def chat(payload: dict):

    if analysis_agent.df is None:
        return {"reply": "Please upload dataset first", "chart": None}

    try:

        df = analysis_agent.df.copy()

        user_question = (
            payload.get("message")
            or payload.get("question")
            or payload.get("text")
            or ""
        ).strip()

        dataset_columns = list(df.columns)

        chart_response = None
        python_result = None


        # =====================================================
        # DETERMINISTIC INTENT MATCHING (RESTRICTED)
        # =====================================================
        
        q_lower = user_question.lower()
        flagged_words = ["deploy", "decision", "riders", "analysis", "data", "orders", "zomato", "priority", "status"]
        
        has_flagged = any(word in q_lower for word in flagged_words)
        
        if not has_flagged and q_lower.strip() != "":
            return {
                "reply": "I am unable to handle your request. I only handle operational deployment queries.",
                "decision_json": None,
                "chart": None
            }

        chart_response = None
        python_result = None

        # =====================================================
        # ZOMATO BUSINESS ANALYSIS
        # =====================================================

        summary, all_charts, analyzed_df = analysis_agent.analyze()
        summary = sanitize_dict(summary)

        # Calculate specific metrics from df
        metrics = extract_metrics(df)
        active_orders = metrics["active_orders"]
        avg_rider_wait = metrics["avg_rider_wait"]
        avg_kpt = metrics["avg_kpt"]
        avg_dist = metrics["avg_dist"]
        order_hour = metrics["order_hour"]
        priority_zones = metrics["priority_zones"]
        max_orders_historic = 500  # mock historical max

        # To ensure perfect sync with Dart Dashboard:
        kpt_norm = max(0.0, min(1.0, avg_kpt / 45.0))
        rwt_norm = max(0.0, min(1.0, avg_rider_wait / 30.0))
        time_norm = max(0.0, min(1.0, order_hour / 24.0))
        
        avg_rating = metrics.get("avg_rating", 4.5)
        rating_norm = max(0.0, min(1.0, avg_rating / 5.0))

        of_prediction = OrderFlowAgent.predict(time_norm, rating_norm)
        of_norm = of_prediction["prediction_index"]

        # Decision Agent logic
        decision_json = decision_agent.decide(kpt_norm, rwt_norm, of_norm, priority_zones=priority_zones)

        # Still call fuzzy_agent for backward compatibility payload
        fuzzy = fuzzy_agent.evaluate(kpt_norm, rwt_norm, of_norm)

        # Convert dict to a formatted string for frontend display, or return dict directly
        explanation = f"DEPLOY: {decision_json['deploy_decision']} | LEVEL: {decision_json['deployment_level']}\n"
        explanation += f"Recommended Riders: {decision_json['recommended_riders']}\n"
        explanation += f"Priority Zones: {', '.join(decision_json['priority_zones'])}\n"
        explanation += f"Reasoning: {', '.join(decision_json['reasoning'])}"

        return make_json_safe({
            "reply": explanation,
            "decision_json": decision_json,
            "summary": summary,
            "prediction": fuzzy,
            "chart": chart_response,
            "analysis_result": python_result
        })


    except Exception as e:

        print("CHAT ERROR:", e)

        return {
            "reply": f"Error processing request: {str(e)}",
            "chart": None
        }


@app.post("/decision")
def post_decision(payload: dict):
    """
    Dedicated endpoint for the interactive fuzzy sliders on the Dashboard UI.
    """
    try:
        kpt = float(payload.get("kpt", 0.5))
        rwt = float(payload.get("rwt", 0.5))
        of = float(payload.get("of", 0.5))
        current_allocation = str(payload.get("current_allocation", "HOLD"))
        priority_zones = payload.get("priority_zones", ["Sector 4", "Connaught Place", "Vasant Kunj"])

        fuzzy_output = fuzzy_agent.evaluate(kpt, rwt, of)
        decision_json = decision_agent.decide(fuzzy_output, priority_zones, current_allocation)

        return make_json_safe({
            "status": "success",
            "fuzzy": fuzzy_output,
            "decision": decision_json
        })
    except Exception as e:
        print("DECISION ENDPOINT ERROR:", e)
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/predict_order_flow")
def post_predict_order_flow(payload: dict):
    """
    Endpoint for the Order Flow Agent to calculate order flow from time and rating.
    """
    try:
        time_norm = float(payload.get("time", 0.5))
        rating_norm = float(payload.get("rating", 0.5))

        prediction = OrderFlowAgent.predict(time_norm, rating_norm)

        return make_json_safe({
            "status": "success",
            "prediction": prediction
        })
    except Exception as e:
        print("PREDICT ORDER FLOW ENDPOINT ERROR:", e)
        return {
            "status": "error",
            "message": str(e)
        }