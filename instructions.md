# 🚀 Agentic Data Analysis - Setup & Run Instructions

This repository contains a premium, highly responsive real-time logistics analytics suite powered by a **100% deterministic Cascade Fuzzy Logic & Rule-Based Inference System**. No LLMs or black-box machine learning engines are used, guaranteeing explainable, fluid decision-making for rider allocation.

---

## 🛠️ System Architecture

- **Backend:** FastAPI (Python 3.8+) serving real-time validation endpoints.
- **Frontend:** Flutter Web (Dart VM / WASM compiling) supporting instant offline recalculations at 60fps on slider changes.
- **Prediction Agent:** Predicts system Order Flow based on `Time of Day` and `Customer Rating`.
- **Decision Agent:** Computes final logistics resource allocation (`REDUCE`, `HOLD`, `SCALE UP`) based on `KPT`, `RWT`, and the computed `Order Flow`.

---

## 📥 Prerequisites

Ensure the following tools are installed on your development system:
1. **Python 3.8+** (along with `pip3`)
2. **Flutter SDK** (Channel Stable)
3. **Google Chrome** (for debug web hosting)

---

## ⚙️ Step-by-Step Run Instructions

### 🐍 1. Spin Up the FastAPI Backend

Open a terminal window and navigate to the `backend/` directory:

```bash
# 1. Move to backend folder
cd backend

# 2. Install dependencies (FastAPI, Uvicorn, Pandas, WatchFiles)
pip3 install -r requirements.txt

# Or manually install core modules:
pip3 install fastapi uvicorn pandas watchfiles python-multipart

# 3. Start the reload-enabled development server
uvicorn main:app --reload --port 8000
```

The backend API will be online at: **`http://localhost:8000`**

---

### 💙 2. Run the Flutter Web Frontend

Open a new terminal window and navigate to the `data-analysis-agent/` directory:

#### **Option A: Run in Development Mode (Live Hot-Reload)**

Use this mode for rapid debugging and live code updates:

```bash
# 1. Move to the frontend folder
cd data-analysis-agent

# 2. Retrieve Flutter packages
flutter pub get

# 3. Launch debug mode inside Google Chrome on port 8080
flutter run -d chrome --web-port 8080
```

*Press `r` inside the terminal window to hot-reload after making code modifications.*

---

#### **Option B: Run in Production Mode (Optimized Static Hosting)**

Use this mode to evaluate the compiled release bundle served directly over local hosting:

```bash
# 1. Move to the frontend folder
cd data-analysis-agent

# 2. Build the optimized static release build
flutter build web --release

# 3. Move to the compiled build output folder
cd build/web

# 4. Host the production bundle locally using Python
python3 -m http.server 8080
```

Your high-performance production static build will be online at: **`http://localhost:8080`**

---

## 🧪 System Diagnostics & Testing Guide

Once running, you can evaluate the cascade solver using these key testing scenarios:

### 📉 Scenario A: Low Logistics Pressure (Triggers `REDUCE`)
- **Action:** Drag `Time` and `Rating` down to 0.0. Drag `KPT` and `RWT` below `0.15`.
- **System Behavior:** System State transitions instantly to **`UNDERUTILIZED`**, demand intensity settles at **`LOW`**, Centroid Index stays `< 0.300`, and the decision displays **`REDUCE`**.

### ⚖️ Scenario B: Stable Equilibrium (Triggers `HOLD`)
- **Action:** Drag all inputs to their neutral centers (`0.50`).
- **System Behavior:** System State transitions to **`OPTIMAL`**, demand intensity settles at **`MEDIUM`**, Centroid Index matches `0.500`, and the decision displays **`HOLD`**.

### 📈 Scenario C: Logistic Overload (Triggers `SCALE UP`)
- **Action:** Drag `Time` and `Rating` to 1.0. Drag `KPT` and `RWT` above `0.85`.
- **System Behavior:** System State transitions to **`OVERLOADED`**, demand intensity settles at **`HIGH`**, Centroid Index peaks near `1.000`, and the decision displays **`SCALE UP`**.

---

## 💻 Output JSON Schema

When evaluating the **Real-Time Output JSON** drawer on the dashboard, the data matches this explicit structural design:

```json
{
  "decision_index": 0.75,
  "action": "SCALE UP",
  "system_state": "OVERLOADED",
  "demand_intensity": "HIGH",
  "confidence": 0.25,
  "reason": "High KPT + High RWT + High Order Flow → OVERLOADED system state → HIGH demand intensity → SCALE UP required"
}
```
