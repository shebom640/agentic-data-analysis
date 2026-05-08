class DecisionAgent:
    """
    DecisionAgent is responsible for pure fuzzy logic + rule-based rider allocation decisions.
    It takes the fuzzified membership degrees and runs a series of cascade rule bases:
    Input -> Fuzzification -> Rule Base 1 (System State) -> Rule Base 2 (Demand Intensity) -> Rule Base 3 (Final Decision) -> Defuzzification
    """

    def __init__(self):
        pass

    def decide(self, fuzzy_output: dict, priority_zones: list, current_allocation: str = "HOLD") -> dict:
        """
        Executes cascade fuzzy inference rule bases:
        Input Memberships -> Rule Base 1 (System State) -> Rule Base 2 (Demand Intensity) -> Direct Mapping (Final Decision)
        -> Centroid Defuzzification -> Output Decision.
        """
        kpt_m = fuzzy_output.get("kpt", {"low": 0.0, "medium": 0.0, "high": 0.0})
        rwt_m = fuzzy_output.get("rwt", {"low": 0.0, "medium": 0.0, "high": 0.0})
        of_m = fuzzy_output.get("of", {"low": 0.0, "medium": 0.0, "high": 0.0})

        # =========================================================
        # STEP 2: RULE BASE 1 (System State)
        # =========================================================
        # UNDERUTILIZED
        mu_Underutilized = max(
            min(kpt_m.get("low", 0.0), rwt_m.get("low", 0.0)),
            min(kpt_m.get("medium", 0.0), rwt_m.get("low", 0.0))
        )
        # OPTIMAL
        mu_Optimal = max(
            min(kpt_m.get("low", 0.0), rwt_m.get("medium", 0.0)),
            min(kpt_m.get("low", 0.0), rwt_m.get("high", 0.0)),
            min(kpt_m.get("medium", 0.0), rwt_m.get("medium", 0.0)),
            min(kpt_m.get("high", 0.0), rwt_m.get("low", 0.0))
        )
        # OVERLOADED
        mu_Overloaded = max(
            min(kpt_m.get("medium", 0.0), rwt_m.get("high", 0.0)),
            min(kpt_m.get("high", 0.0), rwt_m.get("medium", 0.0)),
            min(kpt_m.get("high", 0.0), rwt_m.get("high", 0.0))
        )

        # =========================================================
        # STEP 3: RULE BASE 2 (Demand Intensity)
        # =========================================================
        # LOW
        mu_Demand_Low = max(
            min(mu_Underutilized, of_m.get("low", 0.0)),
            min(mu_Underutilized, of_m.get("medium", 0.0)),
            min(mu_Optimal, of_m.get("low", 0.0))
        )
        # MEDIUM
        mu_Demand_Med = max(
            min(mu_Underutilized, of_m.get("high", 0.0)),
            min(mu_Optimal, of_m.get("medium", 0.0)),
            min(mu_Overloaded, of_m.get("low", 0.0))
        )
        # HIGH
        mu_Demand_High = max(
            min(mu_Optimal, of_m.get("high", 0.0)),
            min(mu_Overloaded, of_m.get("medium", 0.0)),
            min(mu_Overloaded, of_m.get("high", 0.0))
        )

        # =========================================================
        # STEP 4: RULE BASE 3 (Final Decision)
        # =========================================================
        mu_Reduce = mu_Demand_Low
        mu_Hold = mu_Demand_Med
        mu_ScaleUp = mu_Demand_High

        # =========================================================
        # STEP 6: DEFUZZIFICATION (Centroid Method)
        # =========================================================
        sum_mu = mu_Reduce + mu_Hold + mu_ScaleUp
        if sum_mu > 0.0:
            decision_index = (mu_Reduce * 0.0 + mu_Hold * 0.5 + mu_ScaleUp * 1.0) / sum_mu
        else:
            decision_index = 0.5  # Fallback to neutral Hold

        # =========================================================
        # STEP 7: FIXED NO-OVERLAP THRESHOLDS
        # =========================================================
        if decision_index < 0.3:
            action = "REDUCE"
        elif decision_index <= 0.7:
            action = "HOLD"
        else:
            action = "SCALE UP"

        # Determine discrete classifications
        states = {"UNDERUTILIZED": mu_Underutilized, "OPTIMAL": mu_Optimal, "OVERLOADED": mu_Overloaded}
        system_state = max(states, key=states.get) if max(states.values()) > 0.0 else "OPTIMAL"

        demands = {"LOW": mu_Demand_Low, "MEDIUM": mu_Demand_Med, "HIGH": mu_Demand_High}
        demand_intensity = max(demands, key=demands.get) if max(demands.values()) > 0.0 else "MEDIUM"

        confidence = max(mu_Reduce, mu_Hold, mu_ScaleUp)
        if sum_mu == 0.0:
            confidence = 1.0

        # Construct dynamic explainable reason
        kpt_desc = "High" if kpt_m.get("high", 0.0) > max(kpt_m.get("low", 0.0), kpt_m.get("medium", 0.0)) else "Medium" if kpt_m.get("medium", 0.0) > kpt_m.get("low", 0.0) else "Low"
        rwt_desc = "High" if rwt_m.get("high", 0.0) > max(rwt_m.get("low", 0.0), rwt_m.get("medium", 0.0)) else "Medium" if rwt_m.get("medium", 0.0) > rwt_m.get("low", 0.0) else "Low"
        of_desc = "High" if of_m.get("high", 0.0) > max(of_m.get("low", 0.0), of_m.get("medium", 0.0)) else "Medium" if of_m.get("medium", 0.0) > of_m.get("low", 0.0) else "Low"
        reason = f"{kpt_desc} KPT + {rwt_desc} RWT + {of_desc} Order Flow → {system_state} system state → {demand_intensity} demand intensity → {action} required"

        explanation_details = [
            f"1. Fuzzified Inputs: KPT(Low={kpt_m.get('low', 0.0):.2f}, Med={kpt_m.get('medium', 0.0):.2f}, High={kpt_m.get('high', 0.0):.2f}); RWT(Low={rwt_m.get('low', 0.0):.2f}, Med={rwt_m.get('medium', 0.0):.2f}, High={rwt_m.get('high', 0.0):.2f}); OF(Low={of_m.get('low', 0.0):.2f}, Med={of_m.get('medium', 0.0):.2f}, High={of_m.get('high', 0.0):.2f}).",
            f"2. System State (Rule Base 1) evaluates to {system_state}: Underutilized={mu_Underutilized:.2f}, Optimal={mu_Optimal:.2f}, Overloaded={mu_Overloaded:.2f}.",
            f"3. Demand Intensity (Rule Base 2) evaluates to {demand_intensity}: Low={mu_Demand_Low:.2f}, Medium={mu_Demand_Med:.2f}, High={mu_Demand_High:.2f}.",
            f"4. Allocation Strategy (Rule Base 3) activates Strategy: Reduce={mu_Reduce:.2f}, Hold={mu_Hold:.2f}, Scale-Up={mu_ScaleUp:.2f}.",
            f"5. Centroid Defuzzification Score is {decision_index:.3f}, triggering final action sector: {action}."
        ]

        # Return identical outputs + backward compatible structures
        return {
            "decision_index": round(decision_index, 4),
            "action": action,
            "system_state": system_state,
            "demand_intensity": demand_intensity,
            "confidence": round(confidence, 4),
            "reason": reason,
            "explanation": "\n".join(explanation_details),

            # Backward compatibility fields to prevent any legacy page issues
            "deploy_decision": "YES" if action == "SCALE UP" else "NO",
            "deployment_level": "LOW" if action == "REDUCE" else "MEDIUM" if action == "HOLD" else "HIGH",
            "recommended_riders": -20 if action == "REDUCE" else 0 if action == "HOLD" else 30,
            "priority_zones": priority_zones,
            "reasoning": explanation_details,
            "operational_load": demand_intensity
        }