from utils.seniority import infer_seniority


def test_seniority():
    assert infer_seniority("Senior Data Analyst") == "senior"
    assert infer_seniority("Lead Engineer") == "lead"
    assert infer_seniority("Data Manager") == "manager"
    assert infer_seniority("Junior Analyst") == "entry"
    assert infer_seniority("Data Analyst") == "mid"


