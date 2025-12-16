import pandas as pd
import sqlite3
import os
import sys

# --- EL TRUCO MÁGICO ---
# Esto asegura que Python encuentre el módulo 'src' sin importar desde dónde lo ejecutes
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# -----------------------

from src.rules import CreditScoringRules
class CreditRiskEngine:
    def __init__(self, db_path="data/processed/scoring_results.db"):
        self.rules = CreditScoringRules()
        self.db_path = db_path
        self.raw_data = None
        
    def ingest_data(self, filepath):
        """
        Paso 1: Ingesta (Extract)
        Lee el archivo CSV raw.
        """
        print(f"📥 Leyendo datos desde: {filepath}")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo {filepath} no existe.")
            
        self.raw_data = pd.read_csv(filepath)
        print(f"   -> {len(self.raw_data)} registros cargados.")

    def run_scoring_pipeline(self):
        """
        Paso 2: Procesamiento (Transform)
        Itera sobre cada cliente y aplica las reglas de negocio.
        """
        print("⚙️ Ejecutando motor de riesgo...")
        results = []

        # Iteramos fila por fila (simulando un proceso caso por caso)
        for index, row in self.raw_data.iterrows():
            applicant_id = row['applicant_id']
            
            # 1. Aplicar Hard Knockouts
            is_rejected, reason = self.rules.check_hard_knockouts(row)
            
            # 2. Si pasa, calcular Score
            score = 0
            if not is_rejected:
                score = self.rules.calculate_score(row)
            
            # Guardamos el resultado estructurado
            results.append({
                'applicant_id': applicant_id,
                'is_rejected': is_rejected,
                'rejection_reason': reason,
                'credit_score': score,
                'original_income': row['annual_income'], # Trazabilidad
                'original_debt': row['current_debt']      # Trazabilidad
            })
            
        return pd.DataFrame(results)

    def save_to_sql(self, df_results):
        """
        Paso 3: Persistencia (Load)
        Guarda los resultados en una base de datos SQLite.
        """
        print(f"💾 Guardando resultados en SQL: {self.db_path}")
        
        # Aseguramos que el directorio exista
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Conexión a SQLite (se crea el archivo si no existe)
        conn = sqlite3.connect(self.db_path)
        
        # Guardar tabla (si existe, la reemplaza para este ejercicio)
        df_results.to_sql('risk_scoring_results', conn, if_exists='replace', index=False)
        
        conn.close()
        print("✅ Proceso finalizado con éxito.")

# Bloque principal para ejecución directa
if __name__ == "__main__":
    # Rutas relativas
    INPUT_FILE = "data/raw/applicants.csv"
    DB_FILE = "data/processed/scoring_results.db"
    
    engine = CreditRiskEngine(db_path=DB_FILE)
    engine.ingest_data(INPUT_FILE)
    scored_df = engine.run_scoring_pipeline()
    engine.save_to_sql(scored_df)
    
    print("\n--- Vista Previa de Resultados ---")
    print(scored_df.head(10))