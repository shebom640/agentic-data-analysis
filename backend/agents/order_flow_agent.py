import math

class OrderFlowAgent:
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
    def predict(cls, time_norm: float, rating_norm: float) -> dict:
        """
        Takes normalized time (0-1) and rating (0-1),
        returns predicted order flow payload.
        """
        # Clamp inputs
        time_norm = max(0.0, min(1.0, time_norm))
        rating_norm = max(0.0, min(1.0, rating_norm))

        # 1. FUZZIFICATION
        # Time
        mu_morning = cls.trapmf_left(time_norm, 0.0, 0.4)
        mu_afternoon = cls.trimf(time_norm, 0.3, 0.5, 0.7)
        mu_evening = cls.trapmf_right(time_norm, 0.6, 1.0)

        # Rating
        mu_rating_low = cls.trapmf_left(rating_norm, 0.0, 0.4)
        mu_rating_med = cls.trimf(rating_norm, 0.3, 0.5, 0.7)
        mu_rating_high = cls.trapmf_right(rating_norm, 0.6, 1.0)

        # 2. RULE BASE 1: Service Demand
        # MORNING -> all LOW DEMAND
        r1 = min(mu_morning, mu_rating_low)
        r2 = min(mu_morning, mu_rating_med)
        r3 = min(mu_morning, mu_rating_high)

        # AFTERNOON -> LOW=MED, MED=MED, HIGH=HIGH
        r4 = min(mu_afternoon, mu_rating_low)
        r5 = min(mu_afternoon, mu_rating_med)
        r6 = min(mu_afternoon, mu_rating_high)

        # EVENING -> LOW=MED, MED=HIGH, HIGH=HIGH
        r7 = min(mu_evening, mu_rating_low)
        r8 = min(mu_evening, mu_rating_med)
        r9 = min(mu_evening, mu_rating_high)

        # Aggregate Service Demand
        demand_low = max(r1, r2, r3)
        demand_med = max(r4, r5, r7)
        demand_high = max(r6, r8, r9)

        # 3. RULE BASE 2: Order Flow
        # Service Demand \ Time -> Order Flow
        
        # LOW ORDER FLOW
        of1 = min(demand_low, mu_morning)
        of2 = min(demand_low, mu_afternoon)
        of3 = min(demand_med, mu_morning)
        
        # MEDIUM ORDER FLOW
        of4 = min(demand_low, mu_evening)
        of5 = min(demand_med, mu_afternoon)
        of6 = min(demand_high, mu_morning)
        
        # HIGH ORDER FLOW
        of7 = min(demand_med, mu_evening)
        of8 = min(demand_high, mu_afternoon)
        of9 = min(demand_high, mu_evening)
        
        of_low = max(of1, of2, of3)
        of_med = max(of4, of5, of6)
        of_high = max(of7, of8, of9)

        # 4. DEFUZZIFICATION (Centroid)
        # Crisp output centers: LOW=0.25, MED=0.50, HIGH=0.75
        numerator = (of_low * 0.25) + (of_med * 0.50) + (of_high * 0.75)
        denominator = of_low + of_med + of_high

        if denominator == 0:
            prediction_index = 0.5
        else:
            prediction_index = numerator / denominator

        # 5. FINAL DECISION THRESHOLDS
        if prediction_index <= 0.3:
            predicted_of = "LOW"
        elif prediction_index <= 0.7:
            predicted_of = "MEDIUM"
        else:
            predicted_of = "HIGH"

        service_demand_str = "HIGH" if demand_high > max(demand_low, demand_med) else ("MEDIUM" if demand_med > demand_low else "LOW")
        confidence = max(of_low, of_med, of_high)
        if confidence == 0: confidence = 1.0

        # Dynamic Reason
        t_str = "Evening" if mu_evening > max(mu_morning, mu_afternoon) else ("Afternoon" if mu_afternoon > mu_morning else "Morning")
        r_str = "high" if mu_rating_high > max(mu_rating_low, mu_rating_med) else ("medium" if mu_rating_med > mu_rating_low else "low")
        reason = f"{t_str} traffic with {r_str} customer rating indicates {service_demand_str.lower()} service demand and {predicted_of.lower()} order flow."

        return {
            "prediction_index": round(prediction_index, 4),
            "predicted_order_flow": predicted_of,
            "service_demand": service_demand_str,
            "confidence": round(confidence, 4),
            "reason": reason,
            "fuzzy_metrics": {
                "time": {"morning": round(mu_morning, 4), "afternoon": round(mu_afternoon, 4), "evening": round(mu_evening, 4)},
                "rating": {"low": round(mu_rating_low, 4), "medium": round(mu_rating_med, 4), "high": round(mu_rating_high, 4)},
                "demand": {"low": round(demand_low, 4), "medium": round(demand_med, 4), "high": round(demand_high, 4)}
            }
        }
