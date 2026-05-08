# Project Synopsis: Arsenic Analytics Logistics Validation Subsystem

## 1. System Architecture Overview
The Arsenic Analytics system is built as a deterministic pipeline that replaces legacy LLM-based reasoning with a transparent, rule-based fuzzy logic engine. It consists of a frontend dashboard (built in Flutter) and a robust Python backend (FastAPI) that processes logistics data and outputs operational deployment insights. 

The core reasoning of the system is divided into three distinct, deterministic agents that run sequentially:
1. Data Pre Processing and Ingestion Agent
2. Prediction Agent
3. Decision Agent

---

## 2. Agent Workflow and Logic

### 1. Data Pre Processing and Ingestion Agent
**Role:** Handles dataset uploads, data standardization, initial cleaning, and statistical summarization.

**How it works:**
- **Ingestion & Standardization:** Reads CSV files uploaded by the user and immediately standardizes column names (e.g., stripping whitespace, converting to lowercase, and replacing spaces with underscores) to ensure downstream processing is robust against messy data.
- **Chronological Sorting:** If temporal data (date/time) is detected, the agent sorts the records chronologically to enable time-series logic.
- **Metric Extraction:** Iterates through the data to extract critical logistics variables such as `Active Orders`, `Average Rider Wait Time (RWT)`, `Kitchen Preparation Time (KPT)`, `Distance`, `Order Hour`, and `Priority Zones`. Missing or malformed data points are gracefully handled and defaulted to safe baseline values.
- **Volatility Analysis:** Calculates statistical aggregates, such as standard deviation over rolling windows (e.g., rating volatility) and average trends, returning a structured summary to the frontend.

### 2. Prediction Agent (Order Flow / Fuzzy Agent)
**Role:** Predicts the incoming order flow and service demand intensity using continuous fuzzy membership functions.

**How it works:**
- **Fuzzification:** Takes normalized continuous inputs (such as KPT, RWT, Active Orders, or Time of Day/Ratings) and maps them into fuzzy membership degrees using explicitly coded Triangular (`trimf`) and Trapezoidal (`trapmf`) membership functions. 
  - For example, Time of Day is mapped to continuous fuzzy sets for `Morning`, `Afternoon`, and `Evening`. KPT is mapped to `Low`, `Medium`, and `High`.
- **Rule Base 1 (Service Demand Inference):** Applies intersection (MIN) operators over IF-THEN rules to determine demand. For instance, if it is Evening and customer ratings are High, the inferred demand heavily leans into the High subset.
- **Defuzzification:** Uses a mathematical Centroid Defuzzification method to condense the fuzzy array into a single, deterministic prediction index ranging from 0.0 to 1.0.
- **Classification:** Evaluates the continuous index against hardcoded thresholds (e.g., `index < 0.3 = LOW`, `index > 0.7 = HIGH`) to output discrete categorical predictions for the order flow.

### 3. Decision Agent
**Role:** Acts as the penultimate decision engine, calculating the final, actionable rider deployment strategy.

**How it works:**
- **Input Integration:** Ingests the fuzzified membership degrees calculated by the Prediction Agent (specifically the degrees of KPT, RWT, and Order Flow).
- **Cascade Fuzzy Inference:** Executes a multi-stage rule base to deduce operational actions:
  - **Step 1 (System State):** Evaluates KPT and RWT to determine if the logistics network is `UNDERUTILIZED`, `OPTIMAL`, or `OVERLOADED`. For example, high kitchen times combined with high rider wait times guarantee an `OVERLOADED` state.
  - **Step 2 (Demand Intensity):** Fuses the calculated System State with the Order Flow prediction to evaluate the immediate operational load (`LOW`, `MEDIUM`, or `HIGH`).
  - **Step 3 (Allocation Strategy):** Maps the Demand Intensity directly to an actionable strategy: `REDUCE`, `HOLD`, or `SCALE UP` riders.
- **Final Defuzzification:** Calculates a continuous decision index using the Centroid method across the Reduce (0.0), Hold (0.5), and Scale-Up (1.0) poles.
- **Actionable Output:** Applies fixed thresholds to generate the final deployment decision. It outputs a comprehensive JSON payload containing the discrete action (`SCALE UP`/`REDUCE`), recommended rider adjustments (e.g., +30 riders), priority zone targeting, and a human-readable list of logic steps explaining exactly *why* the decision was made.
