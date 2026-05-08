import pandas as pd
import numpy as np


# ==========================================
# JSON SAFE CONVERTER
# ==========================================

def json_safe(obj):

    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [json_safe(v) for v in obj]

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating,)):
        return float(obj)

    if isinstance(obj, pd.Series):
        return json_safe(obj.to_dict())

    if isinstance(obj, pd.DataFrame):
        return json_safe(obj.to_dict(orient="records"))

    return obj


# ==========================================
# VALIDATE CHART STRUCTURE
# ==========================================

def validate_chart(chart):

    if not isinstance(chart, dict):
        return None

    required = ["type", "x", "y"]

    for r in required:
        if r not in chart:
            return None

    if not isinstance(chart["x"], list):
        return None

    if not isinstance(chart["y"], list):
        return None

    if len(chart["x"]) != len(chart["y"]):
        return None

    # force safe types
    chart["x"] = [str(v) for v in chart["x"]]
    chart["y"] = [float(v) for v in chart["y"]]

    return chart


# ==========================================
# SAFE PYTHON EXECUTION
# ==========================================

def execute_python_code(code: str, df: pd.DataFrame):

    safe_globals = {
        "pd": pd,
        "np": np,
        "df": df.copy()
    }

    safe_locals = {}

    try:

        exec(code, safe_globals, safe_locals)

        result = safe_locals.get("result", None)
        chart = safe_locals.get("chart", None)

        result = json_safe(result)
        chart = json_safe(chart)

        chart = validate_chart(chart)

        return {
            "result": result,
            "chart": chart
        }

    except Exception as e:

        return {
            "error": str(e)
        }