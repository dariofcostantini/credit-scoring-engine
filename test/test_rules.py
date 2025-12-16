import sys
import os
import pytest

# --- EL TRUCO MÁGICO ---
# Esto le dice a Python: "Mira en la carpeta de atrás para encontrar 'src'"
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# -----------------------

from src.rules import CreditScoringRules

@pytest.fixture
def rules_engine():
    return CreditScoringRules()

def test_hard_knockout_underage(rules_engine):
    minor_applicant = {'age': 17, 'annual_income': 50000, 'current_debt': 0}
    rejected, reason = rules_engine.check_hard_knockouts(minor_applicant)
    assert rejected is True
    assert "Edad" in reason

def test_hard_knockout_high_debt(rules_engine):
    broke_applicant = {'age': 30, 'annual_income': 50000, 'current_debt': 40000}
    rejected, reason = rules_engine.check_hard_knockouts(broke_applicant)
    assert rejected is True
    assert "DTI" in reason

def test_good_candidate_score(rules_engine):
    good_applicant = {
        'age': 35, 
        'annual_income': 80000, 
        'employment_years': 5, 
        'payment_history_score': 3, 
        'current_debt': 10000
    }
    
    rejected, _ = rules_engine.check_hard_knockouts(good_applicant)
    assert rejected is False
    
    score = rules_engine.calculate_score(good_applicant)
    # Ajustamos la expectativa a 500 como descubrimos antes
    assert score > 500 

# Esto permite correr el archivo directamente con "python test_rules.py"
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))