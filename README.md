# Credit Risk Scoring Engine

A Python-based ETL pipeline that simulates a bank's credit decisioning process. It processes loan applications, applies regulatory and risk logic (Hard Knockouts), and calculates a credit score based on financial history.

## Project Overview

This project bridges the gap between **Financial Risk Management** and **Data Engineering**. It demonstrates how to translate business credit policies into clean, testable, and modular Python code.

### Key Features
* **ETL Pipeline:** Ingests raw CSV data -> Transforms via Business Logic -> Loads into SQLite.
* **Risk Engine:** Implements "Hard Knockouts" (e.g., Debt-to-Income ratio > 0.60) and scoring models.
* **Defensive Programming:** Handles data quality issues (negative income, missing values).
* **Unit Testing:** Automated tests using `pytest` to ensure regulatory compliance of the code.

## Tech Stack
* **Language:** Python 3.9+
* **Data Manipulation:** Pandas, NumPy
* **Database:** SQLite (SQL querying)
* **Testing:** Pytest

## Structure
```text
├── data/               # Raw and Processed data (SQLite DB)
├── src/                # Source code
│   ├── engine.py       # Main ETL Orchestrator
│   ├── rules.py        # Business Logic (Separation of Concerns)
│   └── analysis.py     # SQL Reporting script
├── tests/              # Automated Unit Tests
└── requirements.txt    # Dependencies