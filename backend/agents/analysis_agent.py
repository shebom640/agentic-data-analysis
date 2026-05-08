import pandas as pd
import numpy as np

class AnalysisAgent:
    def __init__(self):
        self.df = None

    def load_data(self, file_path):
        df = pd.read_csv(file_path)

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        self.df = df
        return df

    def analyze(self):
        if self.df is None:
            raise ValueError("No dataset loaded")

        df = self.df.copy()

        required = {"rating"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Calculations
        df["volatility"] = df["rating"].rolling(window=3).std()

        # Summary
        summary = {
            "rating_mean": round(df["rating"].mean(), 2),
            "rating_trend": (
                "increasing"
                if df["rating"].iloc[-1] > df["rating"].iloc[0]
                else "decreasing"
            ),
            "volatility": round(df["volatility"].mean(), 2),
        }

        # Charts
        charts = {
            "ratingTrend": df["rating"].tolist(),
            "volatilityTrend": df["volatility"].fillna(0).tolist(),
        }

        return summary, charts, df