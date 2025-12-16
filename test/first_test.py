# Importamos la clase que acabas de crear dentro de la carpeta src
from src.rules import CreditScoringRules

# Intentamos inicializar las reglas
try:
    reglas = CreditScoringRules()
    print("--------------------------------------------------")
    print("✅ ÉXITO: El archivo rules.py se ha leído correctamente.")
    print("--------------------------------------------------")
except Exception as e:
    print("❌ ERROR: Algo falló.")
    print(e)