import uuid
from datetime import datetime


def build_agent_json(
    query,
    analysis_summary,
    fuzzy_output,
    rag_context,
    llm_text,
    charts=None,
    fuzzy_charts=None
):
    """
    Builds a JSON artifact that conditionally includes heavy data
    (charts, fuzzy curves) only when provided.
    """

    include_charts = charts is not None
    include_fuzzy = fuzzy_charts is not None

    json_output = {
        # =========================
        # META
        # =========================
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "model": "mistral",
            "pipeline": "analysis → fuzzy → decision",
            "schema_version": "1.3"
        },

        # =========================
        # ARTIFACT DECLARATION
        # =========================
        "artifacts": {
            "charts": include_charts,
            "fuzzy_membership": include_fuzzy,
            "defuzzification": include_fuzzy,
            "chat_response": True
        },

        # =========================
        # INPUT
        # =========================
        "input": {
            "query": query,
            "context_used": bool(rag_context)
        },

        # =========================
        # CHAT RESPONSE (WHAT USER SAW)
        # =========================
        "chat_response": {
            "reply": llm_text,
            "format": "text"
        },

        # =========================
        # ANALYSIS AGENT
        # =========================
        "analysis_agent": {
            "summary": analysis_summary,
            "confidence": analysis_summary.get("confidence", 0.0)
        },

        # =========================
        # FUZZY PREDICTION AGENT
        # =========================
        "fuzzy_prediction_agent": {
            "predicted_order_flow": fuzzy_output.get(
                "predicted_order_flow", 0.0
            ),
            "order_flow_level": fuzzy_output.get(
                "order_flow_level", "UNKNOWN"
            )
        },

        # =========================
        # DECISION AGENT
        # =========================
        "decision_agent": {
            "decision": fuzzy_output.get(
                "order_flow_level", "REVIEW"
            ),
            "reasoning": llm_text,
            "supporting_docs": rag_context
        }
    }

    # -------------------------
    # CONDITIONAL HEAVY DATA
    # -------------------------
    if include_charts:
        json_output["analysis_agent"]["charts"] = charts

    if include_fuzzy:
        json_output["fuzzy_prediction_agent"]["defuzzification"] = {
            "method": "centroid",
            "crisp_value": fuzzy_output.get(
                "predicted_order_flow", 0.0
            )
        }
        json_output["fuzzy_prediction_agent"]["membership_functions"] = fuzzy_charts

    return json_output
