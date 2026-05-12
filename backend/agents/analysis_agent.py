import pandas as pd
import numpy as np

class AnalysisAgent:
    def __init__(self):
        self.df = None
        self.missing_values_count = 0
        self.transformations_count = 0

    def load_data(self, file_path):
        df = pd.read_csv(file_path)

        # 1. Count original missing/NaN values across the entire dataset
        self.missing_values_count = int(df.isna().sum().sum())
        self.transformations_count = 0

        # 2. Standardize columns and count renames
        original_cols = list(df.columns)
        standardized_cols = []
        for col in original_cols:
            sc = str(col).strip().lower().replace(" ", "_")
            standardized_cols.append(sc)
            if sc != col:
                self.transformations_count += 1
        df.columns = standardized_cols

        # 3. Detect and convert temporal column (date/time/day)
        possible_date_cols = [
            col for col in df.columns
            if isinstance(col, str) and any(k in col.lower() for k in ["date", "time", "day"])
        ]
        if possible_date_cols:
            date_col = possible_date_cols[0]
            try:
                # Count coerced dates as transformations
                raw_nulls_before = df[date_col].isna().sum()
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                nulls_after = df[date_col].isna().sum()
                coerced_count = nulls_after - raw_nulls_before
                if coerced_count > 0:
                    self.transformations_count += coerced_count
                
                # Date parsing and sorting is a transformation sequence
                df = df.sort_values(date_col, ascending=False)
                self.transformations_count += 1  # Sorting operation
                
                df = df.reset_index(drop=True)
                self.transformations_count += 1  # Index reset
            except Exception:
                pass

        # 4. In-place missing value imputation for key logistics variables
        cols_map = {col.lower().replace(" ", "_"): col for col in df.columns}
        
        def find_and_impute_col(keys, default_val, substrings):
            target_col = None
            for k in keys:
                if k in cols_map:
                    target_col = cols_map[k]
                    break
            if not target_col:
                for c in df.columns:
                    if any(sub in c.lower() for sub in substrings):
                        target_col = c
                        break
            if target_col:
                # Coerce to numeric to catch parsing errors
                coerced_series = pd.to_numeric(df[target_col], errors="coerce")
                coerced_nulls = coerced_series.isna().sum()
                
                # Each coerced/filled missing value counts as a transformation
                df[target_col] = coerced_series.fillna(default_val)
                self.transformations_count += int(coerced_nulls)

        # Impute Rider Wait Time
        find_and_impute_col(
            ["rider_wait_time_(minutes)", "rider_wait_time_minutes", "rider_wait_time", "rwt"],
            5.0,
            ["rider", "wait"]
        )
        # Impute Kitchen Prep Time
        find_and_impute_col(
            ["kpt_duration_(minutes)", "kpt_duration_minutes", "kpt_duration", "kpt"],
            15.0,
            ["kpt"]
        )
        # Impute Distance
        find_and_impute_col(
            ["distance_km", "distance", "dist"],
            3.0,
            ["distance"]
        )
        # Impute Hour
        find_and_impute_col(
            ["order_hour", "order_time", "hour"],
            12.0,
            ["hour"]
        )
        # Impute Rating
        find_and_impute_col(
            ["rating"],
            4.5,
            ["rating"]
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