import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# --- Constantes de Generación de Datos ---

RANDOM_SEED = 42
DEFAULT_NUM_RECORDS = 2000
FIRST_APPLICANT_ID = 1000

# Distribución de estados BCRA (calibrada para reflejar la realidad argentina)
BCRA_STATUS_VALUES = [1, 2, 3, 4, 5, 6]
BCRA_STATUS_PROBABILITIES = [0.96, 0.02, 0.01, 0.004, 0.003, 0.003]
BCRA_HISTORY_MONTHS = 12

# Parámetros demográficos y financieros
MIN_AGE = 18
MAX_AGE = 75
MEAN_ANNUAL_INCOME = 540_000
STD_ANNUAL_INCOME = 150_000
MAX_EMPLOYMENT_YEARS = 40
MAX_CONTRIBUTION_MONTHS = 13          # meses_aportes: 0 a 12
MAX_CURRENT_DEBT = 200_000
MIN_LOAN_AMOUNT = 1_000
MAX_LOAN_AMOUNT = 50_000

# Distribución del historial de pagos (Nosis)
PAYMENT_SCORE_VALUES = [0, 1, 2, 3]
PAYMENT_SCORE_PROBABILITIES = [0.1, 0.2, 0.4, 0.3]

# --- Ruta de salida ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "applicants.xlsx")


def _generate_bcra_histories(num_records: int) -> list[str]:
    """Genera historiales BCRA simulados de 12 meses para cada solicitante.

    Cada historial es un string con formato "1|1|2|1|..." que representa
    la situación BCRA mensual durante el último año.

    Args:
        num_records: Cantidad de historiales a generar.

    Returns:
        Lista de strings con formato "estado1|estado2|...|estado12".
    """
    histories = []
    for _ in range(num_records):
        monthly_statuses = np.random.choice(
            BCRA_STATUS_VALUES, BCRA_HISTORY_MONTHS, p=BCRA_STATUS_PROBABILITIES
        )
        history_str = "|".join(map(str, monthly_statuses))
        histories.append(history_str)
    return histories


def _inject_edge_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Introduce casos extremos para validar reglas de Hard Knockout.

    Modifica las primeras filas del DataFrame para crear escenarios
    que deberían ser rechazados automáticamente por el motor de riesgo.

    Args:
        df: DataFrame de solicitantes generados.

    Returns:
        DataFrame con los edge cases inyectados.
    """
    # Caso 1: Ingresos negativos (simula error de datos)
    df.loc[0:5, 'annual_income'] = -100

    # Caso 2: Menores de edad (simula fraude o error de carga)
    df.loc[6:10, 'age'] = 15

    # Caso 3: Deuda excesiva (simula sobre-endeudamiento extremo)
    df.loc[11:15, 'current_debt'] = 1_000_000

    return df


def generate_mock_data(num_records: int = DEFAULT_NUM_RECORDS) -> pd.DataFrame:
    """Genera un dataset ficticio de solicitantes de crédito.

    Crea datos aleatorios pero reproducibles (seed fijo) que simulan
    un portafolio realista de solicitantes argentinos, incluyendo
    edge cases para validación del motor de reglas.

    Args:
        num_records: Cantidad de solicitantes a generar.

    Returns:
        DataFrame con los datos de solicitantes, incluyendo edge cases.
    """
    np.random.seed(RANDOM_SEED)

    bcra_histories = _generate_bcra_histories(num_records)

    data = {
        'applicant_id': range(FIRST_APPLICANT_ID, FIRST_APPLICANT_ID + num_records),
        'cuit': [
            f"20{np.random.randint(10000000, 45000000)}{np.random.randint(0, 9)}"
            for _ in range(num_records)
        ],
        'age': np.random.randint(MIN_AGE, MAX_AGE, num_records),
        'annual_income': np.random.normal(
            MEAN_ANNUAL_INCOME, STD_ANNUAL_INCOME, num_records
        ).astype(int),
        'situation_bcra': [int(h.split('|')[-1]) for h in bcra_histories],
        'historial_bcra': bcra_histories,
        'employment_years': np.random.randint(0, MAX_EMPLOYMENT_YEARS, num_records),
        'meses_aportes': np.random.randint(0, MAX_CONTRIBUTION_MONTHS, num_records),
        'current_debt': np.random.randint(0, MAX_CURRENT_DEBT, num_records),
        'loan_amount_requested': np.random.randint(
            MIN_LOAN_AMOUNT, MAX_LOAN_AMOUNT, num_records
        ),
        'payment_history_score': np.random.choice(
            PAYMENT_SCORE_VALUES, num_records, p=PAYMENT_SCORE_PROBABILITIES
        ),
    }

    df = pd.DataFrame(data)
    df = _inject_edge_cases(df)

    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("Generando datos ficticios...")
    df_applicants = generate_mock_data()

    # Asegurar que el directorio de salida exista
    os.makedirs(os.path.dirname(DEFAULT_OUTPUT_PATH), exist_ok=True)

    df_applicants.to_excel(DEFAULT_OUTPUT_PATH, index=False)
    logger.info("Datos guardados exitosamente en %s", DEFAULT_OUTPUT_PATH)
    logger.info("Primeras 5 filas:")
    print(df_applicants.head())