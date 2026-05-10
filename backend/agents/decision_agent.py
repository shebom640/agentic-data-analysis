class DecisionAgent:

    @staticmethod
    def trimf(x, a, b, c):
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if (b - a) != 0 else 1.0
        elif b < x < c:
            return (c - x) / (c - b) if (c - b) != 0 else 1.0
        return 0.0

    @staticmethod
    def trapmf_left(x, a, b):
        if x <= a: return 1.0
        if x >= b: return 0.0
        return (b - x) / (b - a)

    @staticmethod
    def trapmf_right(x, a, b):
        if x <= a: return 0.0
        if x >= b: return 1.0
        return (x - a) / (b - a)

    @classmethod
    def decide(cls, kpt_norm, rwt_norm=None, of_norm=None, priority_zones=None, current_allocation="HOLD") -> dict:
        """
        Takes normalized KPT, RWT, and Order Flow values (0-1)
        and returns rider allocation strategy using cascading
        fuzzy inference with full Rule Base 3 implementation.
        """
        
        # Backwards compatibility for when decide(fuzzy_output, priority_zones) is called
        if isinstance(kpt_norm, dict):
            fuzzy_output = kpt_norm
            priority_zones = rwt_norm if rwt_norm is not None else []
            inputs = fuzzy_output.get("inputs", {})
            kpt_norm = inputs.get("kpt", 0.5)
            rwt_norm = inputs.get("rwt", 0.5)
            of_norm = inputs.get("of", 0.5)

        if priority_zones is None:
            priority_zones = []

        # =========================================================
        # INPUT CLAMPING
        # =========================================================
        kpt_norm = max(0.0, min(1.0, float(kpt_norm)))
        rwt_norm = max(0.0, min(1.0, float(rwt_norm)))
        of_norm = max(0.0, min(1.0, float(of_norm)))

        # =========================================================
        # STEP 1: FUZZIFICATION
        # =========================================================
        mu_kpt_low = cls.trapmf_left(kpt_norm, 0.0, 0.4)
        mu_kpt_med = cls.trimf(kpt_norm, 0.3, 0.5, 0.7)
        mu_kpt_high = cls.trapmf_right(kpt_norm, 0.6, 1.0)

        mu_rwt_low = cls.trapmf_left(rwt_norm, 0.0, 0.4)
        mu_rwt_med = cls.trimf(rwt_norm, 0.3, 0.5, 0.7)
        mu_rwt_high = cls.trapmf_right(rwt_norm, 0.6, 1.0)

        mu_of_low = cls.trapmf_left(of_norm, 0.0, 0.3)
        mu_of_med = cls.trimf(of_norm, 0.2, 0.4, 0.6)
        mu_of_high = cls.trapmf_right(of_norm, 0.5, 1.0)

        # =========================================================
        # STEP 2: RULE BASE 1 (System State)
        # =========================================================
        # UNDERUTILIZED
        r1 = min(mu_kpt_low, mu_rwt_low)
        r2 = min(mu_kpt_med, mu_rwt_low)

        # OPTIMAL
        r3 = min(mu_kpt_low, mu_rwt_med)
        r4 = min(mu_kpt_low, mu_rwt_high)
        r5 = min(mu_kpt_med, mu_rwt_med)
        r6 = min(mu_kpt_high, mu_rwt_low)

        # OVERLOADED
        r7 = min(mu_kpt_med, mu_rwt_high)
        r8 = min(mu_kpt_high, mu_rwt_med)
        r9 = min(mu_kpt_high, mu_rwt_high)

        mu_underutilized = max(r1, r2)
        mu_optimal = max(r3, r4, r5, r6)
        mu_overloaded = max(r7, r8, r9)

        # =========================================================
        # STEP 3: RULE BASE 2 (Demand Intensity)
        # =========================================================
        # LOW DEMAND
        d1 = min(mu_underutilized, mu_of_low)
        d2 = min(mu_underutilized, mu_of_med)
        d3 = min(mu_optimal, mu_of_low)

        # MEDIUM DEMAND
        d4 = min(mu_underutilized, mu_of_high)
        d5 = min(mu_optimal, mu_of_med)
        d6 = min(mu_overloaded, mu_of_low)

        # HIGH DEMAND
        d7 = min(mu_optimal, mu_of_high)
        d8 = min(mu_overloaded, mu_of_med)
        d9 = min(mu_overloaded, mu_of_high)

        demand_low = max(d1, d2, d3)
        demand_med = max(d4, d5, d6)
        demand_high = max(d7, d8, d9)

        # =========================================================
        # STEP 4: RULE BASE 3 (Allocation Strategy)
        # =========================================================
        alloc_tendency_reduce = demand_low
        alloc_tendency_hold = demand_med
        alloc_tendency_scale = demand_high

        # REDUCE RULES
        a1 = min(demand_low, alloc_tendency_reduce)
        a2 = min(demand_low, alloc_tendency_hold)
        a3 = min(demand_med, alloc_tendency_reduce)

        # HOLD RULES
        a4 = min(demand_low, alloc_tendency_scale)
        a5 = min(demand_med, alloc_tendency_hold)
        a6 = min(demand_high, alloc_tendency_reduce)

        # SCALE-UP RULES
        a7 = min(demand_med, alloc_tendency_scale)
        a8 = min(demand_high, alloc_tendency_hold)
        a9 = min(demand_high, alloc_tendency_scale)

        alloc_reduce = max(a1, a2, a3)
        alloc_hold = max(a4, a5, a6)
        alloc_scale = max(a7, a8, a9)

        # =========================================================
        # STEP 5: DEFUZZIFICATION (Centroid Method)
        # =========================================================
        numerator = (alloc_reduce * 0.0) + (alloc_hold * 0.5) + (alloc_scale * 1.0)
        denominator = alloc_reduce + alloc_hold + alloc_scale

        if denominator == 0:
            decision_index = 0.5
        else:
            decision_index = numerator / denominator

        # =========================================================
        # STEP 6: FINAL DECISION THRESHOLDS
        # =========================================================
        if decision_index < 0.3:
            action = "REDUCE"
        elif decision_index <= 0.7:
            action = "HOLD"
        else:
            action = "SCALE UP"

        # =========================================================
        # SYSTEM STATE LABEL
        # =========================================================
        if mu_overloaded > max(mu_underutilized, mu_optimal):
            system_state = "OVERLOADED"
        elif mu_optimal > mu_underutilized:
            system_state = "OPTIMAL"
        else:
            system_state = "UNDERUTILIZED"

        # =========================================================
        # DEMAND LABEL
        # =========================================================
        if demand_high > max(demand_low, demand_med):
            demand_intensity = "HIGH"
        elif demand_med > demand_low:
            demand_intensity = "MEDIUM"
        else:
            demand_intensity = "LOW"

        confidence = max(alloc_reduce, alloc_hold, alloc_scale)
        if confidence == 0:
            confidence = 1.0

        # =========================================================
        # DYNAMIC REASONING
        # =========================================================
        kpt_desc = "High" if mu_kpt_high > max(mu_kpt_low, mu_kpt_med) else ("Medium" if mu_kpt_med > mu_kpt_low else "Low")
        rwt_desc = "High" if mu_rwt_high > max(mu_rwt_low, mu_rwt_med) else ("Medium" if mu_rwt_med > mu_rwt_low else "Low")
        of_desc = "High" if mu_of_high > max(mu_of_low, mu_of_med) else ("Medium" if mu_of_med > mu_of_low else "Low")

        reason = (
            f"{kpt_desc} KPT + {rwt_desc} RWT + {of_desc} Order Flow indicates "
            f"{system_state.lower()} system state and {demand_intensity.lower()} demand intensity, "
            f"therefore {action.lower()} allocation strategy is recommended."
        )

        explanation_details = [
            f"1. Fuzzified Inputs: KPT(Low={mu_kpt_low:.2f}, Med={mu_kpt_med:.2f}, High={mu_kpt_high:.2f}); RWT(Low={mu_rwt_low:.2f}, Med={mu_rwt_med:.2f}, High={mu_rwt_high:.2f}); OF(Low={mu_of_low:.2f}, Med={mu_of_med:.2f}, High={mu_of_high:.2f}).",
            f"2. System State (Rule Base 1) evaluates to {system_state}: Underutilized={mu_underutilized:.2f}, Optimal={mu_optimal:.2f}, Overloaded={mu_overloaded:.2f}.",
            f"3. Demand Intensity (Rule Base 2) evaluates to {demand_intensity}: Low={demand_low:.2f}, Medium={demand_med:.2f}, High={demand_high:.2f}.",
            f"4. Allocation Strategy (Rule Base 3) activates Strategy: Reduce={alloc_reduce:.2f}, Hold={alloc_hold:.2f}, Scale-Up={alloc_scale:.2f}.",
            f"5. Centroid Defuzzification Score is {decision_index:.3f}, triggering final action sector: {action}."
        ]

        # =========================================================
        # RETURN OUTPUT
        # =========================================================
        return {
            "decision_index": round(decision_index, 4),
            "allocation_strategy": action,
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
            "operational_load": demand_intensity,
            
            "fuzzy_metrics": {
                "kpt": {"low": round(mu_kpt_low, 4), "medium": round(mu_kpt_med, 4), "high": round(mu_kpt_high, 4)},
                "rwt": {"low": round(mu_rwt_low, 4), "medium": round(mu_rwt_med, 4), "high": round(mu_rwt_high, 4)},
                "order_flow": {"low": round(mu_of_low, 4), "medium": round(mu_of_med, 4), "high": round(mu_of_high, 4)},
                "system_state": {"underutilized": round(mu_underutilized, 4), "optimal": round(mu_optimal, 4), "overloaded": round(mu_overloaded, 4)},
                "demand": {"low": round(demand_low, 4), "medium": round(demand_med, 4), "high": round(demand_high, 4)},
                "allocation": {"reduce": round(alloc_reduce, 4), "hold": round(alloc_hold, 4), "scale_up": round(alloc_scale, 4)}
            }
        }