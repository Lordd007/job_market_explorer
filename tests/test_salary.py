from utils.salary import normalize_salary


def test_salary_norm():
    assert normalize_salary(50, 60, "USD", "hourly") == 114400
    assert normalize_salary(100000, 120000, "USD", "yearly") == 110000
