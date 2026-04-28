import logging
import os
import sqlite3

import pandas as pd

try:
    from .rules import CreditScoringRules          # Cuando se ejecuta como módulo: python -m src.engine
except ImportError:
    from rules import CreditScoringRules            # Cuando se ejecuta directo: python src/engine.py

logger = logging.getLogger(__name__)


class CreditRiskEngine:
    """Orquestador del pipeline ETL de scoring crediticio.

    Coordina las tres fases del proceso:
    1. Ingesta (Extract): lectura de datos raw desde Excel.
    2. Scoring (Transform): aplicación de reglas de negocio.
    3. Persistencia (Load): almacenamiento en SQLite.
    """

    REQUIRED_COLUMNS = {
        'applicant_id', 'age', 'annual_income', 'current_debt',
        'situation_bcra', 'historial_bcra', 'employment_years',
        'meses_aportes', 'payment_history_score',
    }

    DEFAULT_SCORE = 0
    DEFAULT_PD = 1.0  # PD = 1.0 para rechazados (máximo riesgo)

    def __init__(self, db_path: str = "data/processed/scoring_results.db"):
        self.rules = CreditScoringRules()
        self.db_path = db_path
        self.raw_data: pd.DataFrame | None = None

    def ingest_data(self, filepath: str) -> None:
        """Paso 1 — Ingesta (Extract): Lee el archivo XLSX raw.

        Args:
            filepath: Ruta al archivo Excel con los datos de solicitantes.

        Raises:
            FileNotFoundError: Si el archivo no existe en la ruta indicada.
            ValueError: Si el archivo no contiene las columnas requeridas.
        """
        logger.info("Leyendo datos desde: %s", filepath)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo {filepath} no existe.")

        self.raw_data = pd.read_excel(filepath)
        logger.info("%d registros cargados.", len(self.raw_data))

        # Validación de columnas requeridas
        missing_columns = self.REQUIRED_COLUMNS - set(self.raw_data.columns)
        if missing_columns:
            raise ValueError(f"Columnas faltantes en el archivo: {missing_columns}")

    def run_scoring_pipeline(self) -> pd.DataFrame:
        """Paso 2 — Scoring (Transform): Aplica reglas de negocio a cada solicitante.

        Itera sobre cada cliente, aplica hard knockouts y, si pasa,
        calcula el credit score y la probabilidad de default.

        Returns:
            DataFrame con los resultados del scoring por solicitante.

        Raises:
            RuntimeError: Si se ejecuta sin haber cargado datos previamente.
        """
        if self.raw_data is None:
            raise RuntimeError("No hay datos cargados. Ejecutá ingest_data() primero.")

        logger.info("Ejecutando motor de riesgo sobre %d registros...", len(self.raw_data))
        results = []

        for _, row in self.raw_data.iterrows():
            # 1. Aplicar Hard Knockouts
            is_rejected, reason = self.rules.check_hard_knockouts(row)

            # 2. Si pasa, calcular Score
            credit_score = self.DEFAULT_SCORE
            probability_of_default = self.DEFAULT_PD

            if not is_rejected:
                credit_score, probability_of_default = self.rules.calculate_score(row)

            # 3. Guardar resultado estructurado
            results.append({
                'applicant_id': row['applicant_id'],
                'is_rejected': is_rejected,
                'rejection_reason': reason,
                'credit_score': credit_score,
                'probability_of_default': probability_of_default,
                'original_income': row['annual_income'],
                'original_debt': row['current_debt'],
            })

        scored_df = pd.DataFrame(results)
        logger.info("Scoring completado. %d aprobados, %d rechazados.",
                     len(scored_df[~scored_df['is_rejected']]),
                     len(scored_df[scored_df['is_rejected']]))
        return scored_df

    def save_to_sql(self, df_results: pd.DataFrame) -> None:
        """Paso 3 — Persistencia (Load): Guarda resultados en SQLite.

        Args:
            df_results: DataFrame con los resultados del scoring.
        """
        logger.info("Guardando %d resultados en SQL: %s", len(df_results), self.db_path)

        # Aseguramos que el directorio exista
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Context manager garantiza cierre de conexión incluso si hay errores
        with sqlite3.connect(self.db_path) as conn:
            df_results.to_sql('risk_scoring_results', conn, if_exists='replace', index=False)

        logger.info("Proceso finalizado con éxito.")


# Bloque principal para ejecución directa
if __name__ == "__main__":
    # Configurar logging para ejecución por consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    # Rutas relativas (ejecutar desde la raíz del proyecto)
    INPUT_FILE = "data/raw/applicants.xlsx"
    DB_FILE = "data/processed/scoring_results.db"

    engine = CreditRiskEngine(db_path=DB_FILE)
    engine.ingest_data(INPUT_FILE)
    scored_df = engine.run_scoring_pipeline()
    engine.save_to_sql(scored_df)

    logger.info("--- Vista Previa de Resultados ---")
    print(scored_df)