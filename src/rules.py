import math

import pandas as pd


class CreditScoringRules:
    """Motor de reglas de negocio para scoring crediticio.

    Centraliza todas las reglas de decisión (hard knockouts, scoring,
    probabilidad de default) y sus parámetros configurables.
    """

    # --- Constantes de Score ---
    BASE_SCORE = 400
    MAX_SCORE = 999
    MIN_SCORE = 1

    # --- Constantes de Solvencia ---
    SUBSISTENCE_THRESHOLD = 12_000       # Canasta básica mensual (ARS)
    MONTHLY_DEBT_RATE = 0.10             # % del capital adeudado como cuota mensual estimada
    MAX_DSTI_RATIO = 0.45                # Debt-Service-To-Income máximo antes de rechazo

    # --- Hard Knockout: Edad ---
    MIN_ALLOWED_AGE = 18
    MAX_ALLOWED_AGE = 75

    # --- Hard Knockout: BCRA ---
    MAX_ALLOWED_BCRA_STATUS = 2          # Situaciones > 2 se rechazan
    MAX_ALLOWED_HISTORICAL_BCRA = 3      # Historial >= 4 se rechaza

    # --- Scoring: Pesos por factor ---
    AGE_BONUS = 50                       # Premio por rango de edad óptimo (35-55)
    OPTIMAL_AGE_MIN = 35
    OPTIMAL_AGE_MAX = 55

    EMPLOYMENT_POINTS_PER_YEAR = 5
    MAX_EMPLOYMENT_BONUS = 50
    CONTRIBUTION_POINTS_PER_MONTH = 10   # Puntos por mes de aportes

    BCRA_SIT1_BONUS = 100                # Premio por situación BCRA = 1
    BCRA_SIT2_PENALTY = 100              # Castigo por situación BCRA = 2

    DSTI_PENALTY_MULTIPLIER = 800        # Multiplicador de penalización no-lineal por DSTI
    RESIDUAL_INCOME_DIVISOR = 15_000     # Divisor para normalizar ingreso residual
    MAX_RESIDUAL_INCOME_BONUS = 100

    PAYMENT_HISTORY_SCORE_MAP = {
        0: -200,
        1: -50,
        2: 50,
        3: 150,
    }

    # --- Probabilidad de Default (Sigmoide) ---
    PD_SIGMOID_K = 0.012
    PD_SIGMOID_MIDPOINT = 350            # Score en el punto de inflexión del riesgo

    def calculate_advanced_solvency(self, applicant: pd.Series) -> tuple[float, float]:
        """Analiza el flujo de caja mensual del solicitante.

        Args:
            applicant: Fila del DataFrame con los datos del solicitante.

        Returns:
            Tupla (debt_service_to_income, residual_income):
                - debt_service_to_income: ratio de carga financiera sobre ingreso.
                - residual_income: ingreso mensual disponible luego de cuotas.
        """
        monthly_income = applicant['annual_income'] / 12
        # Estimación de carga financiera: % del capital adeudado como cuota mensual
        estimated_monthly_payment = applicant['current_debt'] * self.MONTHLY_DEBT_RATE

        debt_service_to_income = estimated_monthly_payment / max(monthly_income, 1)
        residual_income = monthly_income - estimated_monthly_payment

        return debt_service_to_income, residual_income

    def _analyze_bcra_history(self, history_str: str) -> tuple[int, int]:
        """Analiza la cadena de historial BCRA y devuelve métricas de riesgo.

        Args:
            history_str: String con formato "1|1|2|1|..." (12 meses de situación BCRA).

        Returns:
            Tupla (worst_bcra_status, status_changes):
                - worst_bcra_status: peor situación registrada en el período.
                - status_changes: cantidad de veces que cambió de situación (volatilidad).
        """
        history_list = [int(x) for x in str(history_str).split('|')]
        worst_bcra_status = max(history_list)
        # Volatilidad: cuántas veces cambió de situación en 12 meses
        status_changes = sum(
            1 for i in range(len(history_list) - 1)
            if history_list[i] != history_list[i + 1]
        )
        return worst_bcra_status, status_changes

    def check_hard_knockouts(self, applicant: pd.Series) -> tuple[bool, str]:
        """Aplica filtros de exclusión definitiva (hard knockouts).

        Evalúa reglas que causan rechazo automático e inmediato,
        sin posibilidad de compensación por otros factores.

        Args:
            applicant: Fila del DataFrame con los datos del solicitante.

        Returns:
            Tupla (is_rejected, reason): True si se rechaza, con el motivo.
        """
        # 1. Regla de Edad
        if applicant['age'] < self.MIN_ALLOWED_AGE or applicant['age'] > self.MAX_ALLOWED_AGE:
            return True, "RECHAZO: Edad fuera de rango"

        # 2. Situación BCRA Crítica
        worst_bcra_status, _ = self._analyze_bcra_history(applicant['historial_bcra'])

        if applicant['situation_bcra'] > self.MAX_ALLOWED_BCRA_STATUS:
            return True, f"RECHAZO: Morosidad actual ({applicant['situation_bcra']})"
        if worst_bcra_status > self.MAX_ALLOWED_HISTORICAL_BCRA:
            return True, f"RECHAZO: Antecedente grave en historial (Sit. {worst_bcra_status})"

        # 3. Solvencia Avanzada (DSTI y Residual)
        debt_service_to_income, residual_income = self.calculate_advanced_solvency(applicant)

        if debt_service_to_income > self.MAX_DSTI_RATIO:
            return True, f"RECHAZO: DSTI crítico ({debt_service_to_income:.2%})"

        if residual_income < self.SUBSISTENCE_THRESHOLD:
            return True, f"RECHAZO: Ingreso residual insuficiente (${residual_income:.0f})"

        return False, "OK"

    def calculate_score(self, applicant: pd.Series) -> tuple[int, float]:
        """Calcula el credit score mediante ponderación multivariable del riesgo.

        Args:
            applicant: Fila del DataFrame con los datos del solicitante.

        Returns:
            Tupla (final_score, probability_of_default):
                - final_score: puntaje crediticio entre MIN_SCORE y MAX_SCORE.
                - probability_of_default: probabilidad estimada de impago (0 a 1).
        """
        score = self.BASE_SCORE
        debt_service_to_income, residual_income = self.calculate_advanced_solvency(applicant)

        # FACTOR 1: Edad (Ajuste por ciclo de vida)
        # Se premia la madurez financiera (rango óptimo)
        if self.OPTIMAL_AGE_MIN <= applicant['age'] <= self.OPTIMAL_AGE_MAX:
            score += self.AGE_BONUS

        # FACTOR 2: Estabilidad Laboral (Años de empleo + Aportes)
        score += min(applicant['employment_years'] * self.EMPLOYMENT_POINTS_PER_YEAR,
                     self.MAX_EMPLOYMENT_BONUS)
        score += applicant['meses_aportes'] * self.CONTRIBUTION_POINTS_PER_MONTH

        # FACTOR 3: Comportamiento de Pago (Historial Nosis)
        score += self.PAYMENT_HISTORY_SCORE_MAP.get(applicant['payment_history_score'], 0)

        # FACTOR 4: Situación BCRA (Premio/Castigo)
        if applicant['situation_bcra'] == 1:
            score += self.BCRA_SIT1_BONUS
        elif applicant['situation_bcra'] == 2:
            score -= self.BCRA_SIT2_PENALTY

        # FACTOR 5: Solvencia Dinámica (DSTI)
        # Penalización no lineal: el impacto es mayor cuanto más alto es el DSTI
        score -= (debt_service_to_income ** 2) * self.DSTI_PENALTY_MULTIPLIER

        # FACTOR 6: Capacidad Nominal (Ingreso Residual)
        score += min(residual_income / self.RESIDUAL_INCOME_DIVISOR,
                     self.MAX_RESIDUAL_INCOME_BONUS)

        # AJUSTE FINAL: Rango MIN_SCORE a MAX_SCORE
        final_score = int(min(max(score, self.MIN_SCORE), self.MAX_SCORE))

        # CÁLCULO DE PD
        probability_of_default = self._map_score_to_pd(final_score)

        return final_score, probability_of_default

    def _map_score_to_pd(self, score: int) -> float:
        """Mapea un credit score a una probabilidad de default usando una sigmoide.

        Usa una función logística calibrada donde el punto de inflexión
        (50% de probabilidad) se ubica en PD_SIGMOID_MIDPOINT.

        Args:
            score: Credit score (entre MIN_SCORE y MAX_SCORE).

        Returns:
            Probabilidad de default entre 0 y 1, redondeada a 4 decimales.
        """
        probability = 1 / (1 + math.exp(self.PD_SIGMOID_K * (score - self.PD_SIGMOID_MIDPOINT)))
        return round(probability, 4)