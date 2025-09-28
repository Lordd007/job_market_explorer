import random, datetime as dt, json
import pandas as pd

skills = ["python", "sql", "aws", "pandas", "kubernetes"]
start = dt.date.today() - dt.timedelta(weeks=12)

rows = []
for skill in skills:
    count = random.randint(20, 50)
    for week in range(12):
        rows.append({
            "skill": skill,
            "week": (start + dt.timedelta(weeks=week)).isoformat(),
            "count": count + random.randint(-5, 10)
        })

with open("data/mock_trends.json", "w") as f:
    json.dump(rows, f, indent=2)
