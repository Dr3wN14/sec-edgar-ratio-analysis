import requests
import json
from pathlib import Path
import time

headers = {
    "User-Agent": "Drew Norris student financial analysis project YOUR-EMAIL"
}

companies = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801"
}

output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

for ticker, cik in companies.items():
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_path = output_dir / f"{ticker}_companyfacts.json"

        with open(file_path, "w") as file:
            json.dump(response.json(), file, indent=2)

        print(f"{ticker}: saved successfully")

    else:
        print(f"{ticker}: request failed with status {response.status_code}")

    time.sleep(0.2)