def trimf(x, a, b, c):
    """Triangular membership function"""
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        return (x - a) / (b - a) if b > a else 1.0
    if b < x < c:
        return (c - x) / (c - b) if c > b else 1.0
    return 0.0


def trapmf(x, a, b, c, d):
    """Trapezoidal membership function"""
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a) if b > a else 1.0
    if c < x < d:
        return (d - x) / (d - c) if d > c else 1.0
    return 0.0


class FuzzyPredictionAgent:
    """
    Evaluates raw or normalized inputs to continuous fuzzy membership values based on predefined functions.
    Does not use skfuzzy to avoid external system dependencies, ensuring 100% deterministic portability.
    """

    def __init__(self):
        pass

    def evaluate(self, kpt: float, rwt: float, of: float) -> dict:
        """
        Computes fuzzy membership values for KPT, RWT, and OF given normalized [0, 1] inputs.
        """
        kpt = max(0.0, min(1.0, kpt))
        rwt = max(0.0, min(1.0, rwt))
        of = max(0.0, min(1.0, of))

        kpt_memberships = {
            "low": trapmf(kpt, 0.0, 0.0, 0.1, 0.4),
            "medium": trimf(kpt, 0.3, 0.5, 0.7),
            "high": trapmf(kpt, 0.6, 1.0, 1.0, 2.0)
        }

        rwt_memberships = {
            "low": trapmf(rwt, 0.0, 0.0, 0.1, 0.4),
            "medium": trimf(rwt, 0.3, 0.5, 0.7),
            "high": trapmf(rwt, 0.6, 1.0, 1.0, 2.0)
        }

        of_memberships = {
            "low": trapmf(of, 0.0, 0.0, 0.1, 0.3),
            "medium": trimf(of, 0.2, 0.4, 0.6),
            "high": trapmf(of, 0.5, 0.8, 1.0, 2.0)
        }

        return {
            "inputs": {
                "kpt": kpt,
                "rwt": rwt,
                "of": of
            },
            "kpt": kpt_memberships,
            "rwt": rwt_memberships,
            "of": of_memberships
        }

    def predict(self, active_orders, max_orders, rider_wait_time, kpt_duration, order_hour=12, avg_distance=3.0):
        """
        Backward compatible bridge taking raw metrics, normalizing them, and running standard evaluation.
        """
        # Normalization ranges based on old slider maximums or realistic metrics:
        # KPT: Max 45.0
        kpt_norm = max(0.0, min(1.0, kpt_duration / 45.0))
        # RWT: Max 30.0
        rwt_norm = max(0.0, min(1.0, rider_wait_time / 30.0))
        # OF: Max historical 500
        of_norm = max(0.0, min(1.0, active_orders / max(1, max_orders)))

        return self.evaluate(kpt_norm, rwt_norm, of_norm)