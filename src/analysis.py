import logging
import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# Ruta default a la base de datos (relativa al proyecto)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'scoring_results.db')

# Constantes de análisis
TOP_REJECTION_REASONS = 5


def load_scoring_results(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Lee los resultados de scoring desde la base de datos SQLite.

    Args:
        db_path: Ruta al archivo SQLite con los resultados.

    Returns:
        DataFrame con todos los registros de la tabla risk_scoring_results.

    Raises:
        FileNotFoundError: Si la base de datos no existe.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No se encontró la base de datos en {db_path}")

    with sqlite3.connect(db_path) as conn:
        scoring_results = pd.read_sql_query("SELECT * FROM risk_scoring_results", conn)

    logger.info("Cargados %d registros desde %s", len(scoring_results), db_path)
    return scoring_results


def analyze_results(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Analiza el portafolio de riesgo e imprime un resumen por consola.

    Lee los resultados de scoring, calcula estadísticas de aprobación/rechazo,
    e identifica las principales causas de rechazo.

    Args:
        db_path: Ruta al archivo SQLite con los resultados.

    Returns:
        DataFrame con los resultados completos (para uso posterior, ej: gráficos).
    """
    logger.info("ANALIZANDO PORTAFOLIO DE RIESGO...")

    scoring_results = load_scoring_results(db_path)

    # Resumen de aprobación/rechazo con score promedio
    approval_summary = scoring_results.groupby('is_rejected').agg(
        {'credit_score': ['count', 'mean']}
    )
    print("\n--- Resumen de Aprobación ---")
    print(approval_summary)

    # Principales causas de rechazo
    rejected_mask = scoring_results['is_rejected'] == 1
    rejection_reasons = (
        scoring_results[rejected_mask]['rejection_reason']
        .value_counts()
        .head(TOP_REJECTION_REASONS)
    )
    print("\n--- Principales Causas de Rechazo ---")
    print(rejection_reasons)

    return scoring_results


def plot_score_distribution(
    df: pd.DataFrame,
    save_path: str | None = None,
) -> None:
    """Genera un histograma de la distribución de credit scores de aprobados.

    Args:
        df: DataFrame con los resultados de scoring (debe incluir
            columnas 'is_rejected' y 'credit_score').
        save_path: Si se provee, guarda el gráfico en esta ruta en vez de mostrarlo.
    """
    approved_scores = df[df['is_rejected'] == 0]['credit_score']

    plt.figure(figsize=(10, 6))
    sns.histplot(approved_scores, kde=True, color='green')
    plt.title('Distribución de Credit Scores (Aprobados)')
    plt.xlabel('Puntaje')
    plt.ylabel('Frecuencia de Clientes')

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info("Gráfico guardado en %s", save_path)
    else:
        plt.show()

    plt.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    scoring_df = analyze_results()
    plot_score_distribution(scoring_df)