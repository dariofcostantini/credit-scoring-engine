class CreditScoringRules:
    """
    Motor de reglas de negocio para evaluación de crédito.
    Separa la política de riesgo (reglas) de la ejecución técnica.
    """
    
    def __init__(self):
        # Configuración base del scorecard
        self.base_score = 300
        self.max_score = 850
    
    def check_hard_knockouts(self, applicant):
        """
        Aplica reglas de exclusión inmediata (Hard Knockouts).
        Retorna: (is_rejected: bool, reason: str)
        """
        # 1. Regla de Edad: Solo entre 18 y 75 años
        if applicant['age'] < 18 or applicant['age'] > 75:
            return True, "RECHAZO: Edad fuera de rango permitido"
            
        # 2. Regla de Calidad de Datos: Ingresos no pueden ser negativos
        if applicant['annual_income'] < 0:
            return True, "RECHAZO: Error en datos de ingresos"
            
        # 3. Regla de Solvencia: Ratio Deuda/Ingreso (DTI)
        # Si la deuda supera el 60% del ingreso anual, es muy riesgoso.
        if applicant['annual_income'] > 0:
            dti = applicant['current_debt'] / applicant['annual_income']
            if dti > 0.60:
                return True, f"RECHAZO: DTI demasiado alto ({dti:.2f})"
        
        return False, "OK"

    def calculate_score(self, applicant):
        """
        Calcula un credit score simplificado basado en factores de riesgo.
        Solo se ejecuta si el candidato pasó los Knockouts.
        """
        score = self.base_score
        
        # Factor 1: Ingresos (Más ingresos = más puntos, hasta un tope)
        # Añadimos 1 punto por cada 1000 unidades de ingreso, tope 200 puntos
        income_points = min(applicant['annual_income'] / 1000, 200)
        score += income_points
        
        # Factor 2: Historial de Pagos (El factor más fuerte)
        # 0: Malo, 1: Regular, 2: Bueno, 3: Excelente
        payment_history_map = {
            0: -100, # Penalización fuerte
            1: 0,
            2: 50,
            3: 100
        }
        score += payment_history_map.get(applicant['payment_history_score'], 0)
        
        # Factor 3: Estabilidad Laboral
        # 5 puntos por cada año trabajado, tope 100 puntos
        employment_points = min(applicant['employment_years'] * 5, 100)
        score += employment_points
        
        # Normalización final (asegurar que no pase de 850 ni baje de 300)
        return int(min(max(score, 300), 850))