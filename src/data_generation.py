import pandas as pd
import numpy as np
import random

def generate_mock_data(num_records=1000):
    """
    Genera un dataset ficticio de solicitantes de crédito.
    """
    np.random.seed(42) # Para reproducibilidad

    data = {
        'applicant_id': range(1000, 1000 + num_records),
        'age': np.random.randint(18, 75, num_records),
        'annual_income': np.random.normal(55000, 15000, num_records).astype(int),
        'employment_years': np.random.randint(0, 40, num_records),
        'current_debt': np.random.randint(0, 20000, num_records),
        'loan_amount_requested': np.random.randint(1000, 50000, num_records),
        
        # Historial de pagos: 0 (malo), 1 (regular), 2 (bueno), 3 (excelente)
        'payment_history_score': np.random.choice([0, 1, 2, 3], num_records, p=[0.1, 0.2, 0.4, 0.3])
    }
    
    df = pd.DataFrame(data)

    # Introducir algunos casos extremos para probar reglas de "Hard Knockout"
    # Caso 1: Ingresos negativos (Error de datos)
    df.loc[0:5, 'annual_income'] = -100
    
    # Caso 2: Menores de edad (Fraude/Error)
    df.loc[6:10, 'age'] = 17
    
    # Caso 3: Deuda excesiva
    df.loc[11:15, 'current_debt'] = 1000000

    return df

if __name__ == "__main__":
    print("Generando datos ficticios...")
    df_applicants = generate_mock_data()
    
    # Guardar en la carpeta data/raw
    output_path = "../data/raw/applicants.csv"
    # Ajusta la ruta si ejecutas desde dentro de src/ o desde la raíz
    try:
        df_applicants.to_csv(output_path, index=False)
        print(f"Datos guardados exitosamente en {output_path}")
        print(df_applicants.head())
    except OSError:
        # Fallback por si la carpeta no existe (para testing rápido)
        df_applicants.to_csv("applicants.csv", index=False)
        print("Carpeta no encontrada, guardado en directorio actual como applicants.csv")