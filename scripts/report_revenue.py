import csv, sys
from collections import defaultdict
from datetime import datetime

metrics = defaultdict(lambda: {"spend": 0.0, "tweets": 0})
with open("logs/metrics.csv") as f:
    for row in csv.reader(f):
        ts, name, value = row
        day = datetime.fromisoformat(ts).date().isoformat()
        if name == "api_spend_usd":
            metrics[day]["spend"] += float(value)
        if name == "tweets_published":
            metrics[day]["tweets"] += int(value)
for day, m in metrics.items():
    print(f"{day}: ROI = {m['tweets']}/{m['spend']:.2f}") 