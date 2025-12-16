import sqlite3
import pandas as pd
import os

# Ajuste de rutas para ejecutar directo
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_path = os.path.join(parent_dir, 'data', 'processed', 'scoring_results.db')

def analyze_results():
    print("📊 ANALIZANDO PORTAFOLIO DE RIESGO...")
    
    conn = sqlite3.connect(db_path)
    
    # Query 1: Tasa de Aprobación vs Rechazo
    query_summary = """
    SELECT 
        is_rejected, 
        COUNT(*) as count,
        AVG(credit_score) as avg_score
    FROM risk_scoring_results
    GROUP BY is_rejected
    """
    df_summary = pd.read_sql_query(query_summary, conn)
    
    print("\n--- Resumen de Aprobación ---")
    print(df_summary)
    
    # Query 2: Top 5 Causas de Rechazo
    query_reasons = """
    SELECT rejection_reason, COUNT(*) as count
    FROM risk_scoring_results
    WHERE is_rejected = 1
    GROUP BY rejection_reason
    ORDER BY count DESC
    LIMIT 5
    """
    df_reasons = pd.read_sql_query(query_reasons, conn)
    
    print("\n--- Principales Causas de Rechazo ---")
    print(df_reasons)
    
    conn.close()

if __name__ == "__main__":
    analyze_results()