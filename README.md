# 🏦 Credit Risk Scoring Engine

A Python-based **ETL pipeline** that simulates a bank's credit decisioning process. It processes loan applications, applies regulatory and risk logic through **Hard Knockouts**, and calculates a credit score with **probability of default** using a calibrated sigmoid model.

---

## 📋 Project Overview

This project bridges **Financial Risk Management** and **Data Engineering**, demonstrating how to translate real-world credit policies — inspired by the Argentine financial system (BCRA regulations, Nosis bureau data) — into clean, modular, and testable Python code.

### Key Features

| Feature | Description |
|---------|-------------|
| **ETL Pipeline** | Ingests Excel data → Transforms via business rules → Loads into SQLite |
| **Hard Knockouts** | Automatic rejection rules: age limits, BCRA status, DSTI ratio, residual income |
| **Credit Scoring** | Multi-factor scoring model (base 400, range 1–999) with 6 weighted risk components |
| **Probability of Default** | Sigmoid-based PD mapping calibrated at a 350-score midpoint |
| **Solvency Analysis** | Advanced Debt-Service-To-Income (DSTI) and residual income calculations |
| **Portfolio Analytics** | SQL-based reporting with score distribution charts (Matplotlib/Seaborn) |
| **Synthetic Data Generator** | 2,000 realistic applicant records with injected edge cases for validation |

---

## 🏗️ Architecture

```
credit-scoring-engine/
│
├── src/                         # Source code
│   ├── engine.py                # ETL Orchestrator (Extract → Transform → Load)
│   ├── rules.py                 # Business rules engine (Knockouts + Scoring + PD)
│   ├── data_generation.py       # Synthetic data generator with edge cases
│   └── analysis.py              # SQL reporting & score distribution plots
│
├── data/
│   ├── raw/                     # Input data (Excel files)
│   └── processed/               # Output database (SQLite)
│
├── .gitignore
└── README.md
```

---

## ⚙️ How It Works

### Pipeline Flow

```
┌──────────────────┐     ┌───────────────────────┐     ┌──────────────────┐
│   1. EXTRACT     │     │     2. TRANSFORM       │     │     3. LOAD      │
│                  │     │                         │     │                  │
│  Read .xlsx      │────▶│  Hard Knockouts         │────▶│  Save to SQLite  │
│  Validate cols   │     │  Credit Score (1-999)   │     │  risk_scoring_   │
│                  │     │  PD Sigmoid Mapping     │     │  results table   │
└──────────────────┘     └───────────────────────┘     └──────────────────┘
```

### Hard Knockout Rules

Automatic rejection filters — if any condition is met, the applicant is **immediately rejected** with no score calculated:

| Rule | Condition | Rationale |
|------|-----------|-----------|
| Age | `< 18` or `> 75` | Legal/actuarial limits |
| BCRA Status | Current situation `> 2` | Active delinquency |
| BCRA History | Worst historical status `> 3` | Severe past defaults |
| DSTI | Debt-service-to-income `> 45%` | Over-indebtedness |
| Residual Income | Monthly remainder `< $12,000` | Below subsistence threshold |

### Scoring Model (6 Factors)

For approved applicants, the score starts at **400** and is adjusted by:

| Factor | Component | Effect |
|--------|-----------|--------|
| 1 | **Age** (lifecycle) | +50 if between 35–55 |
| 2 | **Employment stability** | +5/year (max +50) + 10/month contributions |
| 3 | **Payment history** (Nosis) | -200 to +150 based on bureau score |
| 4 | **BCRA status** | +100 (Sit. 1) or -100 (Sit. 2) |
| 5 | **DSTI** (non-linear) | -(DSTI² × 800) penalty |
| 6 | **Residual income** | Up to +100 based on available cash |

### Probability of Default

The final score is mapped to a PD using a **logistic sigmoid**:

```
PD = 1 / (1 + e^(0.012 × (score - 350)))
```

Where 350 is the calibrated midpoint (50% default probability).

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/dariofcostantini/credit-scoring-engine.git
cd credit-scoring-engine

# Install dependencies
pip install pandas numpy openpyxl matplotlib seaborn
```

### Usage

```bash
# Step 1: Generate synthetic applicant data
python -m src.data_generation

# Step 2: Run the scoring engine (ETL pipeline)
python -m src.engine

# Step 3: Analyze results and generate charts
python -m src.analysis
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.10+ |
| Data Manipulation | Pandas, NumPy |
| Database | SQLite |
| Visualization | Matplotlib, Seaborn |
| Data Format | openpyxl (Excel I/O) |

---

## 📊 Sample Output

After running the pipeline, the analysis module produces:

- **Approval/Rejection summary** with average scores per group
- **Top rejection reasons** ranked by frequency
- **Score distribution histogram** (KDE) for approved applicants

---

## 🧠 What I Learned

- Translating **financial regulations** (BCRA, Nosis) into deterministic code
- Designing **separation of concerns**: business rules isolated from orchestration
- Building a complete **ETL pipeline** with validation and error handling
- Using **named constants** instead of magic numbers for maintainability
- Applying **defensive programming**: column validation, file existence checks, context managers
- Modeling **probability of default** with calibrated sigmoid functions

---

## 📝 License

This project is for educational and portfolio purposes.

---

## 👤 Author

**Dario Costantini** — [GitHub](https://github.com/dariofcostantini)